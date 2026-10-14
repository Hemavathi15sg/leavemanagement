"""Create the local database with demo employees."""
from src.leave import db

conn = db.connect()
db.init_db(conn)
conn.executemany(
    "INSERT OR IGNORE INTO employees (id, name, months_worked, opening_balance) VALUES (?, ?, ?, ?)",
    [(1, "Asha Rao", 14, 3), (2, "Ben Carter", 9, 0)],
)
conn.commit()
conn.close()
print("Seeded employees")
