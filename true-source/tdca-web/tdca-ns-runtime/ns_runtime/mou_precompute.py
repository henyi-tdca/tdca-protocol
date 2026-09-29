# -*- coding: utf-8 -*-
"""
L1-R3 · MOU 预计算拦截器（MOU Precompute Interceptor）
======================================================
Agent 行为若无法在预计算阶段映射到 T(y_t)>0 的税收锚定 → 自动阻断。
覆盖目标: 经济负空间 100%（A-1）。

设计:
  - MOU 锚定表: 行为类别 → 税收函数 T(y_t)（预计算映射，模拟态参数）
  - 判定: 行为可映射到 T(y_t)>0 的锚定类别 → ALLOWED（进入税收轨道）
  - 无法映射（经济负空间）→ BLOCKED + 上报慢系统（人类裁决，MOU 不可降）
  - 映射表构建后冻结（BV-3；升级经人类裁决 F-4）

锚定: DCD-NS-RUNTIME-001（L1-R3）+ TDCA-NS-RUNTIME-001（经济负空间 100%）
     + NSFL-ACCEL-REF-001 §3.1（T(y_t)>0 税收锚定）
     + 红线「MOU 不可降」（每层有 MOU 验证点）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class MOUAnchor:
    """MOU 税收锚定条目（预计算映射）。"""
    anchor_id: str          # 锚定编号（MOU-ANCHOR-001 ...）
    behavior_domain: str    # 行为域（transaction / collaboration / ...）
    tax_rate: float         # T(y_t) 税率参数（>0 即进入税收轨道）
    remark: str = ""

    @property
    def anchored(self) -> bool:
        """T(y_t) > 0 → 有税收锚定。"""
        return self.tax_rate > 0


@dataclass(frozen=True)
class MOUPrecomputeResult:
    """预计算判定结果。"""
    blocked: bool
    anchor: Optional[MOUAnchor] = None
    reason: str = ""
    escalate_slow: bool = False   # 无法映射 → 上报慢系统（人类裁决）

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "anchor": self.anchor.anchor_id if self.anchor else None,
            "reason": self.reason,
            "escalate_slow": self.escalate_slow,
        }


class MOUPrecomputeInterceptor:
    """MOU 预计算拦截器（映射表不可变）。"""

    # 经济负空间：无税收锚定的行为类别（模拟态全集 V2.0）
    _NEGATIVE_BEHAVIORS: Tuple[str, ...] = (
        "tax_evasion",       # 逃税
        "money_laundering",  # 洗钱
        "shadow_deal",       # 影子交易（无锚定记录）
        "unrecorded_value",  # 未记账价值转移
        "off_chain_settle",  # 链下结算（逃锚定）
    )

    _CANONICAL_ANCHORS: Tuple[Tuple[str, str, float, str], ...] = (
        ("MOU-ANCHOR-001", "transaction", 0.02, "交易类行为税收锚定"),
        ("MOU-ANCHOR-002", "collaboration", 0.015, "协作类行为税收锚定"),
        ("MOU-ANCHOR-003", "cross_border", 0.03, "跨境行为税收锚定"),
        ("MOU-ANCHOR-004", "data_usage", 0.01, "数据使用税收锚定"),
    )

    def __init__(self, anchors: Optional[List[MOUAnchor]] = None):
        if anchors is None:
            anchors = [
                MOUAnchor(anchor_id=aid, behavior_domain=dom, tax_rate=rate, remark=rmk)
                for aid, dom, rate, rmk in self._CANONICAL_ANCHORS
            ]
        self._anchors: FrozenSet[MOUAnchor] = frozenset(anchors)
        self._locked = True

    @property
    def anchors(self) -> FrozenSet[MOUAnchor]:
        return self._anchors

    def check(self, behavior_domain: str, value: float = 0.0) -> MOUPrecomputeResult:
        """预计算: 行为域 → MOU 锚定映射。无法映射（负空间）→ 阻断 + 上报慢系统。"""
        dom = behavior_domain.lower().strip()
        if not dom:
            return MOUPrecomputeResult(
                blocked=True, escalate_slow=True,
                reason="空行为域无法映射税收锚定（经济负空间 fail-closed）",
            )
        # 显式经济负空间行为
        if dom in self._NEGATIVE_BEHAVIORS:
            return MOUPrecomputeResult(
                blocked=True, escalate_slow=True,
                reason=f"行为域 {dom!r} 属于经济负空间（无税收锚定）",
            )
        # 正锚定映射
        for anchor in self._anchors:
            if anchor.behavior_domain == dom:
                if anchor.anchored:
                    return MOUPrecomputeResult(
                        blocked=False, anchor=anchor,
                        reason=f"映射到 MOU 锚定 {anchor.anchor_id}（T(y_t)={anchor.tax_rate}>0）",
                    )
                return MOUPrecomputeResult(
                    blocked=True, escalate_slow=True,
                    reason=f"锚定 {anchor.anchor_id} T(y_t)<=0（MOU 不可降）",
                )
        # 未知域: fail-closed → 上报慢系统（人类裁决，防负空间逃逸）
        return MOUPrecomputeResult(
            blocked=True, escalate_slow=True,
            reason=f"行为域 {dom!r} 无预计算 MOU 映射（经济负空间候选，需人类裁决）",
        )

    def mutate(self, *args, **kwargs):  # pragma: no cover - 防御性
        raise PermissionError("MOU 锚定表不可变（BV-3；MOU 不可降红线）")

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"MOU 锚定表不可变（{name}）")
        super().__setattr__(name, value)
