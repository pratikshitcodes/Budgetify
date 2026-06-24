from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models,oauth,schemas
from .. import utils
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router=APIRouter(
    tags=["Authentication"],
    prefix='/login'
)
#OAuth2PasswordRequestForm is the fastapi helper for reading login form in standard Oauth2 way.This tells the fastapi that this endpoint expects form details such as email and password. 
@router.post("/",response_model=schemas.TokenData,status_code=status.HTTP_200_OK)
def login(user_credentials:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    #db.query(models.User) is same as select something from table(model.User) and filter is same as where
    user=db.query(models.User).filter(models.User.email==user_credentials.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"INVALID CREDENTIALS")
    if not utils.verify(user_credentials.password,user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"INVALID CREDENTIALS")
    access_token=oauth.create_access_token({"user_id":user.id})
    refresh_token=oauth.create_refresh_token({"user_id":user.id})
    return {"access_token":access_token,"refresh_token":refresh_token,"token_type":"bearer"}

@router.post('/refresh_token')
def new_access_token(refresh_token:str=Depends(oauth.oauth2_scheme)):
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})

    token_data=oauth.verify_refresh_token(refresh_token,credentials_exception)
    
    new_access_token=oauth.create_access_token({"user_id":token_data.id})
    return {"new_access_token":new_access_token,"token_type":"bearer"}
