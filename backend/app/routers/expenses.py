from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy import func
from typing import List,Annotated,Optional
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from datetime import datetime
from .. import oauth
from ..utils import calculate_expense,insight_logic,find_monthly_expenses,day_to_day_expenses,most_frequent_entries,insight_logic_this_prev_month
import calendar
from decimal import Decimal
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
        month:Optional[int] =None,
        year:Optional[int]  =None,
        limit:int=10,
        skip:int=0):
   
   query = db.query(models.Expense).filter(models.Expense.owner_id == current_user.id)
    
   if month and year:
        start = datetime(year, month, 1)
        end = datetime(year+1, 1, 1) if month == 12 else datetime(year, month+1, 1)
        query = query.filter(
            models.Expense.created_at >= start,
            models.Expense.created_at < end
        )
    
   return query.order_by(models.Expense.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


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

@expense_router.get('/chart-data')
def get_chart_data(db: DbSession, current_user: CurrentUser,
                   month: int = None, year: int = None):
    
    if month and year:
        start = datetime(year, month, 1)
        end = datetime(year+1, 1, 1) if month == 12 else datetime(year, month+1, 1)
        expenses = db.query(models.Expense).filter(
            current_user.id==models.Expense.owner_id,
            models.Expense.created_at >= start,
            models.Expense.created_at < end
        ).all()
    
    return expenses
@budget_router.get('/monthly-stats')
def analyse_monthly_expenses(
        db:DbSession,
        current_user:CurrentUser,
        month:Optional[int]=None,
        year:Optional[int]=None):
    
    this_month_total=calculate_expense(db,month,year,current_user.id)

    prev_month_total=calculate_expense(db,12,year-1,current_user.id) if month==1 else calculate_expense(db,month-1,year,current_user.id)
    
    this_month_expenses=find_monthly_expenses(db,month,year,current_user.id)

    prev_month_expenses=find_monthly_expenses(db,12,year-1,current_user.id) if month==1 else find_monthly_expenses(db,month-1,year,current_user.id)

    this_month_count=len(this_month_expenses)
    prev_month_count=len(prev_month_expenses)

    highest=max(this_month_expenses,key=lambda e:e.amount,default=None)

    
    avg=sum(float(e.amount) for e in this_month_expenses)/len(this_month_expenses) if this_month_expenses else 0

    

    highest_data=None
    if highest:
        highest_data={
            "title":highest.title,
            "category":highest.category,
            "amount":float(highest.amount)
        }

    #category comparision list
    all_categories=set(
        [e.category for e in this_month_expenses]+
        [e.category for e in prev_month_expenses]
    )

    category_comparison={}
    for cat in all_categories:
        this_total=sum(float(e.amount) for e in this_month_expenses if e.category==cat)
        prev_total=sum(float(e.amount) for e in prev_month_expenses if e.category==cat)
        category_comparison[cat]={
            "this":this_total,
            "prev":prev_total
        }
    most_frequent=most_frequent_entries(db,month,year,current_user.id)
    top3 = sorted(this_month_expenses, key=lambda e: e.amount, reverse=True)[:3]
    this_graph=day_to_day_expenses(db,month,year,current_user.id)
    prev_graph=day_to_day_expenses(db,month-1,year,current_user.id)

    days_in_month=calendar.monthrange(year,month)[1]
    today=datetime.now()
    days_passed=today.day
    days_remaining=days_in_month-days_passed

    projected_daily=avg*days_in_month

    current_avg_pace=float(this_month_total)/days_passed if days_passed>0 else 0

    budget=db.query(models.Budget).filter(
        models.Budget.user_id==current_user.id,
        models.Budget.month==month,
        models.Budget.year==year
    ).first()

    remaining_budget=budget.amount-Decimal(this_month_total)
    safe_daily=(Decimal(budget.amount)-Decimal(this_month_total))/Decimal(days_remaining) if days_remaining>0 else 0


    if current_avg_pace>0:
        day_until_budget_exhausted=round(float(remaining_budget)/current_avg_pace)
    else:
        day_until_budget_exhausted=None
    message=None
    status=None
    if(safe_daily>=avg):
        status="Safe"
        message = f"Great job! You're comfortably within your budget. Your recommended daily spending limit is ₹{safe_daily:.2f} for the rest of the month."
    
    elif(0<safe_daily<avg):
        status="Be cautious"
        if day_until_budget_exhausted is not None and day_until_budget_exhausted < days_remaining:
            message = f"At your current spending pace, your budget may be exhausted in about {day_until_budget_exhausted} days."
        else:
            message = "You're still within budget, but your remaining daily spending limit is getting lower. Spend wisely."
    else:
        status="Warning"
        message="You have already exceeded your monthly budget. Any further spending will be above your planned budget."
    insight_message=insight_logic_this_prev_month(status,this_month_total,projected_daily,current_avg_pace,safe_daily,days_remaining,remaining_budget,float(budget.amount),message)

    return {
        "this_month_total":this_month_total,
        "prev_month_total":prev_month_total,

        "this_month_expenses":this_month_expenses,
        "prev_month_expenses":prev_month_expenses,

        "this_month_count":this_month_count,
        "prev_month_count":prev_month_count,

        "most_frequent_entry":most_frequent,
        "highest":highest_data,
        "recommended_daily_pace":avg,
        "top3_expenses": [
        {"title": e.title, "amount": float(e.amount), "category": e.category}
            for e in top3
        ],
        "category_comparison":category_comparison,

        "this_month_daily":this_graph,
        "prev_month_daily":prev_graph,

        "projected_daily":projected_daily,
        "current_avg_pace":current_avg_pace,
        "safe_daily":safe_daily,
        "remaining_days":days_remaining,

        "remaining_budget":remaining_budget,
        "budget":float(budget.amount),
        "status":status,
        "insight":insight_message,
    }



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
    
    used_percentage=float(total_expenses)/float(amount)
    remaining=float(amount)-float(total_expenses)
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
            change_type="Increased"
        elif total_expenses<previous_month_spent:
            change_type="Decreased"
        else:
            change_type="is Same"
    insight=insight_logic(total_expenses,previous_month_spent,percentage_change,change_type,top_category_name,top_category_spent,amount,remaining);
    return {

        "status": budget_status,
        "budget": float(amount),

        "total_spent": float(total_expenses),
        "previous_month_spent": float(previous_month_spent),

        "percentage_change": float(percentage_change) if percentage_change else None,
        "change_type": change_type,

        "top_category": top_category_name,
        "top_category_spent": float(top_category_spent),
        
        "remaining": float(remaining),
        "insight": insight
}

@budget_router.get('/current')
def get_current_budget(db:DbSession,current_user:CurrentUser):
    today=datetime.now()
    budget=db.query(models.Budget).filter(
        models.Budget.user_id==current_user.id,
        models.Budget.month==today.month,
        models.Budget.year==today.year
    ).first()
    if budget is None:
        return {"amount":None}
    return {"amount":budget.amount}

@budget_router.put('/')
def update_budget(
    updated_details:schemas.Budget_Update,
    db:DbSession,
    current_user:CurrentUser,
    month:int,
    year:int):
    
    
    budget_query=db.query(models.Budget).filter(
        models.Budget.user_id==current_user.id,
        models.Budget.month==month,
        models.Budget.year==year
    )
    budget=budget_query.first()
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No result found")
    budget_query.update(updated_details.model_dump(),synchronize_session=False)
    db.commit()
    return {
        "message":"Budget updated successfully",
        "budget":budget_query.first()
    }

