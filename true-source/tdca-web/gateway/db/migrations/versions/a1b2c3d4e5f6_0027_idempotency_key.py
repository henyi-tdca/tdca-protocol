"""0027 idempotency key 幂等键表（WIDEMPOT-BUILD-001·照准 GSEQ-9091/9093）

- 新表 idempotency_key：九字段（subject／endpoint／key／status／http_code／
  resp_digest／resp_body_ref／nca_seq／created_at）；
- 唯一索引 (subject, endpoint, key)（复合主键同域兜底；status 三态 CHECK）；
- ⛔ 不改既有表（只新增表）；重复请求⛔再落 NCA 链节（键表只存 nca_seq 锚）。
含 downgrade（drop_table 回溯）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'f0a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'idempotency_key',
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('http_code', sa.Integer(), nullable=True),
        sa.Column('resp_digest', sa.Text(), nullable=True),
        sa.Column('resp_body_ref', sa.Text(), nullable=True),
        sa.Column('nca_seq', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('pending','done','failed')",
                           name='ck_idempotency_key_status'),
        sa.PrimaryKeyConstraint('subject', 'endpoint', 'key'),
    )
    op.create_index('uq_idempotency_key_scope', 'idempotency_key',
                    ['subject', 'endpoint', 'key'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_idempotency_key_scope', table_name='idempotency_key')
    op.drop_table('idempotency_key')
