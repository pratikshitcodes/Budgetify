const token = localStorage.getItem("access_token");
if (!token) window.location.href = "./expense_login.html";

const formatAmount = (amount) => parseFloat(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 2, maximumFractionDigits: 2
});

let groups = [];
let activeGroup = null;

const groupsList = document.getElementById("groupsList");
const groupDetailPanel = document.getElementById("groupDetailPanel");
const createGroupModal = document.getElementById("createGroupModal");
const addExpenseModal = document.getElementById("addExpenseModal");

async function loadGroups() {
    try {
        const res = await apiFetch("/groups");
        groups = await res.json();
        renderGroupsList();
    } catch (err) {
        console.error(err);
    }
}

function renderGroupsList() {
    if (!groups.length) {
        groupsList.innerHTML = `<div class="empty-state">No groups yet — create one to get started</div>`;
        return;
    }

    groupsList.innerHTML = groups.map(g => `
        <button class="group-item ${activeGroup?.id === g.id ? 'active' : ''}" data-id="${g.id}">
            <div class="group-item-name">${g.name}</div>
            <div class="group-item-date">${new Date(g.created_at).toLocaleDateString("en-IN")}</div>
        </button>
    `).join("");

    groupsList.querySelectorAll(".group-item").forEach(btn => {
        btn.addEventListener("click", () => loadGroupDetail(Number(btn.dataset.id)));
    });
}

async function loadGroupDetail(groupId) {
    try {
        const res = await apiFetch(`/groups/${groupId}`);
        activeGroup = await res.json();
        renderGroupsList();
        renderGroupDetail();
    } catch (err) {
        console.error(err);
    }
}

function renderGroupDetail() {
    if (!activeGroup) return;

    const settlementsHtml = activeGroup.settlements.length
        ? activeGroup.settlements.map(s => `
            <div class="settlement-row">
                <span class="settle-from">${s.from_name}</span>
                <span class="settle-arrow">→ pays →</span>
                <span class="settle-to">${s.to_name}</span>
                <span class="settle-amt">₹${formatAmount(s.amount)}</span>
            </div>`).join("")
        : `<div class="all-settled"><i class="ti ti-circle-check"></i> Everyone is settled up!</div>`;

    const balancesHtml = activeGroup.balances.map(b => {
        const netClass = b.net > 0 ? "positive" : b.net < 0 ? "negative" : "neutral";
        const netLabel = b.net > 0 ? `gets back ₹${formatAmount(b.net)}`
            : b.net < 0 ? `owes ₹${formatAmount(Math.abs(b.net))}`
                : "settled";
        return `
            <div class="balance-row">
                <span class="balance-name">${b.name}</span>
                <span class="balance-net ${netClass}">${netLabel}</span>
            </div>`;
    }).join("");

    const expensesHtml = activeGroup.expenses.length
        ? activeGroup.expenses.map(e => `
            <div class="expense-row">
                <div class="expense-info">
                    <div class="expense-title">${e.title}</div>
                    <div class="expense-meta">${e.paid_by} paid · split ${e.splits.length} ways</div>
                </div>
                <div class="expense-amt">₹${formatAmount(e.amount)}</div>
                <button class="delete-expense-btn" data-id="${e.id}" title="Delete"><i class="ti ti-trash"></i></button>
            </div>`).join("")
        : `<div class="empty-state small">No expenses added yet</div>`;

    groupDetailPanel.innerHTML = `
        <div class="detail-header">
            <div>
                <h2>${activeGroup.name}</h2>
                <p>${activeGroup.members.length} members · ${activeGroup.expenses.length} expenses</p>
            </div>
            <div class="detail-actions">
                <button class="primary-btn small" id="openAddExpenseBtn"><i class="ti ti-plus"></i> Add Expense</button>
                <button class="danger-btn small" id="deleteGroupBtn"><i class="ti ti-trash"></i></button>
            </div>
        </div>

        <div class="detail-grid">
            <div class="detail-card">
                <div class="card-title"><i class="ti ti-users"></i> Members</div>
                <div class="members-list">
                    ${activeGroup.members.map(m => `<span class="member-chip">${m.name}</span>`).join("")}
                </div>
                <div class="add-member-row">
                    <input type="text" id="newMemberInput" placeholder="Add member name">
                    <button class="ghost-btn" id="addMemberBtn">Add</button>
                </div>
            </div>

            <div class="detail-card">
                <div class="card-title"><i class="ti ti-scale"></i> Balances</div>
                ${balancesHtml}
            </div>

            <div class="detail-card full-width">
                <div class="card-title"><i class="ti ti-arrows-exchange"></i> Settle Up</div>
                ${settlementsHtml}
            </div>

            <div class="detail-card full-width">
                <div class="card-title"><i class="ti ti-receipt"></i> Expenses</div>
                <div class="expenses-list">${expensesHtml}</div>
            </div>
        </div>`;

    document.getElementById("openAddExpenseBtn").addEventListener("click", openExpenseModal);
    document.getElementById("deleteGroupBtn").addEventListener("click", deleteGroup);
    document.getElementById("addMemberBtn").addEventListener("click", addMember);

    groupDetailPanel.querySelectorAll(".delete-expense-btn").forEach(btn => {
        btn.addEventListener("click", () => deleteExpense(Number(btn.dataset.id)));
    });
}

function openCreateGroupModal() {
    createGroupModal.classList.add("show");
    document.getElementById("groupNameInput").value = "";
    document.getElementById("groupMembersInput").value = "";
}

function closeCreateGroupModal() {
    createGroupModal.classList.remove("show");
}

async function createGroup() {
    const name = document.getElementById("groupNameInput").value.trim();
    const members = document.getElementById("groupMembersInput").value
        .split("\n").map(m => m.trim()).filter(Boolean);

    if (!name || members.length < 2) {
        alert("Enter a group name and at least 2 members.");
        return;
    }

    try {
        const res = await apiFetch("/groups", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, members })
        });
        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Could not create group");
            return;
        }
        activeGroup = await res.json();
        closeCreateGroupModal();
        await loadGroups();
        renderGroupDetail();
    } catch (err) {
        console.error(err);
    }
}

function openExpenseModal() {
    if (!activeGroup) return;
    const paidBySelect = document.getElementById("paidBySelect");
    const splitList = document.getElementById("splitMembersList");

    paidBySelect.innerHTML = activeGroup.members.map(m =>
        `<option value="${m.id}">${m.name}</option>`
    ).join("");

    splitList.innerHTML = activeGroup.members.map(m => `
        <label class="split-check">
            <input type="checkbox" value="${m.id}" checked>
            <span>${m.name}</span>
        </label>`).join("");

    document.getElementById("expenseTitleInput").value = "";
    document.getElementById("expenseAmountInput").value = "";
    addExpenseModal.classList.add("show");
}

function closeExpenseModal() {
    addExpenseModal.classList.remove("show");
}

async function addExpense() {
    const title = document.getElementById("expenseTitleInput").value.trim();
    const amount = parseFloat(document.getElementById("expenseAmountInput").value);
    const paidBy = parseInt(document.getElementById("paidBySelect").value);
    const splitIds = [...document.querySelectorAll("#splitMembersList input:checked")].map(i => parseInt(i.value));

    if (!title || !amount || amount <= 0 || !splitIds.length) {
        alert("Fill in all fields and select at least one member to split with.");
        return;
    }

    try {
        const res = await apiFetch(`/groups/${activeGroup.id}/expenses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title,
                amount,
                paid_by_member_id: paidBy,
                split_member_ids: splitIds
            })
        });
        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || "Could not add expense");
            return;
        }
        activeGroup = await res.json();
        closeExpenseModal();
        renderGroupDetail();
    } catch (err) {
        console.error(err);
    }
}

async function addMember() {
    const name = document.getElementById("newMemberInput").value.trim();
    if (!name) return;

    try {
        const res = await apiFetch(`/groups/${activeGroup.id}/members`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        if (!res.ok) return;
        await loadGroupDetail(activeGroup.id);
    } catch (err) {
        console.error(err);
    }
}

async function deleteExpense(expenseId) {
    if (!confirm("Delete this expense?")) return;
    try {
        await apiFetch(`/groups/${activeGroup.id}/expenses/${expenseId}`, { method: "DELETE" });
        await loadGroupDetail(activeGroup.id);
    } catch (err) {
        console.error(err);
    }
}

async function deleteGroup() {
    if (!confirm(`Delete group "${activeGroup.name}"? This cannot be undone.`)) return;
    try {
        await apiFetch(`/groups/${activeGroup.id}`, { method: "DELETE" });
        activeGroup = null;
        groupDetailPanel.innerHTML = `<div class="empty-detail"><i class="ti ti-users-group"></i><p>Select a group or create a new one</p></div>`;
        await loadGroups();
    } catch (err) {
        console.error(err);
    }
}

document.getElementById("openCreateGroupBtn").addEventListener("click", openCreateGroupModal);
document.getElementById("closeCreateGroupModal").addEventListener("click", closeCreateGroupModal);
document.getElementById("cancelCreateGroup").addEventListener("click", closeCreateGroupModal);
document.getElementById("saveCreateGroup").addEventListener("click", createGroup);
document.getElementById("closeExpenseModal").addEventListener("click", closeExpenseModal);
document.getElementById("cancelExpense").addEventListener("click", closeExpenseModal);
document.getElementById("saveExpense").addEventListener("click", addExpense);

createGroupModal.addEventListener("click", e => { if (e.target === createGroupModal) closeCreateGroupModal(); });
addExpenseModal.addEventListener("click", e => { if (e.target === addExpenseModal) closeExpenseModal(); });

loadGroups();
