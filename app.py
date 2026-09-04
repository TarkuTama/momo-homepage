from datetime import datetime
from functools import wraps

import os
import sqlite3

from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session
)
from flask_cors import CORS
from werkzeug.security import check_password_hash





load_dotenv()

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ["SECRET_KEY"]

ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
ADMIN_PASSWORD_HASH = os.environ["ADMIN_PASSWORD_HASH"]

MAIL_ADDRESS = os.environ["MAIL_ADDRESS"]
MAIL_APP_PASSWORD = os.environ["MAIL_APP_PASSWORD"]

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))

        return function(*args, **kwargs)

    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, password)
        ):
            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        error = "ユーザー名またはパスワードが違います。"

    return render_template(
        "login.html",
        error=error
    )



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





def send_booking_email(
    to_email,
    name,
    booking_id,
    checkin,
    checkout,
    guests,
    total_price
):
    message = EmailMessage()

    message["Subject"] = "【明神宿 ○○】ご予約完了のお知らせ"
    message["From"] = MAIL_ADDRESS
    message["To"] = to_email

    body = f"""
{name} 様

この度は、明神宿 ○○をご予約いただきありがとうございます。

以下の内容でご予約を承りました。

予約番号：{booking_id}
チェックイン：{checkin}
チェックアウト：{checkout}
宿泊人数：{guests}名
合計料金：{total_price:,}円

ご来館を心よりお待ちしております。

明神宿 ○○
"""

    message.set_content(body)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            MAIL_ADDRESS,
            MAIL_APP_PASSWORD
        )

        smtp.send_message(message)





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


    # 予約完了メールを送信
    try:
        send_booking_email(
            email,
            name,
            booking_id,
            checkin,
            checkout,
            guests,
            total_price
        )

        mail_sent = True

    except Exception as e:
        print("メール送信エラー:", e)
        mail_sent = False

    if mail_sent:
        message = (
            f"予約が完了しました。"
            f"予約番号は {booking_id} です。"
            "確認メールを送信しました。"
        )
    else:
        message = (
            f"予約が完了しました。"
            f"予約番号は {booking_id} です。"
            "ただし、確認メールの送信に失敗しました。"
        )
    
    return jsonify({
        "success": True,
        "message": message,
        "nights": nights,
        "price_per_night": price_per_night,
        "total_price": total_price
    })


@app.route("/admin")
@login_required
def admin():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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

    reservations = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        reservations=reservations
    )


@app.route(
    "/admin/cancel/<int:booking_id>",
    methods=["POST"]
)
@login_required
def admin_cancel_booking(booking_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reservations
        SET status = 'cancelled'
        WHERE id = ?
    """, (booking_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/admin/logout")
@login_required
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(debug=True)