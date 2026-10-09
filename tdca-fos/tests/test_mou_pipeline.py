# -*- coding: utf-8 -*-
"""
TDCA MOU 税收锚定管线测试（收口 MEMO-023 缺口）
制度锚定: ID79/ID92（MOU 真实性）| skill-mou-anchor | NSFL 经济负空间
版本: V1.0 | FC: TDCA-FC-20260804-006-M5
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_adapters.dcep_adapter import DCEPAdapter
from tdca_adapters.mou_pipeline import (
    MOUPipeline, SimulatedTaxAuthority, SIMULATED_SOURCE,
)


class FakeDCEP:
    """DCEP 智能合约 mock（与 test_adapters_m3 同构）"""
    def __init__(self):
        self.execs = []
        self.queries = []

    def execute_contract(self, contract_type, params):
        self.execs.append((contract_type, params))
        return {"tx_hash": "tx-mou-" + params["transaction_id"]}

    def query_contract(self, transaction_id):
        self.queries.append(transaction_id)
        return True


@pytest.fixture
def pipeline():
    nca = None  # NCA 生成器可空（管线不强制）
    return MOUPipeline(SimulatedTaxAuthority(), DCEPAdapter(FakeDCEP(), nca))


class TestSimulatedTaxAuthority:
    """模拟税务数据源"""

    def test_settle_generates_signed_record(self):
        src = SimulatedTaxAuthority()
        rec = src.settle("TXN-1", tax_in=50, tax_out=30)
        assert rec.simulated is True
        assert rec.source == SIMULATED_SOURCE
        assert rec.data_hash
        assert rec.signature
        assert rec.tax_in == 50 and rec.tax_out == 30

    def test_verify_accepts_valid_record(self):
        src = SimulatedTaxAuthority()
        rec = src.settle("TXN-2", 10, 20)
        assert src.verify(rec) is True

    def test_verify_rejects_tampered_amount(self):
        src = SimulatedTaxAuthority()
        rec = src.settle("TXN-3", 10, 20)
        rec.tax_in = 999  # 篡改进项税收
        assert src.verify(rec) is False

    def test_verify_rejects_negative_tax(self):
        src = SimulatedTaxAuthority()
        rec = src.settle("TXN-4", 10, 20)
        rec.tax_out = -1
        assert src.verify(rec) is False

    def test_settle_missing_tax_blocked(self):
        src = SimulatedTaxAuthority()
        with pytest.raises(ValueError):
            src.settle("TXN-5", None, 10)

    def test_settle_negative_tax_blocked(self):
        src = SimulatedTaxAuthority()
        with pytest.raises(ValueError):
            src.settle("TXN-6", 10, -5)


class TestMOUPipeline:
    """MOU 锚定管线全链路"""

    def test_full_chain(self, pipeline):
        """模拟数据源 → 校验 → 锚定 → 闭环验证"""
        out = pipeline.run("TXN-A", tax_in=50, tax_out=30)
        assert out["mou"] == 80
        assert out["contract_tx"] == "tx-mou-TXN-A"
        assert out["verified"] is True
        assert out["simulated"] is True  # 显式标记
        assert out["record"].source == SIMULATED_SOURCE

    def test_zero_tax_allowed(self, pipeline):
        """真实零税收（合法空转）允许"""
        out = pipeline.run("TXN-B", 0, 0)
        assert out["mou"] == 0
        assert out["verified"] is True

    def test_require_real_rejects_simulated(self, pipeline):
        """require_real_data=True 拒绝模拟数据（ID92 真实性守卫）"""
        with pytest.raises(ValueError):
            pipeline.run("TXN-C", 10, 10, require_real=True)

    def test_require_real_ok_with_real_source(self):
        """真实数据源（simulated=False）通过真实性守卫"""
        class RealTaxAuthority:
            simulated_only = False  # 管线检测标记

            def settle(self, transaction_id, tax_in, tax_out):
                return _RealRecord(tax_in, tax_out)

            def verify(self, record):
                return record.tax_in >= 0 and record.tax_out >= 0

        class _RealRecord:
            simulated = False
            source = "REAL-TAX-AUTHORITY"

            def __init__(self, tax_in, tax_out):
                self.tax_in, self.tax_out = tax_in, tax_out

        p = MOUPipeline(RealTaxAuthority(), DCEPAdapter(FakeDCEP(), None))
        out = p.run("TXN-D", 100, 50, require_real=True)
        assert out["simulated"] is False
        assert out["mou"] == 150
        assert p.require_real_data_available() is True

    def test_real_data_unavailable_flag(self, pipeline):
        assert pipeline.require_real_data_available() is False

    def test_tampered_record_blocked(self):
        """篡改结算数据 → 校验失败 → 拒绝锚定"""
        class TamperingSource(SimulatedTaxAuthority):
            def settle(self, transaction_id, tax_in, tax_out):
                rec = super().settle(transaction_id, tax_in, tax_out)
                rec.tax_out += 1000  # 篡改
                return rec

        p = MOUPipeline(TamperingSource(), DCEPAdapter(FakeDCEP(), None))
        with pytest.raises(ValueError):
            p.run("TXN-E", 10, 20)
