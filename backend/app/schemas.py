from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class UserCreate(BaseModel):
    email:str
    password:str

class UserResponse(BaseModel):
    id:int
    email:str

    class config:
        orm_mode=True

class ExpenseCreate(BaseModel):
    title:str
    amount:int
    description:str
    category:str

class ExpenseResponse(BaseModel):
    title:str
    amount:int
    description:str
    owner_id:int
    created_at:datetime
    id:int
    category:str
    class config:
        orm_mode=True
    
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
    amount:int
    month:int
    year:int

class Budget_Response(BaseModel):
    status:str
    budget:float

    total_spent:float
    previous_month_spent:Optional[float]
    percentage_change:Optional[float]
    change_type:Optional[str]
    
    top_category:str
    top_category_spent:float

    remaining:float
    insight:str