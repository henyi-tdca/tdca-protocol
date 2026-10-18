"""merchant_loop · ROI 三情景仪表盘（悲观/中性/乐观——预算平移对照，剔除资产升值因子）

A-3 验收: 三情景测算与 DCA 框架对照一致（无资产升值因子）。

方法论（TDCA-REVIEW-DCA-LEGACY-001 剥壳取核）:
  ROI = 预算平移后的增量价值 / 平移预算
  增量价值 = 核销带来的净利贡献（核销率 × 客单价 × 毛利率 × 复购系数）− 让利成本
  全部参数 SIMULATED（ID92）——悲观/中性/乐观为参数区间，非预测保证。
  **剔除资产升值因子**：本模型无任何「资产价格/转让收益/倍数回报」项——ROI 只反映消费转化效率。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# 三情景参数（SIMULATED 候选——真实商户数据接入后以实测回填，不冒充定标）
# uplift = 核销毛利中可归因于本次权益活动的增量比例（增量归因系数，谨慎口径）
DEFAULT_SCENARIOS: Dict[str, Dict[str, float]] = {
    "pessimistic": {"redemption_rate": 0.15, "gross_margin": 0.30, "repeat_factor": 1.0, "uplift": 0.50},
    "neutral":     {"redemption_rate": 0.30, "gross_margin": 0.35, "repeat_factor": 1.2, "uplift": 0.70},
    "optimistic":  {"redemption_rate": 0.45, "gross_margin": 0.40, "repeat_factor": 1.5, "uplift": 0.90},
}


@dataclass(frozen=True)
class RoiScenarioResult:
    """单情景 ROI 测算结果。"""
    scenario: str
    redemption_rate: float
    expected_redemptions: float
    redemption_value: float            # 核销产生的消费额
    gross_profit: float                # 毛利贡献
    allowance_cost: float              # 让利成本（discount + rebate）
    net_value: float                   # 增量价值 = gross_profit×uplift − allowance_cost
    budget_ceiling: float              # 平移预算（≤历史预算）
    roi: float                         # net_value / budget_ceiling（budget>0 时）
    no_asset_appreciation: bool = True

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "redemption_rate": self.redemption_rate,
            "expected_redemptions": round(self.expected_redemptions, 2),
            "redemption_value": round(self.redemption_value, 4),
            "gross_profit": round(self.gross_profit, 4),
            "allowance_cost": round(self.allowance_cost, 4),
            "net_value": round(self.net_value, 4),
            "budget_ceiling": round(self.budget_ceiling, 4),
            "roi": round(self.roi, 4),
            "no_asset_appreciation": self.no_asset_appreciation,
            "note": "SIMULATED 参数测算——不含资产升值因子，仅消费转化效率（ID92）",
        }


@dataclass(frozen=True)
class RoiReport:
    """ROI 仪表盘（三情景汇总 + 预算平移对照）。"""
    benefit_id: str
    merchant_id: str
    budget_ceiling: float
    target_audience: float             # 权益触达人数（SIMULATED）
    scenarios: Dict[str, RoiScenarioResult]
    provenance: str = "SIMULATED"

    def to_dict(self) -> dict:
        return {
            "report_type": "merchant_loop_roi",
            "schema_version": "1.0",
            "benefit_id": self.benefit_id,
            "merchant_id": self.merchant_id,
            "budget_ceiling": round(self.budget_ceiling, 4),
            "budget_shift_note": "预算平移：费用 ≤ 历史广告/折扣/佣金预算——非新增投入",
            "target_audience": round(self.target_audience, 2),
            "scenarios": {k: v.to_dict() for k, v in self.scenarios.items()},
            "provenance": self.provenance,
            "disclaimer": "三情景为 SIMULATED 参数区间测算（ID92）；真实 ROI 以核销流水实测回填——非收益承诺",
            "no_asset_appreciation": True,
        }


class RoiService:
    """ROI 三情景测算引擎（A-3）。"""

    def __init__(self, default_provenance: str = "SIMULATED"):
        self._provenance = default_provenance

    def build_report(self, benefit_id: str, merchant_id: str,
                     budget_ceiling: float, target_audience: float,
                     expected_discount_rate: float, expected_rebate_rate: float,
                     scenarios: Optional[Dict[str, Dict[str, float]]] = None,
                     provenance: Optional[str] = None) -> RoiReport:
        """三情景 ROI 测算。

        参数:
          budget_ceiling  平移预算（≤历史预算）
          target_audience 权益触达人数（SIMULATED）
          expected_discount_rate / expected_rebate_rate  平均让利深度（对消费额的比例）
        """
        if budget_ceiling <= 0:
            raise ValueError("[NSFL-TRIGGER] budget_ceiling 须 >0（预算平移基座）")
        if target_audience <= 0:
            raise ValueError("[NSFL-TRIGGER] target_audience 须 >0")
        if not (0 <= expected_discount_rate < 1) or not (0 <= expected_rebate_rate < 1):
            raise ValueError("[NSFL-TRIGGER] 让利深度须在 [0,1)")

        allowance_rate = expected_discount_rate + expected_rebate_rate
        param_set = scenarios or DEFAULT_SCENARIOS
        results: Dict[str, RoiScenarioResult] = {}
        for name, p in param_set.items():
            redemption_rate = float(p["redemption_rate"])
            margin = float(p["gross_margin"])
            repeat = float(p["repeat_factor"])
            uplift = float(p["uplift"])
            expected = target_audience * redemption_rate * repeat
            redemption_value = expected * 100.0    # 客单价 100（SIMULATED 占位——真实客单接入后替换）
            gross_profit = redemption_value * margin
            allowance_cost = redemption_value * allowance_rate
            net_value = gross_profit * uplift - allowance_cost
            roi = net_value / budget_ceiling
            results[name] = RoiScenarioResult(
                scenario=name,
                redemption_rate=redemption_rate,
                expected_redemptions=expected,
                redemption_value=redemption_value,
                gross_profit=gross_profit,
                allowance_cost=allowance_cost,
                net_value=net_value,
                budget_ceiling=budget_ceiling,
                roi=roi,
            )
        return RoiReport(
            benefit_id=benefit_id,
            merchant_id=merchant_id,
            budget_ceiling=budget_ceiling,
            target_audience=target_audience,
            scenarios=results,
            provenance=provenance or self._provenance,
        )
