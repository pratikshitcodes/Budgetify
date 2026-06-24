from fastapi import FastAPI,status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import engine,get_db
from .. import models
from ..schemas import UserCreate,UserResponse
from .. import utils

router=APIRouter(
    prefix='/users',
    tags=['Users']
)

#Before calling this route, run get_db() and give me the yielded database session.
@router.post("/",status_code=status.HTTP_201_CREATED,response_model=UserResponse)
def register(user_details:UserCreate,db:Session=Depends(get_db)):
    user_password=user_details.password
    hashed_password=utils.hash(user_password)
    user_details.password=hashed_password

    new_user=models.User(**user_details.dict())

    db.add(new_user)
    db.commit()
    #refresh is useful it fetches the row that was added kyunki add karne par id was auto generated so wo chez new user me nhi ha
    #so we refersh which means fetch this row again from the database
    db.refresh(new_user)
    #not returning the password not even the hashed password
    return new_user
