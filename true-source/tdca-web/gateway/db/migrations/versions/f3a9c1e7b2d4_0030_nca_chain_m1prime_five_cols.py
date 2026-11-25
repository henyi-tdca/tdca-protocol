"""0030 nca_chain M1″ 五列补录（K1FIX-R1 裁定二／K-9：fresh-install 断链修复）

- 背景：迁移链 0001→0029 不 reproduces 生产 nca_chain 全列——rec_hash／prev_hash／
  anchor_ok／detached／detach_reason 五列系生产带外补齐（-591 回报附带发现），
  全新迁移库跑不了 _nca_append（api_v1），fresh-install 即核心链路断链；
- 本迁移：五列照生产现物镜像（PRAGMA 实取）：rec_hash TEXT 可空／prev_hash TEXT 可空／
  anchor_ok INTEGER NOT NULL DEFAULT 0／detached INTEGER NOT NULL DEFAULT 0／
  detach_reason TEXT 可空；生产无新增索引（仅既有 idx_nca_prev），故不建索引；
- 判存在则跳（每列独立判，幂等可重入）；
- 含 downgrade（五列同撤）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'f3a9c1e7b2d4'
down_revision = '9460a3123168'
branch_labels = None
depends_on = None

TABLE = 'nca_chain'

COLS = (
    ('rec_hash', sa.Column('rec_hash', sa.Text(), nullable=True)),
    ('prev_hash', sa.Column('prev_hash', sa.Text(), nullable=True)),
    ('anchor_ok', sa.Column('anchor_ok', sa.Integer(), nullable=False, server_default='0')),
    ('detached', sa.Column('detached', sa.Integer(), nullable=False, server_default='0')),
    ('detach_reason', sa.Column('detach_reason', sa.Text(), nullable=True)),
)


def _existing() -> set:
    bind = op.get_bind()
    return {r['name'] for r in sa.inspect(bind).get_columns(TABLE)}


def upgrade() -> None:
    have = _existing()
    for name, col in COLS:
        if name not in have:
            op.add_column(TABLE, col)


def downgrade() -> None:
    with op.batch_alter_table(TABLE) as bop:
        for name, _ in reversed(COLS):
            bop.drop_column(name)
