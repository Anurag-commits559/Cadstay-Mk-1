/**
 * search.js — Hostel search & filters page behaviour:
 *   1. Sync the dual-thumb rent slider with its number inputs (both ways)
 *   2. AJAX-submit filter/sort forms, swapping only #sr-results, with a
 *      server-side fallback (a normal full-page GET) if fetch fails or
 *      JS is unavailable — the view renders correctly either way.
 *
 * No framework — vanilla JS so it drops into a Django template with
 * zero build step.
 */
document.addEventListener("DOMContentLoaded", function () {
  initRangeSliders();
  initAjaxFilterForms();
});

/* ---------------------------------------------------------------------
 * 1. Dual-thumb rent range slider
 * ------------------------------------------------------------------- */
function initRangeSliders() {
  document.querySelectorAll("[data-sr-range-slider]").forEach((wrapper) => {
    const minInput = wrapper.querySelector('[data-sr-range="min"]');
    const maxInput = wrapper.querySelector('[data-sr-range="max"]');
    const fill = wrapper.querySelector("[data-sr-range-fill]");
    const numMin = wrapper.parentElement.querySelector('[data-sr-range-number="min"]');
    const numMax = wrapper.parentElement.querySelector('[data-sr-range-number="max"]');
    if (!minInput || !maxInput) return;

    const bounds = { min: Number(wrapper.dataset.min), max: Number(wrapper.dataset.max) };

    function updateFill() {
      const lo = Math.min(Number(minInput.value), Number(maxInput.value));
      const hi = Math.max(Number(minInput.value), Number(maxInput.value));
      const span = bounds.max - bounds.min || 1;
      const left = ((lo - bounds.min) / span) * 100;
      const right = ((hi - bounds.min) / span) * 100;
      fill.style.left = left + "%";
      fill.style.width = Math.max(right - left, 0) + "%";
    }

    function syncFromSliders() {
      if (Number(minInput.value) > Number(maxInput.value)) {
        [minInput.value, maxInput.value] = [maxInput.value, minInput.value];
      }
      if (numMin) numMin.value = minInput.value;
      if (numMax) numMax.value = maxInput.value;
      updateFill();
    }

    function syncFromNumbers() {
      if (numMin && numMin.value !== "") minInput.value = numMin.value;
      if (numMax && numMax.value !== "") maxInput.value = numMax.value;
      updateFill();
    }

    minInput.addEventListener("input", syncFromSliders);
    maxInput.addEventListener("input", syncFromSliders);
    if (numMin) numMin.addEventListener("input", syncFromNumbers);
    if (numMax) numMax.addEventListener("input", syncFromNumbers);

    updateFill();
  });
}

/* ---------------------------------------------------------------------
 * 2. AJAX filtering
 * ------------------------------------------------------------------- */
function initAjaxFilterForms() {
  const resultsEl = document.getElementById("sr-results");
  if (!resultsEl) return; // not on the listings page

  const apiUrl = resultsEl.dataset.apiUrl || "/hostels/api/";

  document
    .querySelectorAll("[data-sr-filter-form], [data-sr-sort-form]")
    .forEach((form) => {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        const params = new URLSearchParams(new FormData(form));
        fetchResults(params);
      });
    });

  function fetchResults(params) {
    const queryString = params.toString();
    resultsEl.setAttribute("aria-busy", "true");

    fetch(apiUrl + "?" + queryString, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then((response) => {
        if (!response.ok) throw new Error("Search request failed");
        return response.json();
      })
      .then((data) => {
        resultsEl.innerHTML = data.html;
        const heading = document.getElementById("sr-results-count-heading");
        if (heading) {
          heading.textContent = `${data.count} listing${data.count === 1 ? "" : "s"} found`;
        }
        const newUrl = window.location.pathname + "?" + queryString;
        window.history.pushState({ srFilters: true }, "", newUrl);
        resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch(() => {
        // Reliable fallback: a plain full-page GET always works, even if
        // the API call failed or JS partially broke.
        window.location.search = queryString;
      })
      .finally(() => {
        resultsEl.removeAttribute("aria-busy");
      });
  }

  // Support browser Back/Forward through the AJAX-updated history states.
  window.addEventListener("popstate", function () {
    window.location.reload();
  });
}
