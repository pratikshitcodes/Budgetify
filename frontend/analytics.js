const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "./expense_login.html";
}
const selectedMonth=localStorage.getItem("selectedMonth");
const selectedYear=localStorage.getItem("selectedYear");

async function loadCharts(){
    const currentRes = await apiFetch(`/budget-status/current?month=${selectedMonth}&year=${selectedYear}`)
    if(!currentRes.status){
        window.location.href="./expense_tracker.html";
        return ;
    }
    // Expenses fetch karo
    const response = await apiFetch(`/expenses/chart-data?month=${selectedMonth}&year=${selectedYear}`)
    const expenses = await response.json()
    renderChart(expenses)

    // Budget check karo — same logic as dashboard
    const currentData = await currentRes.json()
    if(!currentData){
        window.location.href="./expense_tracker.html"
    }
    let amount = currentData.amount

    // Doughnut chart ke liye budget analysis call karo
    const budgetRes = await apiFetch(`/budget-status/analytics?month=${selectedMonth}&year=${selectedYear}`)

    const budgetData = await budgetRes.json()
    renderBudgetChart(budgetData.total_spent, budgetData.remaining>0?budgetData.remaining:0)

    const parts = budgetData.insight.split('TIP:')
    document.getElementById("insightText").textContent = parts[0].replace('INSIGHT:', '').trim()

    document.getElementById("insightTip").textContent = parts[1]?.trim() || ''
}
loadCharts()

document.querySelector(".log-out-btn")
    .addEventListener("click", () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "./expense_login.html"
    });
function renderChart(expenses){
    const categories = {}
    expenses.forEach(e => {
        categories[e.category] = (categories[e.category] || 0) + e.amount
    })

    new Chart(document.getElementById("spendingChart"),{
        type: "bar",
        data:{
            labels: Object.keys(categories),
            datasets:[{
                label: "Spent (₹)",
                data: Object.values(categories),
                backgroundColor:[
                    "rgba(124,92,252,0.8)",
                    "rgba(29,158,117,0.8)",
                    "rgba(239,159,39,0.8)",
                    "rgba(226,71,75,0.8)",
                    "rgba(96,165,250,0.8)",
                    "rgba(251,191,36,0.8)",
                ],
                borderRadius: 6,
            }]
        },
        options:{
            responsive: true,
            plugins:{
                legend:{ display: false }
            },
            scales:{
                x:{
                    ticks:{ color:"#888", font:{ family:"Poppins" }},
                    grid:{ color:"#1e1e28" }
                },
                y:{
                    type: 'logarithmic',
                    ticks:{
                        color:"#888",
                        callback: (val) => `₹${val.toLocaleString("en-IN")}`
                    },
                    grid:{ color:"#1e1e28" }
                }
            }
        }
    })
}
function renderBudgetChart(spent, remaining){
    new Chart(document.getElementById("budgetChart"),{
        type: "doughnut",
        data:{
            labels: ["Spent", "Remaining"],
            datasets:[{
                data: [spent, remaining],
                backgroundColor:[
                    "rgba(124,92,252,0.8)",  // purple — spent
                    "rgba(29,158,117,0.8)",  // green — remaining
                ],
                borderWidth: 0,
                borderRadius: 4,
            }]
        },
        options:{
            responsive: true,
            plugins:{
                legend:{
                    position: "bottom",
                    labels:{ color:"#888", font:{ family:"Poppins" }}
                }
            }
        }
    })
}