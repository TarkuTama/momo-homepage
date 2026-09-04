import sqlite3

booking_id = input("キャンセルする予約IDを入力してください: ")

conn = sqlite3.connect("booking.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE reservations
SET status = 'cancelled'
WHERE id = ?
""", (booking_id,))

conn.commit()

if cursor.rowcount > 0:
    print("予約をキャンセルしました。")
else:
    print("その予約IDは見つかりませんでした。")

conn.close()