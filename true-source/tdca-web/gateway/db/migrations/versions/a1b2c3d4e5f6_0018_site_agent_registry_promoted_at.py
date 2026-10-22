"""0018 site_agent_registry promoted_at + promotion_nca_ref（GO-LIVE-001 步2 转正状态位）

- 仅 ADD COLUMN 两列（nullable，存量 NULL＝未转正，无需回填）：
  promoted_at（转正时点 ISO 串）／promotion_nca_ref（转正存证号，⛔ 存令牌值）；
- 表内同批既有列全不动；downgrade 逆操作为 drop_column（SQLite 重建表模式由
  alembic 批处理承接——本仓 downgrade 口径照 0015~0017 先例）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'f9a0b1c2d3e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_agent_registry',
                  sa.Column('promoted_at', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('promotion_nca_ref', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('site_agent_registry', 'promotion_nca_ref')
    op.drop_column('site_agent_registry', 'promoted_at')
