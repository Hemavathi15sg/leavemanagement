"""Leave Management API and single-page UI."""
from datetime import date
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from src.leave import db
from src.leave.rules import balance, working_days

BASE_DIR = Path(__file__).parent
app = Flask(__name__)


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
    conn = db.connect()
    try:
        ids = [r["id"] for r in conn.execute("SELECT id FROM employees ORDER BY name")]
        return jsonify([employee_balance(conn, i) for i in ids])
    finally:
        conn.close()


@app.get("/api/employees/<int:employee_id>/balance")
def get_balance(employee_id):
    conn = db.connect()
    try:
        return jsonify(employee_balance(conn, employee_id))
    finally:
        conn.close()


@app.get("/api/requests")
def list_requests():
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
    body = request.get_json(force=True)
    start = date.fromisoformat(body["start_date"])
    end = date.fromisoformat(body["end_date"])
    if end < start:
        return jsonify(error="end date is before start date"), 400
    days = working_days(start, end)
    conn = db.connect()
    try:
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



if __name__ == "__main__":
    app.run(debug=True)
