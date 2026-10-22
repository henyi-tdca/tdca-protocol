"""0017 site agent insurance policy/claim 对外补齐 D（履约保证保险）

- 新表 site_agent_insurance_policy：履约保证保险保单（SIP- 前缀；承保方/保额 MOU/
  保障期起止/status 闭集 active|expired|revoked；reg_no 外键回链登记册）；
- 新表 site_agent_insurance_claim：漏洞损失申报留痕（SIC- 前缀；loss_type 闭集
  制度漏洞|技术漏洞；status 闭集 INSURED——触发态口径照在册保险规则）；
- 两表均按 reg_no 建普通索引供转正前置校验与申报登记查询。
含 downgrade（drop_table 回溯，先 claim 后 policy）。
"""
from alembic import op
import sqlalchemy as sa


revision = 'f9a0b1c2d3e4'
down_revision = 'e8f9a0b1c2d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'site_agent_insurance_policy',
        sa.Column('policy_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('insurer', sa.Text(), nullable=False),
        sa.Column('coverage_mou', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Text(), nullable=False),
        sa.Column('period_end', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('nca_ref', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('active','expired','revoked')",
                           name='ck_site_agent_insurance_policy_status'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_insurance_policy_prov'),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no'], ),
        sa.PrimaryKeyConstraint('policy_no'),
    )
    op.create_index('idx_site_agent_insurance_policy_reg', 'site_agent_insurance_policy',
                    ['reg_no'], unique=False)
    op.create_table(
        'site_agent_insurance_claim',
        sa.Column('claim_no', sa.Text(), nullable=False),
        sa.Column('reg_no', sa.Text(), nullable=False),
        sa.Column('loss_type', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount_mou', sa.Integer(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='INSURED'),
        sa.Column('actor', sa.Text(), nullable=False),
        sa.Column('nca_ref', sa.Text(), nullable=True),
        sa.Column('data_provenance', sa.Text(), nullable=False, server_default='real'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("loss_type IN ('制度漏洞','技术漏洞')",
                           name='ck_site_agent_insurance_claim_loss_type'),
        sa.CheckConstraint("status IN ('INSURED')",
                           name='ck_site_agent_insurance_claim_status'),
        sa.CheckConstraint("data_provenance IN ('simulated','real','mixed')",
                           name='ck_site_agent_insurance_claim_prov'),
        sa.ForeignKeyConstraint(['reg_no'], ['site_agent_registry.reg_no'], ),
        sa.PrimaryKeyConstraint('claim_no'),
    )
    op.create_index('idx_site_agent_insurance_claim_reg', 'site_agent_insurance_claim',
                    ['reg_no'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_site_agent_insurance_claim_reg', table_name='site_agent_insurance_claim')
    op.drop_table('site_agent_insurance_claim')
    op.drop_index('idx_site_agent_insurance_policy_reg', table_name='site_agent_insurance_policy')
    op.drop_table('site_agent_insurance_policy')
