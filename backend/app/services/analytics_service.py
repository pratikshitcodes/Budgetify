from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from .. import models
from ..utils import calculate_start_end
from decimal import Decimal

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
