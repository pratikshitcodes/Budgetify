import os
import secrets
import requests
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

from ..database import get_db
from .. import models, oauth

router = APIRouter(
    tags=["Authentication"],
    prefix='/auth/google'
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

class CodeExchangeRequest(BaseModel):
    code: str

@router.get("/login")
def google_login(response: Response):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Generate secure state
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False, # Use True in production with HTTPS
        max_age=300, # 5 minutes
        samesite="lax"
    )
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        "scope=openid%20email%20profile&"
        "access_type=offline&"
        f"state={state}"
    )
    # Return redirect but attach the cookie from the response
    redirect = RedirectResponse(url=auth_url)
    redirect.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False, 
        max_age=300,
        samesite="lax"
    )
    return redirect

@router.get("/callback")
def google_callback(request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Code not provided")
    
    # Validate OAuth state
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or state != cookie_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    response = requests.post(token_url, data=data)
    if not response.ok:
        raise HTTPException(status_code=400, detail="Failed to exchange token with Google")
    
    token_data = response.json()
    id_token_str = token_data.get("id_token")
    if not id_token_str:
        raise HTTPException(status_code=400, detail="No id_token in response")
    
    try:
        # Client ID must match audience
        id_info = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    email = id_info.get("email")
    google_id = id_info.get("sub")
    email_verified = id_info.get("email_verified")
    
    if not email_verified:
        raise HTTPException(status_code=400, detail="Google email not verified")
        
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if user:
        if not user.google_id:
            user.google_id = google_id
            if user.auth_provider == "email":
                user.auth_provider = "email_and_google"
            db.commit()
    else:
        user = models.User(
            email=email,
            password=None,
            auth_provider="google",
            google_id=google_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    # Generate secure short-lived auth code
    auth_code = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    new_auth_code = models.OAuthAuthCode(
        code=auth_code,
        user_id=user.id,
        expires_at=expires_at,
        used=0
    )
    db.add(new_auth_code)
    db.commit()
    
    frontend_redirect_url = f"{FRONTEND_URL}/auth_success.html?code={auth_code}"
    
    redirect = RedirectResponse(url=frontend_redirect_url)
    redirect.delete_cookie("oauth_state")
    return redirect

@router.post("/exchange")
def exchange_code(req: CodeExchangeRequest, db: Session = Depends(get_db)):
    auth_code = db.query(models.OAuthAuthCode).filter(models.OAuthAuthCode.code == req.code).first()
    
    if not auth_code:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
        
    if auth_code.used == 1:
        raise HTTPException(status_code=400, detail="Authorization code already used")
        
    if datetime.now(timezone.utc) > auth_code.expires_at:
        raise HTTPException(status_code=400, detail="Authorization code expired")
        
    # Mark as used
    auth_code.used = 1
    db.commit()
    
    # Issue standard application JWT
    access_token = oauth.create_access_token({"user_id": auth_code.user_id})
    refresh_token = oauth.create_refresh_token({"user_id": auth_code.user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
