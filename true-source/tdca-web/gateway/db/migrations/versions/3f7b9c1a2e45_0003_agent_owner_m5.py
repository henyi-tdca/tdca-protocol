"""0003 agent owner username M5

Revision ID: 3f7b9c1a2e45
Revises: 8c4e2a17f5b9
Create Date: 2026-08-21 11:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '3f7b9c1a2e45'
down_revision = '8c4e2a17f5b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # M5 归属迁移核心：agents.owner_username（TEXT NULL，逻辑 FK→users.username）
    # SQLite 增量加列不重建表；FK 约束由模型层声明（create_all 路径生效），
    # 存量库靠应用层写入强制（写路径 owner=登录用户）保障一致性。
    op.add_column('agents', sa.Column('owner_username', sa.Text(), nullable=True))
    # 存量回填：归属创始人（幂等——仅回填 NULL 行，重跑不回改）
    op.execute("UPDATE agents SET owner_username='founder' WHERE owner_username IS NULL")


def downgrade() -> None:
    op.drop_column('agents', 'owner_username')
