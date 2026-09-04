import sqlite3

conn = sqlite3.connect("booking.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    checkin TEXT NOT NULL,
    checkout TEXT NOT NULL,
    guests INTEGER NOT NULL,
    total_price INTEGER,
    status TEXT NOT NULL DEFAULT 'confirmed'
)
""")

conn.commit()
conn.close()

print("データベースを作成しました。")