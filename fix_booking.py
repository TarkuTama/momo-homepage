import sqlite3

conn = sqlite3.connect("booking.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE reservations
SET checkin = ?, checkout = ?
WHERE id = ?
""", (
    "2026-09-10",
    "2026-09-11",
    1
))

conn.commit()
conn.close()

print("日付を修正しました。")