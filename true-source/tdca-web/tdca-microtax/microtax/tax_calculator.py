# -*- coding: utf-8 -*-
"""M-1 微交付计税器：交付计量 → T(y_t) 分项金额（调度税/版税/交易费 + 合计）。

对齐 CALL-RULES TaxRates 默认值（2% / 7.5% / 0.75%，模拟态 D-011），
补齐 CALL-RULES compute_taxes 缺失的 trade_fee 分项（缺口 3），
形成完整 T(y_t) 金额推导供 M-2 预缴 / M-3 正和税后集成使用。

制度锚定: ID79（MOU 硬锚定 T(y_t)>0）/ ID90（复用 TaxRates，不新建税率）
         / ID71（快系统：单次计税 <10ms）/ ID92（模拟态标注）
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from .models import MicroDelivery

# 复用 CALL-RULES TaxRates（顶层导入惯例；sys.path 注入见 tests/conftest.py）
try:
    from call_rules_engine import TaxRates  # type: ignore
except ImportError:  # pragma: no cover - 运行时兜底（无基座环境）
    from dataclasses import dataclass as _dc

    @_dc
    class TaxRates:  # type: ignore
        dispatch_tax: float = 0.02
        royalty: float = 0.075
        trade_fee: float = 0.0075


@dataclass
class TaxBreakdown:
    """计税分项结果 T(y_t)（金额推导）。"""
    dispatch_tax: float = 0.0
    royalty: float = 0.0
    trade_fee: float = 0.0
    total: float = 0.0
    net_value: float = 0.0
    simulated: bool = True
    meta: Dict[str, object] = field(default_factory=dict)


class MicroTaxCalculator:
    """M-1 微交付计税器（快系统，ID71）。"""

    def __init__(self, rates: Optional[TaxRates] = None):
        self.rates = rates or TaxRates()

    # ---- 核心计税 ----

    def compute_taxes(self, delivery: MicroDelivery) -> TaxBreakdown:
        """交付计量 → T(y_t) 分项金额 + 合计 + 税后净额（A-1 计税 100%）。

        分项规则（对齐 TaxRates 默认值，模拟态 D-011）:
          - dispatch_tax = value × dispatch_tax（调度税，恒征收）
          - royalty      = royalty_base × royalty（版税，化合交付 royalty_base>0 时征收）
          - trade_fee    = value × trade_fee（交易费，恒征收——补齐 CALL-RULES 缺口）
        """
        if delivery.value < 0:
            raise ValueError("[NSFL-TRIGGER] 交付价值为负，非法计税输入")
        if delivery.royalty_base < 0:
            raise ValueError("[NSFL-TRIGGER] 版税基数为负，非法计税输入")

        dispatch_tax = round(delivery.value * self.rates.dispatch_tax, 2)
        royalty = round(delivery.royalty_base * self.rates.royalty, 2) \
            if delivery.royalty_base > 0 else 0.0
        trade_fee = round(delivery.value * self.rates.trade_fee, 2)

        total = round(dispatch_tax + royalty + trade_fee, 2)
        net_value = round(delivery.value - total, 2)

        return TaxBreakdown(
            dispatch_tax=dispatch_tax,
            royalty=royalty,
            trade_fee=trade_fee,
            total=total,
            net_value=net_value,
            simulated=delivery.simulated,
            meta={
                "rates": {
                    "dispatch_tax": self.rates.dispatch_tax,
                    "royalty": self.rates.royalty,
                    "trade_fee": self.rates.trade_fee,
                },
                "royalty_base": delivery.royalty_base,
            },
        )

    # ---- MOU 归零验证（ID79，A-4）----

    @staticmethod
    def validate_mou(taxes: TaxBreakdown) -> bool:
        """MOU 硬锚定：T(y_t) > 0 恒成立（对齐 validate_mou 语义）。"""
        return taxes.total > 0

    # ---- 快系统时延（ID71，A-5）----

    def compute_taxes_timed(self, delivery: MicroDelivery) -> tuple:
        """计时版计税（A-5 时延 <10ms 快系统验收）。返回 (breakdown, elapsed_ms)。"""
        t0 = time.perf_counter()
        breakdown = self.compute_taxes(delivery)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return breakdown, elapsed_ms
