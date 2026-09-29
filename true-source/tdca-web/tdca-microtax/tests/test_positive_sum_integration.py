# -*- coding: utf-8 -*-
"""M-3 正和满意解税后集成验收测试：A-3 税后一致 / A-4 MOU 归零 / ID79 前置纪律。"""
import pytest

from microtax.models import DeliveryCallType, MicroDelivery
from microtax.positive_sum_integration import TaxAfterPositiveSumSettlement
from microtax.prepay_adapter import TaxPrepayAdapter
from microtax.tax_calculator import MicroTaxCalculator


def _delivery_taxed_prepaid(value=1000.0, royalty_base=0.0,
                            participants=None, delivery_id="MD-M3"):
    """构造已计税 + 已预缴的微交付实体（M-1 → M-2 → M-3 输入）。"""
    d = MicroDelivery(
        delivery_id=delivery_id,
        scene="scene-C",
        value=value,
        call_type=DeliveryCallType.COMPOUND if royalty_base > 0 else DeliveryCallType.DISPOSABLE,
        royalty_base=royalty_base,
        participants=(participants if participants is not None
                      else {"agent-a": 60.0, "agent-b": 40.0}),
    )
    calc = MicroTaxCalculator()
    bd = calc.compute_taxes(d)
    d.taxes = {
        "dispatch_tax": bd.dispatch_tax,
        "royalty": bd.royalty,
        "trade_fee": bd.trade_fee,
        "total": bd.total,
    }
    d.net_value = bd.net_value
    TaxPrepayAdapter().prepay(d)
    return d


class TestM3TaxAfterConsistency:
    """A-3 税后一致性: 税后分配总额 = 税前 − 税款（Shapley 效率性保持）。"""

    def test_single_participant_full_net(self):
        """单参与方: 分配 = 净额。"""
        d = _delivery_taxed_prepaid(value=1000.0, participants={"agent-a": 100.0})
        s = TaxAfterPositiveSumSettlement()
        result = s.settle_and_verify(d)
        assert result["allocations"] == {"agent-a": 972.50}   # 1000 − 27.50
        assert result["consistency_ok"] is True

    def test_two_participants_sum_equals_net(self):
        """双参与方: Σ分配 = 净额（972.50）。"""
        d = _delivery_taxed_prepaid(value=1000.0)
        s = TaxAfterPositiveSumSettlement()
        result = s.settle_and_verify(d)
        assert abs(result["allocated_sum"] - 972.50) < 1e-6
        assert result["expected_net"] == 972.50
        assert result["consistency_ok"] is True

    @pytest.mark.parametrize("value,royalty_base", [
        (500.0, 0.0),
        (2000.0, 2000.0),
        (1234.56, 0.0),
        (10_000.0, 5_000.0),
    ])
    def test_consistency_matrix(self, value, royalty_base):
        """税后一致矩阵: Σ分配 = value − total_tax。"""
        d = _delivery_taxed_prepaid(value=value, royalty_base=royalty_base)
        s = TaxAfterPositiveSumSettlement()
        result = s.settle_and_verify(d)
        expected = round(value - result["tax_total"], 2)
        assert result["expected_net"] == expected
        assert result["allocated_sum"] == expected
        assert result["consistency_ok"] is True

    def test_three_participants_shapley_efficiency(self):
        """三参与方 Shapley 效率性: Σ分配 = 净额且分配非负。"""
        d = _delivery_taxed_prepaid(
            value=3000.0,
            participants={"agent-a": 50.0, "agent-b": 30.0, "agent-c": 20.0})
        s = TaxAfterPositiveSumSettlement()
        result = s.settle_and_verify(d)
        assert result["consistency_ok"] is True
        assert result["tax_total"] == 82.50          # 60 + 0 + 22.50
        assert result["expected_net"] == 2917.50
        assert all(v >= 0 for v in result["allocations"].values())

    def test_settle_returns_full_trace(self):
        """结算结果含审计轨迹字段（NCA 衔接）。"""
        d = _delivery_taxed_prepaid(value=1000.0)
        result = TaxAfterPositiveSumSettlement().settle(d)
        assert result["delivery_id"] == "MD-M3"
        assert result["gross_value"] == 1000.0
        assert result["simulated"] is True
        assert result["mou_anchor_ok"] is True


class TestM3MouAnchor:
    """A-4 MOU 归零验证: T(y_t) > 0 恒成立。"""

    def test_mou_anchor_ok_after_settle(self):
        d = _delivery_taxed_prepaid(value=100.0)
        result = TaxAfterPositiveSumSettlement().settle_and_verify(d)
        assert result["mou_anchor_ok"] is True

    def test_zero_tax_rejected(self):
        """T(y_t) 被篡改为 0 → 结算拒绝（ID79 归零；预缴已过则归零门在结算侧生效）。"""
        d = _delivery_taxed_prepaid(value=100.0)   # 预缴成功（27.50 > 0）
        d.taxes = {"dispatch_tax": 0.0, "royalty": 0.0,
                   "trade_fee": 0.0, "total": 0.0}  # 篡改为归零场景
        s = TaxAfterPositiveSumSettlement()
        with pytest.raises(ValueError, match="MOU 归零"):
            s.settle(d)


class TestM3ID79:
    """ID79 纪律: 税款不得绕过预缴。"""

    def test_settle_without_taxes_rejected(self):
        """未计税 → 拒绝税后结算。"""
        d = MicroDelivery(delivery_id="MD-NO-TAX", scene="scene-C",
                          value=1000.0, participants={"agent-a": 100.0})
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            TaxAfterPositiveSumSettlement().settle(d)

    def test_settle_without_prepay_rejected(self):
        """已计税未预缴 → 拒绝税后结算（税款不得绕过预缴）。"""
        d = MicroDelivery(delivery_id="MD-NO-PREPAY", scene="scene-C",
                          value=1000.0, participants={"agent-a": 100.0})
        calc = MicroTaxCalculator()
        bd = calc.compute_taxes(d)
        d.taxes = {"dispatch_tax": bd.dispatch_tax, "royalty": bd.royalty,
                   "trade_fee": bd.trade_fee, "total": bd.total}
        d.net_value = bd.net_value
        with pytest.raises(ValueError, match="未预缴"):
            TaxAfterPositiveSumSettlement().settle(d)

    def test_settle_without_participants_rejected(self):
        """无参与方贡献 → 拒绝。"""
        d = _delivery_taxed_prepaid(value=1000.0, participants={})
        with pytest.raises(ValueError, match="无参与方贡献"):
            TaxAfterPositiveSumSettlement().settle(d)

    def test_verify_flag_raised_on_inconsistency(self):
        """全量验证: 税后不一致 → 抛错（NSFL-TRIGGER）。"""
        d = _delivery_taxed_prepaid(value=1000.0, participants={"agent-a": 100.0})
        s = TaxAfterPositiveSumSettlement()
        result = s.settle(d)
        # 篡改净额制造不一致
        d.net_value = 999.0
        with pytest.raises(ValueError, match="税后一致性失败"):
            s.settle_and_verify(d)
