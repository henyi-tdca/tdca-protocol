"""0028 docs_in_chain（K1FIX-001 外部决断2 采行·docs 表正式入迁移链）

- docs 表（8 列，镜像在役生产库 sqlite_master 之现物定义）判存在则跳——
  生产库已有且有 60 件数据，照 0012/0022/0025 同法「缺者补」；
- fresh 路径由此补全（此前带外建表，换机即崩——0012 判表存在防护之同源缺口）；
- 含 downgrade（drop_table，照重建表模式先例）。
承 TDCA-HANDOFF-EXEC-L1SI229-K1FIX-001 §四 附条件三条。
"""
from alembic import op
import sqlalchemy as sa


revision = 'd331c36716b4'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

TABLE = 'docs'


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table(TABLE):
        return
    op.create_table(
        TABLE,
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('family', sa.Text(), nullable=False),
        sa.Column('slug', sa.Text(), nullable=False, unique=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('body_md', sa.Text(), nullable=False),
        sa.Column('source_path', sa.Text(), nullable=False),
        sa.Column('data_nature', sa.Text(), nullable=False, server_default='simulated'),
        sa.Column('synced_at', sa.Text(), nullable=False,
                  server_default=sa.text("datetime('now')")),
        sa.CheckConstraint("data_nature IN ('simulated','real')", name='ck_docs_prov'),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table(TABLE):
        op.drop_table(TABLE)
