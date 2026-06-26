const token = localStorage.getItem("access_token");

if (!token) {
  window.location.href = "./expense_login.html";
}
const hour = new Date().getHours()
const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"
document.getElementById("greeting").textContent = `${greeting} 👋`

const monthName = new Date().toLocaleDateString("en-IN", { month: "long", year: "numeric" })
document.getElementById("currentMonth").textContent = monthName
async function loadExpenses(){
    const expenseTableBody=document.querySelector("#expenseTableBody");
    expenseTableBody.innerHTML="";
    const response=await apiFetch("/expenses/");

    const expenses=await response.json();
    expenses.forEach(expense => {
        const tr=document.createElement("tr");

        const td_title=document.createElement("td");
        td_title.innerText=expense.title;

        const td_category=document.createElement("td");
        td_category.innerText=expense.category;

        const td_amount=document.createElement("td");
        td_amount.innerText=expense.amount;

        const td_date=document.createElement("td");
        const date=new Date(expense.created_at);
        td_date.innerText = date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            });

        const td_more=document.createElement("td");
        const viewBtn=document.createElement("button");

        viewBtn.innerText="View";
        viewBtn.classList.add("view-btn")

        const deleteBtn=document.createElement("button")
        deleteBtn.innerText="Delete";
        deleteBtn.classList.add("delete-btn");

        deleteBtn.addEventListener("click",async(e)=>{
            e.preventDefault();
            try{
                const response=await apiFetch("/expenses"+`/${expense.id}`,{
                    method:"DELETE",
                });
    
                expenseTableBody.innerHTML="";
                loadExpenses();
            }
            catch(error){
                console.log("Delete failed:",error);
            }
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


const searchInput=document.getElementById("searchInput");

if(searchInput){
    searchInput.addEventListener("input",function(){
        const rows=document.querySelectorAll("tbody tr");
        const searchValue=searchInput.value.toLowerCase();

        rows.forEach(function(row){
            const rowText=row.innerText.toLowerCase();
            
            if(rowText.includes(searchValue)){
                row.style.display="";
            }
            else{
                row.style.display="none";
            }
        })
    });
}

const modal_overlay=document.querySelector("#expenseModal");
const addExpenseBtn=document.querySelector(".addBtn")
const closeBtn=document.querySelector("#closeExpenseModal")
function openForm(){
    modal_overlay.classList.add("show");
}
function removeForm(){
    modal_overlay.classList.remove("show");
}
closeBtn.addEventListener("click",removeForm);
addExpenseBtn.addEventListener("click",openForm);

const addexpenseForm=document.querySelector("#addExpenseForm");
const expense_title=document.querySelector("#expenseTitle");
const expense_amount=document.querySelector("#expenseAmount");
const expense_category=document.querySelector("#expenseCategory");
const expense_desc=document.querySelector("#expenseDescription");
addexpenseForm.addEventListener("submit",async (e)=>{
    e.preventDefault();
    const title=expense_title.value;
    const amount=parseFloat(expense_amount.value);
    const category=expense_category.value;
    const description=expense_desc.value;
    if(!title || !amount || !category){
        alert("Please fill all fields")
        return
    }
    try{
        const response=await apiFetch("/expenses",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({title,amount,description,category})
        });
        const data=await response.json();
        expenseTableBody="";
        loadExpenses();
    }
    catch(error){
        console.log("error:",error);
    }
    removeForm();
});
document.querySelector(".log-out-btn")
    .addEventListener("click", () => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "./expense_login.html"
    })