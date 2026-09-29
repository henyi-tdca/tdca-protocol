# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M1 | 目标函数: M1 数据库层——10 表 ORM 模型（严格按 KIMI-WEB-DB-M1-DESIGN-001 DDL）
# 约束矩阵: 任务书 §二 M1 验收①（表结构覆盖 agents/MOU/NCA/税收/沙盒状态）；金额整分；时间 ISO-8601 UTC 文本
# 制度锚点: ID92（每表 data_provenance CHECK 约束）/ ID71（治理事件人类签批人字段）/ 宪法第 4 条 C01（存证链可观测）
# 先验分布: 前端 15 页面接口定义 + gateway api_v1.py 21 端点（字段溯源见设计包 §一）
# 配置权边界: L2 数据层；不触碰 FROZEN 前端；不改 gateway 既有端点
# 预期分配: 10 个 ORM 模型类，与 0001 迁移一一对应
# 审计轨迹: NCA-KIMIWEB-003/004
# =============================================================================
"""M1 ORM 模型：10 表。字段命名与设计包 DDL 严格一致。"""
from sqlalchemy import REAL, CheckConstraint, ForeignKey, Index, Integer, Text, Computed
from sqlalchemy.orm import Mapped, mapped_column

from . import Base

# ID92：合法取值闭集，非法值插入即被 CHECK 拒绝（fail-closed）
_PROVENANCE_CHECK = "data_provenance IN ('simulated','real','mixed')"


class Agent(Base):
    """1. 智能体注册表（/agents 面板 + /notifier MRCR 角色）。"""

    __tablename__ = "agents"
    agent_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[str | None] = mapped_column(Text)
    capability: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    tdid: Mapped[str | None] = mapped_column(Text)
    five_role: Mapped[str | None] = mapped_column(Text)
    scene: Mapped[str | None] = mapped_column(Text)
    attestation_state: Mapped[str] = mapped_column(Text, nullable=False, default="valid")
    audit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("five_role IN ('H','M','L','mu','G')", name="ck_agents_five_role"),
        CheckConstraint("attestation_state IN ('valid','expiring','invalid')", name="ck_agents_attest"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_agents_prov"),
    )


class MouRecord(Base):
    """2. MOU 效用计量（/tax；MOU = tax_in + tax_out，ID79；金额单位：分）。"""

    __tablename__ = "mou_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    mou_inbound: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mou_outbound: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mou_total: Mapped[int] = mapped_column(
        Integer, Computed("mou_inbound + mou_outbound"), nullable=False
    )
    mou_irreducible: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    note: Mapped[str | None] = mapped_column(Text)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_mou_prov"),
        Index("uq_mou_agent_period", "agent_id", "period", unique=True),
    )


class NcaChain(Base):
    """3. NCA 存证链（/audit + /nca/chain；链式性 = 断链即无效）。"""

    __tablename__ = "nca_chain"
    nca_id: Mapped[str] = mapped_column(Text, primary_key=True)
    prev_nca: Mapped[str | None] = mapped_column(Text)  # 首条 = GENESIS
    action: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    sha256_8: Mapped[str | None] = mapped_column(Text)
    handshake_id: Mapped[str | None] = mapped_column(Text)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_nca_prov"),
        Index("idx_nca_prev", "prev_nca"),
    )


class TaxEvent(Base):
    """4. 税收事件/公共账本（/audit ledger + /tax history + shapley 分配；金额单位：分）。"""

    __tablename__ = "tax_events"
    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.agent_id"))
    call_id: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_bp: Mapped[int | None] = mapped_column(Integer)  # 基点：2%=200 / 7.5%=750 / 0.75%=75
    shapley_phi: Mapped[int | None] = mapped_column(Integer)
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_tax_prov"),
        Index("idx_tax_agent", "agent_id"),
    )


class SandboxState(Base):
    """5a. 沙盒 SEA 要件状态（/sandbox；GREEN/AMBER/RED 闭集）。"""

    __tablename__ = "sandbox_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[str] = mapped_column(Text, nullable=False)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    __table_args__ = (
        CheckConstraint("status IN ('GREEN','AMBER','RED')", name="ck_sea_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_sea_prov"),
    )


class SandboxApplication(Base):
    """5b. 沙盒申请记录（POST /sandbox/apply 落库）。"""

    __tablename__ = "sandbox_applications"
    apply_id: Mapped[str] = mapped_column(Text, primary_key=True)
    applicant: Mapped[str] = mapped_column(Text, nullable=False)
    sea_snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    result: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("result IN ('admitted','denied','pending')", name="ck_apply_result"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_apply_prov"),
    )


class SystemMetric(Base):
    """6. 系统指标快照（/home overview 时序；金额单位：分）。"""

    __tablename__ = "system_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_deliveries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tax_settled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(REAL, nullable=False, default=0)
    total_fused: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_fail_closed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispatch_tax_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    royalty_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=750)
    transaction_fee_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=75)
    theta: Mapped[float | None] = mapped_column(REAL)
    phi: Mapped[float | None] = mapped_column(REAL)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (CheckConstraint(_PROVENANCE_CHECK, name="ck_metrics_prov"),)


class AttestationRequest(Base):
    """7. 确权请求（/attestation queue/history/meta/dynamic）。"""

    __tablename__ = "attestation_requests"
    request_id: Mapped[str] = mapped_column(Text, primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    request_type: Mapped[str] = mapped_column(Text, nullable=False)  # meta/dynamic
    urgency: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    decided_by: Mapped[str | None] = mapped_column(Text)  # HUF 签批人（M3 接鉴权）
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="ck_att_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_att_prov"),
    )


class AssetOrder(Base):
    """8. 五阶资产池（/market，只读优先）。"""

    __tablename__ = "asset_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    asset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    __table_args__ = (
        CheckConstraint("order_no BETWEEN 1 AND 5", name="ck_order_no"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_asset_prov"),
    )


class TermsRegistry(Base):
    """9. 术语注册表（/academy，只读种子；真实口径 → provenance=real）。"""

    __tablename__ = "terms_registry"
    term_id: Mapped[str] = mapped_column(Text, primary_key=True)  # T-001~
    term: Mapped[str] = mapped_column(Text, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    registry_version: Mapped[str] = mapped_column(Text, nullable=False, default="V2.1")
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    __table_args__ = (CheckConstraint(_PROVENANCE_CHECK, name="ck_terms_prov"),)


class GovernanceEvent(Base):
    """10. 治理事件（/governance huf-sign/emergency-fuse；M3 鉴权复用）。"""

    __tablename__ = "governance_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    op: Mapped[str] = mapped_column(Text, nullable=False)  # huf_sign/emergency_fuse
    operator: Mapped[str] = mapped_column(Text, nullable=False)  # 人类签批人标识（ID71）
    payload: Mapped[str | None] = mapped_column(Text)  # JSON
    fuse_state: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("fuse_state IN ('CLOSED','SUSPENDED','BLOCKED')", name="ck_fuse_state"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_gov_prov"),
    )


class User(Base):
    """11. 用户表（M3 鉴权 F-2；密码 PBKDF2 哈希+盐，绝不明文/不可逆）。"""

    __tablename__ = "users"
    username: Mapped[str] = mapped_column(Text, primary_key=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    salt: Mapped[str] = mapped_column(Text, nullable=False)
    iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=120000)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="viewer")
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("role IN ('founder','operator','viewer')", name="ck_users_role"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_users_prov"),
    )


class AuthSession(Base):
    """12. 会话表（M3；token 只存 sha256 哈希；单会话制，登录即吊销旧会话）。"""

    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), nullable=False)
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)
    revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_sessions_prov"),
    )
