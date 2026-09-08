from fastapi import FastAPI
from .database import engine
from . import models
from .routers import users,expenses,auth,ai,reports,groups,google_auth
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()

@app.get("/")
def check():
    return {"message":"API IS RUNNING!!!"}

app.include_router(users.router)
app.include_router(expenses.expense_router)
app.include_router(expenses.budget_router)
app.include_router(auth.router)
app.include_router(google_auth.router)
app.include_router(ai.ai_router)
app.include_router(reports.router)
app.include_router(groups.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



