# FC-ID: DCD-MCP-BRIDGE-001 | INTERFACE-001 批4 测试（B1~B9：成功五字段／八码逐码零消耗
# ／幂等／熔断件留痕／MCP 薄封装零自落证／存证样例全字段）
import json
import os
import socket
import sys
import threading
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

CONTRACT = official_invoke.CONTRACT_VERSION

# 合格卡（照 test_trispace_gate 同一张；J1~J4 全过所需三档/覆盖/declared_fields 齐）
_CARD = {"identity_type": "external", "data_provenance": "simulated",
         "ns_types": {"absolute": ["发币", "公售"],
                      "scene_limited": ["跨境数据"],
                      "approval_required": ["对外缔约"]},
         "forbidden_operators": ["发币"],
         "declared_fields": ["text"]}


def _body(**over) -> dict:
    body = {"caller_id": "agent-A", "callee_id": "tdca-core",
            "operation": "tool:echo", "arguments": {"text": "hello"},
            "space_id": "SBX", "request_id": "req-0001"}
    body.update(over)
    return body


def _invoke(svc, body=None, card=None, contract=CONTRACT, ua="test-ua/1.0",
            source="portal-main"):
    return svc.handle(body if body is not None else _body(),
                      card_header=json.dumps(card if card is not None else _CARD,
                                             ensure_ascii=False),
                      contract=contract, user_agent=ua, source_header=source)


def _nca_files(ev: Path) -> list:
    return sorted(Path(ev).glob("NCA-MCP-*.yaml"))


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    monkeypatch.setenv("TDCA_MCP_EVIDENCE", str(tmp_path / "evidence"))
    return OfficialInvokeService(tmp_path / "evidence")


# ---------------- B1/B2：成功路（五字段＋存证样例全字段＋billing 原文） ----------------

def test_success_five_fields_and_billing(svc):
    status, resp = _invoke(svc)
    assert status == 200
    assert set(resp) == {"result", "nca_id", "space_id", "ledger", "billing"}
    assert resp["space_id"] == "SBX"
    assert resp["ledger"] == "TOOL"            # tool: 前缀导出
    assert resp["billing"] == {"status": "pending-declaration"}  # 原文，一字不加
    assert resp["result"]["ack"] == "tool:echo"


def test_ledger_derivation(svc):
    _, r1 = _invoke(svc, _body(operation="gov:stat", request_id="r-gov"))
    _, r2 = _invoke(svc, _body(operation="asset:read", authz_ref="TDCA-ADMIT-20261104-001",
                               request_id="r-asset"))
    assert r1["ledger"] == "GOV" and r2["ledger"] == "ASSET"


def test_evidence_doc_full_fields(svc):
    _, resp = _invoke(svc)
    doc = yaml.safe_load((svc.ev / f"{resp['nca_id']}.yaml").read_text(encoding="utf-8"))
    # 批2 A4 三必备 + INTERFACE-001 扩展全字段
    assert doc["space_id"] == "SBX" and doc["status"] == "SBX-ACTIVE"
    assert doc["chain_ref"] == trispace.CHAIN_REF
    assert doc["ledger"] == "TOOL"
    assert doc["operation"] == "tool:echo"
    assert doc["caller_id"] == "agent-A" and doc["callee_id"] == "tdca-core"
    assert doc["contract"] == CONTRACT
    assert doc["cert_id"].startswith("NSFL-CERT-")
    src = doc["Source"]
    assert src == {"user_agent": "test-ua/1.0", "source": "portal-main",
                   "request_id": "req-0001"}          # 三项齐全
    assert doc["Operator"] == "anonymous"             # 中性值
    assert doc["billing"] == {"status": "pending-declaration"}


def test_prev_nca_chain_continuity(svc):
    _, r1 = _invoke(svc, _body(request_id="req-c1"))
    _, r2 = _invoke(svc, _body(request_id="req-c2"))
    d1 = yaml.safe_load((svc.ev / f"{r1['nca_id']}.yaml").read_text(encoding="utf-8"))
    d2 = yaml.safe_load((svc.ev / f"{r2['nca_id']}.yaml").read_text(encoding="utf-8"))
    assert d2["Pre-State"]["Hash"] == d1["Post-State"]["Hash"]  # 链式连续


def test_salted_source_when_no_header(svc):
    _, resp = _invoke(svc, source=None)
    doc = yaml.safe_load((svc.ev / f"{resp['nca_id']}.yaml").read_text(encoding="utf-8"))
    assert doc["Source"]["source"].startswith("sha256:")     # 加盐摘要
    assert doc["Source"]["request_id"] == "req-0001"


# ---------------- B3：八码逐码触发（除熔断两码另测），全部零消耗 ----------------

def _assert_zero_consumption(svc, ev_before):
    assert _nca_files(svc.ev) == ev_before          # 不落 ToolCall 存证
    assert svc.state.data["agents"] == {} or all(
        a["writes"] == 0 for a in svc.state.data["agents"].values())


@pytest.mark.parametrize("contract,body_mutation,expect", [
    ("WRONG-V9", {}, "E-VERSION"),                       # ① 版本
    (CONTRACT, {"operation": 1}, "E-FIELD"),             # ② 字段
    (CONTRACT, {"space_id": "PCM"}, "E-SPACE"),          # ③ 空间
])
def test_early_gates_zero_consumption(svc, contract, body_mutation, expect):
    b = _body(**body_mutation)
    ev_before = _nca_files(svc.ev)
    status, resp = svc.handle(b, card_header=None, contract=contract,
                              user_agent=None, source_header=None)
    assert resp["error_code"] == expect and status != 200
    assert resp["billing"] == {"status": "pending-declaration"}  # 计费字段原样，⛔计量
    _assert_zero_consumption(svc, ev_before)


def test_no_card_zero_consumption(svc):
    ev_before = _nca_files(svc.ev)
    status, resp = svc.handle(_body(), card_header=None, contract=CONTRACT,
                              user_agent=None, source_header=None)
    assert resp["error_code"] == "E-NO-CARD" and status == 401
    _assert_zero_consumption(svc, ev_before)


def test_no_authz_asset_ledger(svc):
    ev_before = _nca_files(svc.ev)
    status, resp = _invoke(svc, _body(operation="asset:read", request_id="r-x"))
    assert resp["error_code"] == "E-NO-AUTHZ" and status == 403
    _assert_zero_consumption(svc, ev_before)


def test_degraded_when_evidence_readonly(svc, monkeypatch):
    ev_before = _nca_files(svc.ev)
    monkeypatch.setattr(official_invoke.os, "access", lambda *a, **k: False)
    status, resp = _invoke(svc)
    assert resp["error_code"] == "E-DEGRADED" and status == 503
    _assert_zero_consumption(svc, ev_before)


def test_state_gate_banned_maps_e_ns_fail(svc, monkeypatch):
    fp = trispace.card_fingerprint(_CARD)
    svc.state.ensure(fp)["status"] = trispace.ST_SBX_BANNED
    svc.state.save()
    ev_before = _nca_files(svc.ev)
    status, resp = _invoke(svc)
    assert resp["error_code"] == "E-NS-FAIL" and status == 403
    _assert_zero_consumption(svc, ev_before)


def test_rate_limit_e_limit(svc, monkeypatch):
    monkeypatch.setattr(svc.limiter, "allow", lambda fp: (False, "每分钟写上限已到"))
    ev_before = _nca_files(svc.ev)
    status, resp = _invoke(svc)
    assert resp["error_code"] == "E-LIMIT" and status == 429
    _assert_zero_consumption(svc, ev_before)


def test_judgment_fail_e_ns_fail(svc):
    ev_before = _nca_files(svc.ev)
    status, resp = _invoke(svc, _body(arguments={"undeclared": 1}))  # J4 过度设计
    assert resp["error_code"] == "E-NS-FAIL" and status == 403
    assert "四判未过" in resp["detail"]
    _assert_zero_consumption(svc, ev_before)


# ---------------- B5/B6：熔断两码（唯一非零消耗例外：留痕降级，非正式存证） ----------------

def test_fuse_ban_leaves_fusereject_and_bans(svc):
    ev_before = _nca_files(svc.ev)
    status, resp = _invoke(svc, _body(arguments={"text": "我要发币"}))  # 触法
    assert resp["error_code"] == "E-NS-FAIL" and status == 403
    after = _nca_files(svc.ev)
    assert len(after) == len(ev_before) + 1            # 恰一件熔断件
    doc = yaml.safe_load(after[-1].read_text(encoding="utf-8"))
    assert doc["Operation-Type"] == "FuseReject"
    assert doc["status"] == trispace.ST_SBX_BANNED
    fp = trispace.card_fingerprint(_CARD)
    assert svc.state.agent(fp)["status"] == trispace.ST_SBX_BANNED


def test_crossed_boundary_suspends(svc):
    status, resp = _invoke(svc, _body(arguments={"text": "跨境数据"}))  # 触及 scene_limited
    assert resp["error_code"] == "E-NS-FAIL" and status == 403
    fp = trispace.card_fingerprint(_CARD)
    assert svc.state.agent(fp)["status"] == trispace.ST_SBX_SUSPENDED
    assert "限期重整" in resp["detail"]


# ---------------- B4：幂等（同 request_id 两投一证，缓存原样复放） ----------------

def test_idempotent_replay(svc):
    s1, r1 = _invoke(svc, _body(request_id="req-idem"))
    n_before = len(_nca_files(svc.ev))
    s2, r2 = _invoke(svc, _body(request_id="req-idem"))
    assert (s1, r1) == (s2, r2) == (200, r1)
    assert len(_nca_files(svc.ev)) == n_before          # 一证，不重落


# ---------------- B7~B9：MCP 薄封装（HTTP 转发，证落 API 面，MCP 面零自落） ----------------

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_mcp_tool_forwards_to_api_face(svc, tmp_path, monkeypatch):
    import uvicorn
    import shim  # deploy/mcp/shim.py（sys.path 已含 deploy/mcp）

    port = _free_port()
    monkeypatch.setenv("TDCA_MCP_EVIDENCE", str(svc.ev))
    config = uvicorn.Config(shim.app, host="127.0.0.1", port=port, log_level="error")
    thread = threading.Thread(target=uvicorn.Server(config).run, daemon=True)
    thread.start()
    import time
    for _ in range(50):                                  # 等端口起
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                break
        except OSError:
            time.sleep(0.1)

    from mcp_bridge import server as server_mod
    monkeypatch.setattr(server_mod, "OFFICIAL_INVOKE_URL",
                        f"http://127.0.0.1:{port}/api/v1/official/invoke")
    srv = BridgeServer(tmp_path / "mcp-evidence", caller="mcp-test")
    nca_before = len(_nca_files(svc.ev))
    args = {"caller_id": "agent-A", "callee_id": "tdca-core", "operation": "tool:echo",
            "arguments": {"text": "hello"}, "space_id": "SBX",
            "request_id": "req-mcp-1", "agent_card": dict(_CARD),
            "contract": CONTRACT}
    out = srv.handle_line(json.dumps(
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
         "params": {"name": "official:invoke", "arguments": args}}, ensure_ascii=False))
    assert "result" in out and "error" not in out
    payload = json.loads(out["result"]["content"][0]["text"])
    assert payload["nca_id"].startswith("NCA-MCP-")    # 转发原样承载
    # 证落 API 面（svc.ev），MCP 面（mcp-evidence）零自落
    assert len(_nca_files(svc.ev)) == nca_before + 1
    assert _nca_files(tmp_path / "mcp-evidence") == []


def test_mcp_tools_list_exposes_official_invoke(svc):
    srv = BridgeServer(svc.ev, caller="t")
    out = srv.handle_line(json.dumps({"jsonrpc": "2.0", "id": 1,
                                      "method": "tools/list"}))
    names = [t["name"] for t in out["result"]["tools"]]
    assert "official:invoke" in names and len(names) == 5


def test_mcp_transport_failure_is_jsonrpc_32603(svc, monkeypatch):
    from mcp_bridge import server as server_mod
    monkeypatch.setattr(server_mod, "OFFICIAL_INVOKE_URL",
                        "http://127.0.0.1:1/closed")   # 必拒端口
    srv = BridgeServer(svc.ev, caller="t")
    out = srv.handle_line(json.dumps(
        {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
         "params": {"name": "official:invoke", "arguments": _body()}}, ensure_ascii=False))
    assert out["error"]["code"] == -32603               # 传输层错，⛔业务码
