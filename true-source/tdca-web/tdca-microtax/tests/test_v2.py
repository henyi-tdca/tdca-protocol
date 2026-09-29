# -*- coding: utf-8 -*-
"""M-1 V2 / M-2 V2 验收测试：事件分档 + 双向贡献 + fail-closed + 纳税事实记录 + V1 回归。"""
from decimal import Decimal

import pytest

from microtax import (DeliveryForm, DisputeStatus, EventTaxBreakdown,
                      EventTaxCalculator, MicroDelivery, TaxEventType,
                      V2TaxPrepayAdapter)
from microtax.tax_calculator import MicroTaxCalculator


def _v2_delivery(value=1000.0, event_type=TaxEventType.CONFIG_RIGHT_CALL,
                 tax_in=0.0, tax_out=0.0, form=DeliveryForm.ONLINE,
                 dispute=DisputeStatus.NONE, delivery_id="MD-V2"):
    return MicroDelivery(
        delivery_id=delivery_id,
        scene="scene-V2",
        value=value,
        event_type=event_type,
        tax_in=tax_in,
        tax_out=tax_out,
        delivery_form=form,
        dispute_status=dispute,
    )


class TestM1V2EventComponents:
    """A-1 V2: 事件分档 × 双向贡献（税率数值恒为 CALL-001 三档）。"""

    def test_config_right_call(self):
        """配置权调用 1000 元 → 仅调度税 20.00。"""
        calc = EventTaxCalculator()
        bd = calc.compute(_v2_delivery(value=1000.0))
        assert bd.dispatch_tax == Decimal("20.00")
        assert bd.royalty == Decimal("0")
        assert bd.trade_fee == Decimal("0")
        assert bd.total == Decimal("20.00")

    def test_nca_compound(self):
        """NCA 化合 1000 元 → 调度税 20 + 版税 75（7.5%）。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, event_type=TaxEventType.NCA_COMPOUND))
        assert bd.dispatch_tax == Decimal("20.00")
        assert bd.royalty == Decimal("75.00")
        assert bd.total == Decimal("95.00")

    def test_skill_invocation(self):
        """Skill 调用 1000 元 → 调度税 20 + 交易费 7.50。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, event_type=TaxEventType.SKILL_INVOCATION))
        assert bd.trade_fee == Decimal("7.50")
        assert bd.total == Decimal("27.50")

    def test_cross_domain_transfer(self):
        """跨域转让 1000 元 → 调度税 20 + 交易费 7.50。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, event_type=TaxEventType.CROSS_DOMAIN_TRANSFER))
        assert bd.total == Decimal("27.50")

    def test_escrow_release(self):
        """托管释放 1000 元 → 仅交易费 7.50。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, event_type=TaxEventType.ESCROW_RELEASE))
        assert bd.dispatch_tax == Decimal("0")
        assert bd.total == Decimal("7.50")

    @pytest.mark.parametrize("value", [100.0, 1234.56, 1_000_000.0, 0.01])
    def test_rates_aligned_call_001(self, value):
        """数值一律映射 CALL-001 默认值（2%/7.5%/0.75%），不引入外部档位。"""
        calc = EventTaxCalculator()
        bd = calc.compute(_v2_delivery(value=value))
        assert bd.meta["rates"]["dispatch_tax"] == 0.02
        assert bd.meta["rates"]["royalty"] == 0.075
        assert bd.meta["rates"]["trade_fee"] == 0.0075


class TestM1V2BidirectionalMou:
    """双向进项/出项贡献事实（MOU = 进项 + 出项，ID79）。"""

    def test_mou_equals_input_plus_output(self):
        """MOU = tax_in + tax_out。"""
        d = _v2_delivery(value=1000.0, tax_in=300.0, tax_out=200.0)
        assert d.mou_value == 500.0
        bd = EventTaxCalculator().compute(d)
        assert bd.mou_value == Decimal("500.00")

    def test_mou_verified_when_total_le_mou(self):
        """tax_amount ≤ MOU → 验证通过。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, tax_in=300.0, tax_out=200.0))
        assert bd.mou_verified is True

    def test_mou_overflow_rejected(self):
        """税额 > MOU（溢出）→ 验证不通过（防税率溢出）。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, event_type=TaxEventType.NCA_COMPOUND,
                         tax_in=10.0, tax_out=10.0))  # MOU=20 < 95
        assert bd.total == Decimal("95.00")
        assert bd.mou_verified is False

    def test_mou_zero_zeroes(self):
        """MOU = 0 → 验证不通过（ID79 归零语义）。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=1000.0, tax_in=0.0, tax_out=0.0))
        assert bd.mou_verified is False

    def test_negative_space_fuse_zeroes_tax_but_records_fact(self):
        """负空间熔断: 税额归零，但纳税事实仍记录（语义修正核心）。"""
        d = _v2_delivery(value=50000.0, event_type=TaxEventType.NEGATIVE_SPACE_FUSE,
                         tax_in=0.0, tax_out=0.0)
        bd = EventTaxCalculator().compute(d)
        assert bd.total == Decimal("0")
        assert bd.mou_verified is False
        assert bd.tax_fact_recorded is True    # 纳税事实成立不随归零丢失


class TestM1V2DecimalPrecision:
    """Decimal 定点精度（ROUND_HALF_UP）。"""

    def test_decimal_quantization(self):
        """0.075 × 0.01 等浮点陷阱场景按 Decimal 半进位。"""
        bd = EventTaxCalculator().compute(
            _v2_delivery(value=0.01, event_type=TaxEventType.ESCROW_RELEASE))
        # 0.01 × 0.0075 = 0.000075 → 分位 ROUND_HALF_UP = 0.00
        assert bd.trade_fee == Decimal("0.00")

    def test_to_v1_compat(self):
        """V2 → V1 结构兼容（M-2/M-3 复用）。"""
        bd = EventTaxCalculator().compute(_v2_delivery(value=1000.0))
        v1 = bd.to_v1_taxes()
        assert v1 == {"dispatch_tax": 20.0, "royalty": 0.0,
                      "trade_fee": 0.0, "total": 20.0}

    def test_net_value(self):
        bd = EventTaxCalculator().compute(_v2_delivery(value=1000.0))
        assert bd.net_value == Decimal("980.00")


class TestM2V2FailClosed:
    """M-2 V2: 预缴零漂移 + fail-closed 预冻结 + 纳税事实记录。"""

    def test_prepay_zero_drift(self):
        """正常路径: 预缴额 = 计税额（零漂移）。"""
        d = _v2_delivery(value=1000.0, tax_in=300.0, tax_out=200.0)
        bd = EventTaxCalculator().compute(d)
        adapter = V2TaxPrepayAdapter()
        rec = adapter.prepay(d, bd)
        assert rec.status == "PREPAID"
        assert rec.amount == Decimal("20.00")
        assert rec.verify_zero_drift() is True
        assert d.prepay_status == "PREPAID"

    def test_fail_closed_on_mou_overflow(self):
        """MOU 溢出（税额 > MOU）→ 预冻结（amount=0，不上链）。"""
        d = _v2_delivery(value=1000.0, event_type=TaxEventType.NCA_COMPOUND,
                         tax_in=10.0, tax_out=10.0)
        bd = EventTaxCalculator().compute(d)
        assert bd.mou_verified is False
        rec = V2TaxPrepayAdapter().prepay(d, bd)
        assert rec.status == "FAIL_CLOSED"
        assert rec.amount == Decimal("0")
        assert d.prepay_status == "FAIL_CLOSED"

    def test_fail_closed_on_zero_mou(self):
        """MOU = 0 → 预冻结。"""
        d = _v2_delivery(value=1000.0, tax_in=0.0, tax_out=0.0)
        bd = EventTaxCalculator().compute(d)
        rec = V2TaxPrepayAdapter().prepay(d, bd)
        assert rec.status == "FAIL_CLOSED"

    def test_fuse_records_tax_fact(self):
        """负空间: 归零但纳税事实记录（不随税额归零丢失）。"""
        d = _v2_delivery(value=50000.0, event_type=TaxEventType.NEGATIVE_SPACE_FUSE,
                         tax_in=0.0, tax_out=0.0)
        bd = EventTaxCalculator().compute(d)
        rec = V2TaxPrepayAdapter().prepay(d, bd)
        assert rec.status == "FAIL_CLOSED"
        assert rec.tax_fact_recorded is True
        assert d.tax_fact_recorded is True

    def test_verify_integrity(self):
        """ID91 哈希审计（篡改拒绝）。"""
        d = _v2_delivery(value=1000.0, tax_in=300.0, tax_out=200.0)
        bd = EventTaxCalculator().compute(d)
        adapter = V2TaxPrepayAdapter()
        rec = adapter.prepay(d, bd)
        assert adapter.verify(rec) is True
        rec.amount = Decimal("19.99")
        assert adapter.verify(rec) is False

    def test_escrow_isolation_no_withdraw(self):
        """托管隔离（F-4/BV-3）: 无提款接口。"""
        adapter = V2TaxPrepayAdapter()
        withdraw_attrs = [a for a in dir(adapter) if any(
            k in a.lower() for k in ("withdraw", "transfer", "refund", "release"))]
        assert withdraw_attrs == []

    def test_total_prepaid_excludes_frozen(self):
        """冻结记录不计入已预缴总额。"""
        adapter = V2TaxPrepayAdapter()
        ok_d = _v2_delivery(value=1000.0, tax_in=300.0, tax_out=200.0, delivery_id="OK-1")
        fc_d = _v2_delivery(value=1000.0, tax_in=0.0, tax_out=0.0, delivery_id="FC-1")
        adapter.prepay(ok_d, EventTaxCalculator().compute(ok_d))
        adapter.prepay(fc_d, EventTaxCalculator().compute(fc_d))
        assert adapter.total_prepaid() == Decimal("20.00")


class TestV1Regression:
    """V1 基座回归: 扩展字段不破坏 V1 54 测试绿。"""

    def test_v1_calculator_unchanged(self):
        """V1 MicroTaxCalculator 行为不变。"""
        d = MicroDelivery(delivery_id="MD-V1-REGRESS", scene="s", value=1000.0)
        bd = MicroTaxCalculator().compute_taxes(d)
        assert bd.total == 27.50
        assert bd.net_value == 972.50

    def test_v1_delivery_v2_fields_default(self):
        """V1 构造的 MicroDelivery 带 V2 默认字段（向后兼容）。"""
        d = MicroDelivery(delivery_id="MD-V1", scene="s", value=100.0)
        assert d.event_type == TaxEventType.CONFIG_RIGHT_CALL
        assert d.delivery_form == DeliveryForm.ONLINE
        assert d.dispute_status == DisputeStatus.NONE
        assert d.tax_in == 0.0 and d.tax_out == 0.0
        assert d.mou_value == 0.0


class TestM1V2Latency:
    """A-5 V2 时延（快系统 ID71）: 单次 <10ms。"""

    def test_single_compute_under_10ms(self):
        calc = EventTaxCalculator()
        d = _v2_delivery(value=1234.56, tax_in=300.0, tax_out=200.0)
        bd, elapsed_ms = calc.compute_timed(d)
        assert bd.total == Decimal("24.69")   # 1234.56 × 2% = 24.6912 → ROUND_HALF_UP = 24.69
        assert elapsed_ms < 10.0

    def test_batch_1000_under_10ms_avg(self):
        import time
        calc = EventTaxCalculator()
        d = _v2_delivery(value=888.88, tax_in=100.0, tax_out=100.0)
        t0 = time.perf_counter()
        for _ in range(1000):
            calc.compute(d)
        avg_ms = (time.perf_counter() - t0) * 1000.0 / 1000.0
        assert avg_ms < 10.0
