"""add group tables

Revision ID: a1b2c3d4e5f6
Revises: 196344202908
Create Date: 2026-08-26 20:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '196344202908'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_id'), 'groups', ['id'], unique=False)

    op.create_table(
        'group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_members_id'), 'group_members', ['id'], unique=False)

    op.create_table(
        'group_expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('paid_by_member_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paid_by_member_id'], ['group_members.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_expenses_id'), 'group_expenses', ['id'], unique=False)

    op.create_table(
        'group_expense_splits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('share_amount', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['expense_id'], ['group_expenses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['group_members.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_expense_splits_id'), 'group_expense_splits', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_group_expense_splits_id'), table_name='group_expense_splits')
    op.drop_table('group_expense_splits')
    op.drop_index(op.f('ix_group_expenses_id'), table_name='group_expenses')
    op.drop_table('group_expenses')
    op.drop_index(op.f('ix_group_members_id'), table_name='group_members')
    op.drop_table('group_members')
    op.drop_index(op.f('ix_groups_id'), table_name='groups')
    op.drop_table('groups')
