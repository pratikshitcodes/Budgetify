from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy import func
from datetime import datetime
from typing import List,Annotated
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from .. import oauth
from ..utils import calculate_expense,insight_logic
expense_router=APIRouter(
    tags=['CRUD Operation'],
    prefix='/expenses'
)
budget_router=APIRouter(
    prefix='/budget-status'
)
DbSession=Annotated[Session,Depends(get_db)]
CurrentUser=Annotated[schemas.Token,Depends(oauth.get_current_user)]
@expense_router.get('/',response_model=List[schemas.ExpenseResponse])
def get_expenses(db:DbSession,
        current_user:CurrentUser,
        limit:int=10,
        skip:int=0):
    expenses=db.query(models.Expense)\
    .filter(models.Expense.owner_id==current_user.id)\
    .order_by(models.Expense.created_at.desc())\
    .offset(skip)\
    .limit(limit)\
    .all()
    return expenses

@expense_router.post('/',status_code=status.HTTP_201_CREATED)
def post_expense(post_details:schemas.ExpenseCreate,db:DbSession, current_user:CurrentUser):
    new_item=models.Expense(title=post_details.title,amount=post_details.amount,description=post_details.description,owner_id=current_user.id,category=post_details.category)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item
@expense_router.delete('/{id}')
def delete_expense(id:int,db:DbSession,
                   current_user:CurrentUser):
    expense_query=db.query(models.Expense).filter(models.Expense.id==id,models.Expense.owner_id==current_user.id)
    expense=expense_query.first()
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Expense not found")
    
    expense_query.delete(synchronize_session=False)
    db.commit()
    return 

@expense_router.put('/{id}',response_model=schemas.ExpenseResponse)
def update(id:int,
           updated_details:schemas.ExpenseCreate,
           db:DbSession,
           current_user:CurrentUser):
    expense_query=db.query(models.Expense).filter(models.Expense.id==id,models.Expense.owner_id==current_user.id)
    expense=expense_query.first()
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No such Results found!!!")
    expense_query.update(updated_details.model_dump(),synchronize_session=False)
    db.commit()
    return expense_query.first()

@budget_router.get('/')
def get_monthly_expense(
        db:DbSession,
        current_user:CurrentUser):
    today=datetime.now()
    start_of_month=today.replace(day=1)
    total=db.query(func.sum(models.Expense.amount)).filter(models.Expense.owner_id==current_user.id,models.Expense.created_at>=start_of_month).scalar()
    if total is None:
        total=0
    return total


@budget_router.post('/',response_model=schemas.Budget_Response)
def analyse_budget(budget_details:schemas.Budget_Create,
                  db:DbSession,
                  current_user:CurrentUser):
    amount=budget_details.amount
    month=budget_details.month
    year=budget_details.year

    """checks whether the month is valid or not"""
    if((month<=0 or month>12) or(year<2000 or year>2100)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,detail=f"Enter Valid Details")
    

    is_budget_exist=db.query(models.Budget).filter(models.Budget.user_id==current_user.id,
     models.Budget.month==month,
     models.Budget.year==year).first()
    
    
    if is_budget_exist is None:
        new_budget=models.Budget(amount=amount,month=month,year=year,user_id=current_user.id)
        db.add(new_budget)
    else:
        is_budget_exist.amount=amount
    db.commit()

    """Calculation Of Monthly Expenses"""
    total_expenses=calculate_expense(db,month,year,current_user.id)
    
    used_percentage=total_expenses/amount
    remaining=amount-total_expenses
    budget_status=""
    if(used_percentage<0.5):
        budget_status="Safe"
    elif(used_percentage<0.75):
        budget_status="Warning"
    else:
        budget_status="Danger"
    if remaining < 0:
        budget_status = "Overspent"

    previous_month_spent=0
    if month==1:
        previous_month_spent=calculate_expense(db,12,year-1,current_user.id)
    else:
        previous_month_spent=calculate_expense(db,month-1,year,current_user.id)
    if previous_month_spent==0:
        percentage_change=None
    else:
        percentage_change=((total_expenses-previous_month_spent)/previous_month_spent)*100

    start=datetime(year,month,1)
    if month==12:
        end=datetime(year+1,1,1)
    else:
        end=datetime(year,month+1,1)
    top_category=db.query(models.Expense.category,func.sum(models.Expense.amount))\
                .filter(models.Expense.owner_id==current_user.id,
                        models.Expense.created_at>=start,
                        models.Expense.created_at<end)\
                .group_by(models.Expense.category)\
                .order_by(func.sum(models.Expense.amount).desc()).first()
    if top_category:
        top_category_name=top_category[0]
        top_category_spent=top_category[1]
    else:
        top_category_name=None
        top_category_spent=0

    if previous_month_spent==0:
        change_type=None
    else:
        if total_expenses>previous_month_spent:
            change_type="Increases"
        elif total_expenses<previous_month_spent:
            change_type="Decreases"
        else:
            change_type="No change"
    
    """Logic For insight"""
    insight=insight_logic(total_expenses,previous_month_spent,percentage_change,change_type,top_category_name,top_category_spent)
    
    return {
        "status":budget_status,
        "budget":amount,

        "total_spent":total_expenses,
        "previous_month_spent":previous_month_spent,
        "percentage_change":percentage_change,
        "change_type":change_type,

        "top_category":top_category_name,
        "top_category_spent":top_category_spent,

        "remaining":remaining,
        "insight":insight}
