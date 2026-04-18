function parseJsonArray(value) {
  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
}

function normalizeValue(value) {
  return String(value || "").trim().toLowerCase();
}

function getToggleNode(card) {
  const parent = card.parentElement;
  if (parent && /(^|\s)col(\-|\s|$)/.test(parent.className)) {
    return parent;
  }
  return card;
}

function matchesFilter(card, filterValue, filterDataAttr) {
  const normalizedFilter = normalizeValue(filterValue);
  if (normalizedFilter === "all") {
    return true;
  }

  const rawCardValue = card.getAttribute(filterDataAttr);

  if (filterDataAttr === "data-exams") {
    const examList = parseJsonArray(rawCardValue).map(normalizeValue);
    return examList.includes(normalizedFilter);
  }

  return normalizeValue(rawCardValue) === normalizedFilter;
}

function updateCountBadges(tabs, cards, filterDataAttr, filterAttr) {
  tabs.forEach(function (tab) {
    const tabFilterValue = tab.getAttribute(filterAttr) || "all";
    let count = 0;

    cards.forEach(function (card) {
      if (matchesFilter(card, tabFilterValue, filterDataAttr)) {
        count += 1;
      }
    });

    const badge = tab.querySelector(".tab-count-badge");
    if (badge) {
      badge.textContent = "(" + count + ")";
    }
  });
}

function setCardVisibility(card, shouldShow) {
  const node = getToggleNode(card);
  node.style.transition = "opacity 0.2s ease";

  if (node.__filterTimeoutId) {
    window.clearTimeout(node.__filterTimeoutId);
    node.__filterTimeoutId = null;
  }

  if (shouldShow) {
    node.classList.remove("d-none");
    requestAnimationFrame(function () {
      node.style.opacity = "1";
    });
    return;
  }

  node.style.opacity = "0";
  node.__filterTimeoutId = window.setTimeout(function () {
    node.classList.add("d-none");
    node.__filterTimeoutId = null;
  }, 180);
}

function applyFilter(tabs, cards, filterValue, filterDataAttr, filterAttr) {
  cards.forEach(function (card) {
    const shouldShow = matchesFilter(card, filterValue, filterDataAttr);
    setCardVisibility(card, shouldShow);
  });

  tabs.forEach(function (tab) {
    tab.classList.remove("active");
    if (normalizeValue(tab.getAttribute(filterAttr)) === normalizeValue(filterValue)) {
      tab.classList.add("active");
    }
  });

  updateCountBadges(tabs, cards, filterDataAttr, filterAttr);
}

function initTabFilter(tabsSelector, cardsSelector, filterAttr, filterDataAttr) {
  const tabs = Array.from(document.querySelectorAll(tabsSelector));
  const cards = Array.from(document.querySelectorAll(cardsSelector));

  if (!tabs.length || !cards.length) {
    return;
  }

  cards.forEach(function (card) {
    const node = getToggleNode(card);
    node.style.opacity = "1";
    node.style.transition = "opacity 0.2s ease";
  });

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function (event) {
      event.preventDefault();
      const filterValue = tab.getAttribute(filterAttr) || "all";
      applyFilter(tabs, cards, filterValue, filterDataAttr, filterAttr);
    });
  });

  updateCountBadges(tabs, cards, filterDataAttr, filterAttr);
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector(".faculty-filter-tabs") && document.querySelector(".faculty-card-wrapper")) {
    initTabFilter(
      ".faculty-filter-tabs .nav-link",
      ".faculty-card-wrapper",
      "data-filter",
      "data-exams"
    );
  }

  if (document.querySelector(".results-filter-tabs") && document.querySelector(".result-card-wrapper")) {
    initTabFilter(
      ".results-filter-tabs .nav-link",
      ".result-card-wrapper",
      "data-filter",
      "data-exam"
    );
  }

  if (document.querySelector(".courses-filter-tabs") && document.querySelector(".course-card-wrapper")) {
    initTabFilter(
      ".courses-filter-tabs .nav-link",
      ".course-card-wrapper",
      "data-filter",
      "data-category"
    );
  }
});
