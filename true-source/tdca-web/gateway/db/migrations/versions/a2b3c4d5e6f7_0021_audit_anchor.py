"""0021_audit_anchor

AUDIT-ANCHOR-001：账本锚点两表——audit_day_anchors（日锚，含 none 缺日行与多版本更正）
＋audit_batch_anchors（批锚，与日锚版本同进退）。口径（照 0005/0006 同式）：
- 以 inspect 条件建表（缺者建、存者跳）保幂等；
- 表结构以 db/models.py 现定义为唯一准绳；
- downgrade 只删「本件实际所建」之表：upgrade 将实建表名录入 bookkeeping 表
  （_mig0021_audit_anchor），downgrade 照册精确摘除并自清——存量自建表一律保留。
"""

from alembic import op
import sqlalchemy as sa

from db.models import Base  # noqa: F401  (import registers all tables)

revision = "a2b3c4d5e6f7"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None

# 本件所建两表（与 models.py __tablename__ 对账）
NEW_TABLES = ["audit_day_anchors", "audit_batch_anchors"]

# 自建自清之 bookkeeping 表名
BOOKKEEP = "_mig0021_audit_anchor"


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name in NEW_TABLES and t.name not in existing
    ]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)
        bk = op.create_table(
            BOOKKEEP,
            sa.Column("name", sa.Text, primary_key=True),
        )
        op.bulk_insert(bk, [{"name": t.name} for t in to_create])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    created = set()
    if BOOKKEEP in existing:
        created = {
            row[0]
            for row in bind.execute(sa.text(f"SELECT name FROM {BOOKKEEP}"))
        }

    present = [
        t for t in reversed(Base.metadata.sorted_tables)
        if t.name in created and t.name in existing
    ]
    for tbl in present:
        tbl.drop(bind=bind, checkfirst=True)

    if BOOKKEEP in existing:
        op.drop_table(BOOKKEEP)
