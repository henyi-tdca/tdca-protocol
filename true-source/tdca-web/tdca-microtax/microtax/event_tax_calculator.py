# -*- coding: utf-8 -*-
"""M-1 V2 微交付计税器：TaxEventType 事件分档 + 双向进项/出项贡献事实 + Decimal 精度。

TDCA-TASK-MICROTAX-002（V1.0-FROZEN，DCD-MICROTAX-003）：
  - 本体论基线（TDCA-TAX-SEMANTIC-REVISION-001）: 调用即产生纳税事实——
    纳税义务发生 ≠ 税款缴纳；买卖双向均产生税收贡献事实；负空间熔断不改纳税事实成立。
  - 裁决①（税率口径）: 分档结构采纳；税率数值一律来自 CALL-001 签批默认值
    （调度税 2%/版税 7.5%/交易费 0.75%，模拟态 D-011）——不引入 6%/3%/9% 等无依据档位。
  - ID 纪律: 用 ID79（MOU=进项+出项）/ID71（快系统）/ID92（模拟态）/ID85（NSFL）；不引用 ID69/ID70。

与 V1（MicroTaxCalculator）关系: V1 保持 FROZEN 不动（54 测试绿）；
本模块为 V2 扩展层，接受 V2 扩展后的 MicroDelivery（含 event_type/tax_in/tax_out）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

from .models import MicroDelivery, TaxEventType

# 复用 CALL-RULES TaxRates（CALL-001 签批默认值，模拟态 D-011）
try:
    from call_rules_engine import TaxRates  # type: ignore
except ImportError:  # pragma: no cover - 运行时兜底
    from dataclasses import dataclass as _dc

    @_dc
    class TaxRates:  # type: ignore
        dispatch_tax: float = 0.02
        royalty: float = 0.075
        trade_fee: float = 0.0075


# 事件分档 → 税种组合（数值恒来自 CALL-001 三档，分档结构裁决采纳）
EVENT_TAX_COMPONENTS: Dict[TaxEventType, tuple] = {
    TaxEventType.CONFIG_RIGHT_CALL: ("dispatch_tax",),
    TaxEventType.NCA_COMPOUND: ("dispatch_tax", "royalty"),
    TaxEventType.SKILL_INVOCATION: ("dispatch_tax", "trade_fee"),
    TaxEventType.CROSS_DOMAIN_TRANSFER: ("dispatch_tax", "trade_fee"),
    TaxEventType.ESCROW_RELEASE: ("trade_fee",),
    TaxEventType.NEGATIVE_SPACE_FUSE: (),
}


@dataclass
class EventTaxBreakdown:
    """V2 计税分项结果（Decimal 精度 + 双向贡献 + MOU 验证）。"""
    event_type: TaxEventType
    components: tuple
    dispatch_tax: Decimal = Decimal("0")
    royalty: Decimal = Decimal("0")
    trade_fee: Decimal = Decimal("0")
    total: Decimal = Decimal("0")          # 应税金额 T(y_t)
    input_tax: Decimal = Decimal("0")      # 进项税贡献事实（买方/调用方）
    output_tax: Decimal = Decimal("0")     # 出项税贡献事实（卖方/被调用方）
    mou_value: Decimal = Decimal("0")      # MOU = 进项 + 出项
    net_value: Decimal = Decimal("0")      # 税后净额 = gross − total
    mou_verified: bool = False             # MOU 硬验证通过（total ≤ MOU 且 MOU > 0）
    tax_fact_recorded: bool = True         # 纳税事实记录（成立即记录，不随归零丢失）
    simulated: bool = True                 # ID92 模拟态标注
    meta: Dict[str, object] = field(default_factory=dict)

    def to_v1_taxes(self) -> dict:
        """V2 → V1 兼容结构（供 M-2/M-3 复用，V1 管线无感知）。"""
        return {
            "dispatch_tax": float(self.dispatch_tax),
            "royalty": float(self.royalty),
            "trade_fee": float(self.trade_fee),
            "total": float(self.total),
        }


class EventTaxCalculator:
    """M-1 V2 事件分档计税器（快系统，ID71 <10ms）。"""

    def __init__(self, rates: Optional[TaxRates] = None, precision: int = 2):
        self.rates = rates or TaxRates()
        self.precision = precision
        self._q = Decimal("0." + "0" * precision)  # 精度量级（分）

    # ---- 核心计税 ----

    def compute(self, delivery: MicroDelivery) -> EventTaxBreakdown:
        """事件分档 + 双向贡献事实计税（A-1 V2：分项 × 双向逐项 100%）。

        流程:
          1. 事件分档 → 税种组合（EVENT_TAX_COMPONENTS，数值=CALL-001）
          2. 分项计算（gross × rate，Decimal ROUND_HALF_UP）
          3. 双向贡献: input_tax（买方）+ output_tax（卖方）→ MOU
          4. MOU 硬验证（ID79）: total ≤ MOU（防税率溢出）+ MOU > 0
          5. 纳税事实记录（成立即记录，负空间归零时 total=0 但 fact 仍记录）
        """
        if delivery.value < 0:
            raise ValueError("[NSFL-TRIGGER] 交付价值为负，非法计税输入")

        gross = Decimal(str(delivery.value))
        components = EVENT_TAX_COMPONENTS.get(delivery.event_type, ())

        dispatch = self._calc(gross, self.rates.dispatch_tax) \
            if "dispatch_tax" in components else Decimal("0")
        royalty = self._calc(gross, self.rates.royalty) \
            if "royalty" in components else Decimal("0")
        trade = self._calc(gross, self.rates.trade_fee) \
            if "trade_fee" in components else Decimal("0")

        total = (dispatch + royalty + trade).quantize(self._q, rounding=ROUND_HALF_UP)
        input_tax = Decimal(str(delivery.tax_in)).quantize(self._q, rounding=ROUND_HALF_UP)
        output_tax = Decimal(str(delivery.tax_out)).quantize(self._q, rounding=ROUND_HALF_UP)
        mou = (input_tax + output_tax).quantize(self._q, rounding=ROUND_HALF_UP)

        # 负空间熔断（ID85）: 税额归零，但纳税事实仍记录
        if delivery.event_type == TaxEventType.NEGATIVE_SPACE_FUSE:
            total = Decimal("0")
            mou_verified = False
        else:
            # MOU 硬验证（ID79）: total ≤ MOU（防溢出）+ MOU > 0
            mou_verified = (total <= mou) and (mou > 0)

        net = (gross - total).quantize(self._q, rounding=ROUND_HALF_UP)

        return EventTaxBreakdown(
            event_type=delivery.event_type,
            components=components,
            dispatch_tax=dispatch,
            royalty=royalty,
            trade_fee=trade,
            total=total,
            input_tax=input_tax,
            output_tax=output_tax,
            mou_value=mou,
            net_value=net,
            mou_verified=mou_verified,
            tax_fact_recorded=True,          # 纳税事实成立即记录
            simulated=delivery.simulated,
            meta={"rates": {"dispatch_tax": self.rates.dispatch_tax,
                            "royalty": self.rates.royalty,
                            "trade_fee": self.rates.trade_fee}},
        )

    def _calc(self, base: Decimal, rate: float) -> Decimal:
        return (base * Decimal(str(rate))).quantize(self._q, rounding=ROUND_HALF_UP)

    # ---- 快系统时延（ID71，A-5）----

    def compute_timed(self, delivery: MicroDelivery) -> tuple:
        import time
        t0 = time.perf_counter()
        breakdown = self.compute(delivery)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return breakdown, elapsed_ms
