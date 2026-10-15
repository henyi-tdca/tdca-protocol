"""0008 site agent channel 批1（L1SI147-CHANNEL-B1-001：身份与登记面）

站点通道族两表（物理同库·逻辑分线；命名族 site_agent_*）：
- site_agent_registry：智能体登记（登记即创建、未登记即未创建；主体与执行体二分，
  owner_username 为主体列；智能体侧标识＝登记号 reg_no，⛔ 不叫 TDID、不自造编号体例）；
- site_agent_credential：智能体凭据族（⛔ 只存不可逆指纹，值不入库；人类会话内签发）。
写法照 0007（op.create_table ＋ 检查约束；全新表，无存量兼容问题）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d0'
down_revision = '7e8f9a0b1c2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_registry',
        sa.Column('reg_no', sa.Text(), nullable=False),        # 登记号（智能体侧唯一标识）
        sa.Column('owner_username', sa.Text(), nullable=False),  # 主体（人类账户，⛔ 执行体无财产）
        sa.Column('six_elements_ref', sa.Text(), nullable=False),  # 创世六要素引用
        sa.Column('anchor_ref', sa.Text(), nullable=True),      # 锚定项引用（user_anchors 锚段）
        sa.Column('tier', sa.Text(), nullable=False, server_default='basic'),  # 等第（取值域后续批次裁定）
        sa.Column('status', sa.Text(), nullable=False, server_default='正常'),  # 正常＋惩罚三态
        sa.Column('nca_ref', sa.Text(), nullable=True),          # 登记存证回链
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['owner_username'], ['users.username']),
        sa.PrimaryKeyConstraint('reg_no'),
        sa.CheckConstraint("status IN ('正常','冻结','降权','吊销')",
                           name='ck_site_agent_registry_status'),
    )
    op.create_table(
        'site_agent_credential',
        sa.Column('cred_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('cred_fingerprint', sa.Text(), nullable=False),  # sha256 不可逆指纹（⛔ 值不入库）
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('issued_at', sa.Text(), nullable=False),
        sa.Column('rotated_at', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.Text(), nullable=True),
        sa.Column('issuer_session', sa.Text(), nullable=True),   # 签发人类会话指纹（⛔ 非会话值本身）
        sa.Column('nca_ref', sa.Text(), nullable=True),          # 签发存证回链
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no']),
        sa.PrimaryKeyConstraint('cred_no'),
        sa.CheckConstraint("status IN ('active','revoked')", name='ck_site_agent_credential_status'),
    )


def downgrade() -> None:
    op.drop_table('site_agent_credential')
    op.drop_table('site_agent_registry')
