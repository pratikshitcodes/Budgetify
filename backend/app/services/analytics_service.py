from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from .. import models
from ..utils import calculate_start_end, calculate_expense, find_monthly_expenses, day_to_day_expenses, most_frequent_entries, insight_logic_this_prev_month
from decimal import Decimal
import calendar
from datetime import datetime

def get_monthly_summary(db: Session, user_id: int, month: int, year: int):
    """Returns a basic summary of expenses for a given month and year."""
    date_range = calculate_start_end(month, year)
    
    # Total expenses
    total = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.owner_id == user_id,
        models.Expense.created_at >= date_range["start"],
        models.Expense.created_at < date_range["end"]
    ).scalar() or 0

    # Count
    count = db.query(func.count(models.Expense.id)).filter(
        models.Expense.owner_id == user_id,
        models.Expense.created_at >= date_range["start"],
        models.Expense.created_at < date_range["end"]
    ).scalar() or 0

    # Budget
    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year
    ).first()

    budget_amt = float(budget.amount) if budget else 0
    remaining = budget_amt - float(total)

    # Top expense
    highest = db.query(models.Expense).filter(
        models.Expense.owner_id == user_id,
        models.Expense.created_at >= date_range["start"],
        models.Expense.created_at < date_range["end"]
    ).order_by(models.Expense.amount.desc()).first()

    highest_data = None
    if highest:
        highest_data = {
            "title": highest.title,
            "amount": float(highest.amount),
            "category": highest.category
        }

    return {
        "month": month,
        "year": year,
        "total_expenses": float(total),
        "transaction_count": count,
        "budget": budget_amt,
        "remaining_budget": remaining,
        "highest_expense": highest_data
    }

def get_category_breakdown(db: Session, user_id: int, month: int, year: int):
    """Returns category-wise spending for a given month and year."""
    date_range = calculate_start_end(month, year)
    
    breakdown = db.query(
        models.Expense.category, func.sum(models.Expense.amount)
    ).filter(
        models.Expense.owner_id == user_id,
        models.Expense.created_at >= date_range["start"],
        models.Expense.created_at < date_range["end"]
    ).group_by(models.Expense.category).all()
    
    return {row[0]: float(row[1]) for row in breakdown}

def compare_months(db: Session, user_id: int, m1: int, y1: int, m2: int, y2: int):
    """Generates a comprehensive comparison between two arbitrary months."""
    s1 = get_monthly_summary(db, user_id, m1, y1)
    s2 = get_monthly_summary(db, user_id, m2, y2)
    
    c1 = get_category_breakdown(db, user_id, m1, y1)
    c2 = get_category_breakdown(db, user_id, m2, y2)
    
    abs_diff = s2["total_expenses"] - s1["total_expenses"]
    pct_diff = 0
    if s1["total_expenses"] > 0:
        pct_diff = (abs_diff / s1["total_expenses"]) * 100
        
    all_cats = set(list(c1.keys()) + list(c2.keys()))
    categories = []
    
    max_increase = None
    max_increase_val = -float('inf')
    max_decrease = None
    max_decrease_val = float('inf')
    
    for cat in all_cats:
        v1 = c1.get(cat, 0)
        v2 = c2.get(cat, 0)
        diff = v2 - v1
        
        pct = 0
        if v1 > 0:
            pct = (diff / v1) * 100
            
        categories.append({
            "category": cat,
            "month1_spending": v1,
            "month2_spending": v2,
            "absolute_difference": diff,
            "percentage_difference": pct
        })
        
        if diff > max_increase_val:
            max_increase_val = diff
            max_increase = cat
            
        if diff < max_decrease_val:
            max_decrease_val = diff
            max_decrease = cat

    new_categories = [cat for cat in c2 if cat not in c1]
    disappeared_categories = [cat for cat in c1 if cat not in c2]

    return {
        "month1": {"month": m1, "year": y1, "summary": s1},
        "month2": {"month": m2, "year": y2, "summary": s2},
        "overall": {
            "absolute_difference": abs_diff,
            "percentage_difference": pct_diff,
        },
        "categories": categories,
        "insights": {
            "largest_increase": {"category": max_increase, "amount": max_increase_val} if max_increase_val > 0 else None,
            "largest_decrease": {"category": max_decrease, "amount": max_decrease_val} if max_decrease_val < 0 else None,
            "new_categories": new_categories,
            "disappeared_categories": disappeared_categories
        }
    }

def month_battle(db: Session, user_id: int, m1: int, y1: int, m2: int, y2: int):
    """Compare two months category-by-category. Lower spend wins the category point."""
    comparison = compare_months(db, user_id, m1, y1, m2, y2)

    rounds = []
    month1_points = 0
    month2_points = 0

    for cat in comparison["categories"]:
        v1 = cat["month1_spending"]
        v2 = cat["month2_spending"]

        if v1 == 0 and v2 == 0:
            winner = "tie"
        elif v1 < v2:
            winner = "month1"
            month1_points += 1
        elif v2 < v1:
            winner = "month2"
            month2_points += 1
        else:
            winner = "tie"

        rounds.append({
            "category": cat["category"],
            "month1_spending": v1,
            "month2_spending": v2,
            "difference": abs(v1 - v2),
            "winner": winner,
            "point_awarded_to": winner if winner != "tie" else None
        })

    if month1_points > month2_points:
        overall_winner = "month1"
    elif month2_points > month1_points:
        overall_winner = "month2"
    else:
        overall_winner = "tie"

    return {
        "month1": {
            "month": m1,
            "year": y1,
            "label": f"{m1}/{y1}",
            "points": month1_points,
            "total_spending": comparison["month1"]["summary"]["total_expenses"]
        },
        "month2": {
            "month": m2,
            "year": y2,
            "label": f"{m2}/{y2}",
            "points": month2_points,
            "total_spending": comparison["month2"]["summary"]["total_expenses"]
        },
        "rounds": rounds,
        "total_rounds": len(rounds),
        "overall_winner": overall_winner,
        "comparison": comparison
    }

def get_detailed_monthly_analysis(db: Session, user_id: int, month: int = None, year: int = None, compare_month: int = None, compare_year: int = None):
    """Returns a comprehensive financial analysis for a specific month compared to another."""
    today = datetime.now()
    if month is None:
        month = today.month
    if year is None:
        year = today.year

    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year
    ).first()

    if not budget:
        return None

    current_month_now = today.month
    current_year_now = today.year

    this_month_total = calculate_expense(db, month, year, user_id)

    cm = compare_month if compare_month is not None else (12 if month == 1 else month - 1)
    cy = compare_year if compare_year is not None else (year - 1 if month == 1 else year)

    prev_month_total = calculate_expense(db, cm, cy, user_id)
    
    this_month_expenses = find_monthly_expenses(db, month, year, user_id)
    prev_month_expenses = find_monthly_expenses(db, cm, cy, user_id)

    this_month_count = len(this_month_expenses)
    prev_month_count = len(prev_month_expenses)

    highest = max(this_month_expenses, key=lambda e: e.amount, default=None)
    avg = sum(float(e.amount) for e in this_month_expenses) / len(this_month_expenses) if this_month_expenses else 0

    highest_data = None
    if highest:
        highest_data = {
            "title": highest.title,
            "category": highest.category,
            "amount": float(highest.amount)
        }

    all_categories = set(
        [e.category for e in this_month_expenses] +
        [e.category for e in prev_month_expenses]
    )

    category_comparison = {}
    for cat in all_categories:
        this_total = sum(float(e.amount) for e in this_month_expenses if e.category == cat)
        prev_total = sum(float(e.amount) for e in prev_month_expenses if e.category == cat)
        category_comparison[cat] = {
            "this": this_total,
            "prev": prev_total
        }

    most_frequent = most_frequent_entries(db, month, year, user_id)
    top3 = sorted(this_month_expenses, key=lambda e: e.amount, reverse=True)[:3]
    this_graph = day_to_day_expenses(db, month, year, user_id)
    prev_graph = day_to_day_expenses(db, cm, cy, user_id)

    days_in_month = calendar.monthrange(year, month)[1]
    if month == current_month_now and year == current_year_now:
        days_passed = today.day
    else:
        days_passed = calendar.monthrange(year, month)[1]
    
    days_remaining = days_in_month - days_passed

    current_avg_pace = float(this_month_total) / days_passed if days_passed > 0 else 0
    projected_total = Decimal(current_avg_pace * days_in_month)
    remaining_budget = budget.amount - Decimal(this_month_total)
    safe_daily = (Decimal(budget.amount) - Decimal(this_month_total)) / Decimal(days_remaining) if days_remaining > 0 else 0

    day_until_budget_exhausted = None
    if current_avg_pace > 0:
        day_until_budget_exhausted = round(float(remaining_budget) / current_avg_pace)

    weekend_total = 0
    weekday_total = 0
    for e in this_month_expenses:
        if e.created_at.weekday() >= 5:
            weekend_total += float(e.amount)
        else:
            weekday_total += float(e.amount)
    
    threshold = 10000
    high_value = [e for e in this_month_expenses if float(e.amount) >= threshold]

    max_category = None
    max_change = float("-inf")
    for category, values in category_comparison.items():
        prev = values["prev"]
        curr = values["this"]
        if prev == 0: continue
        percent = ((curr - prev) / prev) * 100
        if percent > max_change:
            max_change = percent
            max_category = category

    spent_days = set(e.created_at.day for e in this_month_expenses)
    no_spend_days = days_in_month - len(spent_days)

    spending_status = ""
    message = ""

    if month == current_month_now and year == current_year_now:
        if safe_daily >= avg:
            spending_status = "Safe"
            message = f"Great job! You're comfortably within your budget. Your recommended daily spending limit is ₹{safe_daily:.2f} for the rest of the month."
        elif 0 < safe_daily < avg:
            spending_status = "Be cautious"
            if day_until_budget_exhausted is not None and day_until_budget_exhausted < days_remaining:
                message = f"At your current spending pace, your budget may be exhausted in about {day_until_budget_exhausted} days."
            else:
                message = "You're still within budget, but your remaining daily spending limit is getting lower. Spend wisely."
        else:
            spending_status = "Warning"
            message = "You have already exceeded your monthly budget. Any further spending will be above your planned budget."
    else:
        if remaining_budget > 0:
            spending_status = "Excellent Budget Control"
            message = f"Did pretty well this month Mate!!! ₹{remaining_budget:.2f}"
        elif remaining_budget == 0:
            spending_status = "Budget Fully Utilized"
            message = "You utilized your entire monthly budget."
        else:
            spending_status = "Overspent"
            message = f"You overspent by {remaining_budget:.2f}"

    insight_message = insight_logic_this_prev_month(
        spending_status, float(this_month_total), float(projected_total), 
        current_avg_pace, float(safe_daily), days_remaining, 
        float(remaining_budget), float(budget.amount), message
    )

    return {
        "this_month_total": float(this_month_total),
        "prev_month_total": float(prev_month_total),
        "this_month_count": this_month_count,
        "prev_month_count": prev_month_count,
        "most_frequent_entry": most_frequent,
        "highest": highest_data,
        "recommended_daily_pace": avg,
        "top3_expenses": [{"title": e.title, "amount": float(e.amount), "category": e.category} for e in top3],
        "category_comparison": category_comparison,
        "this_month_daily": this_graph,
        "prev_month_daily": prev_graph,
        "projected_daily": round(float(projected_total), 2),
        "current_avg_pace": round(current_avg_pace, 2),
        "safe_daily": float(safe_daily),
        "remaining_days": days_remaining,
        "weekend_spending": weekend_total,
        "weekday_spending": weekday_total,
        "high_value_count": len(high_value),
        "threshold": threshold,
        "biggest_increase": None if max_change <= 0 else {"category": max_category, "percentage": round(max_change, 2)},
        "no_spend_days": no_spend_days,
        "remaining_budget": float(remaining_budget),
        "budget": float(budget.amount),
        "status": spending_status,
        "insight": insight_message
    }

def check_affordability(db: Session, user_id: int, amount: float):
    """Evaluates if a user can afford a potential expense based on their current budget."""
    today = datetime.now()
    month = today.month
    year = today.year

    analysis = get_detailed_monthly_analysis(db, user_id, month, year)

    if not analysis:
        return {
            "can_afford": False,
            "reason": "Budget not initialized for this month.",
            "impact": None
        }

    remaining = analysis["remaining_budget"]
    can_afford = amount <= remaining
    
    new_remaining = remaining - amount
    new_safe_daily = new_remaining / analysis["remaining_days"] if analysis["remaining_days"] > 0 else 0

    impact_message = ""
    if can_afford:
        if new_safe_daily < analysis["recommended_daily_pace"]:
            impact_message = f"You can afford this, but it will reduce your safe daily spending from ₹{analysis['safe_daily']:.2f} to ₹{new_safe_daily:.2f}, which is below your current average pace."
        else:
            impact_message = f"Yes, you can afford this! Your new safe daily limit will be ₹{new_safe_daily:.2f}."
    else:
        impact_message = f"This expense of ₹{amount:.2f} exceeds your remaining budget of ₹{remaining:.2f}."

    return {
        "can_afford": can_afford,
        "remaining_budget_before": remaining,
        "remaining_budget_after": float(new_remaining),
        "safe_daily_before": analysis["safe_daily"],
        "safe_daily_after": float(new_safe_daily),
        "impact_message": impact_message
    }
