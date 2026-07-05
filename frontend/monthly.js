const token = localStorage.getItem("access_token")
if (!token) window.location.href = "./expense_login.html"

// Set current month in topbar
const monthName = new Date().toLocaleDateString("en-IN", { month: "long", year: "numeric" })
document.getElementById("currentMonth").textContent = monthName

// Format amount
const formatAmount = (amount) => parseFloat(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 2, maximumFractionDigits: 2
})

// Month names
const monthNames = ["", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]

let wormChartInstance = null

// Navigation
document.getElementById("navDashboard").addEventListener("click", () => window.location.href = "./expense_tracker.html")
document.getElementById("navAnalytics").addEventListener("click", () => window.location.href = "./analytics.html")

// Logout
document.querySelector(".log-out-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    window.location.href = "./expense_login.html"
})

// Load on page start — current vs previous month
async function loadMonthlyData(m1, y1, m2, y2) {
    try {
        // Budget
        const budgetRes = await apiFetch("/budget-status/current")
        const budgetData = await budgetRes.json()
        const budgetAmount = budgetData.amount || 0

        // Month 1 stats
        const stats1Res = await apiFetch(`/budget-status/monthly-stats?month=${m1}&year=${y1}`)
        const stats1 = await stats1Res.json()

        // Month 2 stats
        const stats2Res = await apiFetch(`/budget-status/monthly-stats?month=${m2}&year=${y2}`)
        const stats2 = await stats2Res.json()

        // Cards
        document.getElementById("m1Total").textContent = `₹${formatAmount(stats1.this_month_total)}`
        document.getElementById("m2Total").textContent = `₹${formatAmount(stats2.this_month_total)}`
        document.getElementById("m1Count").textContent = `${stats1.this_month_count} transactions`
        document.getElementById("m2Count").textContent = `${stats2.this_month_count} transactions`

        // Change calculation
        const change = stats1.this_month_total - stats2.this_month_total
        const pct = Math.abs(stats2.this_month_total > 0
            ? ((change / stats2.this_month_total) * 100).toFixed(1)
            : null)

        const changeCard = document.getElementById("diffCard")
        if (pct !== null) {
            const isIncrease = change > 0
            document.getElementById("changeVal").textContent = `${isIncrease ? "+" : ""}${pct}%`
            document.getElementById("changeType").textContent = isIncrease ? "Higher than last month ↑" : "Lower than last month ↓"
            if (isIncrease) changeCard.classList.add("danger")
            else changeCard.classList.remove("danger")
        }

        // Stats — Month 1
        document.getElementById("highest").textContent =
            stats1.highest ? `${stats1.highest.title} ₹${formatAmount(stats1.highest.amount)}` : "—"
        document.getElementById("average").textContent = `₹${formatAmount(stats1.average)}`
        document.getElementById("topCat").textContent =
            stats1.most_frequent_categories?.length
                ? `${stats1.most_frequent_categories[0].name} (${stats1.most_frequent_categories[0].count}×)`
                : "—"
        document.getElementById("weekday").textContent = `₹${formatAmount(stats1.weekday_total)}`
        document.getElementById("weekend").textContent = `₹${formatAmount(stats1.weekend_total)}`
        document.getElementById("firstHalf").textContent = `₹${formatAmount(stats1.first_half)}`
        document.getElementById("secondHalf").textContent = `₹${formatAmount(stats1.second_half)}`

        // Top 3
        const top3 = document.getElementById("top3Container")
        top3.innerHTML = ""
        if (stats1.top3_expenses?.length) {
            stats1.top3_expenses.forEach((e, i) => {
                top3.innerHTML += `
                    <div class="top3-item">
                        <div class="rank">${i + 1}</div>
                        <div class="t3-info">
                            <div class="t3-name">${e.title}</div>
                            <div class="t3-cat">${e.category}</div>
                        </div>
                        <div class="t3-amt">₹${formatAmount(e.amount)}</div>
                    </div>`
            })
        } else {
            top3.innerHTML = `<div class="no-data">No expenses this month</div>`
        }

        // Worm chart
        renderWormChart(stats1.this_month_daily, stats2.this_month_daily, budgetAmount, m1, m2)

        // Category bars — combine both months
        const allCats = new Set([
            ...Object.keys(stats1.category_comparison || {}),
            ...Object.keys(stats2.category_comparison || {})
        ])
        const combined = {}
        allCats.forEach(cat => {
            combined[cat] = {
                this: stats1.category_comparison?.[cat]?.this || 0,
                prev: stats2.category_comparison?.[cat]?.this || 0
            }
        })
        renderCategoryBars(combined)

    } catch (err) {
        console.error("Error:", err)
    }
}
function renderWormChart(thisMonth, prevMonth, budget, m1, m2) {
    if (wormChartInstance) wormChartInstance.destroy()

    const today = new Date().getDate()
    const days = thisMonth.map(d => d.day)
    
    // Average daily spend line
    const totalSpent = thisMonth[thisMonth.length - 1]?.cumulative || 0
    const avgDaily = totalSpent / today
    const avgLine = days.map(d => parseFloat((avgDaily * d).toFixed(2)))

    wormChartInstance = new Chart(document.getElementById("wormChart"), {
        type: "line",
        data: {
            labels: days,
            datasets: [
                {
                    label: monthNames[m1],
                    data: thisMonth.map(d => d.cumulative),
                    borderColor: "#7c5cfc",
                    backgroundColor: "rgba(124,92,252,0.05)",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: days.map(d => d === today ? 5 : 0),
                    pointBackgroundColor: "#7c5cfc",
                    fill: true
                },
                {
                    label: monthNames[m2],
                    data: prevMonth.map(d => d.cumulative),
                    borderColor: "#1D9E75",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Budget Limit",
                    data: Array(days.length).fill(budget),
                    borderColor: "#f87171",
                    borderDash: [8, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Avg Projection",
                    data: avgLine,
                    borderColor: "#fbbf24",
                    borderDash: [4, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: "index",        // ← hover tooltip all lines at once
                intersect: false
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#888", font: { family: "Poppins", size: 12 }, padding: 16 }
                },
                tooltip: {
                    backgroundColor: "#18181f",
                    borderColor: "#2a2a35",
                    borderWidth: 1,
                    titleColor: "#fff",
                    bodyColor: "#aaa",
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString("en-IN")}`
                    }
                },
                // Today's marker — vertical line
                annotation: {
                    annotations: {
                        todayLine: {
                            type: "line",
                            xMin: today - 1,
                            xMax: today - 1,
                            borderColor: "#555",
                            borderWidth: 1,
                            borderDash: [4, 4],
                            label: {
                                display: true,
                                content: "Today",
                                color: "#888",
                                font: { size: 10 }
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#888", font: { family: "Poppins" } },
                    grid: { color: "#1e1e28" }
                },
                y: {
                    ticks: {
                        color: "#888",
                        font: { family: "Poppins" },
                        callback: val => `₹${val.toLocaleString("en-IN")}`
                    },
                    grid: { color: "#1e1e28" }
                }
            }
        }
    })
}
// Compare button
document.getElementById("compareBtn").addEventListener("click", () => {
    const m1 = parseInt(document.getElementById("month1").value)
    const y1 = parseInt(document.getElementById("year1").value)
    const m2 = parseInt(document.getElementById("month2").value)
    const y2 = parseInt(document.getElementById("year2").value)
    loadMonthlyData(m1, y1, m2, y2)
})

// Default load — current vs previous
const today = new Date()
const currentMonth = today.getMonth() + 1
const currentYear = today.getFullYear()
const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1
const prevYear = currentMonth === 1 ? currentYear - 1 : currentYear

document.getElementById("month1").value = currentMonth
document.getElementById("year1").value = currentYear
document.getElementById("month2").value = prevMonth
document.getElementById("year2").value = prevYear

loadMonthlyData(currentMonth, currentYear, prevMonth, prevYear)