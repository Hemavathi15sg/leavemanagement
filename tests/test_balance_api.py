import pytest

from app import app
from src.leave import db


@pytest.fixture
def client():
    conn = db.connect()
    for table in ("carry_forward", "leave_requests", "employees"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
    with app.test_client() as c:
        yield c


def run_sql(*statements):
    conn = db.connect()
    try:
        for sql, params in statements:
            conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def test_balance_splits_earned_carried_and_available(client):
    run_sql(
        ("INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (1, 'Asha', 2, 0)", ()),
        ("INSERT INTO carry_forward (employee_id, year, carried_days, run_at) VALUES (1, 2027, 5, '2027-01-01')", ()),
    )
    body = client.get("/api/employees/1/balance?year=2027").get_json()
    assert body["year"] == 2027
    assert body["earned_days"] == 4.0
    assert body["carried_days"] == 5.0
    assert body["available_days"] == 9.0


def test_last_years_approved_leave_does_not_reduce_this_year(client):
    run_sql(
        ("INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (1, 'Asha', 12, 0)", ()),
        ("INSERT INTO leave_requests (employee_id, start_date, end_date, days, status) "
         "VALUES (1, '2026-03-02', '2026-03-06', 5, 'approved')", ()),
    )
    assert client.get("/api/employees/1/balance?year=2026").get_json()["available_days"] == 19.0
    assert client.get("/api/employees/1/balance?year=2027").get_json()["available_days"] == 24.0


def test_request_spanning_year_end_is_split_by_year(client):
    # Mon 28 Dec 2026 to Tue 5 Jan 2027: 4 days in 2026, 3 in 2027
    run_sql(
        ("INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (1, 'Asha', 12, 0)", ()),
        ("INSERT INTO leave_requests (employee_id, start_date, end_date, days, status) "
         "VALUES (1, '2026-12-28', '2027-01-05', 7, 'approved')", ()),
    )
    assert client.get("/api/employees/1/balance?year=2026").get_json()["approved_days"] == 4.0
    assert client.get("/api/employees/1/balance?year=2027").get_json()["approved_days"] == 3.0


def test_year_must_be_four_digits(client):
    run_sql(("INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (1, 'Asha', 0, 0)", ()))
    resp = client.get("/api/employees/1/balance?year=27")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "year must be a 4-digit year"
    assert client.get("/api/employees?year=abc").status_code == 400


def test_employee_list_includes_breakdown(client):
    run_sql(
        ("INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (1, 'Asha', 2, 1)", ()),
        ("INSERT INTO carry_forward (employee_id, year, carried_days, run_at) VALUES (1, 2027, 5, '2027-01-01')", ()),
    )
    row = client.get("/api/employees?year=2027").get_json()[0]
    assert {"earned_days", "carried_days", "opening_days", "approved_days", "available_days"} <= row.keys()
    assert row["available_days"] == 10.0
