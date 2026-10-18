"""0010 site agent grant + call ledger（L1SI147-CHANNEL-B1-003：批 3 交易接线）

批 3 范围：execute 正空间执行＋授权件机验（四要件）＋计量落账（聚合窗口）：
- site_agent_grant 授权件表：照令七字段（grant_no/reg_no/scene_constraint/legal_signer/
  signature_ref/parent_grant_no/status）＋detail（四要件机验明细 JSON，R2 五阶清单／
  R3 全构成声明／逐条判值——机验可复核载体）＋存证回链；⛔ 不动草案 auth_grants；
- site_agent_call_ledger 计量表：聚合窗口内同（登记号,端点,窗口）一行累计 units，
  ⛔ 不高频直写致锁；units 数值按方案标模拟（SIMULATED 水印），行 provenance=mixed
  （落账事实真＋计量数值模拟）；
- 写法照 0008／0009（op.create_table ＋ 检查约束；全新表；含 downgrade）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'f7a8b9c0d1e2'
down_revision = 'e6f7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_grant',
        sa.Column('grant_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('scene_constraint', sa.Text(), nullable=False),  # R1 场景（未列明场景不在授权范围）
        sa.Column('legal_signer', sa.Text(), nullable=False),      # R4 法律主体签名者（⛔ 智能体不代签）
        sa.Column('signature_ref', sa.Text(), nullable=False),     # R4 签名事件引用（落 NCA）
        sa.Column('parent_grant_no', sa.Text(), nullable=True),    # 转授上层件号（可空）
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('detail', sa.Text(), nullable=True),   # 四要件机验明细（R2 五阶清单/R3 全构成/逐条判值）
        sa.Column('nca_ref', sa.Text(), nullable=True),  # 登记存证回链
        sa.Column('actor', sa.Text(), nullable=True),    # 操作人类账户
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.ForeignKeyConstraint(['parent_grant_no'], ['site_agent_grant.grant_no']),
        sa.PrimaryKeyConstraint('grant_no'),
        sa.CheckConstraint("status IN ('active','revoked')", name='ck_site_agent_grant_status'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_grant_prov'),
    )
    op.create_table(
        'site_agent_call_ledger',
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),  # execute 等正空间端点名
        sa.Column('units', sa.Integer(), nullable=False, server_default='0'),  # 窗口累计（数值模拟）
        sa.Column('nca_anchor', sa.Text(), nullable=True),  # 本窗口最近存证锚
        sa.Column('ts', sa.Text(), nullable=False),         # 聚合窗口起点（ISO 分钟截断）
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='mixed'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('reg_no', 'endpoint', 'ts'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_ledger_prov'),
    )


def downgrade() -> None:
    op.drop_table('site_agent_call_ledger')
    op.drop_table('site_agent_grant')
