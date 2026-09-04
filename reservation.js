document.getElementById("check-button").addEventListener("click", async function () {

    const checkin = document.getElementById("checkin").value;
    const checkout = document.getElementById("checkout").value;
    const guests = document.getElementById("guests").value;

    if (!checkin || !checkout || !guests) {
        document.getElementById("result").textContent =
            "チェックイン日、チェックアウト日、人数を入力してください。";
        return;
    }

    const response = await fetch("http://127.0.0.1:5000/check-availability", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            checkin: checkin,
            checkout: checkout,
            guests: guests
        })
    });

    const data = await response.json();

    document.getElementById("result").textContent = data.message;

    if (data.available) {

        document.getElementById("customer-form").style.display = "block";
        document.getElementById("price-info").style.display = "block";

        document.getElementById("nights").textContent =
            data.nights;

        document.getElementById("price-per-night").textContent =
            data.price_per_night.toLocaleString("ja-JP");

        document.getElementById("total-price").textContent =
            data.total_price.toLocaleString("ja-JP");

    } else {

        document.getElementById("customer-form").style.display = "none";
        document.getElementById("price-info").style.display = "none";

    }
});










document.getElementById("reserve-button").addEventListener("click", async function () {

    const checkin = document.getElementById("checkin").value;
    const checkout = document.getElementById("checkout").value;
    const guests = document.getElementById("guests").value;

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;


    if (!name || !email || !phone) {
        document.getElementById("reserve-result").textContent =
            "お名前、メールアドレス、電話番号を入力してください。";
        return;
    }


    const response = await fetch("http://127.0.0.1:5000/reserve", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            name: name,
            email: email,
            phone: phone,
            checkin: checkin,
            checkout: checkout,
            guests: guests
        })
    });


    const data = await response.json();

    document.getElementById("reserve-result").textContent = data.message;


    if (data.success) {

        document.getElementById("customer-form").style.display = "none";

        document.getElementById("reservation-form").reset();

        document.getElementById("name").value = "";
        document.getElementById("email").value = "";
        document.getElementById("phone").value = "";
    }

});