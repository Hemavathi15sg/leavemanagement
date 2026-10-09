"""Leave Management API and single-page UI."""
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from src.leave import db

BASE_DIR = Path(__file__).parent
app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/employees")
def list_employees():
    conn = db.connect()
    rows = conn.execute(
        "SELECT id, name, months_worked, opening_balance FROM employees ORDER BY name"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)
