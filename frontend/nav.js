const NAV_ROUTES = {
    dashboard: "./expense_tracker.html",
    analytics: "./analytics.html",
    monthly: "./monthly.html",
    battle: "./battle.html",
    groups: "./groups.html",
    records: "./expense_tracker.html"
};

document.querySelectorAll(".sidebar-btn[data-nav]").forEach(btn => {
    btn.addEventListener("click", () => {
        const target = NAV_ROUTES[btn.dataset.nav];
        if (target) window.location.href = target;
    });
});

document.querySelector(".log-out-btn")?.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "./expense_login.html";
});
