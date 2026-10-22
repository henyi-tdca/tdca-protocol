"""0016 site agent utility deposit 对外补齐 C（效用保金）

- 新表 site_agent_utility_deposit：效用保金四态事件账（押付 paid／冻结 frozen／
  没收 confiscated／退还 refunded，SUD- 前缀逐笔落行）；
- 有效保金＝Σpaid−Σconfiscated−Σrefunded（冻结单列记账、不减有效额）；
- 没收去向记 pool（保险金池）；action 状态闭集 CHECK 建表期落约束；
- reg_no 外键回链 site_agent_registry；按 reg_no 建普通索引供准入闸查询。
含 downgrade（drop_table 回溯）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'e8f9a0b1c2d3'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_utility_deposit',
        sa.Column('event_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('amount_mou', sa.Integer(), nullable=False),
        sa.Column('mou_ref', sa.Text(), nullable=True),
        sa.Column('pool', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('actor', sa.Text(), nullable=False),
        sa.Column('nca_ref', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("action IN ('paid','frozen','confiscated','refunded')",
                           name='ck_site_agent_utility_deposit_action'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_utility_deposit_prov'),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no'], ),
        sa.PrimaryKeyConstraint('event_no'),
    )
    op.create_index('idx_site_agent_utility_deposit_reg', 'site_agent_utility_deposit',
                    ['reg_no'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_site_agent_utility_deposit_reg', table_name='site_agent_utility_deposit')
    op.drop_table('site_agent_utility_deposit')
