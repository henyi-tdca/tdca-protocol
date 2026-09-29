# -*- coding: utf-8 -*-
"""
C2 · ⊗⊘⊙ 运算符执行语义（Operator Semantics）
=============================================
将运算符与 NS_Type 组合翻译为「熔断级指令」（Fuse-Level Directive）——
对齐 CCP T6 4 级档位（OBSERVE/SUSPEND/TEARDOWN/PERMANENT_BAN，REV2.1:216）
与 D-2 schema NS_Operator（FORBID/LIMIT_*/RESTRICT_TIER）。

运算符语义:
  ⊗ FORBID  → 绝对禁止（LEGAL 型 = 熔断级 PERMANENT_BAN + alt_path=None，ID86）
  ⊘ LIMIT   → 条件限制（数值上限/下限/定值，对齐 LIMIT_MAX/MIN/EQ）
  ⊙ SCENE   → 场景化约束（档位约束 RESTRICT_TIER + 域标签）

分级熔断（NSFL-ACCEL-REF-001 §3.3.1 Trigger-Block 分级 Soft/Hard/Atomic 采纳）:
  Soft  → OBSERVE/SUSPEND（可恢复，有处置路径）
  Hard  → TEARDOWN（终止执行，需人工复核）
  Atomic→ PERMANENT_BAN（永久冻结，LEGAL 专属，不可重置）

锚定: TDCA-NSFL-COMPILER-001 立项方案 C2 + DCD-NSFL-COMPILER-001
     + D2-NSFL-UNION-SCHEMA-001（NS_Operator/FuseLevel/NS_Type 三元归属）
     + CCP T6 FuseLevel + fuse_engine FuseType.LEGAL（ID86）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FuseLevel(Enum):
    """对齐 CCP T6 4 级档位（D-2 schema FuseLevel）。"""
    OBSERVE = "OBSERVE"
    SUSPEND = "SUSPEND"
    TEARDOWN = "TEARDOWN"
    PERMANENT_BAN = "PERMANENT_BAN"


class FuseTier(Enum):
    """分级熔断（Soft/Hard/Atomic）——NSFL-ACCEL-REF-001 §3.3.1。"""
    SOFT = "SOFT"          # 可恢复：OBSERVE/SUSPEND，有处置路径
    HARD = "HARD"          # 终止：TEARDOWN，需人工复核
    ATOMIC = "ATOMIC"      # 永久：PERMANENT_BAN，LEGAL 专属，不可重置


class NS_Operator(Enum):
    """对齐 D-2 schema NS_Operator（C2 输出算子）。"""
    ALLOW = "ALLOW"
    FORBID = "FORBID"
    LIMIT_MAX = "LIMIT_MAX"
    LIMIT_MIN = "LIMIT_MIN"
    LIMIT_EQ = "LIMIT_EQ"
    RESTRICT_TIER = "RESTRICT_TIER"


@dataclass(frozen=True)
class FuseDirective:
    """熔断级指令（C2 语义输出）。"""
    operator: NS_Operator          # 输出算子
    fuse_level: FuseLevel          # CCP T6 档位
    tier: FuseTier                 # 分级熔断档
    alt_path: Optional[str] = None  # LEGAL 强制 None（ID86）
    parameter: Optional[str] = None
    domain: Optional[str] = None    # ⊙ 场景域标签

    def to_dict(self) -> dict:
        return {
            "operator": self.operator.value,
            "fuse_level": self.fuse_level.value,
            "tier": self.tier.value,
            "alt_path": self.alt_path,
            "parameter": self.parameter,
            "domain": self.domain,
        }


# ⊗ 绝对禁止 → 档位按 NS_Type 推导（LEGAL → PERMANENT_BAN/ATOMIC；其余 → TEARDOWN/HARD）
_FORBID_LEVEL: dict = {
    "LEGAL": (FuseLevel.PERMANENT_BAN, FuseTier.ATOMIC),
    "DATA_CROSS_BORDER": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "TRANSACTION_LIMIT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "SENSITIVE_CONTENT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "TECH_CONSTRAINT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "ETHICAL": (FuseLevel.SUSPEND, FuseTier.SOFT),
    "EMOTIONAL": (FuseLevel.SUSPEND, FuseTier.SOFT),
    "BELIEF": (FuseLevel.SUSPEND, FuseTier.SOFT),
}

# ⊘ LIMIT 参数前缀 → 算子（| max:100 → LIMIT_MAX；| min:0 → LIMIT_MIN；| eq:5 → LIMIT_EQ）
_LIMIT_PREFIX_TO_OP = {
    "max": NS_Operator.LIMIT_MAX,
    "min": NS_Operator.LIMIT_MIN,
    "eq": NS_Operator.LIMIT_EQ,
}

# ⊙ SCENE 档位标签 → FuseLevel（场景化约束降级档位，对齐 CCP T6）
_SCENE_LEVEL = {
    "observe": FuseLevel.OBSERVE,
    "suspend": FuseLevel.SUSPEND,
    "teardown": FuseLevel.TEARDOWN,
}


class NSFLOperatorSemantics:
    """⊗⊘⊙ 执行语义解释器（纯函数，无副作用——BV-3 只读）。"""

    @classmethod
    def resolve(cls, ns_type: str, operator: str,
                parameter: Optional[str] = None) -> FuseDirective:
        """AST 运算符/类型 → 熔断级指令。"""
        if operator == "⊗":
            level, tier = _FORBID_LEVEL[ns_type]
            alt_path = None if ns_type == "LEGAL" else None  # 绝对禁止一律无 alt_path（对齐 fuse_engine alt=∅ 语义）
            return FuseDirective(
                operator=NS_Operator.FORBID,
                fuse_level=level,
                tier=tier,
                alt_path=alt_path,
                parameter=None,
            )

        if operator == "⊘":
            op, value = cls._parse_limit(parameter)
            return FuseDirective(
                operator=op,
                fuse_level=FuseLevel.OBSERVE,   # 数值限制默认观察档（L2 降级 IIE，有处置路径）
                tier=FuseTier.SOFT,
                alt_path=None,
                parameter=value,
            )

        if operator == "⊙":
            domain, level = cls._parse_scene(parameter)
            return FuseDirective(
                operator=NS_Operator.RESTRICT_TIER,
                fuse_level=level,
                tier=FuseTier.HARD,
                alt_path=None,
                parameter=parameter,
                domain=domain,
            )

        raise ValueError(f"未知运算符: {operator!r}")

    # ---- 解析器 ----

    @classmethod
    def _parse_limit(cls, parameter: Optional[str]) -> tuple:
        if not parameter:
            raise ValueError("⊘ LIMIT 语义缺 parameter")
        # 支持 "max:100" / "min:0" / "eq:5" 前缀形式
        if ":" in parameter:
            prefix, value = parameter.split(":", 1)
            op = _LIMIT_PREFIX_TO_OP.get(prefix.strip().lower())
            if op is None:
                raise ValueError(f"⊘ LIMIT 未知约束前缀: {prefix!r}（允许 max/min/eq）")
            return op, value.strip()
        # 无前缀 → 视为上限（LIMIT_MAX，默认语义）
        return NS_Operator.LIMIT_MAX, parameter.strip()

    @classmethod
    def _parse_scene(cls, parameter: Optional[str]) -> tuple:
        if not parameter:
            raise ValueError("⊙ SCENE 语义缺 parameter")
        # 支持 "domain@tier" 或 "domain:tier" 或纯 domain（默认 SUSPEND）
        for sep in ("@", ":"):
            if sep in parameter:
                domain, tier_txt = parameter.rsplit(sep, 1)
                level = _SCENE_LEVEL.get(tier_txt.strip().lower())
                if level is None:
                    raise ValueError(f"⊙ SCENE 未知档位: {tier_txt!r}（允许 observe/suspend/teardown）")
                return domain.strip(), level
        return parameter.strip(), FuseLevel.SUSPEND
