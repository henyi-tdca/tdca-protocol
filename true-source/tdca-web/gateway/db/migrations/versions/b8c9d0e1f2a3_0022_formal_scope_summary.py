"""0022 formal_scope_summary（SITE-CLAIMFIX-001 块 A）

- 仅 ADD COLUMN 一列：formal_conclusions.scope_summary（Text nullable，
  存量 NULL＝未补对外版适用范围，无需回填；simulated 存量 14 条豁免照常列出）；
- upgrade 以 inspect 条件加列（缺者加、存者跳）保幂等——照 0005 先例；
- downgrade 逆操作为 drop_column（SQLite 重建表模式由 alembic 批处理承接，
  照 0015~0018 先例），同样以 inspect 条件保幂等。
"""
from alembic import op
import sqlalchemy as sa


revision = 'b8c9d0e1f2a3'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None

TABLE = 'formal_conclusions'
COLUMN = 'scope_summary'


def _columns(bind) -> set:
    insp = sa.inspect(bind)
    return {c['name'] for c in insp.get_columns(TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    if COLUMN not in _columns(bind):
        op.add_column(TABLE, sa.Column(COLUMN, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if COLUMN in _columns(bind):
        op.drop_column(TABLE, COLUMN)
