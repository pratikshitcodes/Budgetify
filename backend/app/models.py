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

class Group(Base):
    __tablename__="groups"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False)
    owner_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))

class GroupMember(Base):
    __tablename__="group_members"
    id=Column(Integer,primary_key=True,index=True)
    group_id=Column(Integer,ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    name=Column(String,nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=True)

class GroupExpense(Base):
    __tablename__="group_expenses"
    id=Column(Integer,primary_key=True,index=True)
    group_id=Column(Integer,ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    title=Column(String,nullable=False)
    amount=Column(Numeric(10,2),nullable=False)
    paid_by_member_id=Column(Integer,ForeignKey("group_members.id"),nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))

class GroupExpenseSplit(Base):
    __tablename__="group_expense_splits"
    id=Column(Integer,primary_key=True,index=True)
    expense_id=Column(Integer,ForeignKey("group_expenses.id",ondelete="CASCADE"),nullable=False)
    member_id=Column(Integer,ForeignKey("group_members.id"),nullable=False)
    share_amount=Column(Numeric(10,2),nullable=False)