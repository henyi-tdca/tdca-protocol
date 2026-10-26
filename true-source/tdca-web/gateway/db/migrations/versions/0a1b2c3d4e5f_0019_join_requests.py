"""0019 缔约申请评审队列表（批3「门与闸」A块，TDCA-HANDOFF-EXEC-L1SI176-B3-GATE-001）

- join/list（评审只读队列）＋ join/review（审核写）之数据落点；
- status 五态照前端冻结契约：pending／sandbox／active／rejected／nsfl_rejected；
- ⛔ 本表不含凭据值；display_name 为面客展示名（自然人敏感信息不入库）；
- 写法照 0009／0016（op.create_table ＋ 检查约束；全新表）。
"""
from alembic import op
import sqlalchemy as sa


revision = '0a1b2c3d4e5f'
down_revision = '6a7b8c9d0e1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'join_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.Text(), nullable=False),      # 面客展示名（⛔ 自然人敏感信息）
        sa.Column('applicant_kind', sa.Text(), nullable=False),    # 申请主体类别
        sa.Column('channel', sa.Text(), nullable=False),           # 缔约通道
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('nsfl_result', sa.Text(), nullable=False, server_default=''),  # 负空间复核结论
        sa.Column('reviewer_note', sa.Text(), nullable=True),      # 审核备注（留痕）
        sa.Column('nca_ref', sa.Text(), nullable=True),            # 审核存证回链
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending','sandbox','active','rejected','nsfl_rejected')",
                           name='ck_join_requests_status'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_join_requests_prov'),
    )


def downgrade() -> None:
    op.drop_table('join_requests')
