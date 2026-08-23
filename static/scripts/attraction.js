"use strict";

const attractionId = Number(window.location.pathname.split("/").pop());

const nameEl = document.getElementById("attraction-name");
const subtitleEl = document.getElementById("attraction-subtitle");
const descriptionEl = document.getElementById("attraction-description");
const addressEl = document.getElementById("attraction-address");
const transportEl = document.getElementById("attraction-transport");

const slideshowImage = document.getElementById("slideshow-image");
const slideshowIndicators = document.getElementById("slideshow-indicators");
const slideshowPrev = document.getElementById("slideshow-prev");
const slideshowNext = document.getElementById("slideshow-next");

const priceEl = document.getElementById("booking-price");
const timeRadios = document.querySelectorAll('input[name="time"]');

let images = [];
let currentIndex = 0;

async function loadAttraction() {
  try {
    const response = await fetch(`/api/attraction/${attractionId}`);
    const result = await response.json();
    const data = result.data;

    document.title = `${data.name}｜台北一日遊`;
    nameEl.textContent = data.name;
    subtitleEl.textContent = `${data.category} at ${data.mrt}`;
    descriptionEl.textContent = data.description;
    addressEl.textContent = data.address;
    transportEl.textContent = data.transport;

    images = Array.isArray(data.images) ? data.images : [];
    initSlideshow();
  } catch (error) {
    console.error("載入景點資料失敗：", error);
  }
}

function initSlideshow() {
  if (images.length === 0) return;

  slideshowIndicators.innerHTML = "";
  images.forEach(() => {
    const bar = document.createElement("div");
    bar.className = "indicator";
    slideshowIndicators.appendChild(bar);
  });

  currentIndex = 0;
  renderSlide();
}

function renderSlide() {
  slideshowImage.src = images[currentIndex];
  slideshowImage.alt = nameEl.textContent;

  const bars = slideshowIndicators.children;
  for (let i = 0; i < bars.length; i++) {
    bars[i].classList.toggle("indicator--active", i === currentIndex);
  }
}

function showPrev() {
  currentIndex = (currentIndex - 1 + images.length) % images.length;
  renderSlide();
}

function showNext() {
  currentIndex = (currentIndex + 1) % images.length;
  renderSlide();
}

slideshowPrev.addEventListener("click", showPrev);
slideshowNext.addEventListener("click", showNext);

function updatePrice() {
  const selected = document.querySelector('input[name="time"]:checked').value;
  const price = selected === "morning" ? 2000 : 2500;
  priceEl.textContent = `新台幣 ${price} 元`;
}

timeRadios.forEach((radio) => {
  radio.addEventListener("change", updatePrice);
});

loadAttraction();
updatePrice();