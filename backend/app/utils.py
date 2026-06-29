from passlib.context import CryptContext
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
from datetime import datetime
from sqlalchemy import func
from . import models
from groq import Groq
import os



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
    
    Give a 2-3 sentence personalized financial insight.
    Be specific, actionable and encouraging.
    Mention the top category and give one practical tip.
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content