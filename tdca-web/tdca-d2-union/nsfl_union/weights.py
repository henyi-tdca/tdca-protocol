# -*- coding: utf-8 -*-
"""
TDCA D-2 NSFLUnionEngine · risk_premium 权重表（模拟态 V1，抗稀释）
锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL §六（S̄ 最高严重度保护 + n_eff 分层封顶 + M 档位映射
     + 无冲突特例 M + LEGAL 恒 1.0 + R-2 熔断仅由 conflict_set 驱动）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from typing import List, Optional

from .schema import Conflict, FuseLevel, NSLayer, NS_Type, Severity, _severity_rank


class RiskPremiumCalculator:
    """模拟态权重表 V1（交付物）。待 D-010 法学家数据集校准（S-CSCP-002 偏差 <30%）。"""

    W_S = 0.5   # 最高严重度权重
    W_N = 0.3   # 冲突数（分层饱和度）权重
    W_M = 0.2   # 市场权重

    SEVERITY_SCORE = {
        Severity.HIGH: 1.0,
        Severity.MEDIUM: 0.6,
        Severity.LOW: 0.3,
    }
    TIER_SCORE = {
        FuseLevel.OBSERVE: 0.2,
        FuseLevel.SUSPEND: 0.5,
        FuseLevel.TEARDOWN: 0.8,
        FuseLevel.PERMANENT_BAN: 1.0,
    }
    # 分层计数封顶（S-10 抗稀释）: LOW 洪水不压低 HIGH
    LAYER_CAPS = {Severity.HIGH: 5, Severity.MEDIUM: 10, Severity.LOW: 20}
    LAYER_WEIGHT = {Severity.HIGH: 0.5, Severity.MEDIUM: 0.3, Severity.LOW: 0.2}

    def compute(self, conflict_set: List[Conflict],
                tier_a: Optional[FuseLevel] = None,
                tier_b: Optional[FuseLevel] = None) -> float:
        """risk_premium ∈ [0,1]。熔断语义由 conflict_set 驱动（R-2），权重仅定价。"""
        # LEGAL 冲突 → 恒 1.0（熔断语义）
        if any(c.severity == Severity.HIGH for c in conflict_set):
            return 1.0
        # 无冲突 → 仅市场权重（特例分支，REV2 统一 N1）
        if not conflict_set:
            return self._market_score(tier_a, tier_b)

        s_bar = self._highest_severity_score(conflict_set)          # 最高严重度保护（非均值）
        n_eff = self._layered_saturation(conflict_set)              # 分层饱和度 [0,1]
        m = self._market_score(tier_a, tier_b)
        premium = self.W_S * s_bar + self.W_N * n_eff + self.W_M * m
        return round(min(1.0, premium), 4)

    # ---- 内部 ----

    def _highest_severity_score(self, conflicts: List[Conflict]) -> float:
        """S̄ = 最高严重度档（S-10: 防 LOW 洪水稀释 HIGH）。"""
        top = max(conflicts, key=lambda c: _severity_rank(c.severity)).severity
        return self.SEVERITY_SCORE[top]

    def _layered_saturation(self, conflicts: List[Conflict]) -> float:
        """n_eff = Σ 层饱和度 × 层权重（分层封顶 HIGH 5 / MEDIUM 10 / LOW 20）。"""
        counts = {Severity.HIGH: 0, Severity.MEDIUM: 0, Severity.LOW: 0}
        for c in conflicts:
            counts[c.severity] += 1
        total = 0.0
        for sev, cap in self.LAYER_CAPS.items():
            sat = min(1.0, counts[sev] / cap)
            total += sat * self.LAYER_WEIGHT[sev]
        return total

    def _market_score(self, tier_a: Optional[FuseLevel], tier_b: Optional[FuseLevel]) -> float:
        """M = 两侧档位较严者映射（模拟态静态值）。缺省 OBSERVE。"""
        scores = [self.TIER_SCORE[t] for t in (tier_a, tier_b) if t is not None]
        if not scores:
            return self.TIER_SCORE[FuseLevel.OBSERVE]
        return max(scores)
