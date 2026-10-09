"""util_value · 入表评估报告生成（A-3）

结构化评估报告（机器可读，供会计入表引用）：
  地板值 + 五阶分层 + 七要素分解 + 安全熔断 + 存证锚点。
"""
from __future__ import annotations

from typing import Dict, Optional

from .engine import (
    ObservableFloor,
    TierAssessment,
    ValuationSafety,
)


def build_assessment_report(floor: ObservableFloor,
                            tiers: Optional[TierAssessment] = None,
                            safety: Optional[ValuationSafety] = None,
                            seven_elements: Optional[dict] = None,
                            report_id: str = "",
                            basis: str = "TDCA-UTILITY-OBSERVABLE-001") -> dict:
    """入表评估报告（A-3：地板值/分层/依据/存证）。"""
    payload: dict = {
        "report_id": report_id,
        "report_type": "util_value_assessment",
        "schema_version": "1.0",
        "basis": basis,
        "floor": floor.to_dict(),
        "provenance": floor.provenance,
    }
    if tiers is not None:
        payload["tiers"] = tiers.to_dict()
    if safety is not None:
        payload["safety"] = safety.to_dict()
    if seven_elements is not None:
        payload["seven_elements"] = seven_elements
    return payload
