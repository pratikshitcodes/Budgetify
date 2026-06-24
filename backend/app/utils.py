from passlib.context import CryptContext
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
from datetime import datetime
from sqlalchemy import func
from . import models

def hash(password:str):
    return pwd_context.hash(password)
def verify(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def calculate_expense(db,month,year,user_id):
    start=datetime(year,month,1)
    if month==12:
        end=datetime(year+1,1,1)
    else:
        end=datetime(year,month+1,1)
    total_expense=db.query(func.sum(models.Expense.amount)).filter(models.Expense.owner_id==user_id,
                                                  models.Expense.created_at>=start,
                                                  models.Expense.created_at<end).scalar()
    return total_expense or 0

def insight_logic(total_expenses,previous_month_spent,percentage_change,change_type,top_category_name,top_category_spent):
    insight=""
    if previous_month_spent==None or previous_month_spent==0:
        insight="This is your first month to be Tracked"
    else:
        if change_type=="Increases":
            insight=(f"You spent ₹({total_expenses:.2f}) this month which has increased by ({percentage_change})% "
                     f"compared to previous month, where you spent ₹({previous_month_spent:.2f}) last month."
                     f"The main reason for this increase is ({top_category_name}) where you spent ₹({top_category_spent:.2f})")
        elif change_type=="Decreases":
            insight=(f"You have managed your expenses so well," 
                     f"you spent ({abs(percentage_change)})% lesser than the previous month")
        else:
            insight=(
                    f"Your spending this month (₹{total_expenses}) is similar to last month "
                    f"(₹{previous_month_spent})."
                )
    return insight
        
