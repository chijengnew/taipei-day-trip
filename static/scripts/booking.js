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
initBookingPage();