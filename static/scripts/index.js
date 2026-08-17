"use strict";

const attractionList = document.getElementById("attraction-list");

let nextPage = 0;
let isLoading = false;
let currentKeyword = "";
let selectedCategory = null;
let requestId = 0;

async function loadAttractions() {
  if (nextPage === null || isLoading) return;

  const myId = requestId;
  const isFirstPage = nextPage === 0;
  isLoading = true;
  showSkeletons();
  try {
    const params = new URLSearchParams({ page: nextPage });
    if (currentKeyword) params.set("keyword", currentKeyword);
    if (selectedCategory) params.set("category", selectedCategory);

    const response = await fetch(`/api/attractions?${params}`);
    const result = await response.json();

    if (myId !== requestId) return;

    removeSkeletons();

    if (isFirstPage && result.data.length === 0) {
      showNoResult();
    } else {
      hideNoResult();
    }

    renderAttractions(result.data);
    nextPage = result.nextPage;
  } catch (error) {
    if (myId !== requestId) return;
    console.error("載入景點資料失敗：", error);
  } finally {
    if (myId === requestId) {
      removeSkeletons();
      isLoading = false;
      ensureFilled();
    }
  }
}

const SKELETON_COUNT = 8;

function showSkeletons() {
  const fragment = document.createDocumentFragment();
  for (let i = 0; i < SKELETON_COUNT; i++) {
    const li = document.createElement("li");
    li.className = "skeleton";
    li.innerHTML = `
      <div class="skeleton__figure"></div>
      <div class="skeleton__meta">
        <span class="skeleton__line"></span>
        <span class="skeleton__line"></span>
      </div>
    `;
    fragment.appendChild(li);
  }
  attractionList.appendChild(fragment);
}

function removeSkeletons() {
  attractionList.querySelectorAll(".skeleton").forEach((el) => el.remove());
}

function renderAttractions(attractions) {
  const fragment = document.createDocumentFragment();
  attractions.forEach((attraction) => {
    fragment.appendChild(createCard(attraction));
  });
  attractionList.appendChild(fragment);
}

const noResultMessage = document.createElement("p");
noResultMessage.className = "no-result";
noResultMessage.textContent = "找不到符合的景點";
noResultMessage.hidden = true;
attractionList.insertAdjacentElement("afterend", noResultMessage);

function showNoResult() {
  noResultMessage.hidden = false;
}

function hideNoResult() {
  noResultMessage.hidden = true;
}

function createCard(attraction) {
  const li = document.createElement("li");
  li.className = "card";

  const link = document.createElement("a");
  link.className = "card__link";
  link.href = `/attraction/${attraction.id}`;

  const figure = document.createElement("div");
  figure.className = "card__figure";

  const image = document.createElement("img");
  image.className = "card__image";
  image.loading = "lazy";
  image.alt = attraction.name;
  if (Array.isArray(attraction.images) && attraction.images.length > 0) {
    image.src = attraction.images[0];
  }

  const name = document.createElement("h3");
  name.className = "card__name";
  name.textContent = attraction.name;

  figure.append(image, name);

  const meta = document.createElement("div");
  meta.className = "card__meta";

  const mrt = document.createElement("span");
  mrt.className = "card__mrt";
  mrt.textContent = attraction.mrt || "";

  const category = document.createElement("span");
  category.className = "card__category";
  category.textContent = attraction.category || "";

  meta.append(mrt, category);

  link.append(figure, meta);
  li.appendChild(link);
  return li;
}

const sentinel = document.getElementById("sentinel");

const observer = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) {
    loadAttractions();
  }
}, { rootMargin: "200px" });

observer.observe(sentinel);

function ensureFilled() {
  if (nextPage === null || isLoading) return;
  const rect = sentinel.getBoundingClientRect();
  if (rect.top <= window.innerHeight) {
    loadAttractions();
  }
}

loadAttractions();

const categoryButton = document.getElementById("category-button");
const categoryLabel = document.getElementById("category-label");
const categoryPanel = document.getElementById("category-panel");

async function loadCategories() {
  try {
    const response = await fetch("/api/categories");
    const result = await response.json();
    renderCategoryPanel(["全部分類", ...result.data]);
  } catch (error) {
    console.error("載入分類資料失敗：", error);
  }
}

function renderCategoryPanel(categories) {
  categoryPanel.innerHTML = "";
  categories.forEach((category) => {
    const item = document.createElement("li");
    item.className = "category-panel__item";
    item.textContent = category;
    item.addEventListener("click", () => selectCategory(category));
    categoryPanel.appendChild(item);
  });
}

function selectCategory(category) {
  selectedCategory = category === "全部分類" ? null : category;
  categoryLabel.textContent = category;
  closePanel();
  search();
}

function openPanel() {
  categoryPanel.hidden = false;
}

function closePanel() {
  categoryPanel.hidden = true;
}

categoryButton.addEventListener("click", (event) => {
  event.stopPropagation();
  categoryPanel.hidden ? openPanel() : closePanel();
});

categoryPanel.addEventListener("click", (event) => {
  event.stopPropagation();
});

document.addEventListener("click", () => {
  closePanel();
});

loadCategories();

const keywordInput = document.getElementById("keyword-input");
const searchButton = document.getElementById("search-button");

function search() {
  requestId++;
  isLoading = false;
  currentKeyword = keywordInput.value.trim();
  nextPage = 0;
  attractionList.innerHTML = "";
  loadAttractions();
}

searchButton.addEventListener("click", search);

keywordInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") search();
});
const mrtList = document.getElementById("mrt-list");
const mrtViewport = mrtList.parentElement;
const mrtPrevButton = document.getElementById("mrt-prev");
const mrtNextButton = document.getElementById("mrt-next");

async function loadMrts() {
  try {
    const response = await fetch("/api/mrts");
    const result = await response.json();
    renderMrts(result.data);
  } catch (error) {
    console.error("載入捷運站資料失敗：", error);
  }
}

function renderMrts(mrts) {
  const fragment = document.createDocumentFragment();
  mrts.forEach((mrt) => {
    const item = document.createElement("li");
    item.className = "mrt__item";
    item.textContent = mrt;
    item.addEventListener("click", () => searchByMrt(mrt));
    fragment.appendChild(item);
  });
  mrtList.appendChild(fragment);
}

function searchByMrt(mrt) {
  keywordInput.value = mrt;
  search();
}

mrtPrevButton.addEventListener("click", () => {
  mrtViewport.scrollBy({ left: -mrtViewport.clientWidth, behavior: "smooth" });
});

mrtNextButton.addEventListener("click", () => {
  mrtViewport.scrollBy({ left: mrtViewport.clientWidth, behavior: "smooth" });
});

loadMrts();