const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "./expense_login.html";
}
const monthNames=[
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
];
monthNames.forEach((month, index) => {
    const option = document.createElement("option");
    option.value = index + 1;
    option.textContent = month;
    monthSelector.appendChild(option);
});
for (let year = 2024; year <= 2030; year++) {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearSelector.appendChild(option);
}
const hour = new Date().getHours()
const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"
document.getElementById("greeting").textContent = `${greeting} 👋`

const monthSelect = document.getElementById("monthSelector");
const yearSelect = document.getElementById("yearSelector");
const savedMonth = localStorage.getItem("selectedMonth");
const savedYear = localStorage.getItem("selectedYear");

const today = new Date();

const currentMonth = savedMonth
    ? Number(savedMonth)
    : today.getMonth() + 1;

const currentYear = savedYear
    ? Number(savedYear)
    : today.getFullYear();

monthSelect.value = currentMonth;
yearSelect.value = currentYear;

let selectedMonth = currentMonth;
let selectedYear = currentYear;
localStorage.setItem("selectedmonth",selectedMonth);
localStorage.setItem("selectedyear",selectedYear);

document.getElementById("currentMonth").textContent =
    `${monthNames[selectedMonth-1]} ${selectedYear}`;

async function loadExpenses() {
    const month = selectedMonth;
    const year = selectedYear;
    const expenseTableBody = document.querySelector("#expenseTableBody");
    expenseTableBody.innerHTML = "";
    const response = await apiFetch(`/expenses?month=${month}&year=${year}`);

    const expenses = await response.json();
    expenses.forEach(expense => {
        const tr = document.createElement("tr");

        const td_title = document.createElement("td");
        td_title.innerText = expense.title;

        const td_category = document.createElement("td");
        td_category.innerText = expense.category;

        const td_amount = document.createElement("td");
        td_amount.innerText = formatAmount(expense.amount);

        const td_date = document.createElement("td");
        const date = new Date(expense.created_at);
        td_date.innerText = date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        });

        const td_more = document.createElement("td");
        const viewBtn = document.createElement("button");

        viewBtn.innerText = "View";
        viewBtn.classList.add("view-btn")

        const deleteBtn = document.createElement("button")
        deleteBtn.innerText = "Delete";
        deleteBtn.classList.add("delete-btn");

        deleteBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                const response = await apiFetch("/expenses" + `/${expense.id}`, {
                    method: "DELETE",
                });

                expenseTableBody.innerHTML = "";
                loadExpenses();
            }
            catch (error) {
                console.log("Delete failed:", error);
            }
        });
        viewBtn.addEventListener("click",async(e)=>{
            e.preventDefault();
            editingExpenseId=expense.id;

            expense_heading.textContent="Edit Expense";
            submitBtn.textContent="Update Expense";

            expense_title.value=expense.title;
            expense_amount.value=expense.amount;
            expense_desc.value=expense.description;
            expense_category.value=expense.category;
            openForm();

        })
        td_more.appendChild(viewBtn);
        td_more.appendChild(deleteBtn);
        tr.appendChild(td_title);
        tr.appendChild(td_category);
        tr.appendChild(td_amount);
        tr.appendChild(td_date);
        tr.appendChild(td_more)
        expenseTableBody.appendChild(tr);
    });
}

loadExpenses();
let editingExpenseId=null;

const addexpenseForm = document.querySelector("#addExpenseForm");
const expense_heading=document.querySelector(".form-heading");
const expense_title = document.querySelector("#expenseTitle");
const expense_amount = document.querySelector("#expenseAmount");
const expense_category = document.querySelector("#expenseCategory");
const expense_desc = document.querySelector("#expenseDescription");
const submitBtn=document.querySelector(".submit-expense-btn");
addexpenseForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = expense_title.value;
    const amount = parseFloat(expense_amount.value);
    const category = expense_category.value;
    const description = expense_desc.value;
    if (!title || !amount || !category) {
        alert("Please fill all fields")
        return
    }
    if(editingExpenseId===null){
        //add
        try {
            const response = await apiFetch("/expenses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, amount, description, category })
            });
            const data = await response.json();
            expenseTableBody.innerHTML = "";
            loadExpenses();
        }
        catch (error) {
            console.log("error:", error);
        }
        removeForm();
    }
    else{
        try{
            const response=await apiFetch(`/expenses/${editingExpenseId}`,{
                method:"PUT",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    title,
                    amount,
                    description,
                    category
                })
            });
            const data = await response.json();
            expenseTableBody.innerHTML = "";
            loadExpenses();
        }
        catch (error) {
            console.log("error:", error);
        }
        removeForm();
    }
});


const searchInput = document.getElementById("searchInput");

if (searchInput) {
    searchInput.addEventListener("input", function () {
        const rows = document.querySelectorAll("tbody tr");
        const searchValue = searchInput.value.toLowerCase();

        rows.forEach(function (row) {
            const rowText = row.innerText.toLowerCase();

            if (rowText.includes(searchValue)) {
                row.style.display = "";
            }
            else {
                row.style.display = "none";
            }
        })
    });
}

const modal_overlay = document.querySelector("#expenseModal");
const addExpenseBtn = document.querySelector(".addBtn")
const closeBtn = document.querySelector("#closeExpenseModal")
function openForm() {
    modal_overlay.classList.add("show");
}
function removeForm() {
    editingExpenseId=null;
    expense_title.value = "";
    expense_amount.value = "";
    expense_category.value = "";
    expense_desc.value = "";

    expense_heading.textContent = "Add Expense";
    submitBtn.textContent = "Add Expense";
    modal_overlay.classList.remove("show");
}
closeBtn.addEventListener("click", removeForm);
addExpenseBtn.addEventListener("click",async(e)=>{
    openForm();
} );

document.querySelector(".log-out-btn")
    .addEventListener("click", () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "./expense_login.html"
    });
const totalSpent=document.querySelector(".total-spent-val");
const remainingAmount=document.querySelector(".remaining-val");
const budgetStatus=document.querySelector(".status-val");
const formatAmount = (amount) => {
        return parseFloat(amount).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
    }


//analytics page
document.querySelectorAll(".sidebar-btn")[1]
    .addEventListener("click", () => {
        window.location.href = "./analytics.html"
    });
document.querySelectorAll(".sidebar-btn")[2]
    .addEventListener("click", () => {
        window.location.href = "./monthly.html"
    });

const budgetModal=document.getElementById("budgetModal");



// Open Modal
document.getElementById("openBudgetModal").addEventListener("click",()=>{

    document.getElementById("modalMonthYear").textContent=
        `${monthNames[selectedMonth-1]} ${selectedYear}`;

    document.getElementById("budgetInput").value=currentBudget;

    budgetModal.classList.add("show");
});

// Close
function closeBudgetModal(){
    budgetModal.classList.remove("show");
}

document.getElementById("closeBudgetModal")
.addEventListener("click",closeBudgetModal);

document.getElementById("cancelBudget")
.addEventListener("click",closeBudgetModal);

budgetModal.addEventListener("click",(e)=>{

    if(e.target===budgetModal){
        closeBudgetModal();
    }

});

let budgetExists = false;
let currentBudget=0;
function saveBudget(method){
    document.getElementById("saveBudget")
    .addEventListener("click",async()=>{
        console.log("Save button clicked");

        const budget=Number(document.getElementById("budgetInput").value);

        if(budget<=0){
            alert("Please enter a valid budget.");
            return;
        }

        const method = budgetExists ? "PUT" : "POST";

        try{

            await apiFetch("/budget-status",{
                    method:method,
                    headers:{
                        "Content-Type":"application/json"
                    },
                    body:JSON.stringify({
                        amount:budget,
                        month:selectedMonth,
                        year:selectedYear})
            })
            closeBudgetModal();
            await loadDashboard();
            await loadExpenses();

        }
        catch(err){
            console.error(err);
            alert("Unable set the budget.");
        }

    });
}
const saveBudgetBtn = document.getElementById("saveBudget");
saveBudgetBtn.addEventListener("click", saveBudget);

async function loadDashboard(){
        // Shows a popup with a text input
        // User types 10000 and clicks OK
        // budget = "10000" (string)
        const response=await apiFetch(`/budget-status/current?month=${selectedMonth}&year=${selectedYear}`);
        const data=await response.json();
        let amount=data.amount;
        if(!amount){
            document.getElementById("modalMonthYear").textContent=
            `${monthNames[selectedMonth-1]} ${selectedYear}`;

            document.getElementById("budgetInput").value=0;

            budgetModal.classList.add("show");
            return ; 
        } 
        budgetExists=true;
        currentBudget=amount;

        const month = selectedMonth;
        const year = selectedYear;

        try{
            const response=await apiFetch(`/budget-status/analytics?month=${selectedMonth}&year=${selectedYear}`);
            const data=await response.json();
            if(!response.ok){
                alert(data.detail||"Budget Call Failed! Try again")
            }
            totalSpent.textContent=`₹${formatAmount(data.total_spent)}`;
            remainingAmount.textContent=`₹${formatAmount(data.remaining>0?data.remaining:0)}`;
            budgetStatus.textContent=data.remaining>0?`${data.status}`:`${data.status} BY ₹${formatAmount(Math.abs(data.remaining))}`;

            const percentage=(data.total_spent/data.budget)*100;
            document.querySelector("#spentBar").style.width=`${Math.min(percentage,100)}%`;
            document.querySelector("#remainingBar").style.width=`${Math.max(100-percentage,0)}%`;

            //More informations
            document.querySelector("#spentSub").textContent=data.percentage_change?`Your Expenditure ${data.change_type} by ${data.percentage_change.toFixed(1)}% Compared To last month`:"First Month Tracked ";

            document.getElementById("statusSub").textContent = 
            data.top_category?`Top drain: ${data.top_category},
            Spent ${formatAmount(data.top_category_spent)}` 
            : "No expenses yet"

            document.getElementById("remainingSub").textContent = 
            `of ₹${formatAmount(data.budget)} budget`

            }

        catch(error){
            console.error("Network Error,Please Try again !!!");
        }
}
loadDashboard();
monthSelect.addEventListener("change", () => {
    selectedMonth = Number(monthSelector.value);

    localStorage.setItem("selectedMonth", selectedMonth);

    document.getElementById("currentMonth").textContent =
        `${monthNames[selectedMonth-1]} ${selectedYear}`;
    
    loadExpenses();
    loadDashboard();
});

yearSelect.addEventListener("change", () => {
    selectedYear = Number(yearSelector.value);

    localStorage.setItem("selectedYear", selectedYear);

    document.getElementById("currentMonth").textContent =
        `${monthNames[selectedMonth-1]} ${selectedYear}`;
    loadExpenses();
    loadDashboard();
});