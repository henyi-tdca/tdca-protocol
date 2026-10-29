"""0020_use_u1_upload

「用」组 U-1 素材上传：upload_records 表（谁传／何时／多大／哈希／受理类别——站内留痕＋哈希清单）。
口径（照 0005/0006 同式）：
- 以 inspect 条件建表（缺者建、存者跳）保幂等；
- 表结构以 db/models.py 现定义为唯一准绳；
- downgrade 只删「本件实际所建」之表：upgrade 将实建表名录入 bookkeeping 表
  （_mig0020_use_u1_upload），downgrade 照册精确摘除并自清——存量自建表一律保留。
"""

from alembic import op
import sqlalchemy as sa

from db.models import Base  # noqa: F401  (import registers all tables)

revision = "b5c6d7e8f9a0"
down_revision = "0a1b2c3d4e5f"
branch_labels = None
depends_on = None

# 本件所建一表（与 models.py __tablename__ 对账）
NEW_TABLES = ["upload_records"]

# 自建自清之 bookkeeping 表名
BOOKKEEP = "_mig0020_use_u1_upload"


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

    if BOOKKEEP not in existing:
        return  # 本件未建过任何表（或 bookkeeping 已失）——⛔ 不碰存量表
    created = {
        row[0]  # BATCH-001-FIX-001：照同族 0005/0006 先例 row[0]（SA 2.1 Row 不支持字符串下标）
        for row in bind.execute(sa.text(f"SELECT name FROM {BOOKKEEP}"))
    }
    targets = [t for t in Base.metadata.sorted_tables
               if t.name in created and t.name in existing]
    if targets:
        Base.metadata.drop_all(bind=bind, tables=targets)
    op.drop_table(BOOKKEEP)
