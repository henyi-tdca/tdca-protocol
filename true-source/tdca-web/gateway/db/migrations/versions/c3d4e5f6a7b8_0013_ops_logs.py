"""0013 ops logs（L1SI150-OPS-STORAGE-P2-001 乙案：运维日志表单化）

- 新建 ops_logs 表（六组 sections JSON 原键入库；log_date+duty_no 复合主键＝一人一日一行；
  索引 filled_at/duty_no；data_provenance CHECK 照 ID92 体例）；
- ⛔ 不动既有表结构；⛔ 不建 ops_files 表（防双源漂移，令 §一收窄）。
含 downgrade（可回溯）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ops_logs',
        sa.Column('log_date', sa.Text(), nullable=False),   # +08 自然日 YYYY-MM-DD
        sa.Column('duty_no', sa.Text(), nullable=False),    # 工号（⛔ 姓名）
        sa.Column('duty_role', sa.Text(), nullable=False),
        sa.Column('handover', sa.Text(), nullable=False),
        sa.Column('sections', sa.Text(), nullable=False),   # JSON：A~F 六组（键名照 TPL-OPS-LOG-001-MACHINE）
        sa.Column('exceptions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unclosed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('backfill', sa.Text(), nullable=False, server_default='false'),
        sa.Column('backfill_reason', sa.Text(), nullable=True),
        sa.Column('filled_by', sa.Text(), nullable=False),
        sa.Column('filled_at', sa.Text(), nullable=False),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.PrimaryKeyConstraint('log_date', 'duty_no', name='pk_ops_logs'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_ops_logs_prov'),
    )
    op.create_index('idx_ops_logs_filled_at', 'ops_logs', ['filled_at'])
    op.create_index('idx_ops_logs_duty_no', 'ops_logs', ['duty_no'])


def downgrade() -> None:
    op.drop_index('idx_ops_logs_duty_no', table_name='ops_logs')
    op.drop_index('idx_ops_logs_filled_at', table_name='ops_logs')
    op.drop_table('ops_logs')
