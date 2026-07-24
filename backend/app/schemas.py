from pydantic import BaseModel,ConfigDict,validator
from typing import Optional,List,Dict
from datetime import datetime

class UserCreate(BaseModel):
    email:str
    password:str

class UserResponse(BaseModel):
    # It means Pydantic is allowed to extract fields from object attributes, not only dict keys.without config pydantic mainly dictionary style data mapping karta ha like:  data["tittle"] data["amount"]
    model_config = ConfigDict(from_attributes=True)

    id:int
    email:str


class ExpenseCreate(BaseModel):
    title:str
    amount:float
    description:str
    category:str
    
    # Decorator — tells Pydantic "run this function 
    # when 'amount' field is received"
    
    # 'amount' → field name it watches
    @validator('amount')
    def amount_positive(cls,v):
        if v<=0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('title')
    def title_not_empty(cls,v):
        if not v.strip():
            raise ValueError('Title cannot be blank')
        return v

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title:str
    amount:float
    description:str
    owner_id:int
    created_at:datetime
    id:int
    category:str
    
class TokenData(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str

class Token(BaseModel):
    id:int|None=None

class new_access_token(BaseModel):
    new_access_token:str
    type:str

class Budget_Create(BaseModel):
    amount:float
    month:int
    year:int

    @validator('amount')
    def amount_positive(cls,v):
        if v<=0:
            raise ValueError('Budget must be positive')
        return v

class Budget_Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status:str
    budget:float

    total_spent:float
    previous_month_spent:Optional[float]
    percentage_change:Optional[float]
    change_type:Optional[str]
    
    top_category:Optional[str]=None
    top_category_spent:float

    remaining:float
    insight:str

class Budget_Update(BaseModel):
    amount:float
    month:int
    year:int
    @validator('amount')
    def amount_positive(cls,v):
        if v<=0:
            raise ValueError('Budget must be positive')
        return v


class MostFrequent(BaseModel):
    name: str
    count: int
    total_spent: float
class ExpenseInfo(BaseModel):
    title: str
    amount: float
    category: str


class CategoryComparison(BaseModel):
    this: float
    prev: float


class DailyExpense(BaseModel):
    day: int
    cumulative: float

class BiggestIncrease(BaseModel):
    category: str
    percentage: float
class MonthlyAnalysisResponse(BaseModel):
    this_month_total: float
    prev_month_total: float

    this_month_count: int
    prev_month_count: int

    most_frequent_entry: MostFrequent

    highest: Optional[ExpenseInfo]

    recommended_daily_pace: float

    top3_expenses: List[ExpenseInfo]

    category_comparison: Dict[str, CategoryComparison]

    this_month_daily: List[DailyExpense]
    prev_month_daily: List[DailyExpense]

    projected_daily: float
    current_avg_pace: float
    safe_daily: float
    remaining_days: int

    weekend_spending:float
    weekday_spending:float

    high_value_count:int
    threshold:float
    biggest_increase:BiggestIncrease|None=None
    
    no_spend_days:int
    remaining_budget: float
    budget: float

    status: str
    insight: str