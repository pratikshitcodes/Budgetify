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
async function loadMonthlyData(m1, y,m2) {
    try {
        // Budget
        const budgetRes = await apiFetch("/budget-status/current")
        const budgetData = await budgetRes.json()
        const budgetAmount = budgetData.amount || 0

        // Month 1 stats
        const statsRes = await apiFetch(
            `/budget-status/monthly-stats?month=${m1}&year=${y}`
        );

        const stats = await statsRes.json();

        // Cards
        document.getElementById("m1Total").textContent = `₹${formatAmount(stats.this_month_total)}`
        document.getElementById("m2Total").textContent = `₹${formatAmount(stats.prev_month_total)}`
        document.getElementById("m1Count").textContent = `${stats.this_month_count} transactions`
        document.getElementById("m2Count").textContent = `${stats.prev_month_count} transactions`
        document.querySelector("#projectedEnd").textContent = `₹${formatAmount(stats.projected_daily)}`
        document.querySelector(".proj-sub span").textContent = `₹${formatAmount(stats.current_avg_pace)}`


        const card = document.querySelector("#safeCard");
        const status = document.querySelector("#status");

        status.textContent = stats.status;

        card.classList.remove("warning", "be_cautious", "safe");
        status.classList.remove("warning", "caution", "safe");

        if (stats.status === "Warning") {
            card.classList.add("warning");
            status.classList.add("warning");
        }
        else if (stats.status === "Be Cautious") {
            card.classList.add("be_cautious");
            status.classList.add("caution");
        }
        else {
            card.classList.add("safe");
            status.classList.add("safe");
        }
        document.querySelector("#insight").textContent = `${stats.insight}`


        // Change calculation
        const change = stats.this_month_total - stats.prev_month_total
        const pct = Math.abs(stats.prev_month_total > 0
            ? ((change / stats.prev_month_total) * 100).toFixed(1)
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
            stats.highest ? `${stats.highest.title} ₹${formatAmount(stats.highest.amount)}` : "—"
        document.getElementById("average").textContent = `₹${formatAmount(stats.recommended_daily_pace)}`
        const top = stats.most_frequent_entry;

        document.getElementById("topCat").textContent =
            top
                ? `${top.name} (${top.count}×)`
                : "—";
        document.getElementById("weekday").textContent = `₹${formatAmount(stats.weekday_total)}`
        document.getElementById("weekend").textContent = `₹${formatAmount(stats.weekend_total)}`
        document.getElementById("firstHalf").textContent = `₹${formatAmount(stats.first_half)}`
        document.getElementById("secondHalf").textContent = `₹${formatAmount(stats.second_half)}`

        // Top 3
        const top3 = document.getElementById("top3Container")
        top3.innerHTML = ""
        if (stats.top3_expenses?.length) {
            stats.top3_expenses.forEach((e, i) => {
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
        renderWormChart(stats.this_month_daily, stats.prev_month_daily, budgetAmount, m1, m2)

        // Category bars — combine both months
        const comparison=stats.category_comparison;
        //object.keys(data_str)->this returns all the keys of the data_str
        const labels=Object.keys(comparison)
        const thisMonthData=labels.map(cat=> comparison[cat].this)
        const prevMonthData=labels.map(cat=>comparison[cat].prev)
        
        renderCategoryBars(m1,m2,thisMonthData,prevMonthData,labels);

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
                    backgroundColor: "#1D9E75",
                    borderColor: "#1D9E75",
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Budget Limit",
                    data: Array(days.length).fill(budget),
                    backgroundColor: "#f87171",
                    borderColor: "#f87171",
                    borderDash: [8, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Avg Projection",
                    data: avgLine,
                    backgroundColor: "#fbbf24",
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
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#888",
                        boxWidth: 10,
                        boxHeight: 10,
                        usePointStyle:true,
                        pointStyle:"circle",
                        font: { family: "Poppins", size: 12 }, padding: 16 }
                },
                tooltip: {
                    backgroundColor: "#18181f",
                    borderColor: "#2a2a35",
                    borderWidth: 1,
                    titleColor: "#fff",
                    bodyColor: "#aaa",
                    callbacks: {
                        title:context=>{
                            return `Day ${context[0].label}`;
                        },
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
                    grid: { color: "#1e1e28" },
                    title:{
                        display:true,
                        text:"Days"
                    }
                },
                y: {
                    ticks: {
                        color: "#888",
                        font: { family: "Poppins" },
                        callback: val => `₹${val.toLocaleString("en-IN")}`,
                        stepSize:50000
                    },
                    grid: { color: "#1e1e28" },
                    title:{
                        display:true,
                        text:"Expenses (₹)"
                    }
                }
            }
        }
    })
}
let categoryChartInstance=null;
function renderCategoryBars(m1,m2,thisMonth,prevMonth,labels){
    if(categoryChartInstance){
        categoryChartInstance.destroy();
    }
    categoryChartInstance=new Chart(document.querySelector("#categoryChart"),{
        type:"bar",
        data:{
            labels:labels,
            datasets:[
                {
                    label:monthNames[m1],
                    data:thisMonth,
                    backgroundColor:"rgb(121, 60, 227)"

                },
                {
                    label:monthNames[m2],
                    data:prevMonth,
                    backgroundColor:"rgb(19, 177, 72)",
                    borderColor:"rgb(0, 189, 136)"
                }
            ]
        },
        options:{
            responsive:true,
            interaction:{
                mode:"index",
                intersect:false,
                axis:"x"
            },
            plugins:{
                legend:{
                    position:"bottom",
                    labels:{
                        color: "#888",
                        boxWidth: 10,
                        boxHeight: 10,
                        usePointStyle:true,
                        pointStyle:"circle",
                        padding:20,
                        font:{
                            size:12,
                            family:"Poppins"
                        }
                    }
                },
                tooltip: {
                    backgroundColor: "#18181f",
                    borderColor: "#2a2a35",
                    borderWidth: 1,
                    titleColor: "#fff",
                    bodyColor: "#aaa",
                    callbacks: {
                        title:context=>{
                            return `${context[0].label}`;
                        },
                        label: ctx => `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString("en-IN")}`
                    }
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
    loadMonthlyData(m1, y1, m2,y2)
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
 

loadMonthlyData(currentMonth, currentYear, prevMonth)

