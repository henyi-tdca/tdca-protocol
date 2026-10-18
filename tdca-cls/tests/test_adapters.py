"""E-2 适配器层测试 + E-3 前置端到端（接入 MICROTAX 税收）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tdca-cls/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "tdca-microtax"))  # 铁律: 只读复用

import pytest

from tdca_cls.adapters import CLSTaxAdapter, CLSLedgerAdapter, CLSNCAAdapter
from tdca_cls.rtn import RTNNetting
from tdca_cls.gim import GIMOnCycle


def test_tax_adapter_compute():
    """L1 计税: 净额支付 100 → 调度税 2%（T-031 默认）+ MOU>0"""
    adapter = CLSTaxAdapter()
    r = adapter.compute_for_settlement("A", "C", 100.0)
    assert r.dispatch_tax == pytest.approx(2.0)        # 100 × 2% 通用调度税
    assert r.total_tax > 0
    assert r.mou_ok is True                             # MOU>0 硬验证（ID79）
    assert r.net_value == pytest.approx(100.0 - r.total_tax)


def test_tax_adapter_mou_zero():
    """L1 熔断: 零金额/负金额 → MOU 校验"""
    adapter = CLSTaxAdapter()
    r = adapter.compute_for_settlement("A", "C", 0.0)
    assert r.total_tax == 0.0


def test_ledger_adapter_aggregate():
    """跨主体 MOU 聚合（L3 生态周期评估输入）"""
    ledger = CLSLedgerAdapter()
    ledger.record_settlement("T1", "A", 2.0)
    ledger.record_settlement("T2", "B", 1.5)
    assert float(ledger.total_settled()) == pytest.approx(3.5)   # Decimal → float


def test_nca_adapter_generate():
    """NCA 存证（I-4 可审计: DPI + TAX 双轨迹）"""
    adapter = CLSTaxAdapter()
    tax = adapter.compute_for_settlement("A", "C", 50.0)
    nca = CLSNCAAdapter()
    n = nca.from_settlement("T1", "A", "C", 50.0, tax, cycle_ref="RING-001")
    assert n.nca_id == "NCA-CLS-T1"
    assert n.transaction_id == "T1"
    assert len(n.audit_trail) >= 2


def test_end_to_end_with_tax():
    """E-3 前置: 环案例 + 适配器计税 + NCA（全链路）"""
    gim = GIMOnCycle()
    gim.add_edge("A", "B", 10)
    gim.add_edge("B", "C", 10)
    gim.add_edge("C", "A", 5)
    rtn = RTNNetting()
    r = rtn.net(["A", "B", "C"], gim.residual_debt())
    assert r.t_net == pytest.approx(5.0)
    # 净额支付 + 计税 + NCA
    tax_adapter = CLSTaxAdapter()
    nca_adapter = CLSNCAAdapter()
    for i, (payer, payee, amt) in enumerate(r.payment_orders):
        tax = tax_adapter.compute_for_settlement(payer, payee, amt)
        assert tax.mou_ok
        nca_adapter.from_settlement(f"RING-{i}", payer, payee, amt, tax, cycle_ref="RING-001")
    assert len(nca_adapter.all_ncas()) == len(r.payment_orders)
    # 总税 = 净额 5 × 综合税率（dispatch 2% + trade_fee 0.75% ≈ 2.75%）→ 0.14
    total_tax = sum(n.tax_amount for n in nca_adapter.all_ncas())
    assert float(total_tax) == pytest.approx(0.14, abs=1e-6)
