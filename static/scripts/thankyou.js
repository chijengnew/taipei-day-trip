const orderNumber = new URLSearchParams(window.location.search).get("number");

const TIME_TEXT = {
    morning: "上半天（09:00 - 12:00）",
    afternoon: "下半天（14:00 - 17:00）",
};

const numberEl = document.getElementById("order-number");
const detailEl = document.getElementById("order-detail");
const messageEl = document.getElementById("order-message");

function showMessage(text) {
    messageEl.textContent = text;
    messageEl.hidden = false;
}

function renderOrder(data) {
    document.getElementById("detail-image").src = data.trip.attraction.image || "";
    document.getElementById("detail-name").textContent = data.trip.attraction.name;
    document.getElementById("detail-address").textContent = data.trip.attraction.address;
    document.getElementById("detail-date").textContent = data.trip.date;
    document.getElementById("detail-time").textContent = TIME_TEXT[data.trip.time] || data.trip.time;
    document.getElementById("detail-price").textContent = "新台幣 " + data.price + " 元";

    const statusEl = document.getElementById("detail-status");
    if (data.status === "PAID") {
        statusEl.textContent = "已付款";
        statusEl.classList.add("badge--paid");
    } else {
        statusEl.textContent = "尚未付款";
        statusEl.classList.add("badge--unpaid");
    }

    document.getElementById("detail-contact").textContent =
        data.contact.name + "・" + data.contact.email + "・" + data.contact.phone;

    detailEl.hidden = false;
}

async function loadOrder() {
    if (!orderNumber) {
        showMessage("查無訂單編號，請從預定行程重新操作。");
        return;
    }

    numberEl.textContent = orderNumber;

    const token = getToken();
    if (!token) {
        showMessage("請先登入以查看訂單明細。");
        return;
    }

    try {
        const response = await fetch("/api/order/" + orderNumber, {
            headers: { "Authorization": "Bearer " + token },
        });
        const result = await response.json();
        const data = result.data;

        if (!data) {
            showMessage("找不到這筆訂單的明細。");
            return;
        }

        renderOrder(data);
    } catch (error) {
        showMessage("載入訂單時發生錯誤，請稍後再試。");
    }
}

loadOrder();