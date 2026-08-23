"""tdca_mcp_bridge · 挂载模式 E2E 测试（线 1 验收：外部 Agent → MCP → enforce/nca/nsfl）

用例: 握手 / 工具枚举 / 准入 PASS / 注入 BLOCK / NCA 追加 / NCA 伪造拒绝 / NSFL WARN+FUSED
（进程级 E2E——真实 tdcad.exe mcp serve 子进程）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdca_mcp_bridge import TdcaMcpClient, _find_tdcad


def _card(**kw):
    c = {
        "agent_id": "NM-001", "protocol_version": "3.1.2",
        "scene_id": "scene-phy-notification", "role": "NM-Operator",
        "allowed_calls": ["verify", "record"],
        "nsfl_boundary": ["no-key-export", "no-tamper"],
    }
    c.update(kw)
    return c


class TestHandshake:
    def test_initialize(self):
        with TdcaMcpClient() as c:
            info = c.initialize()
            assert info["protocolVersion"] == "2025-06-18"
            assert info["serverInfo"]["name"] == "tdca-core-go-mcp"

    def test_list_tools(self):
        with TdcaMcpClient() as c:
            c.initialize()
            names = {t["name"] for t in c.list_tools()}
            assert names == {"enforce_check", "nca_append", "nca_verify", "nsfl_eval"}


class TestEnforce:
    def test_pass(self):
        with TdcaMcpClient() as c:
            c.initialize()
            res = c.call_tool("enforce_check", {"agent_card": _card()})
            assert res["status"] == "PASS"
            assert len(res["checks"]) == 5

    def test_injection_blocked(self):
        with TdcaMcpClient() as c:
            c.initialize()
            try:
                c.call_tool("enforce_check", {"agent_card": _card(agent_id="<script>alert(1)</script>")})
                assert False, "injection must be blocked"
            except RuntimeError:
                pass

    def test_unknown_field_schema_rejected(self):
        with TdcaMcpClient() as c:
            c.initialize()
            bad = _card()
            bad["__admin__"] = True
            try:
                c.call_tool("enforce_check", {"agent_card": bad})
                assert False, "unknown field must be rejected"
            except RuntimeError as e:
                assert "schema violation" in str(e)


class TestNca:
    def _rec(self, prev="sha256:genesis"):
        return {
            "nca_id": "n1", "type": "fact", "hash": "",
            "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
            "payload_ref": "FactHash_0", "prev_hash": prev,
            "nsfl": {"version": "V0.2"},
        }

    def test_append(self):
        with TdcaMcpClient() as c:
            c.initialize()
            res = c.call_tool("nca_append", {"record": self._rec()})
            assert res["status"] == "appended"
            assert res["count"] == 1

    def test_append_forged_rejected(self):
        with TdcaMcpClient() as c:
            c.initialize()
            try:
                c.call_tool("nca_append", {"record": self._rec(prev="sha256:deadbeef")})
                assert False, "forged prev_hash must be rejected"
            except RuntimeError:
                pass


class TestNsfl:
    def test_warn(self):
        with TdcaMcpClient() as c:
            c.initialize()
            res = c.call_tool("nsfl_eval", {"trigger_id": "t1", "signal": "suspicious-pattern"})
            assert res["action"]["status"] == "WARN"
            assert res["blocked"] is False

    def test_fused_irreversible(self):
        with TdcaMcpClient() as c:
            c.initialize()
            res = c.call_tool("nsfl_eval", {"trigger_id": "t1", "signal": "nsfl-bypass-attempt"})
            assert res["action"]["status"] == "FUSED"
            assert res["action"]["irreversible"] is True


class TestMountE2E:
    def test_full_session(self):
        """外部 Agent 全会话：准入 → 存证 → 熔断。"""
        with TdcaMcpClient() as c:
            c.initialize()
            assert c.call_tool("enforce_check", {"agent_card": _card()})["status"] == "PASS"
            rec = {
                "nca_id": "e2e", "type": "fact", "hash": "",
                "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
                "payload_ref": "FactHash_0", "prev_hash": "sha256:genesis",
                "nsfl": {"version": "V0.2"},
            }
            assert c.call_tool("nca_append", {"record": rec})["status"] == "appended"
            assert c.call_tool("nsfl_eval", {"trigger_id": "e2e", "signal": "suspicious-pattern"})["action"]["status"] == "WARN"
