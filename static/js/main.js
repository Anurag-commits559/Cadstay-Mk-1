// CadStay — shared front-end behaviour. Bootstrap handles the
// navbar toggle and alert dismissal; keep this file light.

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".alert-success, .alert-info").forEach(function (alertEl) {
        setTimeout(function () {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            alert.close();
        }, 5000);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    var pathname = window.location.pathname;
    var links = document.querySelectorAll(".cs-nav-link");
    links.forEach(function (link) {
        var href = link.getAttribute("href");
        if (!href) return;
        var isActive = false;
        if (href === "/") {
            isActive = (pathname === "/" || pathname === "");
        } else {
            isActive = pathname.indexOf(href) === 0;
        }
        if (isActive) {
            link.classList.add("cs-nav-link--active");
        }
    });
});

(function () {
    var header = document.querySelector(".cs-header");
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
