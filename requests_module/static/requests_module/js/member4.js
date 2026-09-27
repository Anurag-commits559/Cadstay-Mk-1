/* ==========================================================
   CADSTAY MEMBER 4 — JAVASCRIPT
   Requests, Favorites, Notifications and Admin Dashboard
   ========================================================== */

(function () {
    "use strict";

    /* -------------------- HELPERS -------------------- */

    function onReady(callback) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback);
        } else {
            callback();
        }
    }

    function confirmAction(message) {
        return window.confirm(message);
    }

    /* -------------------- CONFIRMATION DIALOGS -------------------- */

    function setupConfirmations() {
        document.querySelectorAll("[data-confirm]").forEach(function (element) {
            element.addEventListener("click", function (event) {
                const message =
                    element.getAttribute("data-confirm") ||
                    "Are you sure you want to continue?";

                if (!confirmAction(message)) {
                    event.preventDefault();
                }
            });
        });

        document.querySelectorAll("[data-confirm-submit]").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                const message =
                    form.getAttribute("data-confirm-submit") ||
                    "Are you sure you want to continue?";

                if (!confirmAction(message)) {
                    event.preventDefault();
                }
            });
        });
    }

    /* -------------------- DOUBLE SUBMISSION PREVENTION -------------------- */

    function setupSubmitProtection() {
        document.querySelectorAll("form[data-prevent-double-submit]").forEach(
            function (form) {
                form.addEventListener("submit", function () {
                    const button = form.querySelector(
                        'button[type="submit"], input[type="submit"]'
                    );

                    if (!button) {
                        return;
                    }

                    if (button.dataset.submitted === "true") {
                        return;
                    }

                    button.dataset.submitted = "true";
                    button.disabled = true;

                    if (button.tagName === "BUTTON") {
                        button.dataset.originalText = button.textContent;
                        button.textContent = "Please wait...";
                    }
                });
            }
        );
    }

    /* -------------------- REQUEST MODAL -------------------- */

    function setupRequestModal() {
        const modalElement = document.getElementById("requestModal");

        if (!modalElement) {
            return;
        }

        const roomSelect = modalElement.querySelector('select[name="room"]');

        document.querySelectorAll("[data-room-request]").forEach(
            function (button) {
                button.addEventListener("click", function () {
                    const roomId = button.getAttribute("data-room-id");

                    if (roomSelect && roomId) {
                        roomSelect.value = roomId;
                    }

                    if (
                        window.bootstrap &&
                        window.bootstrap.Modal
                    ) {
                        const modal = window.bootstrap.Modal.getOrCreateInstance(
                            modalElement
                        );
                        modal.show();
                    } else {
                        console.error(
                            "Bootstrap Modal is not available. Check your Bootstrap JavaScript."
                        );
                    }
                });
            }
        );
    }

    /* -------------------- ALERT DISMISSAL -------------------- */

    function setupAlertDismissal() {
        document.querySelectorAll("[data-auto-dismiss]").forEach(
            function (alert) {
                const delay = Number(
                    alert.getAttribute("data-auto-dismiss")
                );

                if (!Number.isFinite(delay) || delay <= 0) {
                    return;
                }

                window.setTimeout(function () {
                    alert.classList.add("m4-alert-hiding");

                    window.setTimeout(function () {
                        alert.remove();
                    }, 300);
                }, delay);
            }
        );
    }

    /* -------------------- ADMIN TABLE SEARCH -------------------- */

    function setupTableSearch() {
        document.querySelectorAll("[data-table-search]").forEach(
            function (input) {
                const selector = input.getAttribute("data-table-search");
                const table = document.querySelector(selector);

                if (!table) {
                    return;
                }

                const rows = Array.from(
                    table.querySelectorAll("tbody tr")
                );

                input.addEventListener("input", function () {
                    const query = input.value.trim().toLowerCase();

                    rows.forEach(function (row) {
                        const text = row.textContent.toLowerCase();

                        row.hidden = !text.includes(query);
                    });
                });
            }
        );
    }

    /* -------------------- FAVORITE BUTTON FEEDBACK -------------------- */

    function setupFavoriteButtons() {
        document.querySelectorAll(".hs-wishlist-form").forEach(
            function (form) {
                form.addEventListener("submit", function () {
                    const button = form.querySelector(".hs-wishlist-btn");

                    if (!button) {
                        return;
                    }

                    button.disabled = true;
                    button.classList.add("m4-loading");
                });
            }
        );
    }

    /* -------------------- CANCEL REQUEST CONFIRMATION -------------------- */

    function setupCancelButtons() {
        document.querySelectorAll(
            'form[action*="/cancel/"]'
        ).forEach(function (form) {
            form.setAttribute(
                "data-confirm-submit",
                "Are you sure you want to cancel this request?"
            );
        });
    }

    /* -------------------- ADMIN ACTION CONFIRMATIONS -------------------- */

    function setupAdminConfirmations() {
        document.querySelectorAll(
            'form[action*="/toggle/"]'
        ).forEach(function (form) {
            const button = form.querySelector("button");

            if (!button) {
                return;
            }

            const text = button.textContent.trim().toLowerCase();

            if (text.includes("deactivate")) {
                form.setAttribute(
                    "data-confirm-submit",
                    "Are you sure you want to deactivate this account or listing?"
                );
            } else if (text.includes("activate")) {
                form.setAttribute(
                    "data-confirm-submit",
                    "Are you sure you want to activate this account or listing?"
                );
            }
        });
    }

    /* -------------------- REJECTION CONFIRMATION -------------------- */

    function setupRejectButtons() {
        document.querySelectorAll(
            'form[action*="/reject/"]'
        ).forEach(function (form) {
            form.setAttribute(
                "data-confirm-submit",
                "Are you sure you want to reject this request?"
            );
        });
    }

    /* -------------------- ACCEPTANCE CONFIRMATION -------------------- */

    function setupAcceptButtons() {
        document.querySelectorAll(
            'form[action*="/accept/"]'
        ).forEach(function (form) {
            form.setAttribute(
                "data-confirm-submit",
                "Are you sure you want to accept this request?"
            );
        });
    }

    /* -------------------- FAVORITE REMOVAL CONFIRMATION -------------------- */

    function setupFavoriteRemoval() {
        document.querySelectorAll(
            'form[action*="/remove/"]'
        ).forEach(function (form) {
            form.setAttribute(
                "data-confirm-submit",
                "Remove this hostel from your favorites?"
            );
        });
    }

    /* -------------------- INITIALIZE -------------------- */

    onReady(function () {
        setupConfirmations();
        setupCancelButtons();
        setupAdminConfirmations();
        setupRejectButtons();
        setupAcceptButtons();
        setupFavoriteRemoval();
        setupSubmitProtection();
        setupRequestModal();
        setupAlertDismissal();
        setupTableSearch();
        setupFavoriteButtons();
    });
})();
