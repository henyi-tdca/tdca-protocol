# -*- coding: utf-8 -*-
"""M-6 领域二交付结算状态机 + M-7 争议仲裁增信保险 + M-9 税收 NCA 验收测试。"""
from decimal import Decimal

import pytest

from microtax import (ArbitrationStage, ArbitrationVerdict, ContractForm,
                      CreditMeasure, DeliveryForm, DeliverySettlementStateMachine,
                      DeliveryState, DisputeResolutionChain, DisputeStatus,
                      EventTaxCalculator, MicroDelivery, TaxEventType,
                      TaxNCAFactory, V2TaxPrepayAdapter)


def _domain2_delivery(value=10000.0, form=DeliveryForm.ONLINE,
                      contract=None, event_type=TaxEventType.CONFIG_RIGHT_CALL,
                      delivery_id="MD-D2", dispute=DisputeStatus.NONE):
    """构造领域二已预缴微交付（达成前置条件）。"""
    d = MicroDelivery(delivery_id=delivery_id, scene="scene-d2", value=value,
                      event_type=event_type, tax_in=3000.0, tax_out=2000.0,
                      delivery_form=form, dispute_status=dispute)
    bd = EventTaxCalculator().compute(d)
    V2TaxPrepayAdapter().prepay(d, bd)
    return d


class TestM6SettlementStateMachine:
    """A-8: 线上/线下/混合 × 合约形态矩阵 100% 正确。"""

    @pytest.mark.parametrize("contract", [
        ContractForm.ONE_TO_ONE, ContractForm.ONE_TO_MANY,
        ContractForm.MANY_TO_ONE, ContractForm.MULTILATERAL])
    def test_online_immediate_settle(self, contract):
        """线上即时交付: 达成即可结算（四种合约形态全过）。"""
        d = _domain2_delivery(form=DeliveryForm.ONLINE, contract=contract)
        sm = DeliverySettlementStateMachine(contract, DeliveryForm.ONLINE)
        r1 = sm.agree(d)
        assert r1.state == DeliveryState.AGREED
        r2 = sm.settle(d)
        assert r2.state == DeliveryState.SETTLED
        assert r2.settled is True
        assert d.prepay_status == "VERIFIED"    # 结算后预缴确认

    @pytest.mark.parametrize("contract", [
        ContractForm.ONE_TO_ONE, ContractForm.MULTILATERAL])
    def test_offline_requires_completion(self, contract):
        """线下交付: 未完成线下禁止结算；完成后才可结算。"""
        d = _domain2_delivery(form=DeliveryForm.OFFLINE, contract=contract)
        sm = DeliverySettlementStateMachine(contract, DeliveryForm.OFFLINE)
        sm.agree(d)
        with pytest.raises(ValueError, match="未完成线下交付禁止结算"):
            sm.settle(d)                       # 未完成线下 → 拒绝
        sm.complete_offline(d)
        r = sm.settle(d)
        assert r.settled is True

    def test_hybrid_requires_offline_completion(self):
        """混合交付: 线下部分须完成才能结算。"""
        d = _domain2_delivery(form=DeliveryForm.HYBRID)
        sm = DeliverySettlementStateMachine(ContractForm.MULTILATERAL, DeliveryForm.HYBRID)
        sm.agree(d)
        with pytest.raises(ValueError, match="未完成线下交付禁止结算"):
            sm.settle(d)
        sm.complete_offline(d)
        assert sm.settle(d).settled is True

    def test_online_complete_offline_idempotent(self):
        """线上交付调用 complete_offline → 幂等（无线下环节）。"""
        d = _domain2_delivery(form=DeliveryForm.ONLINE)
        sm = DeliverySettlementStateMachine(ContractForm.ONE_TO_ONE, DeliveryForm.ONLINE)
        sm.agree(d)
        r = sm.complete_offline(d)
        assert r.state == DeliveryState.AGREED   # 不变
        assert sm.settle(d).settled is True

    def test_agree_requires_prepay(self):
        """达成时未预缴 → 拒绝（ID79 税收预收/预缴在达成时处理）。"""
        d = MicroDelivery(delivery_id="MD-NO-PREPAY", scene="s", value=1000.0,
                          delivery_form=DeliveryForm.ONLINE)
        sm = DeliverySettlementStateMachine(ContractForm.ONE_TO_ONE, DeliveryForm.ONLINE)
        with pytest.raises(ValueError, match="未预缴"):
            sm.agree(d)

    def test_fuse_delivery_rejected(self):
        """负空间熔断交付 → 禁止进入结算流程。

        双重防护: ① 预缴门（熔断交付 prepay_status=FAIL_CLOSED，非 PREPAID/VERIFIED）
        ② 熔断检查（agree 内 event_type 校验）——两门任一先触发即拒绝。
        """
        d = _domain2_delivery(event_type=TaxEventType.NEGATIVE_SPACE_FUSE,
                              delivery_id="MD-FUSE")
        assert d.prepay_status == "FAIL_CLOSED"
        sm = DeliverySettlementStateMachine(ContractForm.ONE_TO_ONE, DeliveryForm.ONLINE)
        with pytest.raises(ValueError) as excinfo:
            sm.agree(d)
        msg = str(excinfo.value)
        assert ("未预缴" in msg) or ("负空间熔断" in msg)

    def test_dispute_blocks_settle(self):
        """争议中禁止结算（转 M-7 仲裁）。"""
        d = _domain2_delivery(form=DeliveryForm.ONLINE, delivery_id="MD-DSP")
        sm = DeliverySettlementStateMachine(ContractForm.ONE_TO_ONE, DeliveryForm.ONLINE)
        sm.agree(d)
        sm.dispute(d, "交付质量争议")
        assert d.dispute_status == DisputeStatus.DISPUTED
        with pytest.raises(ValueError, match="争议中禁止结算"):
            sm.settle(d)

    def test_transition_trail(self):
        """状态转换轨迹记录（审计）。"""
        d = _domain2_delivery(form=DeliveryForm.OFFLINE)
        sm = DeliverySettlementStateMachine(ContractForm.ONE_TO_ONE, DeliveryForm.OFFLINE)
        sm.agree(d)
        sm.complete_offline(d)
        sm.settle(d)
        assert sm._result(d).transitions == ["agreed", "agreed",
                                             "offline_completed", "settled"]


class TestM7DisputeChain:
    """A-9: 争议链路闭环（仲裁 → 效用记录 → 增信/保险联动）。"""

    def test_arbitrate_fault_pledge(self):
        """过错方 → 增信（保证金质押）。"""
        d = _domain2_delivery(delivery_id="MD-ARB1", dispute=DisputeStatus.DISPUTED)
        chain = DisputeResolutionChain()
        v = chain.arbitrate(d, "交付违约", at_fault_agent="agent-b")
        assert v.verdict == "FAULT"
        assert v.utility_recorded is True
        assert v.credit_measure == CreditMeasure.BOND_PLEDGE
        assert d.dispute_status == DisputeStatus.CREDIT_ADJUSTED

    def test_arbitrate_fault_insurance_linked(self):
        """过错方 + 保险触发 → 增信 + 保险联动。"""
        d = _domain2_delivery(delivery_id="MD-ARB2")
        chain = DisputeResolutionChain()
        v = chain.arbitrate(d, "交付违约", at_fault_agent="agent-b",
                            insurance_triggered=True)
        assert v.credit_measure == CreditMeasure.BOTH

    def test_arbitrate_no_fault(self):
        """无过错 → 无增信/保险（效用记录仍完成）。"""
        d = _domain2_delivery(delivery_id="MD-ARB3")
        chain = DisputeResolutionChain()
        v = chain.arbitrate(d, "环境不可抗力")
        assert v.verdict == "NO_FAULT"
        assert v.credit_measure == CreditMeasure.NONE
        assert d.dispute_status == DisputeStatus.ARBITRATED

    def test_insurance_pool_fuse_pauses_insurance(self):
        """保险资金池充足率 <120% → 保险联动暂停（改增信，NSFL 过渡协议）。"""
        d = _domain2_delivery(delivery_id="MD-ARB4")
        chain = DisputeResolutionChain(insurance_pool_ratio=1.0)   # <1.2
        v = chain.arbitrate(d, "交付违约", at_fault_agent="agent-b",
                            insurance_triggered=True)
        assert v.credit_measure == CreditMeasure.BOND_PLEDGE   # 保险暂停

    def test_legal_arbitration_stage(self):
        """三级法定仲裁路径可达。"""
        d = _domain2_delivery(delivery_id="MD-ARB5")
        chain = DisputeResolutionChain()
        v = chain.arbitrate(d, "PARTIAL-部分违约", at_fault_agent="agent-a",
                            stage=ArbitrationStage.LEGAL_ARBITRATION)
        assert v.stage == ArbitrationStage.LEGAL_ARBITRATION
        assert v.verdict == "PARTIAL"


class TestM9TaxNCA:
    """M-9 税收 NCA（ID91 自反化合）。"""

    def test_nca_from_prepay_record(self):
        """预缴记录 → NCA（水印 + 审计轨迹）。"""
        d = _domain2_delivery(delivery_id="MD-NCA1")
        # 重建记录
        bd = EventTaxCalculator().compute(d)
        rec = V2TaxPrepayAdapter().prepay(d, bd)
        nca = TaxNCAFactory.from_prepay_record(rec)
        assert nca.nca_id == f"TAX-NCA-{rec.transaction_id}"
        assert len(nca.to_watermark()) == 16
        assert len(nca.audit_trail) == 1

    def test_watermark_tamper_sensitive(self):
        """水印对篡改敏感（ID56 不可篡改语义）。"""
        d = _domain2_delivery(delivery_id="MD-NCA2")
        bd = EventTaxCalculator().compute(d)
        rec = V2TaxPrepayAdapter().prepay(d, bd)
        nca = TaxNCAFactory.from_prepay_record(rec)
        w1 = nca.to_watermark()
        nca.tax_amount = Decimal("999.99")    # 篡改
        assert nca.to_watermark() != w1

    def test_periodic_report_zero_report_tax(self):
        """周期报告 NCA: 报告税 0（裁决③，不新增税率概念）。"""
        nca = TaxNCAFactory.periodic_report(0, 2 ** 40, Decimal("137.50"))
        assert nca.tax_amount == Decimal("0")
        assert nca.mou_value == Decimal("137.50")
        assert nca.event_type == "periodic_report"

    def test_nca_recursive_compound_semantics(self):
        """自反化合语义: 报告 NCA 本身可参与更高阶配置权调用（ID91）。"""
        nca = TaxNCAFactory.periodic_report(0, 2 ** 40, Decimal("100.00"))
        d = nca.to_dict()
        assert d["watermark"]
        assert d["nsfl_compliance"] is True
        # 报告 NCA 可作为「税收资产」输入——水印可被引用（递归化合前提）
        assert TaxNCAFactory.periodic_report(
            0, 2 ** 40, Decimal("100.00"), period_id="recursive").nca_id
