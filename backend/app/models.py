from sqlalchemy import Column,Integer,String,Float,ForeignKey,UniqueConstraint,Numeric
from .database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    email=Column(String,unique=True,nullable=False,index=True)
    password=Column(String,nullable=False)

class Expense(Base):
    __tablename__="expenses"
    id=Column(Integer,primary_key=True,index=True)
    title=Column(String,nullable=False,index=True)
    amount=Column(Numeric(10,2),nullable=False,index=True)
    description=Column(String,nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    owner_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    category=Column(String,nullable=False)

class Budget(Base):
    __tablename__="budgets"
    id=Column(Integer,primary_key=True,index=True)
    amount=Column(Numeric(10,2),nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    month=Column(Integer,nullable=False)
    year=Column(Integer,nullable=False)
    __table_args__ = (
    UniqueConstraint('user_id', 'month', 'year', name='unique_user_month_budget'),
)