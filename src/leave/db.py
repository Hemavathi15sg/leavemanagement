"""SQLite access. The schema is created on demand; there are no migrations yet."""
import os
import sqlite3

DB_PATH = os.environ.get("LEAVE_DB", "leave.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    months_worked INTEGER NOT NULL DEFAULT 0,
    opening_balance REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    days REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS carry_forward (
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    year INTEGER NOT NULL,            -- calendar year the carried days apply to
    carried_days REAL NOT NULL,
    run_at TEXT NOT NULL,
    PRIMARY KEY (employee_id, year)
);
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
