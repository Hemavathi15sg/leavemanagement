"""Flask test-client tests for POST /api/requests input validation."""
import pytest

import app as app_module
from src.leave import db

VALID = {"employee_id": 1, "start_date": "2026-12-07", "end_date": "2026-12-11"}  # Mon-Fri


@pytest.fixture
def client(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    conn = db.connect(path)
    db.init_db(conn)
    conn.executemany(
        "INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (?, ?, ?, ?)",
        [(1, "Asha Rao", 14, 3), (4, "Dina Haddad", 4, 1)],
    )
    conn.commit()
    conn.close()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def post(client, payload):
    return client.post("/api/requests", json=payload)


@pytest.mark.parametrize("field", ["employee_id", "start_date", "end_date"])
def test_missing_field_returns_400(client, field):
    payload = {k: v for k, v in VALID.items() if k != field}
    resp = post(client, payload)
    assert resp.status_code == 400
    assert field in resp.get_json()["error"]


@pytest.mark.parametrize("body", [[], "text", None])
def test_non_object_body_returns_400(client, body):
    resp = client.post("/api/requests", json=body)
    assert resp.status_code == 400
    assert "JSON object" in resp.get_json()["error"]


def test_malformed_json_returns_400_json(client):
    resp = client.post("/api/requests", data="{not json", content_type="application/json")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.parametrize("employee_id", ["1", None, 1.5, True])
def test_non_integer_employee_id_returns_400(client, employee_id):
    resp = post(client, {**VALID, "employee_id": employee_id})
    assert resp.status_code == 400
    assert "employee_id" in resp.get_json()["error"]


@pytest.mark.parametrize("value", [
    "2026-02-30",     # no such day
    "2026-13-01",     # no such month
    "2026/12/07",     # wrong separator
    "07-12-2026",     # wrong order
    "2026-12-7",      # not zero-padded
    "not-a-date",
    "",
    20,
    None,
])
def test_invalid_start_date_returns_400(client, value):
    resp = post(client, {**VALID, "start_date": value})
    assert resp.status_code == 400
    assert "start_date" in resp.get_json()["error"]


def test_invalid_end_date_returns_400(client):
    resp = post(client, {**VALID, "end_date": "2026-02-30"})
    assert resp.status_code == 400
    assert "end_date" in resp.get_json()["error"]


def test_end_before_start_returns_400(client):
    resp = post(client, {**VALID, "start_date": "2026-12-11", "end_date": "2026-12-07"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "end date is before start date"}


def test_unknown_employee_returns_404_json(client):
    resp = post(client, {**VALID, "employee_id": 999})
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "employee not found"}


def test_insufficient_balance_returns_400(client):
    # Employee 4: 4 months worked (8 days) + 1 opening = 9 available; 10 working days requested.
    resp = post(client, {"employee_id": 4, "start_date": "2026-12-07", "end_date": "2026-12-18"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "requested 10 days but only 9.0 available"}


def test_valid_request_returns_201_with_existing_shape(client):
    resp = post(client, VALID)
    assert resp.status_code == 201
    assert resp.get_json() == {"id": 1, "days": 5, "status": "pending"}
