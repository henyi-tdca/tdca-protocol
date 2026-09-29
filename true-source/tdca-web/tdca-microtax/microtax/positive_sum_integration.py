# -*- coding: utf-8 -*-
"""M-3 正和满意解税后集成：税后净额 → Shapley 分配 → MOU 归零验证。

链路（任务书 §一）: 微交付完成 → 实时计税 → 税收预缴（合约托管）→ 正和满意解（税后）→ MOU 归零 → NCA

制度锚定:
  - ID79（MOU 不可降）: 税后结算前置=已预缴（税款不得绕过预缴）；T(y_t) > 0 恒成立（A-4）
  - A-3 税后一致性: 税后分配总额 = 税前 − 税款（Shapley 效率性保持）
  - ID90 最小化合: 复用 MOUSplitContract（Shapley 数学，同 mou_escrow 先例），不新建平行体系
  - ID77/ID84: 正和性判定（协同价值 synergy 下的 Shapley 分配）
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .models import MicroDelivery

# 复用 Shapley 分割基座（顶层导入惯例；conftest 注入 translator-market 父路径）
try:
    from translator_market.mou_split import MOUSplitContract, default_mou_value_fn  # type: ignore
except ImportError:  # pragma: no cover - 运行时兜底
    from ._fallback_split import MOUSplitContract, default_mou_value_fn  # type: ignore

PREPAID_OK = ("PREPAID", "VERIFIED")


class TaxAfterPositiveSumSettlement:
    """M-3 正和满意解税后集成。

    settle(delivery, contributions):
      1. 前置检查: 已计税 + 已预缴（ID79——税款不得绕过预缴）
      2. MOU 归零验证（A-4）: T(y_t) > 0
      3. Shapley 比例（default_mou_value_fn，协同价值 synergy）
      4. 税后分配: ratio × net_value（税后净额参与分配）
      5. 税后一致性验证（A-3）: Σ分配 = net_value = value − total
    """

    def __init__(self, splitter: Optional[MOUSplitContract] = None, synergy: float = 1.2):
        self._splitter = splitter or MOUSplitContract()
        self.synergy = synergy

    def settle(self, delivery: MicroDelivery,
               contributions: Optional[Dict[str, float]] = None) -> dict:
        """税后正和结算。

        :param delivery: 微交付实体（须已计税 + 已预缴）
        :param contributions: 参与方贡献 {agent_id: contribution}（默认取 delivery.participants）
        :raises ValueError: 未计税/未预缴/计税额非正（ID79）
        """
        # 1. 前置: 已计税（MOU 不可降）
        if not delivery.taxes:
            raise ValueError("[NSFL-TRIGGER] 微交付未计税，禁止税后结算（ID79）")
        total_tax = float(delivery.taxes.get("total", 0.0))

        # 2. 前置: 已预缴（税款不得绕过预缴，ID79）
        if delivery.prepay_status not in PREPAID_OK:
            raise ValueError(
                f"[NSFL-TRIGGER] 微交付未预缴（status={delivery.prepay_status}），"
                "税款不得绕过预缴（ID79）")

        # 3. MOU 归零验证（A-4）: T(y_t) > 0 恒成立
        if total_tax <= 0:
            raise ValueError("[NSFL-TRIGGER] 计税额 T(y_t) <= 0，MOU 归零（ID79）")

        contrib = contributions or delivery.participants
        if not contrib:
            raise ValueError("[NSFL-TRIGGER] 无参与方贡献，无法进行正和分配")

        agent_ids = list(contrib.keys())
        net_value = delivery.net_value

        # 4. Shapley 比例（协同正和价值函数）
        fn = default_mou_value_fn(contrib, synergy=self.synergy)
        raw = self._splitter.split(agent_ids, fn)
        total_share = sum(raw.values())
        if total_share <= 0:
            raise ValueError("[NSFL-TRIGGER] Shapley 总值必须 > 0")
        ratios = {a: v / total_share for a, v in raw.items()}

        # 5. 税后分配（税后净额参与分配）
        allocations = {a: round(r * net_value, 2) for a, r in ratios.items()}

        # 6. A-3 税后一致性验证: Σ分配 = net_value = value − total_tax
        allocated_sum = round(sum(allocations.values()), 2)
        expected_net = round(delivery.value - total_tax, 2)
        consistency_ok = (abs(allocated_sum - expected_net) < 1e-6) and \
            (abs(allocated_sum - net_value) < 1e-6)

        return {
            "delivery_id": delivery.delivery_id,
            "gross_value": delivery.value,
            "taxes": delivery.taxes,
            "tax_total": total_tax,
            "net_value": net_value,
            "allocations": allocations,
            "allocated_sum": allocated_sum,
            "expected_net": expected_net,
            "consistency_ok": consistency_ok,          # A-3 税后一致
            "mou_anchor_ok": delivery.mou_anchor_ok,   # A-4 MOU 归零（T(y_t)>0）
            "synergy": self.synergy,
            "simulated": delivery.simulated,           # ID92 模拟态标注
        }

    def settle_and_verify(self, delivery: MicroDelivery,
                          contributions: Optional[Dict[str, float]] = None) -> dict:
        """结算 + 全量验证（A-3 一致 / A-4 归零），不合格抛错（NSFL-TRIGGER）。"""
        result = self.settle(delivery, contributions)
        if not result["consistency_ok"]:
            raise ValueError(
                f"[NSFL-TRIGGER] 税后一致性失败: Σ分配 {result['allocated_sum']} "
                f"≠ 税后净额 {result['expected_net']}（A-3）")
        if not result["mou_anchor_ok"]:
            raise ValueError("[NSFL-TRIGGER] MOU 归零验证失败: T(y_t) <= 0（A-4）")
        return result
