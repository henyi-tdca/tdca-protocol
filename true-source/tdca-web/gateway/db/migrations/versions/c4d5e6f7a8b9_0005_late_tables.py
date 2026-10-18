"""0005_late_tables

补 14 张新表之迁移（workflow_defs 等，逐表见 LATE_TABLES）。
口径（照 8c 方案 + 施工件）：
- 单个迁移接 0004 之链，不改 0001~0004 一字；
- 以 inspect 条件建表（缺者建、存者跳）保幂等；
- 表结构以 db/models.py 现定义为唯一准绳（H-5：不代定表结构语义）；
- tool_items 条件补 nca_ref 列（PR #91 所增列）；
- downgrade 只删「本件实际所建」之表：upgrade 将实建表名录入 bookkeeping 表
  （_mig0005_late_tables），downgrade 照册精确摘除并自清——
  由此区分「本件所建新表」与「存量库自建表」（如运行期库经 create_all 所建），
  存量表在 downgrade 中一律保留，只摘回本件所补之列；
- bookkeeping 表由本迁移自管自建自清，降级后无残留。
"""

from alembic import op
import sqlalchemy as sa

from db.models import Base  # noqa: F401  (import registers all tables)

revision = "c4d5e6f7a8b9"
down_revision = "9d3f6a28c4b1"
branch_labels = None
depends_on = None

# 14 张新表（与 models.py __tablename__ 逐一对账；0001~0004 未覆盖者）
LATE_TABLES = [
    "workflow_defs",
    "workflow_runs",
    "signature_requests",
    "auth_grants",
    "lineage_entries",
    "formal_conclusions",
    "tool_items",
    "ci_runs",
    "copyright_events",
    "ownership_records",
    "market_sim_runs",
    "ops_tickets",
    "announcements",
    "authorization_records",
]

# 自建自清之 bookkeeping 表名（记录本件实际所建表，供 downgrade 精确摘除）
BOOKKEEP = "_mig0005_late_tables"


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    # 条件建表：缺者建、存者跳（checkfirst 双保险，幂等）
    to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name in LATE_TABLES and t.name not in existing
    ]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)
        # 录入实建表名（downgrade 凭此册精确摘除，区分存量自建表）
        bk = op.create_table(
            BOOKKEEP,
            sa.Column("name", sa.Text, primary_key=True),
        )
        op.bulk_insert(bk, [{"name": t.name} for t in to_create])

    # tool_items 条件补 nca_ref 列（存量库可能已有表但缺列；
    # 补列为裸 Text 不带 FK——SQLite ALTER 限制，且新库全建路径已带 FK，故不重复约束）
    insp2 = sa.inspect(bind)
    if "tool_items" in set(insp2.get_table_names()):
        cols = {c["name"] for c in insp2.get_columns("tool_items")}
        if "nca_ref" not in cols:
            op.add_column(
                "tool_items",
                sa.Column("nca_ref", sa.Text, nullable=True),
            )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    # 读本件实建表名录（无存则本件未建任何表，即纯存量库场景）
    created = set()
    if BOOKKEEP in existing:
        created = {
            row[0]
            for row in bind.execute(sa.text(f"SELECT name FROM {BOOKKEEP}"))
        }

    # 逆依赖序 drop 本件所建表（只删记录在册且现存者；
    # 存量自建表不在册，一律保留；0001~0004 的表更不触碰）
    present = [
        t for t in reversed(Base.metadata.sorted_tables)
        if t.name in created and t.name in existing
    ]
    for tbl in present:
        tbl.drop(bind=bind, checkfirst=True)

    # bookkeeping 表自清（降级后无残留）
    if BOOKKEEP in existing:
        op.drop_table(BOOKKEEP)

    # 存量 tool_items（非本件所建）摘回本件 upgrade 所补之列。
    # 该列系裸 Text（无 FK），SQLite 可直接 drop；
    # 若 tool_items 系本件所建，已随上步整体 drop，不会走到本分支。
    if "tool_items" in existing and "tool_items" not in created:
        cols = {c["name"] for c in insp.get_columns("tool_items")}
        if "nca_ref" in cols:
            op.drop_column("tool_items", "nca_ref")
