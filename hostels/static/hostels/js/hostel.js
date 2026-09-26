/**
 * hostel.js — Add/Edit Hostel form behaviour:
 *   1. Multi-step wizard navigation (Steps 1-7)
 *   2. Drag & drop image upload with instant previews + "set primary"
 *   3. Dynamically add/remove Room rows in the RoomFormSet
 *   4. Disable submit button + show loading state on submit
 *
 * No framework — vanilla JS so it drops into a Django template with
 * zero build step.
 */
document.addEventListener("DOMContentLoaded", function () {
  initWizard();
  initImageUploader();
  initRoomFormset();
  initSubmitLoadingState();
  initDeleteModals();
});

/* ---------------------------------------------------------------------
 * 1. Multi-step wizard
 * ------------------------------------------------------------------- */
function initWizard() {
  const steps = document.querySelectorAll(".hs-step");
  const fieldsets = document.querySelectorAll(".hs-fieldset");
  if (!steps.length || !fieldsets.length) return;

  let current = 0;

  function show(index) {
    fieldsets.forEach((fs, i) => fs.classList.toggle("is-active", i === index));
    steps.forEach((s, i) => {
      s.classList.toggle("is-active", i === index);
      s.classList.toggle("is-done", i < index);
    });
    window.scrollTo({ top: document.querySelector(".hs-form-shell").offsetTop - 20, behavior: "smooth" });
  }

  document.querySelectorAll("[data-hs-next]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!validateStep(fieldsets[current])) return;
      current = Math.min(current + 1, fieldsets.length - 1);
      show(current);
      if (current === fieldsets.length - 1) fillReviewSummary();
    });
  });

  document.querySelectorAll("[data-hs-prev]").forEach((btn) => {
    btn.addEventListener("click", () => {
      current = Math.max(current - 1, 0);
      show(current);
    });
  });

  steps.forEach((step, i) => {
    step.addEventListener("click", () => {
      if (i <= current) {
        current = i;
        show(current);
      }
    });
  });

  show(current);
}

function validateStep(fieldset) {
  const inputs = fieldset.querySelectorAll("input, select, textarea");
  let valid = true;
  inputs.forEach((el) => {
    if (!el.checkValidity()) {
      el.reportValidity();
      valid = false;
    }
  });
  return valid;
}

function fillReviewSummary() {
  const summary = document.getElementById("hs-review-summary");
  if (!summary) return;
  const get = (name) => {
    const el = document.querySelector(`[name="${name}"]`);
    return el ? el.value : "";
  };
  summary.innerHTML = `
    <dl class="row mb-0">
      <dt class="col-sm-4">Hostel name</dt><dd class="col-sm-8">${escapeHtml(get("hostel_name")) || "—"}</dd>
      <dt class="col-sm-4">Address</dt><dd class="col-sm-8">${escapeHtml(get("address")) || "—"}, ${escapeHtml(get("area"))}, ${escapeHtml(get("city"))}</dd>
      <dt class="col-sm-4">Contact</dt><dd class="col-sm-8">${escapeHtml(get("contact_phone")) || "—"}</dd>
    </dl>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

/* ---------------------------------------------------------------------
 * 2. Drag & drop image uploader with instant previews
 * ------------------------------------------------------------------- */
function initImageUploader() {
  const dropzone = document.getElementById("hs-dropzone");
  const input = document.getElementById("hs-image-input");
  const previewGrid = document.getElementById("hs-preview-grid");
  if (!dropzone || !input || !previewGrid) return;

  let dataTransfer = new DataTransfer();

  function renderPreviews() {
    previewGrid.innerHTML = "";
    Array.from(dataTransfer.files).forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const tile = document.createElement("div");
        tile.className = "hs-preview-tile";
        tile.innerHTML = `
          <img src="${e.target.result}" alt="Preview">
          ${index === 0 ? '<span class="hs-preview-primary-badge">Primary</span>' : ""}
          <button type="button" class="hs-preview-remove" data-index="${index}" aria-label="Remove image">✕</button>
        `;
        previewGrid.appendChild(tile);
      };
      reader.readAsDataURL(file);
    });
  }

  function addFiles(fileList) {
    Array.from(fileList).forEach((file) => {
      if (file.type.match(/^image\/(jpeg|png|webp)$/)) {
        dataTransfer.items.add(file);
      }
    });
    input.files = dataTransfer.files;
    renderPreviews();
  }

  dropzone.addEventListener("click", () => input.click());
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("is-dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-dragover");
    addFiles(e.dataTransfer.files);
  });
  input.addEventListener("change", () => addFiles(input.files));

  previewGrid.addEventListener("click", (e) => {
    const btn = e.target.closest(".hs-preview-remove");
    if (!btn) return;
    const index = parseInt(btn.dataset.index, 10);
    const newDataTransfer = new DataTransfer();
    Array.from(dataTransfer.files).forEach((file, i) => {
      if (i !== index) newDataTransfer.items.add(file);
    });
    dataTransfer = newDataTransfer;
    input.files = dataTransfer.files;
    renderPreviews();
  });
}

/* ---------------------------------------------------------------------
 * 3. Dynamic Room rows (Django management-form aware)
 * ------------------------------------------------------------------- */
function initRoomFormset() {
  const container = document.getElementById("hs-room-formset");
  const addBtn = document.getElementById("hs-add-room-btn");
  const totalFormsInput = document.querySelector("[name$='-TOTAL_FORMS']");
  const emptyTemplate = document.getElementById("hs-room-empty-form");
  if (!container || !addBtn || !totalFormsInput || !emptyTemplate) return;

  addBtn.addEventListener("click", () => {
    const formIndex = parseInt(totalFormsInput.value, 10);
    const newRowHtml = emptyTemplate.innerHTML.replace(/__prefix__/g, formIndex);
    const wrapper = document.createElement("div");
    wrapper.className = "hs-room-row";
    wrapper.innerHTML = `<div class="hs-room-row-title">Room ${formIndex + 1}</div>${newRowHtml}
      <button type="button" class="hs-btn hs-btn-ghost hs-room-remove-btn" data-hs-remove-room>Remove</button>`;
    container.appendChild(wrapper);
    totalFormsInput.value = formIndex + 1;
  });

  container.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-hs-remove-room]");
    if (!btn) return;
    const row = btn.closest(".hs-room-row");
    const deleteCheckbox = row.querySelector("input[type='checkbox'][name$='-DELETE']");
    if (deleteCheckbox) {
      // Existing (already-saved) room: mark for deletion via Django's
      // formset DELETE field and hide it, rather than removing the DOM
      // node outright — Django needs this input submitted to delete it.
      deleteCheckbox.checked = true;
      row.style.display = "none";
    } else {
      row.remove();
    }
  });
}

/* ---------------------------------------------------------------------
 * 4. Loading state on submit
 * ------------------------------------------------------------------- */
function initSubmitLoadingState() {
  document.querySelectorAll("form[data-hs-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      form.querySelectorAll("button[type='submit']").forEach((btn) => {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Saving…`;
      });
    });
  });
}

/* ---------------------------------------------------------------------
 * 5. Delete confirmation modals (Bootstrap 5 modal, populated per-row)
 * ------------------------------------------------------------------- */
function initDeleteModals() {
  const modalEl = document.getElementById("hs-delete-modal");
  if (!modalEl) return;
  const nameEl = modalEl.querySelector("[data-hs-delete-name]");
  const formEl = modalEl.querySelector("form");

  document.querySelectorAll("[data-hs-delete-trigger]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      nameEl.textContent = trigger.dataset.hsDeleteName;
      formEl.action = trigger.dataset.hsDeleteUrl;
    });
  });
}
