from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Dict

from .. import models


def _ensure_group_access(db: Session, group_id: int, user_id: int) -> models.Group:
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.owner_id == user_id
    ).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def create_group(db: Session, user_id: int, name: str, member_names: List[str]) -> models.Group:
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name is required")

    cleaned_members = [m.strip() for m in member_names if m.strip()]
    if len(cleaned_members) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least 2 members")

    group = models.Group(name=name.strip(), owner_id=user_id)
    db.add(group)
    db.flush()

    for member_name in cleaned_members:
        db.add(models.GroupMember(group_id=group.id, name=member_name))

    db.commit()
    db.refresh(group)
    return group


def list_groups(db: Session, user_id: int):
    groups = db.query(models.Group).filter(models.Group.owner_id == user_id).order_by(models.Group.created_at.desc()).all()
    return groups


def get_group_detail(db: Session, group_id: int, user_id: int):
    group = _ensure_group_access(db, group_id, user_id)
    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()
    expenses = db.query(models.GroupExpense).filter(models.GroupExpense.group_id == group_id).order_by(models.GroupExpense.created_at.desc()).all()

    expense_rows = []
    for expense in expenses:
        splits = db.query(models.GroupExpenseSplit).filter(models.GroupExpenseSplit.expense_id == expense.id).all()
        payer = next((m for m in members if m.id == expense.paid_by_member_id), None)
        expense_rows.append({
            "id": expense.id,
            "title": expense.title,
            "amount": float(expense.amount),
            "paid_by": payer.name if payer else "Unknown",
            "paid_by_member_id": expense.paid_by_member_id,
            "created_at": expense.created_at,
            "splits": [
                {
                    "member_id": split.member_id,
                    "member_name": next((m.name for m in members if m.id == split.member_id), "Unknown"),
                    "share_amount": float(split.share_amount)
                }
                for split in splits
            ]
        })

    balances = calculate_balances(members, expense_rows)
    settlements = calculate_settlements(balances)

    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at,
        "members": [{"id": m.id, "name": m.name} for m in members],
        "expenses": expense_rows,
        "balances": balances,
        "settlements": settlements
    }


def add_member(db: Session, group_id: int, user_id: int, name: str):
    group = _ensure_group_access(db, group_id, user_id)
    if not name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member name is required")

    member = models.GroupMember(group_id=group.id, name=name.strip())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def add_expense(
    db: Session,
    group_id: int,
    user_id: int,
    title: str,
    amount: float,
    paid_by_member_id: int,
    split_member_ids: List[int] | None = None
):
    group = _ensure_group_access(db, group_id, user_id)
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")

    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()
    member_ids = {m.id for m in members}
    if paid_by_member_id not in member_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payer")

    participants = split_member_ids if split_member_ids else list(member_ids)
    participants = [pid for pid in participants if pid in member_ids]
    if not participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one member to split with")

    share = Decimal(str(amount)) / Decimal(len(participants))

    expense = models.GroupExpense(
        group_id=group.id,
        title=title.strip(),
        amount=Decimal(str(amount)),
        paid_by_member_id=paid_by_member_id
    )
    db.add(expense)
    db.flush()

    for member_id in participants:
        db.add(models.GroupExpenseSplit(
            expense_id=expense.id,
            member_id=member_id,
            share_amount=share
        ))

    db.commit()
    return get_group_detail(db, group_id, user_id)


def delete_expense(db: Session, group_id: int, expense_id: int, user_id: int):
    _ensure_group_access(db, group_id, user_id)
    expense = db.query(models.GroupExpense).filter(
        models.GroupExpense.id == expense_id,
        models.GroupExpense.group_id == group_id
    ).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"status": "deleted"}


def delete_group(db: Session, group_id: int, user_id: int):
    group = _ensure_group_access(db, group_id, user_id)
    db.delete(group)
    db.commit()
    return {"status": "deleted"}


def calculate_balances(members, expenses) -> List[Dict]:
    balances = {m.id: {"member_id": m.id, "name": m.name, "paid": 0.0, "owed": 0.0, "net": 0.0} for m in members}

    for expense in expenses:
        payer_id = expense["paid_by_member_id"]
        if payer_id in balances:
            balances[payer_id]["paid"] += expense["amount"]

        for split in expense["splits"]:
            if split["member_id"] in balances:
                balances[split["member_id"]]["owed"] += split["share_amount"]

    for member_id, row in balances.items():
        row["net"] = round(row["paid"] - row["owed"], 2)

    return list(balances.values())


def calculate_settlements(balances) -> List[Dict]:
    creditors = [{"member_id": b["member_id"], "name": b["name"], "amount": round(b["net"], 2)} for b in balances if b["net"] > 0]
    debtors = [{"member_id": b["member_id"], "name": b["name"], "amount": round(abs(b["net"]), 2)} for b in balances if b["net"] < 0]

    settlements = []
    i = 0
    j = 0
    while i < len(creditors) and j < len(debtors):
        pay_amount = round(min(creditors[i]["amount"], debtors[j]["amount"]), 2)
        if pay_amount > 0:
            settlements.append({
                "from_member_id": debtors[j]["member_id"],
                "from_name": debtors[j]["name"],
                "to_member_id": creditors[i]["member_id"],
                "to_name": creditors[i]["name"],
                "amount": pay_amount
            })
        creditors[i]["amount"] = round(creditors[i]["amount"] - pay_amount, 2)
        debtors[j]["amount"] = round(debtors[j]["amount"] - pay_amount, 2)
        if creditors[i]["amount"] <= 0.01:
            i += 1
        if debtors[j]["amount"] <= 0.01:
            j += 1

    return settlements
