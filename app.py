"""Leave Management API and single-page UI."""
from datetime import date
from pathlib import Path

from flasgger import Swagger
from flask import Flask, abort, jsonify, request, send_from_directory

from src.leave import db
from src.leave.rules import balance, working_days

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
                "available_days": {"type": "number"},
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


def approved_days(conn, employee_id):
    row = conn.execute(
        "SELECT COALESCE(SUM(days), 0) AS total FROM leave_requests "
        "WHERE employee_id = ? AND status = 'approved'",
        (employee_id,),
    ).fetchone()
    return row["total"]


def employee_balance(conn, employee_id):
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if emp is None:
        abort(404, description="employee not found")
    available = balance(emp["opening_balance"], emp["months_worked"], approved_days(conn, employee_id))
    return {"id": emp["id"], "name": emp["name"], "available_days": available}


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/employees")
def list_employees():
    """List all employees with their available leave balance.
    ---
    tags: [Employees]
    responses:
      200:
        description: Employees with balances, ordered by name.
        schema:
          type: array
          items:
            $ref: '#/definitions/EmployeeBalance'
    """
    conn = db.connect()
    try:
        ids = [r["id"] for r in conn.execute("SELECT id FROM employees ORDER BY name")]
        return jsonify([employee_balance(conn, i) for i in ids])
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
    responses:
      200:
        description: Employee balance.
        schema:
          $ref: '#/definitions/EmployeeBalance'
      404:
        description: Employee not found.
        schema:
          $ref: '#/definitions/Error'
    """
    conn = db.connect()
    try:
        return jsonify(employee_balance(conn, employee_id))
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
    body = request.get_json(force=True)
    start = date.fromisoformat(body["start_date"])
    end = date.fromisoformat(body["end_date"])
    if end < start:
        return jsonify(error="end date is before start date"), 400
    days = working_days(start, end)
    conn = db.connect()
    try:
        # FIXME: pending requests are not counted against the balance, so two pending requests can overbook.
        available = employee_balance(conn, body["employee_id"])["available_days"]
        if days > available:
            return jsonify(error=f"requested {days} days but only {available} available"), 400
        cur = conn.execute(
            "INSERT INTO leave_requests (employee_id, start_date, end_date, days) VALUES (?, ?, ?, ?)",
            (body["employee_id"], start.isoformat(), end.isoformat(), days),
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
