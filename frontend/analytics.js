const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "./expense_login.html";
}
async function loadCharts(){
    const response = await apiFetch("/expenses/")
    const expenses = await response.json()
    renderChart(expenses)  // bar chart

    // Budget data ke liye loadDashboard jaisa call
    const amount = parseFloat(prompt("Enter monthly budget:"))
    if(!amount || isNaN(amount)) return
    const month = new Date().getMonth() + 1
    const year = new Date().getFullYear()
    
    const budgetRes = await apiFetch("/budget-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, month, year })
    })
    const budgetData = await budgetRes.json()
    renderBudgetChart(budgetData.total_spent, budgetData.remaining)
}

loadCharts()  // page load pe call karo
// Dashboard button
document.querySelectorAll(".sidebar-btn")[0]
    .addEventListener("click", () => {
        window.location.href = "./expense_tracker.html"
    })
// Page load hone par analytics button ko active karo
document.querySelectorAll(".sidebar-btn")[1].classList.add("active")
document.querySelectorAll(".sidebar-btn")[0].classList.remove("active")
document.querySelector(".log-out-btn")
    .addEventListener("click", () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "./expense_login.html"
    });
//analytics page
document.querySelectorAll(".sidebar-btn")[1]
    .addEventListener("click", () => {
        window.location.href = "./analytics.html"
    })
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