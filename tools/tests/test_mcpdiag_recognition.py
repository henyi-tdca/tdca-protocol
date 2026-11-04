# FC-ID: DCD-MCP-BRIDGE-001 | L1SI196-MCPDIAG-002 断言集（S-4 加令＋批2 认定面）
"""MCPDIAG-002：official_invoke 第四处同型防御 ＋ 新证认定面（两字段）。

S-4 加令：official_invoke 路四型坏卡（ns_types 缺键/null/字符串/空列表）——
干净拒绝码 E-NS-FAIL＋四判读数照出、零 raise、零落证（件数与状态机两读数）。
批2 P2-4：①新证两字段在（agent_card_fingerprint 顶层＋Audit-Trail 两步）；
②旧形样本（无新字段、单步 Audit-Trail）读取不崩、不判缺；
③审计步顺序与字面断言（Step1「调用执行」原样、Step2「认定: 四判+闸门」）。
P2-3：Post-State.Hash 计算口径不因加字段而变（有/无 recognition 同输入同哈希）。

⛔不部署、⛔合 main、⛔改判据语义与拒绝码闭集、⛔旧证回填。
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parent.parent
DEPLOY_MCP = TOOLS.parent / "deploy" / "mcp"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(DEPLOY_MCP))
from mcp_bridge import official_invoke, trispace  # noqa: E402
from mcp_bridge.official_invoke import OfficialInvokeService  # noqa: E402
from mcp_bridge.server import BridgeServer  # noqa: E402
from mcp_bridge.watermark import Watermark  # noqa: E402

CONTRACT = official_invoke.CONTRACT_VERSION

_CARD = {"identity_type": "external", "data_provenance": "simulated",
         "ns_types": {"absolute": ["发币", "公售"],
                      "scene_limited": ["跨境数据"],
                      "approval_required": ["对外缔约"]},
         "forbidden_operators": ["发币"],
         "declared_fields": ["text"]}


def _bad_card(shape):
    card = {"forbidden_operators": ["发币"], "declared_fields": ["text"]}
    if shape != "missing":
        card["ns_types"] = {"null": None, "str": "not-a-dict", "list": []}[shape]
    return card


_BAD_SHAPES = ["missing", "null", "str", "list"]


def _j(obj):
    return json.dumps(obj, ensure_ascii=False)


@pytest.fixture()
def srv(tmp_path):
    return BridgeServer(tmp_path / "evidence", caller="test-client")


@pytest.fixture()
def osvc(tmp_path, monkeypatch):
    monkeypatch.setenv("TDCA_MCP_EVIDENCE", str(tmp_path / "evidence"))
    return OfficialInvokeService(tmp_path / "evidence")


def _call(srv, name, args, rid=1):
    return srv.handle_line(_j({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                               "params": {"name": name, "arguments": args}}))


def _body(**over):
    body = {"caller_id": "agent-A", "callee_id": "tdca-core",
            "operation": "tool:echo", "arguments": {"text": "hello"},
            "space_id": "SBX", "request_id": "req-0001"}
    body.update(over)
    return body


def _invoke(osvc, card=None, body=None):
    return osvc.handle(body if body is not None else _body(),
                       card_header=json.dumps(card if card is not None else _CARD,
                                              ensure_ascii=False),
                       contract=CONTRACT, user_agent="test-ua/1.0",
                       source_header="portal-main")


def _nca_files(ev):
    return sorted(Path(ev).glob("NCA-MCP-*.yaml"))


# ============ S-4 加令：official_invoke 第四处同型防御 ============

@pytest.mark.parametrize("shape", _BAD_SHAPES)
def test_official_invoke_bad_ns_types_clean_reject(osvc, shape):
    """四型坏卡走 official_invoke 全路：403 E-NS-FAIL＋四判读数，零 raise、零落证。"""
    ev_before = _nca_files(osvc.ev)
    status, resp = _invoke(osvc, card=_bad_card(shape))
    assert status == 403
    assert resp["error_code"] == "E-NS-FAIL"
    assert "J1_NS-Type完整性" in resp["detail"]     # 判据读数照出
    assert "J2_⊗覆盖度" in resp["detail"]
    assert _nca_files(osvc.ev) == ev_before          # 零落证（件数读数）
    assert osvc.state.data["agents"] == {}           # 状态机不增殖（第二读数）


# ============ P2-4①：新证两字段在（桥路＋官方路） ============

def test_bridge_new_cert_recognition_fields(srv):
    fp = trispace.card_fingerprint(_CARD)
    r = _call(srv, "tdca:echo", {"text": "hi", "agent_card": _CARD})
    assert "error" not in r
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    assert doc["agent_card_fingerprint"] == fp.upper()        # 16 位大写、独立顶层
    assert len(doc["agent_card_fingerprint"]) == 16
    assert len(doc["Audit-Trail"]) == 2                       # 两步


def test_official_new_cert_recognition_fields(osvc):
    fp = trispace.card_fingerprint(_CARD)
    status, resp = _invoke(osvc)
    assert status == 200
    doc = yaml.safe_load((osvc.ev / f"{resp['nca_id']}.yaml").read_text(encoding="utf-8"))
    assert doc["agent_card_fingerprint"] == fp.upper()
    assert len(doc["Audit-Trail"]) == 2
    assert doc["Operation-Type"] == "ToolCall" and doc["ledger"] == "TOOL"  # 既有字段不动


# ============ P2-4③：审计步顺序与字面 ============

def test_audit_trail_order_and_literals(srv):
    fp = trispace.card_fingerprint(_CARD)
    _call(srv, "tdca:echo", {"text": "hi", "agent_card": _CARD})
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    s1, s2 = doc["Audit-Trail"]
    # Step 1 原样不动（既有读者兼容）
    assert s1["Step"] == "调用执行: tdca:echo"
    assert "Time" in s1 and s1["Evidence"].startswith("sha256:")
    assert "Judgments" not in s1 and "Gate" not in s1
    # Step 2 认定步：字面与五要素
    assert s2["Step"] == "认定: 四判+闸门"
    assert set(s2["Judgments"]) == {"J1_NS-Type完整性", "J2_⊗覆盖度",
                                    "J3_法律负空间绝对化", "J4_最小化合"}
    assert all(v["pass"] is True and isinstance(v["detail"], str)
               for v in s2["Judgments"].values())
    assert s2["Gate"] == "SBX→PCM PASS"
    assert s2["RateLimit"] is True
    assert s2["Fuse"] is False
    assert s2["AgentCardFingerprint"] == fp.upper()
    assert "Time" in s2


# ============ P2-4②：旧形样本兼容（读取不崩、不判缺） ============

def _old_shape_doc():
    """批1 形态样本：无 agent_card_fingerprint、Audit-Trail 仅一步（024/025 同形）。"""
    return {"NCA-ID": "NCA-MCP-20261001-001", "Function-Call-ID": "TDCA-FC-MCP-001",
            "Operation-Type": "ToolCall", "Operator": "legacy-agent",
            "Timestamp": "2026-10-01T00:00:00+00:00",
            "space_id": "SBX", "status": "SBX-ACTIVE",
            "chain_ref": trispace.CHAIN_REF,
            "Scope": "MCP 工具调用: tdca:echo（旧形样本）",
            "Pre-State": {"Path": "", "Hash": "genesis", "Size": 0},
            "Post-State": {"Path": "sbx:tdca:echo", "Hash": "sha256:" + "a" * 64,
                           "Size": 12},
            "Config-Right-Token": {"Scope": "MCP 桥接存证", "Rollback": "链式回退",
                                   "Audit-Trail": "NCA 链", "Human-Signature-Required": False,
                                   "Max-Retry": 0, "Granted-By": "mcp-bridge M1",
                                   "Expires": None},
            "Audit-Trail": [{"Step": "调用执行: tdca:echo",
                             "Time": "2026-10-01T00:00:00+00:00",
                             "Evidence": "sha256:" + "a" * 64}],
            "Human-Signature": {"Status": "Not-Required", "Signed-By": None,
                                "Signed-At": None},
            "payload_ref": "sha256:" + "a" * 64,
            "data_provenance": "simulated"}


def test_old_shape_sample_reads_tolerant(srv):
    (srv.wm.dir / "NCA-MCP-20261001-001.yaml").write_text(
        yaml.safe_dump(_old_shape_doc(), allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    r = _call(srv, "nca:get", {"nca_id": "NCA-MCP-20261001-001"})
    assert "error" not in r
    body = r["result"]["content"][0]["text"]
    doc = json.loads(body)
    assert doc["NCA-ID"] == "NCA-MCP-20261001-001"      # 读取不崩
    assert "缺失" not in body and "缺字段" not in body     # 不判缺（无缺失告警）
    r2 = _call(srv, "nca:chain", {})
    assert "error" not in r2
    chain = json.loads(r2["result"]["content"][0]["text"])
    entry = [c for c in chain if c["NCA-ID"] == "NCA-MCP-20261001-001"]
    assert len(entry) == 1 and entry[0]["Hash"] == "sha256:" + "a" * 64  # 链读数照出


# ============ P2-3：Post-State.Hash 口径不变 ============

def test_post_state_hash_unchanged_with_recognition(tmp_path):
    out = "same-output"
    expect = "sha256:" + hashlib.sha256(out.encode()).hexdigest()
    d_plain = Watermark(tmp_path / "a").stamp("c", "t", {"text": "x"}, out)
    d_recog = Watermark(tmp_path / "b").stamp(
        "c", "t", {"text": "x"}, out,
        recognition=trispace.recognition_bundle("ab12cd34ef56ab12",
                                                {"judgments": {}}))
    assert d_plain["Post-State"]["Hash"] == expect
    assert d_recog["Post-State"]["Hash"] == expect        # 加字段不改哈希语义
    assert d_plain["Post-State"] == d_recog["Post-State"]
