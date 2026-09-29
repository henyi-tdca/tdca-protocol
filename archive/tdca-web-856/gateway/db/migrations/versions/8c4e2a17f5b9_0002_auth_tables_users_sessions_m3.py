"""0002 auth tables users sessions M3

Revision ID: 8c4e2a17f5b9
Revises: 50d63a4b5da2
Create Date: 2026-08-21 00:35:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '8c4e2a17f5b9'
down_revision = '50d63a4b5da2'
branch_labels = None
depends_on = None

_PROV = "data_provenance IN ('simulated','real','mixed')"


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('salt', sa.Text(), nullable=False),
        sa.Column('iterations', sa.Integer(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('data_provenance', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("role IN ('founder','operator','viewer')", name='ck_users_role'),
        sa.CheckConstraint(_PROV, name='ck_users_prov'),
        sa.PrimaryKeyConstraint('username'),
    )
    op.create_table(
        'sessions',
        sa.Column('token_hash', sa.Text(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.Text(), nullable=False),
        sa.Column('revoked', sa.Integer(), nullable=False),
        sa.Column('data_provenance', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint(_PROV, name='ck_sessions_prov'),
        sa.ForeignKeyConstraint(['username'], ['users.username']),
        sa.PrimaryKeyConstraint('token_hash'),
    )


def downgrade() -> None:
    op.drop_table('sessions')
    op.drop_table('users')
