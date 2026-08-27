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
    total_expense=db.query(func.sum(models.Expense.amount)).filter(models.Expense.owner_id==user_id,
                                                            models.Expense.created_at>=data_range["start"],
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
    ).first()

    if most_frequent:
        cat,count,amount=most_frequent
        return {
            "name":cat,
            "count":count,
            "total_spent":float(amount)
        }
    return None
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
    INSIGHT: [3 sentences about their spending of 1 line.]
    TIP: [1 actionable tip]

    Give personalized financial insight.
    Be specific, actionable and encouraging.

    Then give practicals tips,1 sentence tip.
    
    IMPORTANT: Reply in plain text only. No markdown, no bullet points, 
    no asterisks, no headers. Just plain sentences.
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
def insight_logic_this_prev_month(status,this_month_total,projected_daily,current_avg_pace,safe_daily,days_remaining,remaining_budget,budget,message):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
    User financial data for this month:
    Currency:INR
    - Budget: {budget}
    - status: {status}
    - backend_insight: {message},
    - remaining_budget:{remaining_budget}
    - this_month_total:{this_month_total}
    -projected_month_end:{projected_daily}
    -days_remaining:{days_remaining}
    -current_avg_daily_spending:{current_avg_pace}
    -safe_daily:{safe_daily}
    

    You are a personal finance assistant.

    Generate a personalized financial insight in 2-3 sentences.

    Field descriptions:
    - status: Current budget health (Safe, Be Cautious, Warning).
    - this_month_total: Total amount spent in the current month.
    - projected_month_end: Estimated total spending by the end of the month based on the current spending pace.
    - current_avg_pace: Average amount spent per day so far this month.
    - safe_daily: Maximum amount the user can spend per day for the remaining days without exceeding the budget.
    - days_remaining: Number of days left in the current month.
    - remaining_budget: Budget still available for the current month.
    - budget: Total monthly budget.
    - backend_insight: Rule-based insight generated by the backend.
    If safe_daily is negative, do not mention it as a daily spending limit.
    If safe_daily is 0 and days_remaining is 0 then its the record of previous month which already concluded,so give times on the remaining_budget instead of safe_daily.s 
    Instead, explain that the user has already exceeded the budget and focus on reducing further spending.
    Avoid repeating the same sentence structure in every response.
    Write naturally as if you are a financial coach.
    
    If the backend_insight is present, use it as the primary fact and only improve its wording. Do not contradict it.
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """
    You are a personal finance assistant.

    Generate a personalized financial insight in 2-3 sentences.

    Rules:
    - Use only the provided data.
    - Do not invent numbers.
    - Keep the response under 60 words.
    - Be encouraging but realistic.
    - If backend_insight is provided, treat it as the primary fact.
    - If safe_daily is negative, do not describe it as a daily spending limit.
    - Return only the insight. Do not use markdown or bullet points.
    """
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    return response.choices[0].message.content
