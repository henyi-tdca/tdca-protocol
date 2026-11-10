"""0018 site me nca attestation3（SMALL2-001 块 B：存证举证三字段）

- nca_chain 增三列（皆 Text nullable，⛔ 不改既有四字段）：
  subject_ref    主体（本钥标识之脱敏形 = sha256(actor)[:12]，不可逆、⛔ 返全值）
  authz_ref      授权依据（授权件编号，⛔ 返授权正文）
  compare_result 比对结论（值域封闭三值；CHECK 约束锁死，写端另加校验双保险）
- 不回填：历史行三列全 NULL，页面照旧标「本期无」（无可靠数据源，⛔ 造值）。
含 downgrade（批模式回滚：先删约束后删三列；SQLite 方言 constraint 变更须 batch）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'a0b1c2d3e4f5'
down_revision = 'f9a0b1c2d3e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('nca_chain', sa.Column('subject_ref', sa.Text(), nullable=True))
    op.add_column('nca_chain', sa.Column('authz_ref', sa.Text(), nullable=True))
    op.add_column('nca_chain', sa.Column('compare_result', sa.Text(), nullable=True))
    with op.batch_alter_table('nca_chain') as bop:
        bop.create_check_constraint(
            'ck_nca_chain_compare_result',
            "compare_result IN ('match','mismatch','not_compared')",
        )


def downgrade() -> None:
    with op.batch_alter_table('nca_chain') as bop:
        bop.drop_constraint('ck_nca_chain_compare_result', type_='check')
    op.drop_column('nca_chain', 'compare_result')
    op.drop_column('nca_chain', 'authz_ref')
    op.drop_column('nca_chain', 'subject_ref')
