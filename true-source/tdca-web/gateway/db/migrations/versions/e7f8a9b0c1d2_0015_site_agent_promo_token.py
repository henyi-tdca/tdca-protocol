"""0015 site agent promo token 对外补齐 B（转正令牌）

- 新表 site_agent_promo_token：转正令牌（与身份凭据族物理分离——独立表／独立 SPT- 前缀）；
- 只存 sha256 指纹；四要件（人／时／物／意）四列＋签发到旋转到吊销三时点；
- 状态闭集 active／revoked（模型层 CHECK，建表期落约束）；
- 指纹非唯一（轮换史保留），建普通索引供验伪端查询。
含 downgrade（drop_table 回溯）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'e7f8a9b0c1d2'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_promo_token',
        sa.Column('token_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('token_fingerprint', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('approver', sa.Text(), nullable=False),
        sa.Column('approved_at', sa.Text(), nullable=False),
        sa.Column('sandbox_approval_ref', sa.Text(), nullable=False),
        sa.Column('approval_intent', sa.Text(), nullable=False),
        sa.Column('issued_at', sa.Text(), nullable=False),
        sa.Column('rotated_at', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.Text(), nullable=True),
        sa.Column('issuer_session', sa.Text(), nullable=True),
        sa.Column('nca_ref', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('active','revoked')",
                           name='ck_site_agent_promo_token_status'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_promo_token_prov'),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no'], ),
        sa.PrimaryKeyConstraint('token_no'),
    )
    op.create_index('idx_site_agent_promo_token_fp', 'site_agent_promo_token',
                    ['token_fingerprint'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_site_agent_promo_token_fp', table_name='site_agent_promo_token')
    op.drop_table('site_agent_promo_token')
