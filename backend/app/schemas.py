from pydantic import BaseModel,ConfigDict
from typing import Optional
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