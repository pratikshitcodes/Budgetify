from fastapi import HTTPException,status
from .. import models
from typing import Optional
from datetime import datetime

def get_expense(db,current_user, month:Optional[int]=None, year:Optional[int]=None,limit:int=100,skip:int=0):
    if month is None:
        month=datetime.now().month
    if year is None:
        year=datetime.now().year

    query = db.query(models.Expense).filter(models.Expense.owner_id == current_user.id)
        
    start = datetime(year, month, 1)
    end = datetime(year+1, 1, 1) if month == 12 else datetime(year, month+1, 1)
    query = query.filter(
        models.Expense.created_at >= start,
        models.Expense.created_at < end
    )
    
    return query.order_by(models.Expense.created_at.desc()).offset(skip).limit(limit).all()

def add_expense(post_details:dict,db,current_user):
    new_item=models.Expense(title=post_details["title"],amount=post_details["amount"],description=post_details["description"],owner_id=current_user.id,category=post_details["category"])
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def delete_expense(id,db,current_user):
    expense_query=db.query(models.Expense).filter(models.Expense.id==id,models.Expense.owner_id==current_user.id)
    expense=expense_query.first()
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Expense not found")
    
    expense_query.delete(synchronize_session=False)
    db.commit()

def search_expenses(keyword: str, db, current_user, month:Optional[int]=None, year:Optional[int]=None):
    query = db.query(models.Expense).filter(models.Expense.owner_id == current_user.id)
    if month and year:
        start = datetime(year, month, 1)
        end = datetime(year+1, 1, 1) if month == 12 else datetime(year, month+1, 1)
        query = query.filter(
            models.Expense.created_at >= start,
            models.Expense.created_at < end
        )
    if keyword:
        search = f"%{keyword}%"
        query = query.filter(models.Expense.title.ilike(search) | models.Expense.category.ilike(search))
    return query.order_by(models.Expense.created_at.desc()).limit(20).all()

def update_expense(id: int, updated_details: dict, db, current_user):
    expense_query=db.query(models.Expense).filter(models.Expense.id==id,models.Expense.owner_id==current_user.id)
    expense=expense_query.first()
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Expense not found")
    
    expense_query.update(updated_details, synchronize_session=False)
    db.commit()
    return expense_query.first()
