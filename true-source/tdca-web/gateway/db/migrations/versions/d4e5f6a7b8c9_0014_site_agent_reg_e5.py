"""0014 site agent registry 块 E（L1SI167-AGENT-REG-UI-001：自助登记入口）

- site_agent_registry 加列：channel_type（ANCHOR／GUEST，存量回填 ANCHOR）＋
  创世六要素逐项六列（设备／算力／协议／角色／知识／权限时效，第8条第1款原文）＋
  锚定项两列（锚定之人类账户／根令牌引用，第8条第2款，单列不计入六要素）＋
  participants（资产配置参与方，JSON 文本，第8条第3款）＋
  source_lineage（来源谱系，第10条派生登记必填）＋
  agent_card／ext_declaration／ext_contact（GUEST 路，条例第9条；⛔ 不上公开面）＋
  idem_key（幂等键 sha256_16，唯一索引；NULL 允许多行——存量行不回填）；
- SQLite ALTER ADD COLUMN 只许常量缺省：文本列缺省 ''（可空列不带缺省）；
- 存量行六要素逐项列留空串、channel_type 回填 'ANCHOR'（当时只有原生路，如实）；
- channel_type 取值约束在模型层 CHECK（SQLite 建表期），迁移只加列不重建表。
含 downgrade（可回溯：删列以重建表式回退——0014 仅新列，重命名互换后拷回）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_agent_registry',
                  sa.Column('channel_type', sa.Text(), nullable=False, server_default='ANCHOR'))
    op.add_column('site_agent_registry',
                  sa.Column('six_device', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('six_compute', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('six_protocol', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('six_role', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('six_knowledge', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('six_permission_ttl', sa.Text(), nullable=False, server_default=''))
    op.add_column('site_agent_registry',
                  sa.Column('anchor_account', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('root_token_ref', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('participants', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('site_agent_registry',
                  sa.Column('source_lineage', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('agent_card', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('ext_declaration', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('ext_contact', sa.Text(), nullable=True))
    op.add_column('site_agent_registry',
                  sa.Column('idem_key', sa.Text(), nullable=True))
    # 幂等键唯一（NULL 可多行；同键再提交＝复用原登记号，⛔ 重复建档）
    op.create_index('uq_site_agent_registry_idem_key', 'site_agent_registry',
                    ['idem_key'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_site_agent_registry_idem_key', table_name='site_agent_registry')
    for col in ('idem_key', 'ext_contact', 'ext_declaration', 'agent_card',
                'source_lineage', 'participants', 'root_token_ref', 'anchor_account',
                'six_permission_ttl', 'six_knowledge', 'six_role', 'six_protocol',
                'six_compute', 'six_device', 'channel_type'):
        op.drop_column('site_agent_registry', col)
