"""0025_authorization_special_terms（ALPHA-D D-2：授权件特别条款栏位落地）

- authorization_records 增两列（Text nullable，存量 NULL＝未载特别条款，无需回填）：
  special_terms（约定文本）／special_terms_sha256（文本 sha256 机验锚）；
- upgrade 以 inspect 条件加列（缺者加、存者跳）保幂等——照 0022 先例；
- downgrade 逆操作为 drop_column（SQLite 重建表模式由 alembic 批处理承接，
  照 0015~0018 先例），同样以 inspect 条件保幂等。
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d1'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None

TABLE = 'authorization_records'
COLUMNS = ('special_terms', 'special_terms_sha256')


def _columns(bind) -> set:
    insp = sa.inspect(bind)
    return {c['name'] for c in insp.get_columns(TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    existing = _columns(bind)
    for col in COLUMNS:
        if col not in existing:
            op.add_column(TABLE, sa.Column(col, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = _columns(bind)
    for col in reversed(COLUMNS):
        if col in existing:
            op.drop_column(TABLE, col)
