"""DVP 定向条件支付模拟（T-035 · R-CLS-1 SETTLED 步）

数字人民币条件支付模拟态（D-011 参数）：
条件 = C_MOU(>0) ∧ C_delivery(验收) ∧ C_dpi(DPI 校验) —— 支付=结算+纳税同刻（票款同步 T-038）
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from .dpi import DPI, State


@dataclass
class DVPResult:
    tx_id: str
    state: State
    message: str
    tax: float = 0.0     # 同刻计税（占位：E-2 接 MICROTAX tax_calculator）


class DVPExecutor:
    """DVP 定向条件支付执行器（T-035 模拟）"""

    def __init__(self, mou_threshold: float = 0.0):
        self.mou_threshold = mou_threshold

    def conditional_pay(self, tx_id: str, dpi: DPI, env: Dict[str, bool]) -> DVPResult:
        """条件支付: C_MOU ∧ C_delivery ∧ C_dpi 全真 → SETTLED；否则 HELD"""
        conditions = {
            "C_MOU": env.get("mou", 0.0) > self.mou_threshold,      # MOU>0 硬验证（ID79）
            "C_delivery": env.get("delivery", False),               # 交付验收
            "C_dpi": dpi.check(),                                   # DPI 校验（定向+金额+条件）
        }
        ok = all(conditions.values())
        # 同刻计税（票款同步）：税率占位（E-2 接 tax_calculator 真实计税）
        tax = round(dpi.amount * env.get("tax_rate", 0.02), 6) if ok else 0.0
        if ok:
            return DVPResult(tx_id, State.SETTLED, f"SETTLED: 定向支付 {dpi.payer}→{dpi.payee} {dpi.amount}（同刻计税 {tax}）", tax)
        failed = [k for k, v in conditions.items() if not v]
        return DVPResult(tx_id, State.HELD, f"HELD: 条件不满足 {failed}", 0.0)
