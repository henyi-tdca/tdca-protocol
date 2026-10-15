"""0009 site agent admission 闸步表（L1SI147-CHANNEL-B1-002：批 2 通道本体）

六步硬序之状态机落点（①protocol-load／③ns-review／④sandbox 批 2 接真；⑤execute 批 3）：
- 每（登记号, 步）至多一行，状态闭集 passed／failed／pending（fail-closed：非 passed 即未达）；
- 负空间审查未过／沙盒未过如实记 failed（⛔ 不得正空间执行／拒绝入网）；
- ②token 步状态由凭据表（active 指纹）派生，⛔ 不在本表落行（单一事实源）；
- 写法照 0007／0008（op.create_table ＋ 检查约束；全新表）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'e6f7a8b9c0d1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_admission',
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('step', sa.Text(), nullable=False),      # protocol-load|ns-review|sandbox|execute
        sa.Column('state', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('result_ref', sa.Text(), nullable=True),  # 结果引用（哈希/运行号，⛔ 非凭据值）
        sa.Column('detail', sa.Text(), nullable=True),      # 要件绑定/申报摘要（JSON 文本）
        sa.Column('nca_ref', sa.Text(), nullable=True),     # 本步存证回链
        sa.Column('actor', sa.Text(), nullable=True),       # 操作人类账户
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('reg_no', 'step'),
        sa.CheckConstraint("step IN ('protocol-load','ns-review','sandbox','execute')",
                           name='ck_site_agent_admission_step'),
        sa.CheckConstraint("state IN ('passed','failed','pending')",
                           name='ck_site_agent_admission_state'),
    )


def downgrade() -> None:
    op.drop_table('site_agent_admission')
