// CadStay — Shared Frontend Architecture & Interactive Polish

// 1. Unhandled Promise Rejection & Global Error Guard
window.addEventListener("unhandledrejection", function (event) {
    console.warn("CadStay: Caught unhandled promise rejection:", event.reason);
});

// 2. Alert Dismissal: Auto-dismiss success/info alerts, keep error/danger alerts visible
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".alert-success, .alert-info").forEach(function (alertEl) {
        setTimeout(function () {
            try {
                if (typeof bootstrap !== "undefined" && bootstrap.Alert) {
                    const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
                    alert.close();
                }
            } catch (err) {
                // Ignore dismissal errors
            }
        }, 5000);
    });
});

// 3. Active Nav Link Highlighting
document.addEventListener("DOMContentLoaded", function () {
    const pathname = window.location.pathname;
    const links = document.querySelectorAll(".cs-nav-link");
    links.forEach(function (link) {
        const href = link.getAttribute("href");
        if (!href) return;
        let isActive = false;
        if (href === "/" || href === "") {
            isActive = (pathname === "/" || pathname === "");
        } else {
            isActive = pathname.indexOf(href) === 0;
        }
        if (isActive) {
            link.classList.add("cs-nav-link--active");
        }
    });
});

// 4. Header Scroll State
(function () {
    const header = document.querySelector(".cs-header");
    if (!header) return;
    function onScroll() {
        if (window.scrollY > 40) {
            header.classList.add("cs-header--scrolled");
        } else {
            header.classList.remove("cs-header--scrolled");
        }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
})();

// 5. Submit Button Loading Spinners & Double-Submission Prevention
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form").forEach(function (form) {
        // Skip search/filter get forms or forms explicitly opted out
        if (form.method && form.method.toUpperCase() === "GET") return;
        if (form.hasAttribute("data-no-spinner")) return;

        form.addEventListener("submit", function (e) {
            // If HTML5 form validation fails, let native UI highlight the error
            if (form.checkValidity && !form.checkValidity()) {
                return;
            }

            const submitBtns = form.querySelectorAll("button[type='submit'], input[type='submit']");
            submitBtns.forEach(function (btn) {
                // Avoid breaking if already submitted
                if (btn.disabled) return;
                
                // Store original text
                btn.dataset.originalHtml = btn.innerHTML;
                
                // Prepend loading spinner
                const spinner = document.createElement("span");
                spinner.className = "spinner-border spinner-border-sm me-2";
                spinner.setAttribute("role", "status");
                spinner.setAttribute("aria-hidden", "true");
                
                if (btn.tagName === "BUTTON") {
                    btn.disabled = true;
                    btn.classList.add("disabled");
                    btn.innerHTML = "";
                    btn.appendChild(spinner);
                    btn.appendChild(document.createTextNode(" Processing…"));
                }
            });
        });
    });
});

// 6. Smooth Reveal Animations via IntersectionObserver
document.addEventListener("DOMContentLoaded", function () {
    if ("IntersectionObserver" in window) {
        const revealElements = document.querySelectorAll("[data-reveal]");
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: "0px 0px -40px 0px"
        });

        revealElements.forEach(function (el) {
            observer.observe(el);
        });
    } else {
        // Fallback for older browsers
        document.querySelectorAll("[data-reveal]").forEach(function (el) {
            el.classList.add("is-visible");
        });
    }
});
