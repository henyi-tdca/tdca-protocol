# -*- coding: utf-8 -*-
"""税务官智能体（TaxOfficerAgent）编排层验收测试。"""
from decimal import Decimal

import pytest

from microtax import (ContractForm, DeliveryForm, DisputeStatus, MicroDelivery,
                      TaxEventType, TaxOfficerAgent)


def _d(delivery_id, value=1000.0, event_type=TaxEventType.CONFIG_RIGHT_CALL,
       tax_in=300.0, tax_out=200.0, form=DeliveryForm.ONLINE,
       participants=None):
    return MicroDelivery(delivery_id=delivery_id, scene="officer-scene",
                         value=value, event_type=event_type,
                         tax_in=tax_in, tax_out=tax_out, delivery_form=form,
                         participants=participants or {"agent-a": 60.0, "agent-b": 40.0})


class TestTaxOfficerOnDelivery:
    """统一入口: 计税 → 预缴 → 账本 → NCA 全流程。"""

    def test_full_pipeline(self):
        agent = TaxOfficerAgent(agent_id="TAX-OFFICER-TEST")
        out = agent.on_delivery(_d("MD-O1"))
        assert out["agent_id"] == "TAX-OFFICER-TEST"
        assert out["taxes"]["total"] == 20.0          # 1000 × 2%
        assert out["prepay"]["status"] == "PREPAID"
        assert out["prepay"]["tax_fact_recorded"] is True
        assert out["ledger_event"] == "EVT-00000000"
        assert len(out["nca"]["watermark"]) == 16
        assert agent.dashboard()["ledger_events"] == 1

    def test_fail_closed_path(self):
        """MOU 溢出（税额 > MOU）→ fail-closed（纳税事实仍记录，不触发法规熔断）。"""
        agent = TaxOfficerAgent()
        d = _d("MD-FC1", tax_in=10.0, tax_out=10.0,
               event_type=TaxEventType.NCA_COMPOUND)   # total 95 > MOU 20
        out = agent.on_delivery(d)
        assert out["prepay"]["status"] == "FAIL_CLOSED"
        assert out["prepay"]["tax_fact_recorded"] is True
        assert out["regulatory"] == []
        assert agent.dashboard()["fail_closed_count"] == 1
        assert agent.dashboard()["total_tax_settled"] == "0"

    def test_fuse_path(self):
        """负空间熔断 → 归零 + 事实记录 + fused 计数。"""
        agent = TaxOfficerAgent()
        d = _d("MD-FS1", event_type=TaxEventType.NEGATIVE_SPACE_FUSE,
               tax_in=0.0, tax_out=0.0)
        out = agent.on_delivery(d)
        assert out["prepay"]["status"] == "FAIL_CLOSED"
        assert agent.dashboard()["fused_count"] == 1


class TestTaxOfficerDomain1:
    """领域一聚合缴纳。"""

    def test_aggregate_zero_drift(self):
        agent = TaxOfficerAgent()
        batch = [_d(f"MD-B{i}") for i in range(3)]
        out = agent.domain1_aggregate(batch)
        assert out["count"] == 3
        assert out["drift_verified"] is True
        assert out["total_tax"] == "60.00"          # 3 × 20.00
        # 聚合后仍逐笔入账
        assert agent.dashboard()["ledger_events"] == 3
        assert agent.dashboard()["total_tax_settled"] == "60.00"


class TestTaxOfficerDomain2:
    """领域二交付结算。"""

    def test_online_settle(self):
        agent = TaxOfficerAgent()
        d = _d("MD-D2-1")
        agent.on_delivery(d)
        out = agent.domain2_settle(d, ContractForm.ONE_TO_ONE)
        assert out["settled"] is True
        assert out["state"] == "settled"
        assert agent.dashboard()["settled_domain2"] == 1

    def test_offline_requires_completion(self):
        agent = TaxOfficerAgent()
        d = _d("MD-D2-2", form=DeliveryForm.OFFLINE)
        agent.on_delivery(d)
        # domain2_settle 内部 complete_offline → settle（线下完成路径）
        out = agent.domain2_settle(d, ContractForm.ONE_TO_ONE)
        assert out["settled"] is True

    def test_settle_without_prepay_rejected(self):
        """未预缴交付直接结算 → 拒绝（ID79）。"""
        agent = TaxOfficerAgent()
        d = _d("MD-D2-3")
        with pytest.raises(ValueError, match="未预缴"):
            agent.domain2_settle(d, ContractForm.ONE_TO_ONE)


class TestTaxOfficerDispute:
    """争议联动。"""

    def test_dispute_credit_adjustment(self):
        agent = TaxOfficerAgent()
        d = _d("MD-DSP1")
        agent.on_delivery(d)
        out = agent.handle_dispute(d, "quality-dispute", at_fault_agent="agent-b")
        assert out["verdict"] == "FAULT"
        assert out["utility_recorded"] is True
        assert out["credit_measure"] == "bond_pledge"
        assert out["dispute_status"] == "credit_adjusted"
        assert agent.dashboard()["disputes"] == 1


class TestTaxOfficerReport:
    """仪表盘 + 周期报告。"""

    def test_dashboard_aggregates(self):
        agent = TaxOfficerAgent()
        for i in range(5):
            agent.on_delivery(_d(f"MD-R{i}"))
        dash = agent.dashboard()
        assert dash["total_deliveries"] == 5
        assert dash["total_tax_settled"] == "100.00"     # 5 × 20
        assert dash["avg_latency_ms"] < 10.0
        assert dash["simulated"] is True

    def test_periodic_report_zero_report_tax(self):
        agent = TaxOfficerAgent()
        agent.on_delivery(_d("MD-RP1"))
        report = agent.periodic_report(0, 2 ** 40)
        assert report["event_type"] == "periodic_report"
        assert report["tax_amount"] == "0"               # 裁决③
        assert report["mou_value"] == "20.00"

    def test_no_three_pool_split(self):
        """裁决②: 仪表盘不含三池分流字段。"""
        agent = TaxOfficerAgent()
        dash = agent.dashboard()
        pool_keys = [k for k in dash if any(
            p in k for p in ("treasury", "social", "ecology", "pool"))]
        assert pool_keys == []
