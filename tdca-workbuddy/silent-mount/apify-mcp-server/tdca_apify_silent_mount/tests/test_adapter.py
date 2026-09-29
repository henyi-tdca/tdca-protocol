# -*- coding: utf-8 -*-
"""tdca-apify-silent-mount 测试套件（管道冒烟）。

覆盖：NCA 六要素齐 + 水印；NSFL 边界；MOU 15% 模拟态记账；
full_pipeline 成功路径 + 零网络发送硬断言；负空间熔断。
"""

import pytest

from tdca_apify_silent_mount import TdcaApifySilentMount
from tdca_apify_silent_mount.mou import MouLedger
from tdca_apify_silent_mount.nca import derive_audit_step, generate_nca
from tdca_apify_silent_mount.nsfl import NsflChecker, NsflVerdict


# ---------- nca ----------

class TestNca:
    def test_six_elements(self):
        nca = generate_nca(
            objective="o", constraints=["c"], prior={}, config_boundary={},
            expected_allocation={}, audit_trail=[],
        )
        keys = {"objective_function", "constraint_matrix", "prior_distribution",
                "config_boundary", "expected_allocation", "audit_trail", "integrity"}
        assert keys.issubset(nca["six_elements"].keys())

    def test_nca_id_prefixed(self):
        nca = generate_nca(objective="o", constraints=[], prior={}, config_boundary={},
                           expected_allocation={}, audit_trail=[])
        assert nca["nca_id"].startswith("NCA-SM-APIFY-")

    def test_integrity_watermark(self):
        nca = generate_nca(objective="o", constraints=[], prior={}, config_boundary={},
                           expected_allocation={}, audit_trail=[])
        wm = nca["six_elements"]["integrity"]["sha256_8"]
        assert len(wm) == 8 and isinstance(wm, str)

    def test_nca_id_unique(self):
        a = generate_nca(objective="o1", constraints=[], prior={}, config_boundary={},
                         expected_allocation={}, audit_trail=[])
        b = generate_nca(objective="o2", constraints=[], prior={}, config_boundary={},
                         expected_allocation={}, audit_trail=[])
        assert a["nca_id"] != b["nca_id"]

    def test_audit_step(self):
        s = derive_audit_step("silent_mount", "2026-09-06T00:00:00Z", "ev")
        assert s["step"] == "silent_mount" and s["evidence"] == "ev"


# ---------- nsfl ----------

class TestNsfl:
    def test_pass_clean(self):
        assert NsflChecker().check("静默挂载只读引用声明") == NsflVerdict.PASS

    def test_block_on_illegal(self):
        assert NsflChecker().check("执行违法工具调用") == NsflVerdict.BLOCK

    def test_block_upstream_write(self):
        assert NsflChecker().check("未授权写入上游代码") == NsflVerdict.BLOCK

    def test_custom_rule(self):
        chk = NsflChecker()
        chk.add_rule("内幕交易")
        assert chk.check("涉及内幕交易") == NsflVerdict.BLOCK


# ---------- mou ----------

class TestMou:
    def test_profit_share_15pct(self):
        rec = MouLedger(tax_rate=0.15).record_profit_share(1.0)
        assert rec.tax_out == 0.15

    def test_cumulative(self):
        lg = MouLedger(tax_rate=0.15)
        lg.record_profit_share(1.0)
        lg.record_profit_share(2.0)
        assert lg.cumulative == 0.45  # (1+2)*0.15

    def test_snapshot_simulated(self):
        s = MouLedger().snapshot()
        assert s["simulated"] is True and "ID92" in s["note"]


# ---------- adapter ----------

class TestAdapter:
    def make(self, **kw):
        return TdcaApifySilentMount(**kw)

    def test_constants_from_registry(self):
        a = self.make()
        assert a.TARGET == "apify/apify-mcp-server"
        assert a.LICENSE == "MIT"
        assert a.MOUNT_NCA == "NCA-MOUNT-20260929-006"
        assert a.NETWORK_SEND is False

    def test_full_pipeline_success(self):
        r = self.make().full_pipeline(task="记忆检索增强", capability_tags=["memory", "agent-runtime"])
        assert r["nsfl_verdict"] == NsflVerdict.PASS
        assert r["positive_sum_pass"] is True
        assert r["silent_mount_ok"] is True

    def test_zero_network_send(self):
        r = self.make().full_pipeline(task="t", capability_tags=["memory"])
        # 硬纪律：对方零感知
        assert r["upstream_notified"] is False
        assert r["simulated"] is True
        assert r["upstream_payload_simulated"]["_network_send"] is False
        assert r["upstream_payload_simulated"]["_simulated"] is True

    def test_nca_generated(self):
        r = self.make().full_pipeline(task="t", capability_tags=["memory"])
        assert r["nca"]["nca_id"].startswith("NCA-SM-APIFY-")
        assert "integrity" in r["nca"]["six_elements"]

    def test_mou_recorded_simulated(self):
        a = self.make()
        before = a.ledger.count
        r = a.full_pipeline(task="t", capability_tags=["memory"], base_utility=1.0)
        assert a.ledger.count == before + 1
        assert r["mou"]["tax_rate"] == 0.15
        assert r["mou"]["simulated"] is True

    def test_coordinate_maps_target(self):
        r = self.make().full_pipeline(task="t", capability_tags=["memory"])
        assert r["coordinate"]["target"] == "apify/apify-mcp-server"
        assert r["coordinate"]["mount_nca"] == "NCA-MOUNT-20260929-006"

    def test_blocked_on_negative_space(self):
        a = self.make(negative_space=["未授权写入"])
        r = a.full_pipeline(task="未授权写入上游代码", capability_tags=["x"])
        assert r["nsfl_verdict"] == NsflVerdict.BLOCK
        assert r["silent_mount_ok"] is False
