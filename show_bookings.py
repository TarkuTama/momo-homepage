import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "booking.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id,
        name,
        email,
        phone,
        checkin,
        checkout,
        guests,
        total_price,
        status
    FROM reservations
    ORDER BY checkin
""")

rows = cursor.fetchall()

if len(rows) == 0:
    print("予約はありません。")

else:
    print()
    print("===== 予約一覧 =====")
    print()

    for row in rows:

        booking_id = row[0]
        name = row[1]
        email = row[2]
        phone = row[3]
        checkin = row[4]
        checkout = row[5]
        guests = row[6]
        total_price = row[7]
        status = row[8]

        if status == "confirmed":
            status_text = "予約確定"
        elif status == "cancelled":
            status_text = "キャンセル"
        else:
            status_text = status

        if total_price is None:
            price_text = "未登録"
        else:
            price_text = f"{total_price:,}円"

        print(f"予約番号：{booking_id}")
        print(f"お名前：{name}")
        print(f"メール：{email}")
        print(f"電話番号：{phone}")
        print(f"チェックイン：{checkin}")
        print(f"チェックアウト：{checkout}")
        print(f"宿泊人数：{guests}名")
        print(f"合計料金：{price_text}")
        print(f"予約状態：{status_text}")

        print("-" * 40)

conn.close()