from pydantic import BaseModel,ConfigDict,validator
from typing import Optional,List,Dict
from datetime import datetime

from pydantic import BaseModel, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    report: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
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

class GroupCreate(BaseModel):
    name: str
    members: List[str]

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Group name cannot be blank')
        return v.strip()

class GroupMemberCreate(BaseModel):
    name: str

class GroupExpenseCreate(BaseModel):
    title: str
    amount: float
    paid_by_member_id: int
    split_member_ids: Optional[List[int]] = None

    @validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class GroupMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class GroupListItem(BaseModel):
    id: int
    name: str
    created_at: datetime

class GroupBalance(BaseModel):
    member_id: int
    name: str
    paid: float
    owed: float
    net: float

class GroupSettlement(BaseModel):
    from_member_id: int
    from_name: str
    to_member_id: int
    to_name: str
    amount: float

class GroupExpenseSplitResponse(BaseModel):
    member_id: int
    member_name: str
    share_amount: float

class GroupExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    paid_by: str
    paid_by_member_id: int
    created_at: datetime
    splits: List[GroupExpenseSplitResponse]

class GroupResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    members: List[GroupMemberResponse]
    expenses: List[GroupExpenseResponse]
    balances: List[GroupBalance]
    settlements: List[GroupSettlement]

class BattleRound(BaseModel):
    category: str
    month1_spending: float
    month2_spending: float
    difference: float
    winner: str
    point_awarded_to: Optional[str] = None

class MonthBattleResponse(BaseModel):
    month1: Dict[str, Any]
    month2: Dict[str, Any]
    rounds: List[BattleRound]
    total_rounds: int
    overall_winner: str
