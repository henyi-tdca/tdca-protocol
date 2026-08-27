"""正和博弈验证（效用精灵的轻量实现，ID24/正和验证）。

规则：调用产生的效用 - 成本 > 0 即正和放行；效用归零或为负 → 拒绝。
"""

from dataclasses import dataclass
from typing import Dict, Optional

# 场景权重（单一场景效用函数基值）
_SCENARIO_BASE = {
    "default": 1.0,
    "code-analysis": 1.2,
    "security": 1.5,
    "ops": 1.1,
    "research": 1.0,
}


@dataclass
class PositiveSumResult:
    surplus: float
    passed: bool
    detail: Dict


class PositiveSumValidator:
    """正和验证器：surplus = utility - cost > 0 → pass。"""

    def validate(
        self,
        utility_weight: float,
        cost: float,
        scenario: str = "default",
        confidence: float = 1.0,
    ) -> PositiveSumResult:
        base = _SCENARIO_BASE.get(scenario, 1.0)
        utility = utility_weight * base * confidence
        surplus = round(utility - cost, 6)
        return PositiveSumResult(
            surplus=surplus,
            passed=surplus > 0,
            detail={
                "utility_weight": utility_weight,
                "cost": cost,
                "scenario_base": base,
                "confidence": confidence,
                "utility": utility,
                "surplus": surplus,
            },
        )

    def validate_zero_utility(self) -> PositiveSumResult:
        """效用归零场景（MOU 归零原则：T(y_t)<=0 → 自动归零）。"""
        return PositiveSumResult(
            surplus=0.0, passed=False,
            detail={"reason": "utility-zeroed", "principle": "TDCA-PRINCIPLE-MOU-001"},
        )
