"""0029 subject_bindings（K1FIX-001 任务1：主体绑定表）

- 五列照 GSEQ-9102 §三之二：subject_username／role（本批值域 registrant|grantee，
  signer 行第二批）／object_ref（授权件号等）／ref_value（机器锚：reg:<登记号>|
  tok:<主体标识>，承 AMEND-1 二之二，⛔自由文本）／binding_state（active|revoked）；
- 唯一索引 (subject_username, role, object_ref, ref_value) 防重复绑定；
- 建行路径仅服务端（登记成功建 registrant 行／授权件生效建 grantee 行），
  ⛔被授权方自建自改（无对外端点）；
- 含 downgrade。
"""
from alembic import op
import sqlalchemy as sa


revision = '9460a3123168'
down_revision = 'd331c36716b4'
branch_labels = None
depends_on = None

TABLE = 'subject_bindings'


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table(TABLE):
        return
    op.create_table(
        TABLE,
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('subject_username', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('object_ref', sa.Text(), nullable=False),
        sa.Column('ref_value', sa.Text(), nullable=False),
        sa.Column('binding_state', sa.Text(), nullable=False, server_default='active'),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.UniqueConstraint('subject_username', 'role', 'object_ref', 'ref_value',
                            name='uq_subject_bindings'),
        sa.CheckConstraint("role IN ('registrant','grantee')", name='ck_sb_role'),
        sa.CheckConstraint("binding_state IN ('active','revoked')", name='ck_sb_state'),
        sa.CheckConstraint("data_provenance IN ('simulated','real')", name='ck_sb_prov'),
        sa.CheckConstraint("ref_value LIKE 'reg:%' OR ref_value LIKE 'tok:%'",
                           name='ck_sb_anchor_format'),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table(TABLE):
        op.drop_table(TABLE)
