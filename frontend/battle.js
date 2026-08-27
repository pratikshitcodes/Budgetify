const token = localStorage.getItem("access_token");
if (!token) window.location.href = "./expense_login.html";

const monthNames = ["", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

const formatAmount = (amount) => parseFloat(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 2, maximumFractionDigits: 2
});

const selectedMonth = Number(localStorage.getItem("selectedMonth")) || new Date().getMonth() + 1;
const selectedYear = Number(localStorage.getItem("selectedYear")) || new Date().getFullYear();
const prevMonth = selectedMonth === 1 ? 12 : selectedMonth - 1;
const prevYear = selectedMonth === 1 ? selectedYear - 1 : selectedYear;

const month1Select = document.getElementById("month1");
const month2Select = document.getElementById("month2");
const year1Input = document.getElementById("year1");
const year2Input = document.getElementById("year2");

for (let i = 1; i <= 12; i++) {
    month1Select.innerHTML += `<option value="${i}">${monthNames[i]}</option>`;
    month2Select.innerHTML += `<option value="${i}">${monthNames[i]}</option>`;
}

month1Select.value = selectedMonth;
year1Input.value = selectedYear;
month2Select.value = prevMonth;
year2Input.value = prevYear;

let battleData = null;
let simRunning = false;

const roundsContainer = document.getElementById("roundsContainer");
const startSimBtn = document.getElementById("startSimBtn");
const resetSimBtn = document.getElementById("resetSimBtn");
const winnerBanner = document.getElementById("winnerBanner");

function monthLabel(month, year) {
    return `${monthNames[month]} ${year}`;
}

function renderRoundCards(rounds, revealIndex = -1) {
    if (!rounds.length) {
        roundsContainer.innerHTML = `<div class="empty-state">No category data for these months</div>`;
        return;
    }

    roundsContainer.innerHTML = rounds.map((round, index) => {
        const revealed = index <= revealIndex;
        const winnerClass = revealed
            ? round.winner === "month1" ? "m1-win"
                : round.winner === "month2" ? "m2-win"
                    : "tie-win"
            : "";

        const pointText = revealed
            ? round.winner === "tie"
                ? "Draw — no point"
                : `+1 point to ${round.winner === "month1" ? monthLabel(battleData.month1.month, battleData.month1.year) : monthLabel(battleData.month2.month, battleData.month2.year)}`
            : "Waiting…";

        return `
            <div class="round-card ${revealed ? "revealed " + winnerClass : "pending"}" data-index="${index}">
                <div class="round-header">
                    <span class="round-num">Round ${index + 1}</span>
                    <span class="round-cat">${round.category}</span>
                </div>
                <div class="round-body">
                    <div class="round-side m1-side">
                        <div class="side-label">${monthLabel(battleData.month1.month, battleData.month1.year)}</div>
                        <div class="side-amt">₹${formatAmount(round.month1_spending)}</div>
                    </div>
                    <div class="round-vs">vs</div>
                    <div class="round-side m2-side">
                        <div class="side-label">${monthLabel(battleData.month2.month, battleData.month2.year)}</div>
                        <div class="side-amt">₹${formatAmount(round.month2_spending)}</div>
                    </div>
                </div>
                <div class="round-result">${pointText}</div>
            </div>`;
    }).join("");
}

function updateScoreboard(data, m1Points = 0, m2Points = 0) {
    document.getElementById("m1Label").textContent = `${monthNames[data.month1.month]} ${data.month1.year}`;
    document.getElementById("m2Label").textContent = `${monthNames[data.month2.month]} ${data.month2.year}`;
    document.getElementById("m1Points").textContent = m1Points;
    document.getElementById("m2Points").textContent = m2Points;
    document.getElementById("m1Total").textContent = `₹${formatAmount(data.month1.total_spending)} spent`;
    document.getElementById("m2Total").textContent = `₹${formatAmount(data.month2.total_spending)} spent`;
}

async function loadBattle() {
    const m1 = parseInt(month1Select.value);
    const y1 = parseInt(year1Input.value);
    const m2 = parseInt(month2Select.value);
    const y2 = parseInt(year2Input.value);

    if (m1 === m2 && y1 === y2) {
        alert("Pick two different months to compare.");
        return;
    }

    winnerBanner.classList.add("hidden");
    startSimBtn.disabled = true;
    resetSimBtn.disabled = true;

    try {
        const res = await apiFetch(`/reports/battle?month1=${m1}&year1=${y1}&month2=${m2}&year2=${y2}`);
        if (!res.ok) throw new Error("Failed to load battle");
        battleData = await res.json();

        updateScoreboard(battleData, 0, 0);
        renderRoundCards(battleData.rounds, -1);
        startSimBtn.disabled = battleData.rounds.length === 0;
        resetSimBtn.disabled = false;
    } catch (err) {
        console.error(err);
        roundsContainer.innerHTML = `<div class="empty-state">Could not load battle data</div>`;
    }
}

async function runSimulation() {
    if (!battleData || simRunning) return;
    simRunning = true;
    startSimBtn.disabled = true;
    winnerBanner.classList.add("hidden");

    let m1Points = 0;
    let m2Points = 0;

    for (let i = 0; i < battleData.rounds.length; i++) {
        await new Promise(r => setTimeout(r, 700));
        const round = battleData.rounds[i];
        if (round.winner === "month1") m1Points++;
        else if (round.winner === "month2") m2Points++;

        updateScoreboard(battleData, m1Points, m2Points);
        renderRoundCards(battleData.rounds, i);

        const card = roundsContainer.querySelector(`[data-index="${i}"]`);
        if (card) card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    await new Promise(r => setTimeout(r, 500));

    const m1Name = `${monthNames[battleData.month1.month]} ${battleData.month1.year}`;
    const m2Name = `${monthNames[battleData.month2.month]} ${battleData.month2.year}`;

    if (battleData.overall_winner === "month1") {
        winnerBanner.innerHTML = `<i class="ti ti-trophy"></i><span>${m1Name} wins ${m1Points}–${m2Points}!</span>`;
        document.getElementById("fighterM1").classList.add("champion");
        document.getElementById("fighterM2").classList.remove("champion");
    } else if (battleData.overall_winner === "month2") {
        winnerBanner.innerHTML = `<i class="ti ti-trophy"></i><span>${m2Name} wins ${m2Points}–${m1Points}!</span>`;
        document.getElementById("fighterM2").classList.add("champion");
        document.getElementById("fighterM1").classList.remove("champion");
    } else {
        winnerBanner.innerHTML = `<i class="ti ti-scale"></i><span>It's a tie — ${m1Points}–${m2Points}!</span>`;
        document.getElementById("fighterM1").classList.remove("champion");
        document.getElementById("fighterM2").classList.remove("champion");
    }

    winnerBanner.classList.remove("hidden");
    simRunning = false;
    startSimBtn.disabled = false;
}

function resetSimulation() {
    if (!battleData) return;
    winnerBanner.classList.add("hidden");
    document.getElementById("fighterM1").classList.remove("champion");
    document.getElementById("fighterM2").classList.remove("champion");
    updateScoreboard(battleData, 0, 0);
    renderRoundCards(battleData.rounds, -1);
    startSimBtn.disabled = battleData.rounds.length === 0;
}

document.getElementById("loadBattleBtn").addEventListener("click", loadBattle);
startSimBtn.addEventListener("click", runSimulation);
resetSimBtn.addEventListener("click", resetSimulation);

roundsContainer.innerHTML = `<div class="empty-state">Choose two months above, then click <strong>Load Battle</strong></div>`;
