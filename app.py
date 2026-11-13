"""Leave Management API and single-page UI."""
import re
from datetime import date
from pathlib import Path

from flasgger import Swagger
from flask import Flask, abort, jsonify, request, send_from_directory

from src.leave import db
from src.leave.rules import accrued_days, balance, days_in_year, working_days

BASE_DIR = Path(__file__).parent
app = Flask(__name__)
# Swagger UI at /apidocs/, raw spec at /apispec_1.json
swagger = Swagger(app, template={
    "info": {
        "title": "Leave Management API",
        "version": "1.0.0",
        "description": "Employee leave balances and leave requests.",
    },
    "definitions": {
        "EmployeeBalance": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "year": {"type": "integer", "example": 2026},
                "earned_days": {"type": "number", "example": 4.0},
                "carried_days": {"type": "number", "example": 5.0},
                "opening_days": {"type": "number", "example": 0.0},
                "approved_days": {"type": "number", "example": 0.0},
                "available_days": {"type": "number", "example": 9.0},
            },
        },
        "LeaveRequest": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "employee_id": {"type": "integer"},
                "employee_name": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "days": {"type": "integer"},
                "status": {"type": "string", "enum": ["pending", "approved", "rejected"]},
            },
        },
        "NewRequest": {
            "type": "object",
            "required": ["employee_id", "start_date", "end_date"],
            "properties": {
                "employee_id": {"type": "integer"},
                "start_date": {"type": "string", "format": "date", "example": "2026-12-01"},
                "end_date": {"type": "string", "format": "date", "example": "2026-12-03"},
            },
        },
        "CreatedRequest": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "days": {"type": "integer"},
                "status": {"type": "string", "example": "pending"},
            },
        },
        "StatusChange": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "status": {"type": "string", "enum": ["approved", "rejected"]},
            },
        },
        "Error": {
            "type": "object",
            "properties": {"error": {"type": "string"}},
        },
    },
})


# Create any missing tables (CREATE TABLE IF NOT EXISTS, so safe on an existing leave.db).
_conn = db.connect()
try:
    db.init_db(_conn)
finally:
    _conn.close()


def approved_days(conn, employee_id, year):
    """Approved working days inside `year`. A request spanning a year end is split by year."""
    rows = conn.execute(
        "SELECT start_date, end_date FROM leave_requests "
        "WHERE employee_id = ? AND status = 'approved' AND start_date <= ? AND end_date >= ?",
        (employee_id, f"{year}-12-31", f"{year}-01-01"),
    ).fetchall()
    return sum(
        days_in_year(date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"]), year)
        for r in rows
    )


def carried_in(conn, employee_id, year):
    """Days carried into `year` from the carry_forward ledger, 0 if none."""
    row = conn.execute(
        "SELECT carried_days FROM carry_forward WHERE employee_id = ? AND year = ?",
        (employee_id, year),
    ).fetchone()
    return row["carried_days"] if row else 0.0


ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_date(value, field):
    """Parse a strict YYYY-MM-DD string, raising ValueError with a client-facing message."""
    if not isinstance(value, str) or not ISO_DATE.match(value):
        raise ValueError(f"{field} must be a date in YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} is not a valid date") from None


YEAR = re.compile(r"^\d{4}$")


def parse_year(raw):
    """Year from a ?year= value, or the current calendar year when absent."""
    if raw is None:
        return date.today().year
    if not YEAR.match(raw):
        raise ValueError("year must be a 4-digit year")
    return int(raw)


def employee_balance(conn, employee_id, year=None):
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if emp is None:
        abort(404, description="employee not found")
    year = year or date.today().year
    earned = accrued_days(emp["months_worked"])
    carried = carried_in(conn, employee_id, year)
    used = approved_days(conn, employee_id, year)
    available = balance(emp["opening_balance"], emp["months_worked"], used, carried)
    return {
        "id": emp["id"],
        "name": emp["name"],
        "year": year,
        "earned_days": earned,
        "carried_days": carried,
        "opening_days": emp["opening_balance"],
        "approved_days": used,
        "available_days": available,
    }


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/employees")
def list_employees():
    """List all employees with their leave balance for a year.
    ---
    tags: [Employees]
    parameters:
      - name: year
        in: query
        type: integer
        required: false
        description: Calendar year. Defaults to the current year.
    responses:
      400:
        description: Year is not a 4-digit number.
        schema:
          $ref: '#/definitions/Error'
      200:
        description: Employees with balances, ordered by name.
        schema:
          type: array
          items:
            $ref: '#/definitions/EmployeeBalance'
    """
    try:
        year = parse_year(request.args.get("year"))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    conn = db.connect()
    try:
        ids = [r["id"] for r in conn.execute("SELECT id FROM employees ORDER BY name")]
        return jsonify([employee_balance(conn, i, year) for i in ids])
    finally:
        conn.close()


@app.get("/api/employees/<int:employee_id>/balance")
def get_balance(employee_id):
    """Get one employee's available leave balance.
    ---
    tags: [Employees]
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
      - name: year
        in: query
        type: integer
        required: false
        description: Calendar year. Defaults to the current year.
    responses:
      200:
        description: Employee balance, split into earned, carried and approved days.
        schema:
          $ref: '#/definitions/EmployeeBalance'
      400:
        description: Year is not a 4-digit number.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Employee not found.
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        year = parse_year(request.args.get("year"))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    conn = db.connect()
    try:
        return jsonify(employee_balance(conn, employee_id, year))
    finally:
        conn.close()


@app.get("/api/requests")
def list_requests():
    """List all leave requests, newest first.
    ---
    tags: [Requests]
    responses:
      200:
        description: Leave requests with the employee name.
        schema:
          type: array
          items:
            $ref: '#/definitions/LeaveRequest'
    """
    conn = db.connect()
    try:
        rows = conn.execute(
            "SELECT r.*, e.name AS employee_name FROM leave_requests r "
            "JOIN employees e ON e.id = r.employee_id ORDER BY r.id DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/api/requests")
def create_request():
    """Create a pending leave request. Days are working days (Mon-Fri).
    ---
    tags: [Requests]
    consumes: [application/json]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/NewRequest'
    responses:
      201:
        description: Request created as pending.
        schema:
          $ref: '#/definitions/CreatedRequest'
      400:
        description: End date before start date, or not enough balance.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Employee not found.
        schema:
          $ref: '#/definitions/Error'
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="request body must be a JSON object"), 400
    missing = [f for f in ("employee_id", "start_date", "end_date") if f not in body]
    if missing:
        return jsonify(error=f"missing fields: {', '.join(missing)}"), 400
    employee_id = body["employee_id"]
    if not isinstance(employee_id, int) or isinstance(employee_id, bool):
        return jsonify(error="employee_id must be an integer"), 400
    try:
        start = parse_iso_date(body["start_date"], "start_date")
        end = parse_iso_date(body["end_date"], "end_date")
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    if end < start:
        return jsonify(error="end date is before start date"), 400
    days = working_days(start, end)
    conn = db.connect()
    try:
        if conn.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,)).fetchone() is None:
            return jsonify(error="employee not found"), 404
        # FIXME: pending requests are not counted against the balance, so two pending requests can overbook.
        available = employee_balance(conn, employee_id)["available_days"]
        if days > available:
            return jsonify(error=f"requested {days} days but only {available} available"), 400
        cur = conn.execute(
            "INSERT INTO leave_requests (employee_id, start_date, end_date, days) VALUES (?, ?, ?, ?)",
            (employee_id, start.isoformat(), end.isoformat(), days),
        )
        conn.commit()
        return jsonify(id=cur.lastrowid, days=days, status="pending"), 201
    finally:
        conn.close()


def change_status(request_id, new_status):
    conn = db.connect()
    try:
        row = conn.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            abort(404, description="request not found")
        if row["status"] != "pending":
            return jsonify(error=f"request is already {row['status']}"), 409
        if new_status == "approved":
            available = employee_balance(conn, row["employee_id"])["available_days"]
            if row["days"] > available:
                return jsonify(error="insufficient balance"), 409
        conn.execute("UPDATE leave_requests SET status = ? WHERE id = ?", (new_status, request_id))
        conn.commit()
        return jsonify(id=request_id, status=new_status)
    finally:
        conn.close()


# FIXME: no authentication. Any caller can approve or reject. Add a manager check before pilot.
@app.post("/api/requests/<int:request_id>/approve")
def approve(request_id):
    """Approve a pending leave request.
    ---
    tags: [Requests]
    parameters:
      - name: request_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Request approved.
        schema:
          $ref: '#/definitions/StatusChange'
      404:
        description: Request not found.
        schema:
          $ref: '#/definitions/Error'
      409:
        description: Not pending, or insufficient balance.
        schema:
          $ref: '#/definitions/Error'
    """
    return change_status(request_id, "approved")


@app.post("/api/requests/<int:request_id>/reject")
def reject(request_id):
    """Reject a pending leave request.
    ---
    tags: [Requests]
    parameters:
      - name: request_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Request rejected.
        schema:
          $ref: '#/definitions/StatusChange'
      404:
        description: Request not found.
        schema:
          $ref: '#/definitions/Error'
      409:
        description: Request is not pending.
        schema:
          $ref: '#/definitions/Error'
    """
    return change_status(request_id, "rejected")

if __name__ == "__main__":
    app.run(debug=True)
