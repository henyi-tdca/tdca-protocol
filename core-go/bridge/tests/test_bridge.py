"""tdca_core_go · Python↔Go 桥接测试（融入方案 I-2，≥8 用例 + 回归不破）。"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdca_core_go import TdcadBridge


def _bridge():
    # 优先使用构建产物 tdcad.exe（位于 tdca-core-go 根）
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe = os.path.join(root, "tdcad.exe")
    return TdcadBridge(tdcad_path=exe if os.path.exists(exe) else None)


def _card(**kw):
    c = {
        "agent_id": "NM-001", "protocol_version": "3.1.2",
        "scene_id": "scene-phy-notification", "role": "NM-Operator",
        "allowed_calls": ["verify", "record"],
        "nsfl_boundary": ["no-key-export", "no-tamper"],
    }
    c.update(kw)
    return c


class TestEnforceBridge:
    def test_check_pass(self):
        b = _bridge()
        res = b.enforce_check(_card())
        assert res["status"] == "PASS"
        assert len(res["checks"]) == 5

    def test_check_reject_protocol(self):
        b = _bridge()
        res = b.enforce_check(_card(protocol_version="9.9.9"))
        assert res["status"] == "REJECT"

    def test_check_injection_blocked(self):
        """注入 → 拒绝（fail-closed）。"""
        b = _bridge()
        res = b.enforce_check(_card(agent_id="<script>alert(1)</script>"))
        assert res["status"] in ("REJECT", "BLOCK")


class TestNcaBridge:
    def test_append(self):
        b = _bridge()
        rec = {"nca_id": "n1", "type": "fact", "hash": "",
               "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
               "payload_ref": "FactHash_0", "prev_hash": "sha256:genesis",
               "nsfl": {"version": "V0.2"}}
        res = b.nca_append(rec)
        assert res["status"] == "appended"
        assert res["count"] == 1

    def test_append_tamper_rejected(self):
        b = _bridge()
        rec = {"nca_id": "n1", "type": "fact", "hash": "",
               "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
               "payload_ref": "FactHash_0", "prev_hash": "sha256:deadbeef",
               "nsfl": {"version": "V0.2"}}
        with pytest.raises(RuntimeError):
            b.nca_append(rec)

    def test_verify(self):
        b = _bridge()
        recs = [{"nca_id": "n1", "type": "fact", "hash": "",
                 "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
                 "payload_ref": "FactHash_0", "prev_hash": "sha256:genesis",
                 "nsfl": {"version": "V0.2"}}]
        res = b.nca_verify(recs)
        assert res["verify"] is True
        assert res["count"] == 1


class TestNsflBridge:
    def test_eval_warn(self):
        b = _bridge()
        res = b.nsfl_eval("t1", "suspicious-pattern")
        assert res["action"]["status"] == "WARN"

    def test_eval_block(self):
        b = _bridge()
        res = b.nsfl_eval("t1", "unauthenticated")
        assert res["blocked"] is True
        assert res["action"]["status"] == "BLOCK"

    def test_eval_fused_irreversible(self):
        """绕过尝试 → FUSED 不可逆。"""
        b = _bridge()
        res = b.nsfl_eval("t1", "nsfl-bypass-attempt")
        assert res["action"]["status"] == "FUSED"
        assert res["action"]["irreversible"] is True

    def test_json_compat(self):
        """JSON 可序列化（接口熵=0）。"""
        b = _bridge()
        res = b.nsfl_eval("t1", "suspicious-pattern")
        json.dumps(res)
