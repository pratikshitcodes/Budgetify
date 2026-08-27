from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from ..database import get_db
from .. import oauth, schemas
from ..services import group_service

router = APIRouter(
    prefix='/groups',
    tags=['Groups']
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[schemas.Token, Depends(oauth.get_current_user)]


@router.post('', response_model=schemas.GroupResponse)
def create_group(payload: schemas.GroupCreate, db: DbSession, current_user: CurrentUser):
    group = group_service.create_group(db, current_user.id, payload.name, payload.members)
    return group_service.get_group_detail(db, group.id, current_user.id)


@router.get('', response_model=List[schemas.GroupListItem])
def list_groups(db: DbSession, current_user: CurrentUser):
    groups = group_service.list_groups(db, current_user.id)
    return [{"id": g.id, "name": g.name, "created_at": g.created_at} for g in groups]


@router.get('/{group_id}', response_model=schemas.GroupResponse)
def get_group(group_id: int, db: DbSession, current_user: CurrentUser):
    return group_service.get_group_detail(db, group_id, current_user.id)


@router.post('/{group_id}/members', response_model=schemas.GroupMemberResponse)
def add_member(group_id: int, payload: schemas.GroupMemberCreate, db: DbSession, current_user: CurrentUser):
    member = group_service.add_member(db, group_id, current_user.id, payload.name)
    return member


@router.post('/{group_id}/expenses', response_model=schemas.GroupResponse)
def add_expense(group_id: int, payload: schemas.GroupExpenseCreate, db: DbSession, current_user: CurrentUser):
    return group_service.add_expense(
        db,
        group_id,
        current_user.id,
        payload.title,
        payload.amount,
        payload.paid_by_member_id,
        payload.split_member_ids
    )


@router.delete('/{group_id}/expenses/{expense_id}')
def delete_expense(group_id: int, expense_id: int, db: DbSession, current_user: CurrentUser):
    return group_service.delete_expense(db, group_id, expense_id, current_user.id)


@router.delete('/{group_id}')
def delete_group(group_id: int, db: DbSession, current_user: CurrentUser):
    return group_service.delete_group(db, group_id, current_user.id)
