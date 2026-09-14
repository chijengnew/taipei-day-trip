const memberName = document.getElementById("member-name");
const bookingContent = document.getElementById("booking-content");
const emptyState = document.getElementById("empty-state");

const tripImage = document.getElementById("trip-image");
const tripTitle = document.getElementById("trip-title");
const tripDate = document.getElementById("trip-date");
const tripTime = document.getElementById("trip-time");
const tripPrice = document.getElementById("trip-price");
const tripAddress = document.getElementById("trip-address");
const tripDelete = document.getElementById("trip-delete");

const contactName = document.getElementById("contact-name");
const contactEmail = document.getElementById("contact-email");
const totalPrice = document.getElementById("total-price");
const APP_ID = 171100;
const APP_KEY = "app_rZ1VxrMtx8AqmmGwvpbNL8gmSUhOSc2cTKZmSNOCc0VJnexUfsiV9MUMCWhz";
const contactPhone = document.getElementById("contact-phone");
const confirmSubmit = document.getElementById("confirm-submit");
let currentBooking = null;

const TIME_TEXT = {
  morning: "早上 9 點到下午 4 點",
  afternoon: "下午 2 點到晚上 9 點",
};

async function fetchBooking() {
  const response = await fetch("/api/booking", {
    headers: { "Authorization": "Bearer " + getToken() },
  });
  const result = await response.json();
  return result.data;
}

function renderBooking(data) {
  currentBooking = data;
  tripImage.src = data.attraction.image;
  tripImage.alt = data.attraction.name;
  tripTitle.textContent = "台北一日遊：" + data.attraction.name;
  tripDate.textContent = data.date;
  tripTime.textContent = TIME_TEXT[data.time];
  tripPrice.textContent = "新台幣 " + data.price + " 元";
  tripAddress.textContent = data.attraction.address;
  totalPrice.textContent = data.price;

  bookingContent.hidden = false;
  emptyState.hidden = true;
  setupTappay();
}

function setupTappay() {
  TPDirect.setupSDK(171100, "app_rZ1VxrMtx8AqmmGwvpbNL8gmSUhOSc2cTKZmSNOCc0VJnexUfsiV9MUMCWhz", "sandbox");
  TPDirect.card.setup({
    fields: {
      number:         { element: "#card-number",     placeholder: "**** **** **** ****" },
      expirationDate: { element: "#card-expiration", placeholder: "MM / YY" },
      ccv:            { element: "#card-ccv",         placeholder: "CVV" },
    },
    styles: { "input": { "color": "#666" }, ".valid": { "color": "green" }, ".invalid": { "color": "red" } },
  });
}

function renderEmpty() {
  bookingContent.hidden = true;
  emptyState.hidden = false;
}

async function handleDelete() {
  try {
    const response = await fetch("/api/booking", {
      method: "DELETE",
      headers: { "Authorization": "Bearer " + getToken() },
    });
    if (response.ok) {
      window.location.reload();
    }
  } catch (error) {}
}

async function handleSubmit() {
  const name = contactName.value.trim();
  const email = contactEmail.value.trim();
  const phone = contactPhone.value.trim();
  if (!name || !email || !phone) {
    alert("請完整填寫聯絡資訊");
    return;
  }

  const status = TPDirect.card.getTappayFieldsStatus();
  if (!status.canGetPrime) {
    alert("信用卡資訊有誤，請重新確認");
    return;
  }

  TPDirect.card.getPrime(async (result) => {
    if (result.status !== 0) {
      alert("取得付款資訊失敗，請重試");
      return;
    }

    const response = await fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + getToken(),
      },
      body: JSON.stringify({
        prime: result.card.prime,
        order: {
          price: currentBooking.price,
          trip: {
            attraction: {
              id: currentBooking.attraction.id,
              name: currentBooking.attraction.name,
              address: currentBooking.attraction.address,
              image: currentBooking.attraction.image,
            },
            date: currentBooking.date,
            time: currentBooking.time,
          },
          contact: { name, email, phone },
        },
      }),
    });
    const data = (await response.json()).data;
    if (data && data.payment.status === 0) {
      window.location.href = "/thankyou?number=" + data.number;
    } else {
      alert(data ? data.payment.message : "付款失敗，請稍後再試");
    }
  });
}

async function initBookingPage() {
  const user = await fetchCurrentUser();
  if (!user) {
    window.location.href = "/";
    return;
  }

  memberName.textContent = user.name;
  contactName.value = user.name;
  contactEmail.value = user.email;

  const data = await fetchBooking();
  if (data) {
    renderBooking(data);
  } else {
    renderEmpty();
  }
}

tripDelete.addEventListener("click", handleDelete);
confirmSubmit.addEventListener("click", handleSubmit);
initBookingPage();