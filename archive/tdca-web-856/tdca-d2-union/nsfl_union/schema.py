# -*- coding: utf-8 -*-
"""
TDCA D-2 NSFLUnionEngine · 数据模型与 schema 校验
锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL（FROZEN 待签批基线）+ fuse_engine.py FuseType 5 类
     + R-1 IIE 三层（T-021）+ CCP T6 FuseLevel（REV2.1）+ TDCA-TERMINOLOGY-REGISTRY V1.1
术语基线: 注册表 V1.1 + 防火墙 V1.0（禁用「V2.1」声称）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 基础枚举（锚定源）
# ---------------------------------------------------------------------------

class NSFuseType(Enum):
    """锚定 fuse_engine.FuseType 5 类（值对齐，本地定义避免跨项目 import）。"""
    ETHICAL = "ETHICAL"      # 情绪/共情/审美/信仰/道德（上位类）
    LEGAL = "LEGAL"          # 法律禁止 — 绝对熔断，无替代路径（ID86）
    EMOTIONAL = "EMOTIONAL"
    BELIEF = "BELIEF"
    TECHNICAL = "TECHNICAL"


class NSLayer(Enum):
    """IIE 分层（T-021）：与 T-023 制度坐标 L0-L3 为不同编号体系（schema 消歧注 2）。"""
    L0 = "L0"   # 制度层：完整 IIE，绝对熔断（ID86），无 alt_path，不可重置，enabled 恒 True
    L2 = "L2"   # 场景层：降级 IIE（T-021），RESTRICT 档位（T6），有处置路径
    L1 = "L1"   # 主体层：主体负空间（T-016）自律声明「我不会」——不构成 IIE，违约→信用降信


class Severity(Enum):
    HIGH = "HIGH"      # 完整 IIE（仅 fuse_type==LEGAL 可声明）
    MEDIUM = "MEDIUM"  # 降级 IIE（L2 场景型 RESTRICT）
    LOW = "LOW"        # 主体自律（L1，不构成 IIE）


class NS_Operator(Enum):
    ALLOW = "ALLOW"            # 允许（parameter 可选：允许域限定）
    FORBID = "FORBID"          # 禁止（parameter 可选：禁止对象限定）
    LIMIT_MAX = "LIMIT_MAX"    # 上限约束（取严=min）
    LIMIT_MIN = "LIMIT_MIN"    # 下限约束（取严=max）
    LIMIT_EQ = "LIMIT_EQ"      # 定值约束
    RESTRICT_TIER = "RESTRICT_TIER"  # 档位约束（parameter ∈ FuseLevel）


class FuseLevel(Enum):
    """对齐 CCP T6 4 级档位（REV2.1:216 enum FuseLevel）。"""
    OBSERVE = "OBSERVE"
    SUSPEND = "SUSPEND"
    TEARDOWN = "TEARDOWN"
    PERMANENT_BAN = "PERMANENT_BAN"


class Resolution(Enum):
    FORBID = "FORBID"                # 允许 vs 禁止 → 禁止
    TAKE_STRICTER = "TAKE_STRICTER"  # 数值约束 → 取严
    TIER_ESCALATE = "TIER_ESCALATE"  # 档位约束 → 取更高档位
    EMPTY_DOMAIN = "EMPTY_DOMAIN"    # 交集域为空 → 拒绝该域
    UNKNOWN = "UNKNOWN"              # 未列组合 → 上报人工复核


# ---------------------------------------------------------------------------
# NS_Type 枚举（schema §三，含 fuse_type/layer/severity_max 三元归属）
# ---------------------------------------------------------------------------

class NS_Type(Enum):
    # 制度层 L0（fuse_type=LEGAL，severity 恒 HIGH，alt_path 恒 None，enabled 恒 True）
    LEGAL = "LEGAL"                       # 法律禁止（ID85/ID86）
    # 场景层 L2（severity 上限 MEDIUM）
    DATA_CROSS_BORDER = "DATA_CROSS_BORDER"   # 数据跨境合规性（场景化声明；法律禁止须声明为 LEGAL）
    TRANSACTION_LIMIT = "TRANSACTION_LIMIT"   # 交易限额（含 unit）
    SENSITIVE_CONTENT = "SENSITIVE_CONTENT"   # 敏感内容（场景化声明）
    TECH_CONSTRAINT = "TECH_CONSTRAINT"       # 技术性约束
    # 主体层 L1（severity 上限 LOW）
    ETHICAL = "ETHICAL"                   # 道德/共情边界（注: 区别于 FuseType.ETHICAL 上位类）
    EMOTIONAL = "EMOTIONAL"               # 情绪边界
    BELIEF = "BELIEF"                     # 信仰/价值观边界

    @property
    def fuse_type(self) -> NSFuseType:
        """fuse_type==LEGAL 仅 LEGAL 一个值（schema REV 修正 S-02: 移除「LEGAL 派生」概念）。"""
        return {
            NS_Type.LEGAL: NSFuseType.LEGAL,
            NS_Type.DATA_CROSS_BORDER: NSFuseType.ETHICAL,   # 场景化声明（非 LEGAL！）
            NS_Type.TRANSACTION_LIMIT: NSFuseType.TECHNICAL,
            NS_Type.SENSITIVE_CONTENT: NSFuseType.ETHICAL,   # 场景化声明（非 LEGAL！）
            NS_Type.TECH_CONSTRAINT: NSFuseType.TECHNICAL,
            NS_Type.ETHICAL: NSFuseType.ETHICAL,
            NS_Type.EMOTIONAL: NSFuseType.EMOTIONAL,
            NS_Type.BELIEF: NSFuseType.BELIEF,
        }[self]

    @property
    def layer(self) -> NSLayer:
        return {
            NS_Type.LEGAL: NSLayer.L0,
            NS_Type.DATA_CROSS_BORDER: NSLayer.L2,
            NS_Type.TRANSACTION_LIMIT: NSLayer.L2,
            NS_Type.SENSITIVE_CONTENT: NSLayer.L2,
            NS_Type.TECH_CONSTRAINT: NSLayer.L2,
            NS_Type.ETHICAL: NSLayer.L1,
            NS_Type.EMOTIONAL: NSLayer.L1,
            NS_Type.BELIEF: NSLayer.L1,
        }[self]

    @property
    def severity_max(self) -> Severity:
        return {
            NS_Type.LEGAL: Severity.HIGH,
            NS_Type.DATA_CROSS_BORDER: Severity.MEDIUM,
            NS_Type.TRANSACTION_LIMIT: Severity.MEDIUM,
            NS_Type.SENSITIVE_CONTENT: Severity.MEDIUM,
            NS_Type.TECH_CONSTRAINT: Severity.MEDIUM,
            NS_Type.ETHICAL: Severity.LOW,
            NS_Type.EMOTIONAL: Severity.LOW,
            NS_Type.BELIEF: Severity.LOW,
        }[self]

    @property
    def severity_default(self) -> Severity:
        return self.severity_max


# ---------------------------------------------------------------------------
# 数据类（schema §四 NS_Rule / §五 Conflict）
# ---------------------------------------------------------------------------

def _coerce_decimal(value: Any) -> Optional[Decimal]:
    """LIMIT_* 参数: 有限正 Decimal；NaN/Inf/负数/非法 → 抛 ValueError（schema §四 S-07）。"""
    if value is None:
        return None
    if isinstance(value, FuseLevel):
        return None  # 档位参数不走数值校验
    try:
        d = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"parameter 非法数值: {value!r}")
    if not d.is_finite():
        raise ValueError(f"parameter 必须有限（NaN/Inf 拒绝）: {value!r}")
    if d < 0:
        raise ValueError(f"parameter 必须非负（负数拒绝，需定义语义）: {value!r}")
    return d


@dataclass(frozen=True)
class NS_Rule:
    """负空间规则（schema §四，VALIDATE_RULES 在 __post_init__ 执行）。"""
    rule_id: str
    ns_type: NS_Type
    operator: NS_Operator
    parameter: Optional[Any] = None     # Decimal（LIMIT_*）/ FuseLevel（RESTRICT_TIER）/ None
    unit: Optional[str] = None          # LIMIT_* 必填
    severity: Optional[Severity] = None  # 默认=ns_type.severity_default
    layer: Optional[NSLayer] = None      # 默认=ns_type.layer
    alt_path: Optional[str] = None
    source_ref: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        sev = self.severity or self.ns_type.severity_default
        lyr = self.layer or self.ns_type.layer
        ft = self.ns_type.fuse_type

        # 标识符安全（红队 #2 #6）: rule_id 长度 ≤64 且仅安全字符（防 NCA/审计日志注入）
        if (not self.rule_id or len(self.rule_id) > 64
                or not all(c.isalnum() or c in "_-" for c in self.rule_id)):
            raise ValueError(f"rule_id 非法: {self.rule_id!r}（长度 ≤64 且仅字母数字/_-）")
        # 非数值 parameter 类型白名单（红队 #2 #5）: ALLOW/FORBID 仅 str 域标签
        if self.operator in (NS_Operator.ALLOW, NS_Operator.FORBID) \
                and self.parameter is not None and not isinstance(self.parameter, str):
            raise ValueError(f"{self.operator.value} 的 parameter 仅允许 str 域标签，拒绝 {type(self.parameter).__name__}")

        # —— 制度底线（schema §四 VALIDATE_RULES）——
        if ft == NSFuseType.LEGAL:
            if self.operator != NS_Operator.FORBID:
                raise ValueError("LEGAL 规则 operator 仅限 FORBID（N5）")
            if sev != Severity.HIGH:
                raise ValueError("LEGAL 规则 severity 恒 HIGH，不可降级（S-01）")
            if self.alt_path is not None:
                raise ValueError("LEGAL 规则 alt_path 恒 None（ID86 绝对熔断）")
            if not self.enabled:
                raise ValueError("LEGAL 规则 enabled 恒 True，禁止翻转（S-03）")
        if lyr != self.ns_type.layer:
            raise ValueError(f"layer {lyr.value} 与 ns_type {self.ns_type.value} 的 layer {self.ns_type.layer.value} 不一致")
        if _severity_rank(sev) > _severity_rank(self.ns_type.severity_max):
            raise ValueError(f"severity {sev.value} 超过 {self.ns_type.value} 上限 {self.ns_type.severity_max.value}（S-06）")

        # —— 数值规范（S-07）——
        if self.operator in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN, NS_Operator.LIMIT_EQ):
            if self.parameter is None:
                raise ValueError(f"{self.operator.value} 必须提供 parameter")
            _coerce_decimal(self.parameter)
            if not self.unit:
                raise ValueError(f"{self.operator.value} 必须提供 unit")
        # —— 档位规范（S-08/S-12）——
        if self.operator == NS_Operator.RESTRICT_TIER:
            if not isinstance(self.parameter, FuseLevel):
                raise ValueError("RESTRICT_TIER 的 parameter 必须 ∈ FuseLevel（OBSERVE/SUSPEND/TEARDOWN/PERMANENT_BAN）")
            if self.parameter == FuseLevel.PERMANENT_BAN and self.alt_path is not None:
                raise ValueError("RESTRICT_TIER==PERMANENT_BAN → alt_path 强制 None（S-12）")

        object.__setattr__(self, "severity", sev)
        object.__setattr__(self, "layer", lyr)
        object.__setattr__(self, "parameter", _coerce_decimal(self.parameter)
                           if self.operator in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN, NS_Operator.LIMIT_EQ)
                           else self.parameter)

    @property
    def is_legal(self) -> bool:
        return self.ns_type.fuse_type == NSFuseType.LEGAL


def _severity_rank(s: Severity) -> int:
    return {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}[s]


# 同类型组规则比较硬上限（红队 #2 #1 延迟 DoS 防线）——超限直接上报 UNKNOWN，不做 O(n·m) 全笛卡尔
MAX_RULES_PER_TYPE = 100


@dataclass(frozen=True)
class Conflict:
    ns_type: NS_Type
    rule_a: NS_Rule
    rule_b: NS_Rule
    severity: Severity
    resolution: Resolution
    reason: str
    resolution_value: Optional[Any] = None   # 取严结果值（如 50 万）


@dataclass
class SceneNSFL:
    """场景负空间声明（任务书 §二 SceneNSFL）。"""
    scene_id: str
    nsfl_declaration: str = ""
    ns_types: List[NS_Type] = field(default_factory=list)
    rules: List[NS_Rule] = field(default_factory=list)

    def legal_rules(self) -> List[NS_Rule]:
        return [r for r in self.rules if r.is_legal]

    def has_legal_or_high_tier(self) -> bool:
        """含 LEGAL 或档位≥TEARDOWN（schema §5.1 兜底判定）。"""
        if self.legal_rules():
            return True
        return any(
            r.operator == NS_Operator.RESTRICT_TIER
            and r.parameter in (FuseLevel.TEARDOWN, FuseLevel.PERMANENT_BAN)
            for r in self.rules
        )


@dataclass(frozen=True)
class AltPathCandidate:
    """绕行场景候选（引擎内部计算结构；对外契约仅输出 scene_id 列表，schema §九 N4）。"""
    scene_c_id: str
    union_ac_conflicts: int
    union_cb_conflicts: int
    total_risk_premium: float
    rationale: str


@dataclass
class NegativeSpaceUnion:
    """输出（对齐 5CC MASTER NegativeSpaceUnion 契约 + schema §九）。"""
    scene_a: str
    scene_b: str
    union_set: List[NS_Type]
    conflict_set: List[Conflict]
    risk_premium: float
    recommended_alt_path: Optional[List[str]] = None
    computation_time_ms: float = 0.0
    nca_ref: str = ""
    review_queue: List[str] = field(default_factory=list)   # 审计面（schema §5.3/S-15），不进 MASTER 契约
    schema_version: str = "D2-NSFL-UNION-SCHEMA-001-V0.1-REV2-FINAL"
    decision_table_version: str = "dt-v1.0"
