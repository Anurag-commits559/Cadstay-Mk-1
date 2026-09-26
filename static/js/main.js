// NoBroker Hostel & Roommate Finder
// Placeholder for shared front-end behaviour. Bootstrap JS handles the
// navbar toggle and alert dismissal already; add project-wide JS here
// as future modules need it.

document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss success/info alerts after a few seconds.
    document.querySelectorAll(".alert-success, .alert-info").forEach(function (alertEl) {
        setTimeout(function () {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            alert.close();
        }, 5000);
    });
});
