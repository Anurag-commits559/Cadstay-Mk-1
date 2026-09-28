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
