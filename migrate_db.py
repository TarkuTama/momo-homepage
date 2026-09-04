import sqlite3

conn = sqlite3.connect("booking.db")
cursor = conn.cursor()

# 現在の列を確認
cursor.execute("PRAGMA table_info(reservations)")
columns = [column[1] for column in cursor.fetchall()]

# total_price がまだなければ追加
if "total_price" not in columns:
    cursor.execute("""
        ALTER TABLE reservations
        ADD COLUMN total_price INTEGER
    """)

    conn.commit()
    print("total_price列を追加しました。")
else:
    print("total_price列はすでに存在します。")

conn.close()