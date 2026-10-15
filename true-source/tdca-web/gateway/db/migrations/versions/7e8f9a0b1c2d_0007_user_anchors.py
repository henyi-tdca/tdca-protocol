"""0007 user anchors（L1SI145-ANCHOR-B2-001：注册选锚落存证＋人工受理核验）

新增 user_anchors 表持久化身份锚选择：
- 锚段只收引用（anchor_kind 枚举引用＋evidence_ref 引用），⛔ 不落实名/手机号明文；
- 未选锚者注册时照常建一行（anchor_kind NULL，anchor_tier='记名级'，tier_state='待补'）；
- tier_state『待补|已补』——核验受理后置『已补』（人工受理，⛔ 不引外部服务）；
- 写法照 0004（op.create_table ＋ 检查约束；本表为全新表，无存量兼容问题）。
"""
from alembic import op
import sqlalchemy as sa


revision = '7e8f9a0b1c2d'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_anchors',
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('anchor_kind', sa.Text(), nullable=True),   # NULL=注册时未选
        sa.Column('anchor_tier', sa.Text(), nullable=False, server_default='记名级'),
        sa.Column('tier_state', sa.Text(), nullable=False, server_default='待补'),
        sa.Column('real_name_present', sa.Integer(), nullable=True),   # 核验后：1/0；未核=NULL
        sa.Column('phone_present', sa.Integer(), nullable=True),       # 同上（手机号非必填，可为 0）
        sa.Column('evidence_ref', sa.Text(), nullable=True),           # 证据引用编号（⛔ 非明文取值）
        sa.Column('verified_at', sa.Text(), nullable=True),
        sa.Column('verifier', sa.Text(), nullable=True),               # 受理人账号
        sa.Column('nca_ref', sa.Text(), nullable=True),                # 最近锚段存证回链
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['username'], ['users.username']),
        sa.PrimaryKeyConstraint('username'),
        sa.CheckConstraint("anchor_kind IN ('notifier','realname-phone')",
                           name='ck_user_anchors_kind'),
        sa.CheckConstraint("anchor_tier IN ('固锚级','移锚级','记名级','未达门槛','未定档')",
                           name='ck_user_anchors_tier'),
        sa.CheckConstraint("tier_state IN ('待补','已补')", name='ck_user_anchors_state'),
        sa.CheckConstraint('real_name_present IN (0,1)', name='ck_user_anchors_rn'),
        sa.CheckConstraint('phone_present IN (0,1)', name='ck_user_anchors_ph'),
    )


def downgrade() -> None:
    op.drop_table('user_anchors')
