# -*- coding: utf-8 -*-
"""
TDCA OTA 版本控制 + IRP 网关 + TP 推理机 + NCA 占位器测试
制度锚定: TDCA-KG-001 §2.3/§3.1 | TypeSystem-Confirmation-001 §5.2/§9.3
       | ID71/ID91 | FC: TDCA-FC-20260804-006
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_graph.version.ota_control import (
    OTAController, NSFLTrigger, SlowSystemRequired, GraphVersion,
)
from tdca_irp.gateway import IRPGateway, ConfigRightCall
from tdca_tp.engine.inference_engine import TDCATPReasoner, AlertSeverity


class TestOTAController:
    """OTA 活宪法版本控制 — TDCA-KG-001 §3.1 / ID71"""

    def test_normal_update_advances_version(self):
        ota = OTAController()
        vid = ota.propose_update("node-A", {"priority": 3}, "DeepSeek-V4")
        assert vid.startswith("v1.0.1")
        assert ota.current_version == vid

    def test_immutable_anchor_blocked(self):
        ota = OTAController()
        with pytest.raises(NSFLTrigger) as exc:
            ota.propose_update("REPO-003-type-tag", {}, "x")
        assert exc.value.rule_id == "TDCA-PRINCIPLE-IMMUTABLE-ANCHOR-001"

    def test_all_four_anchors_hardcoded(self):
        ota = OTAController()
        for anchor in ota._IMMUTABLE_ANCHORS:
            with pytest.raises(NSFLTrigger):
                ota.propose_update(anchor, {}, "x")

    def test_constitution_requires_signature(self):
        ota = OTAController()
        with pytest.raises(SlowSystemRequired):
            ota.propose_update("node-C", {}, "x", is_constitution=True,
                               human_signed=False)

    def test_priority5_requires_signature(self):
        ota = OTAController()
        with pytest.raises(SlowSystemRequired):
            ota.propose_update("node-D", {}, "x", priority=5, human_signed=False)

    def test_priority5_with_signature_ok(self):
        ota = OTAController()
        vid = ota.propose_update("node-D", {}, "x", priority=5, human_signed=True)
        assert vid.startswith("v1.0.1")

    def test_lineage_chain(self):
        ota = OTAController()
        v1 = ota.propose_update("a", {}, "m")
        v2 = ota.propose_update("b", {}, "m")
        assert ota.verify_chain(v2) is True

    def test_lineage_broken(self):
        ota = OTAController()
        assert ota.verify_chain("v99.0.0-nope") is False

    def test_graph_version_frozen(self):
        v = GraphVersion(version_id="v1.0.0", parent_version=None,
                         timestamp=1, merkle_root="r", changed_nodes=["a"])
        with pytest.raises(Exception):
            v.version_id = "篡改"  # frozen dataclass 应拒绝


class TestIRPGateway:
    """跨库互操作网关 — TypeSystem-Confirmation-001 §5.2/§6"""

    def _repo(self, converted=True):
        return {
            "institutional_conversion": {
                "accepts_tda_constitution": converted,
                "accepts_upda": True, "accepts_config_right_pole": True,
                "accepts_nia_macm_3_0": True, "waives_external_interpretation": True,
                "admission_oath_nca_ref": "NCA-OATH-001",
            }
        }

    def test_cross_query_ok(self, nca_placeholder):
        repo_a = self._repo()
        repo_b = self._repo()
        repo_b["query"] = lambda q: {"result": q}
        gw = IRPGateway({"a": repo_a, "b": repo_b}, nca_generator=nca_placeholder)
        cr = ConfigRightCall(who="did-1", what="kb", when=1, how="query",
                             share=0.5, cfg="cfg-hash", tax=100)
        out = gw.cross_query("a", "b", {"scene": "s"}, cr)
        assert out["mou_contribution"] == 100
        assert len(out["nca_trace"]) == 1

    def test_cross_query_unconverted_blocked(self):
        gw = IRPGateway({"a": self._repo(False), "b": self._repo()}, None)
        cr = ConfigRightCall(who="d", what="k", when=1, how="query",
                             share=0.5, cfg="c", tax=1)
        with pytest.raises(PermissionError):
            gw.cross_query("a", "b", {}, cr)

    def test_bad_config_right_rejected(self, nca_placeholder):
        repo_a, repo_b = self._repo(), self._repo()
        repo_b["query"] = lambda q: {}
        gw = IRPGateway({"a": repo_a, "b": repo_b}, nca_generator=nca_placeholder)
        bad = ConfigRightCall(who="", what="", when=0, how="", share=2.0,
                              cfg="", tax=-1)
        with pytest.raises(ValueError):
            gw.cross_query("a", "b", {}, bad)

    def test_cross_invoke_requires_nca_chain(self, nca_placeholder):
        gw = IRPGateway({"a": self._repo(), "b": self._repo()},
                        nca_generator=nca_placeholder)
        cr = ConfigRightCall(who="d", what="k", when=1, how="invoke",
                             share=0.5, cfg="c", tax=1)
        with pytest.raises(ValueError):
            gw.cross_invoke("a", "b", cr, nca_trace=[])


class TestTDCATPReasoner:
    """思维协议推理机 — TDCA-KG-001 §2.3（M2 API: execute / rule_registry）"""

    def test_five_rules_registered(self):
        r = TDCATPReasoner()
        assert set(r.rule_registry.keys()) == {
            "ExceptionDetection", "InterfaceEntropyZero", "MRCRSceneIsolation",
            "MOUContinuousVerification", "NCANestingDepth",
        }

    def test_exception_detection_critical(self, nca_placeholder):
        r = TDCATPReasoner(nca_generator=nca_placeholder)
        out = r.execute("ExceptionDetection", {
            "principle_id": "ID29", "principle_priority": 5,
            "draft_text": "申请绕过 ID29",
        })
        assert out.severity == AlertSeverity.CRITICAL
        assert out.alert["type"] == "PSEUDO_INNOVATION"
        assert nca_placeholder.count() == 1

    def test_unknown_rule_raises(self):
        r = TDCATPReasoner()
        with pytest.raises(ValueError):
            r.execute("NoSuchRule", {})

    def test_entropy_rule_alert(self):
        r = TDCATPReasoner()
        out = r.execute("InterfaceEntropyZero", {
            "code_module_id": "m", "compiler": "DeepSeek-V4",
            "calculated_entropy": 0.1,
        })
        assert out.alert["action"] == "BLOCK_DEPLOYMENT"

    def test_nesting_rule_info(self):
        r = TDCATPReasoner()
        out = r.execute("NCANestingDepth", {
            "nca_id": "n", "nesting_depth": 11, "max_depth": 10,
        })
        assert out.severity == AlertSeverity.INFO


class TestNCAPlaceholder:
    """NCA 占位生成器 — ID91"""

    def test_record_query(self, nca_placeholder):
        nid = nca_placeholder.record_query("Q1", {"a": 1}, {})
        rec = nca_placeholder.get(nid)
        assert rec["type"] == "COGNITIVE"
        assert len(rec["seal"]) == 64

    def test_verify_chain_valid(self, nca_placeholder):
        ids = [nca_placeholder.record_query("Q", {}, {}) for _ in range(3)]
        assert nca_placeholder.verify_chain(ids) is True

    def test_verify_chain_invalid(self, nca_placeholder):
        assert nca_placeholder.verify_chain(["NOPE-1"]) is False

    def test_cross_call_and_inference(self, nca_placeholder):
        a = nca_placeholder.record_cross_call("kg", "nca", "cross_query",
                                              result_hash="h1")
        b = nca_placeholder.record_inference("R1", "ID38", {}, {})
        assert nca_placeholder.verify_chain([a, b]) is True
