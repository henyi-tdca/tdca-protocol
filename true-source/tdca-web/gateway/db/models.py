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
    # M5：归属字段——人类用户 ↔ 智能体唯一纽带（/me 个人后台聚合锚点；NULL=未认领存量）
    owner_username: Mapped[str | None] = mapped_column(ForeignKey("users.username"))
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


class UserIdentity(Base):
    """13. 用户身份扩展表（GSEQ-0700：identity_type/agent_card/owner_auth 持久化，
    注册端点不再静默丢弃；非原生性链上可机验）。"""

    __tablename__ = "user_identities"
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)
    identity_type: Mapped[str] = mapped_column(Text, nullable=False, default="native")  # native|external
    agent_card_json: Mapped[str | None] = mapped_column(Text)   # external 必填（JSON 序列化）
    owner_auth: Mapped[str | None] = mapped_column(Text)        # external 必填（授权引用编号）
    nca_ref: Mapped[str | None] = mapped_column(Text)           # 缔约/补录存证回链
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("identity_type IN ('native','external')", name="ck_user_identities_type"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_user_identities_prov"),
    )


class WorkflowDef(Base):
    """14. 工作流定义（P1 WorkBuddy 上站：POST /api/v1/workbuddy/workflow/create 落库；DSL JSON 全量）。"""

    __tablename__ = "workflow_defs"
    workflow_id: Mapped[str] = mapped_column(Text, primary_key=True)
    owner_username: Mapped[str | None] = mapped_column(ForeignKey("users.username"))
    dsl_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING_HUMAN_GATE")
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (CheckConstraint(_PROVENANCE_CHECK, name="ck_wfdef_prov"),)


class WorkflowRun(Base):
    """15. 工作流执行记录（execute 落库：状态/步骤/NCA 全链可追溯；端到端 <10s 硬指标留痕）。"""

    __tablename__ = "workflow_runs"
    execution_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow_defs.workflow_id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="RUNNING")
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nsfl_status: Mapped[str] = mapped_column(Text, nullable=False, default="CLEAR")
    nca_refs_json: Mapped[str | None] = mapped_column(Text)
    results_json: Mapped[str | None] = mapped_column(Text)
    elapsed_ms: Mapped[float | None] = mapped_column(REAL)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    started_at: Mapped[str] = mapped_column(Text, nullable=False)
    finished_at: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('RUNNING','COMPLETED','BLOCKED','FAILED')", name="ck_wfrun_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_wfrun_prov"),
    )


class SignatureRequest(Base):
    """16. 人类签名请求（signature/request→confirm 全链留痕；硬件签名模拟校验 ≥8 字符，自动化签名熔断）。"""

    __tablename__ = "signature_requests"
    request_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workflow_id: Mapped[str | None] = mapped_column(Text)
    gate_id: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    applicant: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    tx_hash: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    signed_at: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('pending','signed')", name="ck_sig_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_sig_prov"),
    )


class AuthGrant(Base):
    """17. 授权件登记（P2 准入闸门：配置类调用须授权件机验——四要件逐条核验，
    智能体不得代签代持；parent_grant_id 承载多层转授链）。"""

    __tablename__ = "auth_grants"
    grant_id: Mapped[str] = mapped_column(Text, primary_key=True)  # AG-xxx
    subject_agent: Mapped[str] = mapped_column(Text, nullable=False)
    scene_constraint: Mapped[str] = mapped_column(Text, nullable=False)  # 要件①场景约束
    asset_order: Mapped[int] = mapped_column(Integer, nullable=False)    # 要件②五阶资产形态 1~5
    full_composition: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 要件③全构成已授权
    legal_signer: Mapped[str] = mapped_column(Text, nullable=False)      # 要件④法律主体签名
    signature: Mapped[str] = mapped_column(Text, nullable=False)         # 模拟硬件签 ≥8 字符
    parent_grant_id: Mapped[str | None] = mapped_column(Text)            # 转授链上级（首授=NULL）
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("asset_order BETWEEN 1 AND 5", name="ck_grant_order"),
        CheckConstraint("full_composition IN (0,1)", name="ck_grant_full"),
        CheckConstraint("status IN ('active','revoked')", name="ck_grant_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_grant_prov"),
        Index("idx_grant_subject", "subject_agent"),
    )


class LineageEntry(Base):
    """18. 谱系账本（P2：授权谱系——授权件＋多层转授链全量留痕，只增不改）。"""

    __tablename__ = "lineage_entries"
    entry_id: Mapped[str] = mapped_column(Text, primary_key=True)  # LE-xxx
    agent_id: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)  # grant/subgrant/revoke
    grant_id: Mapped[str | None] = mapped_column(Text)
    parent_grant_id: Mapped[str | None] = mapped_column(Text)  # 链上级（谱系追溯）
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    ts: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("kind IN ('grant','subgrant','revoke')", name="ck_lineage_kind"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_lineage_prov"),
        Index("idx_lineage_agent", "agent_id"),
    )


class FormalConclusion(Base):
    """19. 形式化与实验线结论入站（P3：只做结论面——不转公式、不引数值、不带内部编号；
    数据性质显式标注；入站 ≠ 入主仓 ≠ 对外）。"""

    __tablename__ = "formal_conclusions"
    conclusion_id: Mapped[str] = mapped_column(Text, primary_key=True)  # FC-xxx
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)       # 结论面（纯文字）
    data_nature: Mapped[str] = mapped_column(Text, nullable=False)      # formal-proved/simulated/assessed
    scope_note: Mapped[str | None] = mapped_column(Text)                # 适用边界（条件形态须载明）
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("data_nature IN ('formal-proved','simulated','assessed')",
                        name="ck_fc_nature"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_fc_prov"),
    )


class ToolItem(Base):
    """20. 工具货架（P4：站内工具/模板目录——编译器、适配器等；requires_grant 标记配置类）。"""

    __tablename__ = "tool_items"
    tool_id: Mapped[str] = mapped_column(Text, primary_key=True)  # TL-xxx
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)   # compiler/adapter/template/other
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(Text)
    requires_grant: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="available")
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("category IN ('compiler','adapter','template','other')",
                        name="ck_tool_cat"),
        CheckConstraint("requires_grant IN (0,1)", name="ck_tool_grant"),
        CheckConstraint("status IN ('available','offline')", name="ck_tool_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_tool_prov"),
    )


class CiRun(Base):
    """21. CI 手动触发机验记录（P5：手动入口先行——lake build＋core-go 测试＋网关回归；
    绿灯徽章供 P3 页面展示；自动门禁待官方 CI 白名单，期一后半再补）。"""

    __tablename__ = "ci_runs"
    run_id: Mapped[str] = mapped_column(Text, primary_key=True)  # CI-xxx
    suite: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)    # PASS/FAIL/ERROR
    exit_code: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[str | None] = mapped_column(Text)             # 输出尾部留痕
    operator: Mapped[str | None] = mapped_column(Text)
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    started_at: Mapped[str] = mapped_column(Text, nullable=False)
    finished_at: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('PASS','FAIL','ERROR')", name="ck_ci_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_ci_prov"),
        Index("idx_ci_suite", "suite"),
    )


class CopyrightEvent(Base):
    """22. 权属登记事件（P6：登记／变更／注销——跑在版权链模拟锚（NCA 链）上；
    ⛔ 转让／许可不在一期（归 8b）；全程 SIMULATED）。"""

    __tablename__ = "copyright_events"
    event_id: Mapped[str] = mapped_column(Text, primary_key=True)  # CE-xxx
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    work_title: Mapped[str] = mapped_column(Text, nullable=False)
    owner_ref: Mapped[str] = mapped_column(Text, nullable=False)
    source_lineage: Mapped[str | None] = mapped_column(Text)   # 生成来源谱系（登记必填）
    note: Mapped[str | None] = mapped_column(Text)
    template_ref: Mapped[str | None] = mapped_column(Text)     # CRIGHT-EVENT-001~003
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("event_type IN ('register','amend','cancel')", name="ck_ce_type"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_ce_prov"),
        Index("idx_ce_type", "event_type"),
    )


class OwnershipRecord(Base):
    """24. 权属登记记录（P8a 一期段：登记／变更／注销／查询——权属侧；
    登记二分之本面只做「归谁」，授权侧归 8b；入口＝凡具表达形式者皆可登记；
    须载生成来源谱系；场景非必须；法域四支仅为索引分支，⛔ 不代作法律判定）。"""

    __tablename__ = "ownership_records"
    record_id: Mapped[str] = mapped_column(Text, primary_key=True)  # OR-xxx
    work_title: Mapped[str] = mapped_column(Text, nullable=False)   # 登记对象（表达形式）
    owner_ref: Mapped[str] = mapped_column(Text, nullable=False)    # 权利人引用
    expression_form: Mapped[str | None] = mapped_column(Text)       # 表达形式描述（可空）
    jurisdiction_branch: Mapped[str] = mapped_column(
        Text, nullable=False, default="unspecified")                # copyright/patent/data/trademark/unspecified
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)  # 生成来源谱系（登记必填）
    scene: Mapped[str | None] = mapped_column(Text)                 # 场景（⛔ 非必须；无场景不得拒登记）
    status: Mapped[str] = mapped_column(Text, nullable=False, default="registered")
    note: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("jurisdiction_branch IN ('copyright','patent','data',"
                        "'trademark','unspecified')", name="ck_own_branch"),
        CheckConstraint("status IN ('registered','amended','cancelled')",
                        name="ck_own_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_own_prov"),
        Index("idx_own_owner", "owner_ref"),
    )


class MarketSimRun(Base):
    """25. 配置权市场沙盒最小链运行记录（P9：发布→准入审查→撮合→结算，
    全程 SIMULATED 硬标注；准入审查复用 P2 授权件机验结果，⛔ 不重做）。"""

    __tablename__ = "market_sim_runs"
    run_id: Mapped[str] = mapped_column(Text, primary_key=True)  # MS-xxx
    offer_json: Mapped[str] = mapped_column(Text, nullable=False)   # 发布要约（JSON）
    steps_json: Mapped[str] = mapped_column(Text, nullable=False)   # 逐步留痕（含 NCA refs）
    result: Mapped[str] = mapped_column(Text, nullable=False)       # settled / denied
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("result IN ('settled','denied')", name="ck_msim_result"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_msim_prov"),
    )


class OpsTicket(Base):
    """23. 运维工单（P7：反馈→红线分类→提案→沙盒→上线；触碰红线升 ESCALATED_DCD；
    上线 NCA 存证＋reconcile 对账可回滚）。"""

    __tablename__ = "ops_tickets"
    ticket_id: Mapped[str] = mapped_column(Text, primary_key=True)  # OPS-xxx
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="INTAKE")
    redline_hit: Mapped[str | None] = mapped_column(Text)   # 命中的红线名目（升 DCD 依据）
    classifier_note: Mapped[str | None] = mapped_column(Text)
    proposal: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('INTAKE','CLASSIFIED','PROPOSED','SANDBOXED',"
                        "'RELEASED','ESCALATED_DCD')", name="ck_ops_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_ops_prov"),
        Index("idx_ops_status", "status"),
    )


class Announcement(Base):
    """26. 公告栏（对外公告区：标题／日期／正文；初始空栏——⛔ 不预置内容；
    发布须 operator／founder 且内容须经创始人明示；发布落 NCA 存证链）。"""

    __tablename__ = "announcements"
    announcement_id: Mapped[str] = mapped_column(Text, primary_key=True)  # AN-xxx
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)               # 正文（纯文字）
    published_by: Mapped[str | None] = mapped_column(Text)                # 发布账号（内部面）
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    published_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_ann_prov"),
    )


class AuthorizationRecord(Base):
    """26. 授权登记记录（P8b 一期段：登记／变更／注销／查询／操作——授权侧；
    登记二分之本面只做「谁能怎么用」；四要件（场景约束／五阶资产形态／全构成已授权／
    法律主体签名）缺一即拒；授权件模板八字段以 template_fields 透传存证；
    签名＝电子签名与授权码皆须本人，智能体不代持、不代填；公开面仅四字段）。"""

    __tablename__ = "authorization_records"
    record_id: Mapped[str] = mapped_column(Text, primary_key=True)  # AR-xxx
    asset_ref: Mapped[str] = mapped_column(Text, nullable=False)    # 授权对象引用
    grantee_ref: Mapped[str] = mapped_column(Text, nullable=False)  # 被授权方引用
    scene: Mapped[str] = mapped_column(Text, nullable=False)        # 场景（四要件①载体）
    req_scene: Mapped[bool] = mapped_column(nullable=False, default=False)          # ① 场景约束
    req_five_forms: Mapped[bool] = mapped_column(nullable=False, default=False)     # ② 五阶资产形态
    req_full_grant: Mapped[bool] = mapped_column(nullable=False, default=False)     # ③ 全构成已授权
    req_legal_signature: Mapped[bool] = mapped_column(nullable=False, default=False)  # ④ 法律主体签名
    scope_note: Mapped[str | None] = mapped_column(Text)            # 权限范围说明（⛔ 不代定取值）
    term_note: Mapped[str | None] = mapped_column(Text)             # 期限说明（⛔ 不代定取值）
    template_fields: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # 模板八字段 JSON
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    note: Mapped[str | None] = mapped_column(Text)
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="simulated")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('pre-accepted','active','amended','cancelled')",
                        name="ck_authz_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_authz_prov"),
        Index("idx_authz_grantee", "grantee_ref"),
    )


class MarketListing(Base):
    """29. 配置权市场挂出件（管理面 A-1/A-3/A-4：挂出／状态变更／下架；
    先有成件闸门（权属成件＋授权成件＋四要件齐；例外仅沙盒演练显式标记）；
    初始条件必公开；下架不溯及已生成授权件；操作限权属登记人本人）。"""

    __tablename__ = "market_listings"
    listing_id: Mapped[str] = mapped_column(Text, primary_key=True)  # ML-xxx
    owner_ref: Mapped[str] = mapped_column(Text, nullable=False)     # 权属登记人本人
    ownership_record_id: Mapped[str] = mapped_column(Text, nullable=False)   # 权属成件
    authorization_record_id: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 授权成件（沙盒例外空）
    asset_summary: Mapped[str] = mapped_column(Text, nullable=False)
    scene: Mapped[str] = mapped_column(Text, nullable=False)
    scope_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    term_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    initial_conditions: Mapped[str] = mapped_column(Text, nullable=False)  # 初始条件（必公开）
    sandbox_flag: Mapped[int] = mapped_column(nullable=False, default=0)   # 沙盒例外显式标记
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    published_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('active','paused','delisted')", name="ck_ml_status"),
        CheckConstraint("sandbox_flag IN (0,1)", name="ck_ml_sandbox"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_ml_prov"),
        Index("idx_ml_owner", "owner_ref"),
        Index("idx_ml_status", "status"),
    )


class MarketListingEvent(Base):
    """30. 挂出件事件留痕（双留痕：事件表＋NCA；publish／pause／resume／delist
    各记原态与新态；操作人限权属登记人本人）。"""

    __tablename__ = "market_listing_events"
    event_id: Mapped[str] = mapped_column(Text, primary_key=True)    # MLE-xxx
    listing_id: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)        # publish/pause/resume/delist
    from_status: Mapped[str] = mapped_column(Text, nullable=False, default="")
    to_status: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(Text, nullable=False)
    nca_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("nca_chain.nca_id"))
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("action IN ('publish','pause','resume','delist')", name="ck_mle_action"),
        CheckConstraint("to_status IN ('active','paused','delisted')", name="ck_mle_to"),
        Index("idx_mle_listing", "listing_id"),
    )


class UserAnchor(Base):
    """31. 用户身份锚表（L1SI145-ANCHOR-B2-001：注册选锚落存证＋人工受理核验）。

    明文最小化硬约束：只落 anchor_kind 枚举引用与 *_present 布尔＋evidence_ref 引用，
    ⛔ 绝不落真实姓名/手机号明文取值；选锚不产生权限、不发身份类令牌。
    未选锚者注册时照常建一行（anchor_kind NULL＝未选如实，tier 记名级·态待补）。
    """

    __tablename__ = "user_anchors"
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)
    anchor_kind: Mapped[str | None] = mapped_column(Text)          # notifier|realname-phone；NULL=未选
    anchor_tier: Mapped[str] = mapped_column(Text, nullable=False, default="记名级")
    tier_state: Mapped[str] = mapped_column(Text, nullable=False, default="待补")   # 待补|已补
    real_name_present: Mapped[int | None] = mapped_column(Integer)  # 核验后 1/0；未核 NULL
    phone_present: Mapped[int | None] = mapped_column(Integer)      # 同上（非必填，可为 0）
    evidence_ref: Mapped[str | None] = mapped_column(Text)          # 证据引用编号（⛔ 非明文）
    verified_at: Mapped[str | None] = mapped_column(Text)
    verifier: Mapped[str | None] = mapped_column(Text)              # 受理人账号
    nca_ref: Mapped[str | None] = mapped_column(Text)               # 最近锚段存证回链
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("anchor_kind IN ('notifier','realname-phone')", name="ck_user_anchors_kind"),
        CheckConstraint("anchor_tier IN ('固锚级','移锚级','记名级','未达门槛','未定档')",
                        name="ck_user_anchors_tier"),
        CheckConstraint("tier_state IN ('待补','已补')", name="ck_user_anchors_state"),
        CheckConstraint("real_name_present IN (0,1)", name="ck_user_anchors_rn"),
        CheckConstraint("phone_present IN (0,1)", name="ck_user_anchors_ph"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_user_anchors_prov"),
    )


class SiteAgentRegistry(Base):
    """32. 站点智能体通道·登记表（L1SI147-CHANNEL-B1-001：登记即创建、未登记即未创建）。

    主体与执行体二分：owner_username 为主体（人类账户）列，智能体执行体无财产；
    智能体侧标识＝登记号 reg_no（⛔ 不叫 TDID、不自造编号体例）；
    status＝正常＋惩罚三态（冻结／降权／吊销，批 4 执行器落表）。
    """

    __tablename__ = "site_agent_registry"
    reg_no: Mapped[str] = mapped_column(Text, primary_key=True)          # 登记号（通道内唯一）
    owner_username: Mapped[str] = mapped_column(ForeignKey("users.username"), nullable=False)
    six_elements_ref: Mapped[str] = mapped_column(Text, nullable=False)  # 创世六要素引用
    anchor_ref: Mapped[str | None] = mapped_column(Text)                 # 锚定项引用（user_anchors 锚段）
    tier: Mapped[str] = mapped_column(Text, nullable=False, default="basic")  # 等第（取值域后续批次裁定）
    status: Mapped[str] = mapped_column(Text, nullable=False, default="正常")
    nca_ref: Mapped[str | None] = mapped_column(Text)                    # 登记存证回链
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('正常','冻结','降权','吊销')", name="ck_site_agent_registry_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_site_agent_registry_prov"),
    )


class SiteAgentCredential(Base):
    """33. 站点智能体通道·凭据族（⛔ 只存不可逆指纹，凭据值一律不入库）。

    人类会话内签发（issuer_session 存会话指纹，⛔ 非会话值本身）；
    吊销即时生效（批 4 执行器；status=revoked 即全库拒）。
    """

    __tablename__ = "site_agent_credential"
    cred_no: Mapped[str] = mapped_column(Text, primary_key=True)
    reg_no: Mapped[str] = mapped_column(ForeignKey("site_agent_registry.reg_no"), nullable=False)
    cred_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)  # sha256 不可逆指纹
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    issued_at: Mapped[str] = mapped_column(Text, nullable=False)
    rotated_at: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[str | None] = mapped_column(Text)
    issuer_session: Mapped[str | None] = mapped_column(Text)             # 签发人类会话指纹（⛔ 非值）
    nca_ref: Mapped[str | None] = mapped_column(Text)                    # 签发存证回链
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    __table_args__ = (
        CheckConstraint("status IN ('active','revoked')", name="ck_site_agent_credential_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_site_agent_credential_prov"),
    )


class SiteAgentAdmission(Base):
    """34. 站点智能体通道·闸步表（批 2：六步硬序之状态机落点，①③④ 批 2 接真、⑤批 3）。

    每（登记号, 步）一行；状态闭集 passed／failed／pending——fail-closed 非 passed 即未达；
    负空间未过/沙盒未过如实记 failed（拒绝入网／⛔ 不得正空间执行）；
    ②token 步状态由凭据表 active 指纹派生，⛔ 不在本表落行（单一事实源）。
    """

    __tablename__ = "site_agent_admission"
    reg_no: Mapped[str] = mapped_column(ForeignKey("site_agent_registry.reg_no"), primary_key=True)
    step: Mapped[str] = mapped_column(Text, primary_key=True)   # protocol-load|ns-review|sandbox|execute
    state: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    result_ref: Mapped[str | None] = mapped_column(Text)        # 结果引用（⛔ 非凭据值）
    detail: Mapped[str | None] = mapped_column(Text)            # 要件绑定/申报摘要（JSON 文本）
    nca_ref: Mapped[str | None] = mapped_column(Text)           # 本步存证回链
    actor: Mapped[str | None] = mapped_column(Text)             # 操作人类账户
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("step IN ('protocol-load','ns-review','sandbox','execute')",
                        name="ck_site_agent_admission_step"),
        CheckConstraint("state IN ('passed','failed','pending')",
                        name="ck_site_agent_admission_state"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_site_agent_admission_prov"),
    )


class SiteAgentGrant(Base):
    """35. 站点智能体通道·授权件表（批 3：四要件机验，缺一不成立；配置即侵权口径）。

    照令七字段（grant_no/reg_no/scene_constraint/legal_signer/signature_ref/
    parent_grant_no/status）＋detail 四要件机验明细（R2 五阶清单/R3 全构成声明/逐条判值）；
    四要件依在册《授权件模板》（R1 场景约束/R2 五阶资产形态/R3 全构成已授权/R4 法律主体签名）；
    人类会话内登记（⛔ 智能体不代签代持）；⛔ 不承接不动草案 auth_grants。
    """

    __tablename__ = "site_agent_grant"
    grant_no: Mapped[str] = mapped_column(Text, primary_key=True)
    reg_no: Mapped[str] = mapped_column(ForeignKey("site_agent_registry.reg_no"), nullable=False)
    scene_constraint: Mapped[str] = mapped_column(Text, nullable=False)   # R1（未列明场景不在授权范围）
    legal_signer: Mapped[str] = mapped_column(Text, nullable=False)       # R4 法律主体签名者
    signature_ref: Mapped[str] = mapped_column(Text, nullable=False)      # R4 签名事件引用（落 NCA）
    parent_grant_no: Mapped[str | None] = mapped_column(
        ForeignKey("site_agent_grant.grant_no"))                          # 转授上层件号
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    detail: Mapped[str | None] = mapped_column(Text)   # 四要件机验明细（JSON）
    nca_ref: Mapped[str | None] = mapped_column(Text)  # 登记存证回链
    actor: Mapped[str | None] = mapped_column(Text)    # 操作人类账户
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="real")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('active','revoked')", name="ck_site_agent_grant_status"),
        CheckConstraint(_PROVENANCE_CHECK, name="ck_site_agent_grant_prov"),
    )


class SiteAgentCallLedger(Base):
    """36. 站点智能体通道·计量表（批 3：聚合窗口落账，⛔ 不高频直写致锁）。

    聚合窗口内同（登记号,端点,窗口起点）一行累计 units（窗口值施工取 60 秒，方案未定值）；
    units 数值按方案标模拟（SIMULATED 水印）；provenance=mixed（落账事实真＋计量数值模拟）。
    """

    __tablename__ = "site_agent_call_ledger"
    reg_no: Mapped[str] = mapped_column(ForeignKey("site_agent_registry.reg_no"), primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, primary_key=True)     # execute 等正空间端点名
    ts: Mapped[str] = mapped_column(Text, primary_key=True)           # 聚合窗口起点（ISO 分钟截断）
    units: Mapped[int] = mapped_column(nullable=False, default=0)     # 窗口累计（数值模拟）
    nca_anchor: Mapped[str | None] = mapped_column(Text)              # 本窗口最近存证锚
    data_provenance: Mapped[str] = mapped_column(Text, nullable=False, default="mixed")
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(_PROVENANCE_CHECK, name="ck_site_agent_ledger_prov"),
    )
