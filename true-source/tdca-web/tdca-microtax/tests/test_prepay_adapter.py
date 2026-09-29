# -*- coding: utf-8 -*-
"""M-2 税收预缴合约适配器验收测试：A-2 预缴零漂移 / ID79 语义 / 托管隔离。"""
import pytest

from microtax.models import DeliveryCallType, MicroDelivery
from microtax.prepay_adapter import TaxPrepayAdapter, TaxPrepayRecord
from microtax.tax_calculator import MicroTaxCalculator


def _delivery_with_taxes(value=1000.0, royalty_base=0.0):
    """构造已计税微交付实体（M-1 输出 → M-2 输入）。"""
    d = MicroDelivery(
        delivery_id=f"MD-TAX-{value}-{royalty_base}",
        scene="scene-B",
        value=value,
        call_type=DeliveryCallType.COMPOUND if royalty_base > 0 else DeliveryCallType.DISPOSABLE,
        royalty_base=royalty_base,
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
    return d


class TestM2Prepay:
    """A-2 预缴托管完整性：预缴额 = 计税额（零漂移）。"""

    def test_prepay_zero_drift(self):
        """预缴额 = 计税额（1000 元 → 27.50）。"""
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert record.amount == 27.50
        assert record.verify_semantic() is True
        assert record.tax_breakdown["total"] == 27.50

    @pytest.mark.parametrize("value,royalty_base", [
        (100.0, 0.0),
        (2000.0, 2000.0),
        (1234.56, 0.0),
        (1_000_000.0, 500_000.0),
    ])
    def test_zero_drift_matrix(self, value, royalty_base):
        """零漂移矩阵：预缴额恒等于计税额。"""
        d = _delivery_with_taxes(value=value, royalty_base=royalty_base)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert record.amount == d.taxes["total"]
        assert abs(record.amount - d.tax_total) < 1e-9

    def test_prepay_updates_delivery_state(self):
        """预缴后微交付实体状态回写：PREPAID + prepay_ref。"""
        d = _delivery_with_taxes(value=500.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert d.prepay_status == "PREPAID"
        assert d.prepay_ref == record.transaction_id

    def test_prepay_semantics_distinct_from_budget_escrow(self):
        """预缴语义区分：TaxPrepayRecord 为税款托管记录，非预算 Shapley 分割（缺口 4）。"""
        record_fields = {f.name for f in TaxPrepayRecord.__dataclass_fields__.values()}
        # 预算 escrow（MOUEscrowVerifier）按 ratio×budget 分割；税款预缴按 amount=计税额
        # 语义差异由 verify_semantic（amount==total）强制——断言存在该语义校验
        assert hasattr(TaxPrepayRecord, "verify_semantic")
        assert "amount" in record_fields

    def test_escrow_isolation_no_withdraw(self):
        """托管隔离（F-4/BV-3）：适配器无任何提款/转移接口（税款不可挪用）。"""
        adapter = TaxPrepayAdapter()
        withdraw_attrs = [a for a in dir(adapter) if any(
            k in a.lower() for k in ("withdraw", "transfer", "refund", "release"))]
        assert withdraw_attrs == [], f"发现提款路径: {withdraw_attrs}"

    def test_simulated_flag_explicit(self):
        """ID92 模拟态显式标注（D-011）。"""
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert record.simulated is True


class TestM2ID79:
    """ID79 纪律：税款不得绕过预缴。"""

    def test_prepay_without_taxes_rejected(self):
        """未计税微交付 → 拒绝预缴（MOU 不可降）。"""
        d = MicroDelivery(delivery_id="MD-NO-TAX", scene="scene-B", value=1000.0)
        adapter = TaxPrepayAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.prepay(d)

    def test_prepay_zero_tax_rejected(self):
        """T(y_t) = 0 → 拒绝预缴（ID79 归零）。"""
        d = _delivery_with_taxes(value=0.01)
        adapter = TaxPrepayAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.prepay(d)


class TestM2Verify:
    """ID91 哈希审计：预缴记录完整性校验。"""

    def test_verify_ok(self):
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert adapter.verify(record) is True

    def test_verify_tampered_amount_fails(self):
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        record.amount = 999.99  # 篡改预缴额
        assert adapter.verify(record) is False

    def test_verify_tampered_hash_fails(self):
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        record.data_hash = "0" * 64
        assert adapter.verify(record) is False

    def test_query_and_total(self):
        adapter = TaxPrepayAdapter()
        d1 = _delivery_with_taxes(value=1000.0)
        d2 = _delivery_with_taxes(value=2000.0)
        r1 = adapter.prepay(d1)
        adapter.prepay(d2)
        assert adapter.get(r1.transaction_id) is r1
        assert adapter.total_prepaid() == round(27.50 + 55.00, 2)  # 27.50 + (40+0+15)=55.00

    def test_tx_id_derived(self):
        """默认交易 ID 派生自 delivery_id。"""
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter()
        record = adapter.prepay(d)
        assert record.transaction_id == f"TAXPRE-{d.delivery_id}"

    def test_custom_escrow_account(self):
        """自定义托管账户。"""
        d = _delivery_with_taxes(value=1000.0)
        adapter = TaxPrepayAdapter(escrow_account="TAX-ESCROW-TEST-002")
        record = adapter.prepay(d)
        assert record.escrow_account == "TAX-ESCROW-TEST-002"
        assert adapter.verify(record) is True
