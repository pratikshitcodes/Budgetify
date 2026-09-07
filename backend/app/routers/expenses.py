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
from ..services import expense_service, analytics_service
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
@expense_router.get('/chart-data')
def get_chart_data(db: DbSession, current_user: CurrentUser,
                   month: Optional[int] = None, year: Optional[int] = None):
    
    now = datetime.now()
    if month is None:
        month = now.month
    if year is None:
        year = now.year
        
    month = int(month)
    year = int(year)
    
    start = datetime(year, month, 1)
    end = datetime(year+1, 1, 1) if month == 12 else datetime(year, month+1, 1)
    expenses = db.query(models.Expense).filter(
            current_user.id==models.Expense.owner_id,
            models.Expense.created_at >= start,
            models.Expense.created_at < end
        ).all()
    
    return expenses

@expense_router.get('/{id}',response_model=schemas.ExpenseResponse)
def get_expenses(id:int,db:DbSession,
        current_user:CurrentUser):
   expense=db.query(models.Expense).filter(models.Expense.id==id,models.Expense.owner_id==current_user.id).first()
   if expense is None:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No such Results found!!!")
   return expense

@expense_router.get('/',response_model=List[schemas.ExpenseResponse])
def get_expenses(db:DbSession,
        current_user:CurrentUser,
        month:Optional[int] =None,
        year:Optional[int]  =None,
        limit:int=10,
        skip:int=0):
   
   return expense_service.get_expense(db,current_user,month,year,limit,skip)



@expense_router.post('/',status_code=status.HTTP_201_CREATED)
def post_expense(post_details:schemas.ExpenseCreate,db:DbSession, current_user:CurrentUser):
    return expense_service.add_expense(post_details.model_dump(),db,current_user)

@expense_router.delete('/{id}')
def delete_expense(id:int,db:DbSession,
                   current_user:CurrentUser):
    expense_service.delete_expense(id,db,current_user)
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



@budget_router.get('/monthly-stats',response_model=schemas.MonthlyAnalysisResponse)
def analyse_monthly_expenses(
        db:DbSession,
        current_user:CurrentUser,
        month:Optional[int]=None,
        year:Optional[int]=None,
        compare_month:Optional[int]=None,
        compare_year:Optional[int]=None):
    
    result = analytics_service.get_detailed_monthly_analysis(db, current_user.id, month, year, compare_month, compare_year)
    
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget Is Not Initialised For This Month...")
    
    return result


@budget_router.get("/analytics",response_model=schemas.Budget_Response)
def analytics(db:DbSession,
              current_user:CurrentUser,
              month:int,
              year:int):
    budget=db.query(models.Budget).filter(models.Budget.user_id==current_user.id,
     models.Budget.month==month,
     models.Budget.year==year).first()
    
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget Is Not Initialised For This Month...")
        
    amount=budget.amount

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
        previous_month_spent=float(calculate_expense(db,12,year-1,current_user.id))
    else:
        previous_month_spent=float(calculate_expense(db,month-1,year,current_user.id))
    if previous_month_spent==0:
        percentage_change=None
    else:
        percentage_change=Decimal(((float(total_expenses)-previous_month_spent)/previous_month_spent)*100)

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
        "budget": amount,

        "total_spent": float(total_expenses),
        "previous_month_spent":round( float(previous_month_spent),2),

        "percentage_change": round(float(percentage_change),2) if percentage_change else None,
        "change_type": change_type,

        "top_category": top_category_name,
        "top_category_spent": round(float(top_category_spent),2),
        
        "remaining": round(float(remaining),2),
        "insight": insight
    }

@budget_router.post('/')
def create_budget(budget_details:schemas.Budget_Create,
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

    db.commit()
    return {"message":"Budget Created Successfully!!!"}

@budget_router.get('/current')
def get_current_budget(
    db:DbSession,
    current_user:CurrentUser,
    month:int,
    year:int):
    budget=db.query(models.Budget).filter(
        models.Budget.user_id==current_user.id,
        models.Budget.month==month,
        models.Budget.year==year
    ).first()
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Budget Is Not Initialised For This Month...")
    else:
        return {"amount":budget.amount}

@budget_router.put('/')
def update_budget(
    updated_details:schemas.Budget_Update,
    db:DbSession,
    current_user:CurrentUser):
    
    
    budget_query=db.query(models.Budget).filter(
        models.Budget.user_id==current_user.id,
        models.Budget.month==updated_details.month,
        models.Budget.year==updated_details.year
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


