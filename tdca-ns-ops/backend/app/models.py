# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——约束管理 CRUD + 三层视图 + 调整权面板
# 约束矩阵:     宪法十六条 + UPDA + FC-NS-OPS-001 BV-1~7（BV-3 人类写权 / BV-5 NCA / BV-6 快慢分离）
# 先验分布:     NS-GOVERNANCE-SYSTEM-001 + 红队审查结论 + 论丛 NS-008/009/010/011 规格提取
# 配置权边界:    L2 配置权市场层；负空间约束写操作仅人类可执行（BV-3 硬隔离）
# 预期分配:     数据模型层（Pydantic schema），前后端契约唯一权威（接口熵=0，ID82）
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}（原型阶段仅登记，不涉及真实税收）
# =============================================================================

"""NS-OPS M1 数据模型层。

制度锚定: FC-NS-OPS-001 F1/F2/F3 | NS-GOVERNANCE-SYSTEM-001 三层负空间 | 论丛 FNSCM/NSI/NSAR 规格
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# 枚举定义（论丛规格映射）
# ---------------------------------------------------------------------------


class ConstraintLayer(str, Enum):
    """三层负空间（NS-009）。layer 直接映射四重底线之一：
    主体=合理 / 场景=合规 / 制度=合法（+合情在场景层叠加）。"""

    SUBJECT = "subject"            # 主体负空间:「我不会」
    SCENE = "scene"                # 场景负空间:「这里不能」（意义维持系统）
    INSTITUTIONAL = "institutional"  # 制度负空间:「任何人不能」（宪法/NSFL/L0 法律）


class ConstraintScope(str, Enum):
    """FNSCM Scope（NS-009 §3.1）。"""

    GLOBAL = "global"            # L1 全局
    INDUSTRY = "industry"        # L2 行业
    SCENE = "scene"              # L3 场景
    ORGANIZATION = "organization"  # L4 组织
    PERSONAL = "personal"        # L5 个人


class Certainty(str, Enum):
    """NSI 底线条目 Certainty（NS-008 §2.2）。"""

    ABSOLUTE = "absolute"        # 绝对（制度负空间/法律底线）
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConstraintStatus(str, Enum):
    """NS-011 状态机（原型精简版）：草案→审议→沙盒→确定(冻结)→编码(刚性)→部署→退役。"""

    DRAFT = "draft"                    # 草案（人类起草）
    DELIBERATING = "deliberating"      # 审议中（HRC 三级裁决）
    SANDBOX = "sandbox"                # 沙盒验证中（BV-4 先模拟后生效）
    FROZEN = "frozen"                  # 确定-冻结态（≥3 人类签名，生效时间/回滚版本已定）
    RIGID = "rigid"                    # 编码-刚性态（智能合约硬约束，快系统 <100ms 执行）
    DEPRECATED = "deprecated"          # 退役（保留审计轨迹）


class AdjustmentStatus(str, Enum):
    """NSAR-Registry 调整流程状态（NS-011 §4.2 + §2.2）。"""

    DELIBERATION = "deliberation"      # 审议（人类专属）
    SANDBOX = "sandbox"                # 沙盒验证
    DETERMINATION = "determination"    # 确定（冻结态版本）
    ENCODING = "encoding"              # 编码（NSFL 编译 + 人类验证意图）
    DEPLOYMENT = "deployment"          # 部署（灰度→全量）
    FEEDBACK = "feedback"              # 反馈（快系统异常上报，慢系统 30 天未响应继续执行）
    CLOSED = "closed"                  # 闭合


class SandboxStage(str, Enum):
    """NS-011 三层沙盒：技术→经济→社会。"""

    TECHNICAL = "technical"
    ECONOMIC = "economic"
    SOCIAL = "social"


class Decision(str, Enum):
    """NS-006 五步查询判定枚举。"""

    BLOCK = "block"                          # 绝对阻断（制度负空间/法律底线）
    RESTRICT = "restrict"                    # 受限执行
    ALLOW_WITH_CONDITIONS = "allow_with_conditions"  # 附条件允许
    ALLOW = "allow"                          # 允许


class BottomLine(str, Enum):
    """四重底线（NS-009 §6.2）：合法/合规/合理/合情。"""

    LEGAL = "合法"
    COMPLIANT = "合规"
    REASONABLE = "合理"
    HUMANISTIC = "合情"


# ---------------------------------------------------------------------------
# 约束模型（FNSCM.NS_Entries + NSI 底线条目合并，M1 统一约束表）
# ---------------------------------------------------------------------------


class Constraint(BaseModel):
    """负空间约束条目（FNSCM.NS_Entries 字段级落地）。

    六要素声明:
    目标函数: 表示一条负空间约束的完整生命周期数据（三层负空间统一表）
    约束矩阵: 输入校验——layer/scope/certainty/status 枚举合法；action 非空；
              输出格式——符合 NS-009 FNSCM 字段规范；禁止——AI 无签名写权（BV-3）
    先验分布: NS-008 §2.2 NSI 底线条目 (Scope,Action,Context,Certainty,Verification_Method,Consequence)
              + NS-009 §3.1 FNSCM.NS_Entries
    配置权边界: L2 层；人类可写，AI 仅读（BV-3）
    预期分配: 返回约束对象；副作用=写操作必须经 HumanGate（人类签名门）；失败=校验异常
    审计轨迹: 输入哈希=request json hash；输出哈希=约束 id hash；时间戳=updated_at；NCA=写操作生成
    """

    id: str = Field(default_factory=lambda: f"NS-{uuid.uuid4().hex[:8].upper()}")
    layer: ConstraintLayer
    scope: ConstraintScope
    action: str = Field(..., min_length=2, description="自然语言声明（「我不会 X」/「这里不能 Y」/「任何人不能 Z」）")
    action_code: str = Field(default="", description="NSFL 代码表述（如 ⊗ data.leak()）")
    context: str = Field(default="", description="场景参数（时间/地点/事件/主体/内容/交互 六要素子集）")
    certainty: Certainty = Certainty.MEDIUM
    rationale: str = Field(default="", description="理由/溯因（NS-011 审议输出）")
    consequence: str = Field(default="", description="违反后果（NS-008：触碰绝对禁止=配置权调度税 10 倍等）")
    bottom_lines: list[BottomLine] = Field(
        default_factory=lambda: [BottomLine.LEGAL, BottomLine.COMPLIANT],
        description="四重底线标记（合法/合规/合理/合情）",
    )
    verification_method: str = Field(default="", description="验证方式（Code_Fuse/Runtime_Audit/Human_Review 等）")
    status: ConstraintStatus = ConstraintStatus.DRAFT
    version: int = 1
    owner: str = Field(default="", description="声明主体（主体负空间=DID/名称；场景=治理者；制度=TDCA 制度体系）")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    human_signatures: list[str] = Field(default_factory=list, description="人类签名列表（BV-3 硬隔离，确定态 ≥3 个）")
    effective_date: Optional[str] = None
    rollback_version: Optional[int] = None
    nca_refs: list[str] = Field(default_factory=list, description="关联 NCA 记录（BV-5 全存证）")

    @field_validator("action")
    @classmethod
    def _action_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("action 不可为空")
        return v

    @field_validator("certainty")
    @classmethod
    def _legal_absolute(cls, v: Certainty, info) -> Certainty:
        # BV-1 制度负空间（institutional）强制 absolute——L0 法律负空间无变通（红队 F-1 返修）
        layer = info.data.get("layer")
        if layer == ConstraintLayer.INSTITUTIONAL and v != Certainty.ABSOLUTE:
            raise ValueError("制度负空间约束 certainty 必须为 absolute（L0 法律底线不可协商）")
        return v


class ConstraintCreate(BaseModel):
    """约束创建请求（BV-3：必须携带 human_signature）。"""

    layer: ConstraintLayer
    scope: ConstraintScope
    action: str = Field(..., min_length=2)
    action_code: str = ""
    context: str = ""
    certainty: Certainty = Certainty.MEDIUM
    rationale: str = ""
    consequence: str = ""
    bottom_lines: list[BottomLine] = [
        BottomLine.LEGAL,
        BottomLine.COMPLIANT,
    ]
    verification_method: str = ""
    owner: str = ""
    human_signature: str = Field(..., min_length=3, description="人类签名标识（BV-3 写权限门）")


class ConstraintUpdate(BaseModel):
    """约束更新请求（BV-3：必须携带 human_signature；版本递增）。"""

    action: Optional[str] = None
    action_code: Optional[str] = None
    context: Optional[str] = None
    certainty: Optional[Certainty] = None
    rationale: Optional[str] = None
    consequence: Optional[str] = None
    bottom_lines: Optional[list[BottomLine]] = None
    verification_method: Optional[str] = None
    human_signature: str = Field(..., min_length=3)


# ---------------------------------------------------------------------------
# 调整权模型（NSAR-Registry，NS-011 §4.2 落地）
# ---------------------------------------------------------------------------


class DeliberationRecord(BaseModel):
    """审议记录（人类专属，HRC 三级裁决）。"""

    trigger: str = Field(..., description="调整信号（立法雷达/政策扫描/熔断事件/数据异常等）")
    participants: list[str] = Field(default_factory=list, description="参与人（L1 技术/L2 行业/L3 异构三角）")
    proposal: str = Field(default="", description="调整草案")
    dissenting_opinions: list[str] = Field(default_factory=list, description="异议意见（强制记录）")
    nca_ref: str = Field(default="", description="NCA-Deliberation-Record")


class SandboxResult(BaseModel):
    """沙盒验证结果（BV-4 先模拟后生效）。"""

    technical: bool = False
    economic: bool = False
    social: bool = False
    report: str = Field(default="", description="沙盒报告（各层验证要点）")
    nca_ref: str = Field(default="")


class DeterminationRecord(BaseModel):
    """确定记录（冻结态：生效时间 + 回滚版本 + ≥3 人类签名）。"""

    final_version: int = 1
    effective_date: str = Field(default="", description="生效时间（不可立即生效）")
    rollback_version: int = Field(default=0, description="回滚版本")
    human_signatures: list[str] = Field(default_factory=list, description="≥3 个人类签名（异构三角）")
    nca_ref: str = Field(default="")


class DeploymentRecord(BaseModel):
    """部署记录（GDP 渐进：5%→50%→100%）。"""

    gray_start: Optional[str] = None
    full_start: Optional[str] = None
    status: Literal["pending", "gray", "full", "rolled_back"] = "pending"
    nca_ref: str = Field(default="")


class FeedbackRecord(BaseModel):
    """快→慢反馈（5 条件触发：误触发率>0.1% / 漏触发率>0.01% / 影响>1000 节点 / 严重冲突 / 系统性绕过）。"""

    alert_type: str = Field(default="", description="异常类型")
    severity: Literal["info", "warning", "critical"] = "info"
    description: str = Field(default="", description="异常描述")
    evidence: dict = Field(default_factory=dict, description="证据（fuse_count/false_positive_rate 等）")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Adjustment(BaseModel):
    """调整权操作记录（NSAR-Registry JSON 落地，NS-011 §4.2）。"""

    adjustment_id: str = Field(default_factory=lambda: f"NSAR-{uuid.uuid4().hex[:8].upper()}")
    initiator: str = Field(..., description="发起人（人类）")
    target_constraint_id: str = Field(..., description="目标约束")
    status: AdjustmentStatus = AdjustmentStatus.DELIBERATION
    deliberation: Optional[DeliberationRecord] = None
    sandbox: Optional[SandboxResult] = None
    determination: Optional[DeterminationRecord] = None
    deployment: Optional[DeploymentRecord] = None
    feedbacks: list[FeedbackRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    nca_refs: list[str] = Field(default_factory=list)


class AdjustmentStartRequest(BaseModel):
    """发起调整请求（BV-3：人类发起）。"""

    target_constraint_id: str
    trigger: str = Field(..., min_length=3, description="调整信号")
    proposal: str = Field(..., min_length=3, description="调整草案")
    initiator: str = Field(..., min_length=2, description="发起人（人类）")
    human_signature: str = Field(..., min_length=3)


# ---------------------------------------------------------------------------
# 三层视图模型
# ---------------------------------------------------------------------------


class SubjectView(BaseModel):
    """主体负空间视图（NS-008：NSI 底线条目 + 信用）。"""

    subject: str
    entries: list[Constraint]
    nsc_credit: int = Field(default=100, description="NSCredit（触碰主体 -5 / 制度 -10+ERI 清零）")


class SceneView(BaseModel):
    """场景负空间视图（NS-010：六要素 + 主题意义）。"""

    scene: str
    six_elements: dict = Field(default_factory=dict, description="时间/地点/事件/主体/内容/交互")
    theme: str = Field(default="", description="主题意义")
    theme_health: float = Field(default=1.0, ge=0.0, le=1.0, description="Theme_Health_Index")
    entries: list[Constraint]


class InstitutionalView(BaseModel):
    """制度负空间视图（NS-006/NS-009：L0-L1 全局规则）。"""

    layer_label: str = "L0-L1 全局只读（宪法/NSFL/L0 法律）"
    entries: list[Constraint]


class TripleLayerView(BaseModel):
    """三层负空间总视图（F1）。

    H4 修复：subject/scene 支持多组（多主体/多场景），不再单取 [0] 导致数据丢失。
    """

    subjects: list[SubjectView] = Field(default_factory=list)
    scenes: list[SceneView] = Field(default_factory=list)
    institutional: InstitutionalView
    bottom_lines: dict = Field(default_factory=dict, description="四重底线 Pass/Fail")
    safe_domain: str = Field(default="", description="安全域 = Ω \\ (制度∪场景∪主体∪文化)")


class JudgmentRequest(BaseModel):
    """声明-行为校验请求（F3，NS-006 五步查询）。"""

    actor: str = Field(..., min_length=2)
    action: str = Field(..., min_length=2)
    scene: str = Field(default="", description="场景标识（六要素 JSON 序列）")
    context: dict = Field(default_factory=dict)


class JudgmentResponse(BaseModel):
    """校验判定（NS-006 判定枚举 + NS-008 兼容性）。"""

    decision: Decision
    reason: str
    matched_constraints: list[str] = Field(default_factory=list, description="命中的约束 id")
    fuse_triggered: bool = False
    nca_ref: str = Field(default="", description="NCA-Judgment 存证")
