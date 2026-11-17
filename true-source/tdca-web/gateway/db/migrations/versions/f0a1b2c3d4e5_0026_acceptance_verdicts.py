"""0026_acceptance_verdicts（L1SI218-ACCTABLE-001 乙路：验收结论另建表，账不动）

- 新表 acceptance_verdicts：两栏合表（公示 4 字段＋私域 5 字段），CHECK 闭集 fail-closed；
- 两个视图分隔两栏（硬规：⛔前端隐藏代隔离）：
    acceptance_verdicts_public  ── 只含公示四字段（verdict/decided_at/subject_ref/evidence_nca_id）
    acceptance_verdicts_ops     ── 全列（仅运维面用）
- 只加不删：upgrade 建表＋建视图（inspect 幂等）；downgrade 逆序删视图＋删表；
- evidence_nca_id 为 nca_chain 外链（⛔复制台账内容⛔双写），首批数据空表为常态
  （台账无验收结论字段可派生——-414 S-AC1 已报），登记走「谁判谁登」登记口。
"""
from alembic import op
import sqlalchemy as sa


revision = 'f0a1b2c3d4e5'
down_revision = 'e5f6a7b8c9d1'
branch_labels = None
depends_on = None

TABLE = 'acceptance_verdicts'

PUBLIC_VIEW = 'acceptance_verdicts_public'
OPS_VIEW = 'acceptance_verdicts_ops'

PUBLIC_COLS = ('verdict', 'decided_at', 'subject_ref', 'evidence_nca_id')

CREATE_TABLE = sa.Table(
    TABLE, sa.MetaData(),
    sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column('verdict', sa.Text(), nullable=False),
    sa.Column('decided_at', sa.Text(), nullable=False),
    sa.Column('subject_type', sa.Text(), nullable=False),
    sa.Column('subject_ref', sa.Text(), nullable=False),
    sa.Column('evidence_nca_id', sa.Text(), nullable=False),
    sa.Column('ops_process', sa.Text(), nullable=True),
    sa.Column('ops_actions', sa.Text(), nullable=True),
    sa.Column('ops_trace', sa.Text(), nullable=True),
    sa.Column('credential_ref', sa.Text(), nullable=True),
    sa.Column('internal_ref', sa.Text(), nullable=True),
    sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
    sa.Column('created_at', sa.Text(), nullable=False),
    sa.CheckConstraint("verdict IN ('passed','conditional','failed')", name='ck_acc_verdict'),
    sa.CheckConstraint("subject_type IN ('institution_effective','doc_ingest',"
                       "'site_function','batch_construction','agent_network')",
                       name='ck_acc_subject_type'),
    sa.Index('idx_acceptance_verdicts_subject', 'subject_type', 'subject_ref'),
    sa.Index('idx_acceptance_verdicts_nca', 'evidence_nca_id'),
)


def _tables(bind) -> set:
    return set(sa.inspect(bind).get_table_names())


def _views(bind) -> set:
    insp = sa.inspect(bind)
    try:
        return {v['name'] for v in insp.get_view_names()}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    if TABLE not in _tables(bind):
        CREATE_TABLE.create(bind, checkfirst=True)
    views = _views(bind)
    if PUBLIC_VIEW not in views:
        cols = ', '.join(PUBLIC_COLS)
        op.execute(f'CREATE VIEW {PUBLIC_VIEW} AS SELECT {cols} FROM {TABLE}')
    if OPS_VIEW not in views:
        op.execute(f'CREATE VIEW {OPS_VIEW} AS SELECT * FROM {TABLE}')


def downgrade() -> None:
    bind = op.get_bind()
    views = _views(bind)
    for v in (OPS_VIEW, PUBLIC_VIEW):
        if v in views:
            op.execute(f'DROP VIEW IF EXISTS {v}')
    if TABLE in _tables(bind):
        op.drop_table(TABLE)
