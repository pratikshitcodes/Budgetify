from jose import JWTError,jwt
from fastapi import HTTPException,status,Depends
from datetime import datetime,timezone,timedelta
from . import schemas
from fastapi.security.oauth2 import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

#Tokens are obtained from the /login endpoint.
oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')

# Login with email/password
# → backend verifies
# → backend creates JWT
# → frontend stores JWT
# → frontend sends JWT in Authorization header for protected routes
# → OAuth2PasswordBearer extracts it
# → backend verifies it
# → backend gets user_id
# → protected route runs only for that user

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY IS not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

def create_access_token(token_data:dict):
    to_encode=token_data.copy()
    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp":expire,
        "type":"access"
    })
    jwt_token=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return jwt_token


def create_refresh_token(token_data:dict):
    to_encode=token_data.copy()
    expire=datetime.utcnow()+timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp":expire,
        "type":"refresh"})
    jwt_token=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return jwt_token

def verify_access_token(token:str,credential_exception):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        # jwt.decode checks and if any of there violated it raise an exception
        # 1. Is token signature valid?
        # 2. Has token been modified?
        # 3. Does it contain exp?
        # 4. Is current time past exp?
        user_id:str=payload.get("user_id")
        token_type:str=payload.get("type")
        if user_id is None or token_type!="access":
            raise credential_exception
        token_data=schemas.Token(id=user_id)
    except JWTError:
        raise credential_exception
    return token_data

def verify_refresh_token(token:str,credential_exception):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id:str=payload.get("user_id")
        token_type:str=payload.get("type")
        if user_id is None or token_type!="refresh":
            raise credential_exception
        token_data=schemas.Token(id=user_id)
    except JWTError:
        raise credential_exception
    return token_data

def get_current_user(token: str=Depends(oauth2_scheme)):
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})

    return verify_access_token(token,credentials_exception)