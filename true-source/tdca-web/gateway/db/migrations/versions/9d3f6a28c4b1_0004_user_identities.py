"""0004 user identities (agent_card 持久化, GSEQ-0700)

Revision ID: 9d3f6a28c4b1
Revises: 3f7b9c1a2e45
Create Date: 2026-08-29 23:35:00.000000

注册端点静默丢弃 identity_type/agent_card/owner_auth（WorkBuddy D2 核验发现）——
新增 user_identities 表持久化身份三要素，非原生性（external + owner_auth）链上可机验。
"""
from alembic import op
import sqlalchemy as sa


revision = '9d3f6a28c4b1'
down_revision = '3f7b9c1a2e45'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_identities',
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('identity_type', sa.Text(), nullable=False, server_default='native'),
        sa.Column('agent_card_json', sa.Text(), nullable=True),
        sa.Column('owner_auth', sa.Text(), nullable=True),
        sa.Column('nca_ref', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['username'], ['users.username']),
        sa.PrimaryKeyConstraint('username'),
        sa.CheckConstraint("identity_type IN ('native','external')",
                           name='ck_user_identities_type'),
    )


def downgrade() -> None:
    op.drop_table('user_identities')
