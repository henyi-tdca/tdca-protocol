# -*- coding: utf-8 -*-
"""M-1 微交付计税器验收测试：A-1 计税 100% / A-4 MOU 归零 / A-5 时延 <10ms。"""
import pytest

from microtax.models import DeliveryCallType, MicroDelivery
from microtax.tax_calculator import MicroTaxCalculator, TaxBreakdown

# 对齐 CALL-RULES TaxRates 默认值（模拟态 D-011）
RATES = {"dispatch_tax": 0.02, "royalty": 0.075, "trade_fee": 0.0075}


def _delivery(value=1000.0, call_type=DeliveryCallType.DISPOSABLE,
              royalty_base=0.0, scene="scene-A"):
    return MicroDelivery(
        delivery_id=f"MD-{value}-{royalty_base}",
        scene=scene,
        value=value,
        call_type=call_type,
        royalty_base=royalty_base,
    )


class TestM1ComputeTaxes:
    """A-1 计税正确率 100%（分项税率 × 价值逐项）。"""

    def test_disposable_value_1000(self):
        """日抛交付 1000 元：调度税 20.00 / 版税 0 / 交易费 7.50 / 合计 27.50。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=1000.0))
        assert bd.dispatch_tax == 20.00
        assert bd.royalty == 0.0
        assert bd.trade_fee == 7.50
        assert bd.total == 27.50
        assert bd.net_value == 972.50

    def test_compound_with_royalty(self):
        """化合交付 2000 元 + 版税基数 2000：调度税 40 / 版税 150 / 交易费 15 / 合计 205。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(
            _delivery(value=2000.0, call_type=DeliveryCallType.COMPOUND, royalty_base=2000.0))
        assert bd.dispatch_tax == 40.00
        assert bd.royalty == 150.00
        assert bd.trade_fee == 15.00
        assert bd.total == 205.00
        assert bd.net_value == 1795.00

    @pytest.mark.parametrize("value,royalty_base,exp_d,exp_r,exp_t,exp_total", [
        (100.0, 0.0, 2.00, 0.0, 0.75, 2.75),
        (100.0, 100.0, 2.00, 7.50, 0.75, 10.25),
        (1234.56, 0.0, 24.69, 0.0, 9.26, 33.95),   # round 两位
        (1_000_000.0, 500_000.0, 20000.00, 37500.00, 7500.00, 65000.00),
        (0.01, 0.0, 0.00, 0.0, 0.00, 0.00),        # 极小值（四舍五入为 0）
    ])
    def test_rates_matrix(self, value, royalty_base, exp_d, exp_r, exp_t, exp_total):
        """A-1 分项税率 × 价值 = 100% 正确（多组数值矩阵，对齐 TaxRates 默认值）。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=value, royalty_base=royalty_base))
        assert bd.dispatch_tax == exp_d
        assert bd.royalty == exp_r
        assert bd.trade_fee == exp_t
        assert bd.total == exp_total

    def test_tax_total_equals_sum_of_parts(self):
        """合计 = 分项之和（金额守恒）。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=777.77, royalty_base=333.33))
        assert bd.total == round(bd.dispatch_tax + bd.royalty + bd.trade_fee, 2)
        assert bd.net_value == round(777.77 - bd.total, 2)

    def test_rates_aligned_with_call_rules_defaults(self):
        """复用 CALL-RULES TaxRates 默认值（2% / 7.5% / 0.75%）。"""
        calc = MicroTaxCalculator()
        assert calc.rates.dispatch_tax == 0.02
        assert calc.rates.royalty == 0.075
        assert calc.rates.trade_fee == 0.0075

    def test_trade_fee_gap_filled(self):
        """缺口 3 补齐：CALL-RULES compute_taxes 缺 trade_fee，M-1 补齐分项。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=1000.0))
        assert "trade_fee" in bd.meta or bd.trade_fee == 7.50
        assert bd.trade_fee == 7.50

    def test_negative_value_rejected(self):
        """负值交付价值 → 拒绝（NSFL 触发）。"""
        calc = MicroTaxCalculator()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            calc.compute_taxes(_delivery(value=-100.0))

    def test_negative_royalty_base_rejected(self):
        """负版税基数 → 拒绝。"""
        calc = MicroTaxCalculator()
        d = _delivery(value=100.0)
        d.royalty_base = -10.0
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            calc.compute_taxes(d)

    def test_custom_rates_respected(self):
        """自定义税率注入（不破坏默认值对齐）。"""
        from call_rules_engine import TaxRates
        calc = MicroTaxCalculator(rates=TaxRates(dispatch_tax=0.03, royalty=0.05, trade_fee=0.01))
        bd = calc.compute_taxes(_delivery(value=1000.0))
        assert bd.dispatch_tax == 30.00
        assert bd.royalty == 0.0
        assert bd.trade_fee == 10.00
        assert bd.total == 40.00


class TestM1MouAnchor:
    """A-4 MOU 归零验证：T(y_t) > 0 恒成立（对齐 validate_mou）。"""

    def test_positive_tax_anchors(self):
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=100.0))
        assert calc.validate_mou(bd) is True
        assert bd.total > 0

    def test_zero_tax_zeroes_mou(self):
        """T(y_t) = 0（极小值场景）→ MOU 归零（ID79）。"""
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(_delivery(value=0.01))
        assert bd.total == 0.00
        assert calc.validate_mou(bd) is False


class TestM1Latency:
    """A-5 时延（实时计税快系统，ID71）：单次 <10ms。"""

    def test_single_compute_under_10ms(self):
        calc = MicroTaxCalculator()
        bd, elapsed_ms = calc.compute_taxes_timed(_delivery(value=1234.56))
        assert bd.total > 0
        assert elapsed_ms < 10.0, f"计税时延 {elapsed_ms:.3f}ms 超过 10ms 快系统阈值"

    def test_batch_1000_under_10ms_avg(self):
        """批量 1000 次平均时延 <10ms（快系统吞吐验收）。"""
        calc = MicroTaxCalculator()
        d = _delivery(value=888.88)
        t0 = __import__("time").perf_counter()
        for _ in range(1000):
            calc.compute_taxes(d)
        avg_ms = (__import__("time").perf_counter() - t0) * 1000.0 / 1000.0
        assert avg_ms < 10.0, f"平均时延 {avg_ms:.3f}ms 超阈值"
