"""0011 site agent punish statemachine（T-037：任务 A 判级档＋任务 B 恢复径＋任务 C 超期升档）

IMPL-002（L1SI147-CHANNEL-T037-IMPL-002）：依已核证设计要件落码，全部增量新表：
- site_agent_classification 判级事件表：引擎只写事件＋存证，⛔ 永不写 status；
- site_agent_remediation 恢复径周期表：重塑／重新验证独立记录（⛔ 不并步），⛔ 无 TTL 字段；
- site_agent_permanent 永久终态标记表：写口仅定时扫掠、只许写永久（⛔ 不动 registry.status 闭集）；
写法照 0008-0010（op.create_table ＋ 检查约束；全新表；含 downgrade）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_classification',
        sa.Column('event_id', sa.Text(), nullable=False),      # PRS-＋12 位十六进制
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('signal_source', sa.Text(), nullable=False),  # 档位由服务端依三空间分档导出
        sa.Column('signal_ref', sa.Text(), nullable=False),     # 信号锚（可核）
        sa.Column('band', sa.Text(), nullable=False),           # 轻度|中度|严重|法律级
        sa.Column('band_basis', sa.Text(), nullable=False),     # 分档依据（在册口径引用位）
        sa.Column('ruling_state', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('ruling_ref', sa.Text(), nullable=True),      # 裁决回链
        sa.Column('nca_ref', sa.Text(), nullable=True),         # 判级存证回链
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('event_id'),
        sa.CheckConstraint("signal_source IN ('sensor_warning','sensor_cryogenic','sensor_blocked','legal_matrix')",
                           name='ck_site_agent_classification_source'),
        sa.CheckConstraint("band IN ('轻度','中度','严重','法律级')",
                           name='ck_site_agent_classification_band'),
        sa.CheckConstraint("ruling_state IN ('pending','ruled','dismissed')",
                           name='ck_site_agent_classification_ruling'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_classification_prov'),
    )
    op.create_table(
        'site_agent_remediation',
        sa.Column('cycle_no', sa.Text(), nullable=False),       # REM-＋12 位十六进制
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('cycle_seq', sa.Integer(), nullable=False),   # 主体内周期序（自 1 递增）
        sa.Column('remediated_at', sa.Text(), nullable=True),   # 重塑时点（同周期可续重塑）
        sa.Column('remediate_nca_ref', sa.Text(), nullable=True),
        sa.Column('reverify_at', sa.Text(), nullable=True),     # 重新验证时点（独立记录，⛔ 不并步）
        sa.Column('reverify_result', sa.Text(), nullable=True),  # passed|failed
        sa.Column('reverify_nca_ref', sa.Text(), nullable=True),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('cycle_no'),
        sa.CheckConstraint("reverify_result IN ('passed','failed')",
                           name='ck_site_agent_remediation_rev'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_remediation_prov'),
    )
    op.create_table(
        'site_agent_permanent',
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('source', sa.Text(), nullable=False, server_default='sweep_upgrade'),
        sa.Column('nca_ref', sa.Text(), nullable=True),         # 升档存证回链（独立存证类型）
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('reg_no'),
        sa.CheckConstraint("source IN ('sweep_upgrade')", name='ck_site_agent_permanent_source'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_permanent_prov'),
    )


def downgrade() -> None:
    op.drop_table('site_agent_permanent')
    op.drop_table('site_agent_remediation')
    op.drop_table('site_agent_classification')
