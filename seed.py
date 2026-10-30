"""Reset the local database with demo employees and leave requests."""
import os

from src.leave import db


def main():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    conn = db.connect()
    db.init_db(conn)
    conn.executemany(
        "INSERT INTO employees (id, name, months_worked, opening_balance) VALUES (?, ?, ?, ?)",
        [(1, "Asha Rao", 14, 3), (2, "Ben Carter", 9, 0),
         (3, "Chen Wei", 22, 5), (4, "Dina Haddad", 4, 1)],
    )
    conn.executemany(
        "INSERT INTO leave_requests (employee_id, start_date, end_date, days, status) VALUES (?, ?, ?, ?, ?)",
        [(1, "2026-03-02", "2026-03-06", 5, "approved"),
         (1, "2026-08-10", "2026-08-11", 2, "approved"),
         (3, "2026-06-15", "2026-06-19", 5, "approved"),
         (2, "2026-09-07", "2026-09-08", 2, "rejected")],
    )
    conn.commit()
    conn.close()
    print(f"Seeded {db.DB_PATH}")


if __name__ == "__main__":
    main()
