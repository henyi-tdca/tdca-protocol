# -*- coding: utf-8 -*-
"""
W5 · MOU 分割 escrow 验证（Shapley 预计算 → CBDC 锁定 → escrow 释放全链路）
锚定: TDCA-PLAN-5CC-PHASE-C §六（W5: MOU 分割模拟态落地）+ CCP T3 shapleyAllocate（偏差 <1%）
     + CCP T4 escrow（escrowRefund M-4）+ W4 MOUSplitContract（前置交付）
链路: D-2 RiskPremium → CSCP Step-3 定价 → Step-4 CBDC lock（Shapley 分割 escrow）→ escrowRefund
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from typing import Dict, List, Optional

from translator_market.mou_split import MOUSplitContract, default_mou_value_fn


class MOUEscrowVerifier:
    """MOU 分割 escrow 验证器：Shapley 预计算分割比例 + escrow 金额完整性验证。"""

    def __init__(self, splitter: Optional[MOUSplitContract] = None):
        self._splitter = splitter or MOUSplitContract()

    def compute_split(self, scene_ids: List[str],
                      contributions: Dict[str, float]) -> Dict[str, float]:
        """Shapley 分割（按贡献 + 协同正和），输出各场景比例（Σ=1）。"""
        fn = default_mou_value_fn(contributions)
        raw = self._splitter.split(scene_ids, fn)
        total = sum(raw.values())
        if total <= 0:
            raise ValueError("Shapley 总值必须 > 0")
        return {s: round(v / total, 6) for s, v in raw.items()}

    def verify_escrow(self, escrow_total: float, split: Dict[str, float],
                      budget: float) -> Dict[str, object]:
        """escrow 完整性验证：Σ(ratio × budget) = escrow_total（零漂移）。"""
        expected = round(sum(r * budget for r in split.values()), 4)
        allocated = {s: round(r * budget, 4) for s, r in split.items()}
        ok = abs(expected - round(escrow_total, 4)) < 1e-6
        return {"verified": ok, "escrow_total": round(escrow_total, 4),
                "expected_total": expected, "allocated": allocated,
                "delta": round(expected - round(escrow_total, 4), 6)}
