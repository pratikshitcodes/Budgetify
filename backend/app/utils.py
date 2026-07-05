from passlib.context import CryptContext
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
from datetime import datetime
from sqlalchemy import func,extract
from . import models
from groq import Groq
import calendar
import os



def hash(password:str):
    return pwd_context.hash(password)
def verify(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)


def calculate_start_end(month,year):
    start=datetime(year,month,1)
    if month==12:
        end=datetime(year+1,1,1)
    else:
        end=datetime(year,month+1,1)
    return {"start":start,"end":end}

def calculate_expense(db,month,year,user_id):
    data_range=calculate_start_end(month,year)
    total_expense=db.query(func.sum(models.Expense.amount)).filter(models.Expense.owner_id==user_id,                             models.Expense.created_at>=data_range["start"],
    models.Expense.created_at<data_range["end"]).scalar()
    return total_expense or 0

def find_monthly_expenses(db,month,year,user_id):
    data_range=calculate_start_end(month,year)
    expenses=db.query(models.Expense).filter(
        user_id==models.Expense.owner_id,
        models.Expense.created_at>=data_range["start"],
        models.Expense.created_at<data_range["end"]
    ).all()
    return expenses
def most_frequent_entries(db,month,year,user_id):
    data_range=calculate_start_end(month,year)
    most_frequent=db.query(models.Expense.category,func.count(models.Expense.id),func.sum(models.Expense.amount)).filter(user_id==models.Expense.owner_id,
     models.Expense.created_at>=data_range["start"],
     models.Expense.created_at<data_range["end"]
    ).group_by(
        models.Expense.category
    ).order_by(
        func.count(models.Expense.id).desc()
    ).limit(3).all()

    return  [
    {"name": cat, "count": count,"total_spent":amount}
    for cat, count,amount in most_frequent
]
def build_cumulative_graph(month, year, daily_totals):
    days_in_month=calendar.monthrange(year,month)[1]
    running=0
    res=[]
    for day in range(1,days_in_month+1):
        running+=daily_totals.get(day,0)
        res.append({"day":day,"cumulative":running})
    return res

def day_to_day_expenses(db,month,year,user_id):
    data_range=calculate_start_end(month,year)
    result=db.query(
        extract("day",models.Expense.created_at).label("day"),func.sum(models.Expense.amount).label("total")
        ).filter(
            models.Expense.owner_id==user_id,
            models.Expense.created_at>=data_range["start"],
            models.Expense.created_at<data_range["end"]
        ).group_by(
            extract("day",models.Expense.created_at)
        ).all()
    dict_res={}
    for row in result:
        dict_res[int(row.day)]=float(row.total)
    
    return build_cumulative_graph(month,year,dict_res)
def insight_logic(total_expenses, previous_month_spent, percentage_change, change_type, top_category_name, top_category_spent, budget, remaining):
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""
    User financial data for this month:
    - Budget: ₹{budget}
    - Total spent: ₹{total_expenses}
    - Remaining: ₹{remaining}
    - Previous month spent: ₹{previous_month_spent}
    - Change: {percentage_change}% ({change_type})
    - Top spending category: {top_category_name} (₹{top_category_spent})
    

    Respond in exactly this format:
    INSIGHT: [5 sentences about their spending]
    TIP: [2 actionable tip]

    Give personalized financial insight.
    Be specific, actionable and encouraging in 2-3 sentences.

    Then give practicals tips,1 sentence tip.
    
    IMPORTANT: Reply in plain text only. No markdown, no bullet points, 
    no asterisks, no headers. Just plain sentences.
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content