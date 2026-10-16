"""0012 lib docs scope（LIB-DOCS-SCOPE-001 IMPL-004 任务 E＋归族落地）

- 公告栏 announcements 加 category 列（闭集四值拟名：通知／信息公开／动态周报／资讯；
  模型侧 CHECK 约束；SQLite ALTER 加列只许常量缺省——存量 1 行随缺省回填「通知」，
  恰为裁定赋值（⛔ 只动该行，无其它行）；分类名本侧拟名待签批）；
- docs 表归族 4 件（裁定 IMPL-004 §二）：IDENTITY-WORKBUDDY／REGISTER-CONTRACT-001 中英／README-7
  family→help（TERMS 按实质＝规则，仍在 regulation 不动；NSFL-COLLAB-NOTICE 按实质＝常设须知，
  仍在 regulation 不动——判定依据随回报）；⛔ 不造数据、不碰其它行。
含 downgrade（可回溯）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

# 归族清单（裁定）：此 4 件自 regulation 移 help
_REHOME = (
    'IDENTITY-WORKBUDDY',
    'TDCA-REGISTER-CONTRACT-001-en',
    'TDCA-REGISTER-CONTRACT-001-zh',
    'README-7',
)


def upgrade() -> None:
    # E：category 列（NOT NULL＋常量缺省「通知」；SQLite ADD COLUMN 之唯一合法形式，
    # 存量行随缺省回填＝裁定之「存量 1 行赋通知」）
    op.add_column('announcements',
                  sa.Column('category', sa.Text(), nullable=False, server_default='通知'))
    # 归族：4 件 regulation→help（逐件点名，幂等）
    for slug in _REHOME:
        op.execute(f"UPDATE docs SET family='help' WHERE slug='{slug}' AND family='regulation'")


def downgrade() -> None:
    # 归族回溯：4 件回 regulation（原值在册：5 件边界件本皆 regulation 族）
    for slug in _REHOME:
        op.execute(f"UPDATE docs SET family='regulation' WHERE slug='{slug}' AND family='help'")
    op.drop_column('announcements', 'category')
