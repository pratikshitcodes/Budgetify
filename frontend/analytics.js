const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "./expense_login.html";
}

// Safer month/year extraction with fallbacks
const storedMonth = localStorage.getItem("selectedMonth");
const storedYear = localStorage.getItem("selectedYear");

const selectedMonth = (storedMonth && storedMonth !== "null") ? Number(storedMonth) : (new Date().getMonth() + 1);
const selectedYear = (storedYear && storedYear !== "null") ? Number(storedYear) : new Date().getFullYear();

const monthNames = ["", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

// Update UI text for current month
if (document.getElementById("currentMonth")) {
    document.getElementById("currentMonth").textContent = `${monthNames[selectedMonth]} ${selectedYear}`;
}

async function loadCharts() {
    console.log(`Loading analytics for ${selectedMonth}/${selectedYear}`);
    try {
        // 1. Fetch Category Expenses
        const response = await apiFetch(`/expenses/chart-data?month=${selectedMonth}&year=${selectedYear}`);
        if (response.ok) {
            const expenses = await response.json();
            console.log("Chart Data Received:", expenses);
            if (expenses && expenses.length > 0) {
                renderChart(expenses);
            } else {
                showEmptyChartMessage("spendingChart", "No expenses logged for this month.");
            }
        } else {
            console.error("Chart data fetch failed:", response.status);
            showEmptyChartMessage("spendingChart", "Failed to load category data.");
        }

        // 2. Check Budget Status
        const currentRes = await apiFetch(`/budget-status/current?month=${selectedMonth}&year=${selectedYear}`);
        
        if (!currentRes.ok) {
            console.warn("Budget not found for this month.");
            showNoBudgetMessage();
        } else {
            const currentData = await currentRes.json();
            console.log("Budget Data Received:", currentData);
            
            // 3. Fetch AI Analytics & Budget Overview (only if budget exists)
            const budgetRes = await apiFetch(`/budget-status/analytics?month=${selectedMonth}&year=${selectedYear}`);
            if (budgetRes.ok) {
                const budgetData = await budgetRes.json();
                renderBudgetChart(budgetData.total_spent, budgetData.remaining > 0 ? budgetData.remaining : 0);

                if (budgetData.insight) {
                    const parts = budgetData.insight.split('TIP:');
                    if (document.getElementById("insightText")) {
                        document.getElementById("insightText").textContent = parts[0].replace('INSIGHT:', '').trim();
                    }
                    if (document.getElementById("insightTip")) {
                        document.getElementById("insightTip").textContent = parts[1]?.trim() || 'Keep tracking your expenses!';
                    }
                }
            } else {
                showEmptyChartMessage("budgetChart", "Could not load budget analytics.");
            }
        }

    } catch (error) {
        console.error("Analytics Error:", error);
        if (document.getElementById("insightText")) {
            document.getElementById("insightText").textContent = "An error occurred while connecting to the server.";
        }
    }
}

function showNoBudgetMessage() {
    if (document.getElementById("insightText")) {
        document.getElementById("insightText").innerHTML = `
            <div style="color: #888; font-size: 14px;">
                No budget found for ${monthNames[selectedMonth]} ${selectedYear}.<br>
                <a href="./expense_tracker.html" style="color: #7c5cfc; text-decoration: none; font-weight: 600;">Set one up in the Dashboard</a> to see complete analytics.
            </div>
        `;
    }
    if (document.getElementById("insightTip")) {
        document.getElementById("insightTip").textContent = "Set a budget to unlock AI insights.";
    }
    showEmptyChartMessage("budgetChart", "Budget not initialized.");
}

function showEmptyChartMessage(canvasId, message) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw message
    ctx.fillStyle = "#555";
    ctx.font = "14px Poppins";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(message, width / 2, height / 2);
}

loadCharts();

const logoutBtn = document.querySelector(".log-out-btn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "./expense_login.html";
    });
}

let spendingChartInst = null;
let budgetChartInst = null;

function renderChart(expenses) {
    const categories = {};
    expenses.forEach(e => {
        const cat = e.category || "Uncategorized";
        categories[cat] = (categories[cat] || 0) + parseFloat(e.amount);
    });

    const ctx = document.getElementById("spendingChart");
    if (!ctx) return;

    if (spendingChartInst) {
        spendingChartInst.destroy();
    }

    spendingChartInst = new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(categories),
            datasets: [{
                label: "Spent (₹)",
                data: Object.values(categories),
                backgroundColor: [
                    "rgba(124, 92, 252, 0.7)",
                    "rgba(52, 211, 153, 0.7)",
                    "rgba(251, 191, 36, 0.7)",
                    "rgba(248, 113, 113, 0.7)",
                    "rgba(96, 165, 250, 0.7)",
                    "rgba(167, 139, 250, 0.7)"
                ],
                borderColor: [
                    "#7c5cfc", "#10b981", "#fbbf24", "#f87171", "#60a5fa", "#a78bfa"
                ],
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#18181f',
                    titleColor: '#fff',
                    bodyColor: '#ccc',
                    borderColor: '#2a2a35',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    ticks: { color: "#888", font: { family: "Poppins", size: 11 } },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#888",
                        font: { size: 10 },
                        callback: (val) => `₹${val.toLocaleString("en-IN")}`
                    },
                    grid: { color: "rgba(255, 255, 255, 0.05)" }
                }
            }
        }
    });
}

function renderBudgetChart(spent, remaining) {
    const ctx = document.getElementById("budgetChart");
    if (!ctx) return;

    if (budgetChartInst) {
        budgetChartInst.destroy();
    }

    budgetChartInst = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Spent", "Remaining"],
            datasets: [{
                data: [spent, remaining],
                backgroundColor: [
                    "rgba(124, 92, 252, 0.8)",
                    "rgba(91, 255, 116, 0.78)"
                ],
                hoverBackgroundColor: [
                    "rgba(124, 92, 252, 1)",
                    "rgba(91, 255, 116, 0.78)"
                ],
                borderWidth: 0,
                weight: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#aaa",
                        font: { family: "Poppins", size: 11 },
                        padding: 15,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}
