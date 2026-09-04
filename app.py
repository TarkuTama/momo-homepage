from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "booking.db")





def calculate_price(checkin, checkout, guests):
    checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()

    nights = (checkout_date - checkin_date).days

    # 1～2名は55,000円
    # 3名以上は1名追加ごとに7,700円
    price_per_night = 55000 + max(guests - 2, 0) * 7700

    total_price = price_per_night * nights

    return nights, price_per_night, total_price





@app.route("/check-availability", methods=["POST"])
def check_availability():

    data = request.get_json()

    checkin = data["checkin"]
    checkout = data["checkout"]
    guests = int(data["guests"])


    if guests < 1 or guests > 6:
        return jsonify({
            "available": False,
            "message": "宿泊人数は1名～6名で指定してください。"
        })


    if checkin >= checkout:
        return jsonify({
            "available": False,
            "message": "チェックアウト日はチェックイン日より後の日付を指定してください。"
        })


    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    cursor.execute("""
        SELECT COUNT(*)
        FROM reservations
        WHERE status = 'confirmed'
        AND checkin < ?
        AND checkout > ?
    """, (checkout, checkin))


    count = cursor.fetchone()[0]

    conn.close()


    if count > 0:

        return jsonify({
            "available": False,
            "message": "申し訳ありません。ご指定の日程は予約済みです。"
        })


    nights, price_per_night, total_price = calculate_price(
        checkin,
        checkout,
        guests
    )

    return jsonify({
        "available": True,
        "message": "ご指定の日程は空いています。",
        "nights": nights,
        "price_per_night": price_per_night,
        "total_price": total_price
    })


@app.route("/reserve", methods=["POST"])
def reserve():

    data = request.get_json()

    name = data["name"].strip()
    email = data["email"].strip()
    phone = data["phone"].strip()

    checkin = data["checkin"]
    checkout = data["checkout"]
    guests = int(data["guests"])


    # お客様情報の確認
    if not name or not email or not phone:
        return jsonify({
            "success": False,
            "message": "お客様情報をすべて入力してください。"
        }), 400


    # 人数の確認
    if guests < 1 or guests > 6:
        return jsonify({
            "success": False,
            "message": "宿泊人数は1名～6名で指定してください。"
        }), 400


    # 日付の確認
    if checkin >= checkout:
        return jsonify({
            "success": False,
            "message": "宿泊日の指定が正しくありません。"
        }), 400


    # ----------------------------
    # ここで料金をもう一度計算
    # ----------------------------

    nights, price_per_night, total_price = calculate_price(
        checkin,
        checkout,
        guests
    )


    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    # 予約確定直前にもう一度空室確認
    cursor.execute("""
        SELECT COUNT(*)
        FROM reservations
        WHERE status = 'confirmed'
        AND checkin < ?
        AND checkout > ?
    """, (checkout, checkin))


    count = cursor.fetchone()[0]


    if count > 0:

        conn.close()

        return jsonify({
            "success": False,
            "message": "申し訳ありません。先に他の予約が入りました。"
        }), 409


    # 予約を登録
    cursor.execute("""
        INSERT INTO reservations
        (name, email, phone, checkin, checkout, guests, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?,?)
    """, (
        name,
        email,
        phone,
        checkin,
        checkout,
        guests,
        total_price,
        "confirmed"
    ))


    booking_id = cursor.lastrowid

    conn.commit()
    conn.close()


    return jsonify({
        "success": True,
        "message": f"予約が完了しました。予約番号は {booking_id} です。",
        "nights": nights,
        "price_per_night": price_per_night,
        "total_price": total_price
    })


if __name__ == "__main__":
    app.run(debug=True)