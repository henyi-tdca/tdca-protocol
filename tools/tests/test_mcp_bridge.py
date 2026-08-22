# FC-ID: DCD-MCP-BRIDGE-001 | mcp-bridge 测试（A-1~A-5，≥12 例）
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
from mcp_bridge.core import load_core  # noqa: E402
from mcp_bridge.fuse import precheck  # noqa: E402
from mcp_bridge.server import BridgeServer  # noqa: E402
from mcp_bridge.watermark import Watermark  # noqa: E402


@pytest.fixture()
def srv(tmp_path):
    return BridgeServer(tmp_path / "evidence", caller="test-client")


def _j(obj):
    return json.dumps(obj, ensure_ascii=False)


# ---- A-1 MCP 协议兼容 ----

def test_initialize(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-06-18"}}))
    assert r["result"]["protocolVersion"] == "2025-06-18"
    assert r["result"]["serverInfo"]["name"] == "tdca-mcp-bridge"
    assert "capabilities" in r["result"]


def test_tools_list(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    names = {t["name"] for t in r["result"]["tools"]}
    assert {"tdca:echo", "nca:get", "nca:chain", "tdca:core"} <= names


def test_notification_no_reply(srv):
    assert srv.handle_line(_j({"jsonrpc": "2.0", "method": "notifications/initialized"})) is None


def test_unknown_method(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 9, "method": "resources/list"}))
    assert r["error"]["code"] == -32601


def test_parse_error(srv):
    r = srv.handle_line("{not json")
    assert r["error"]["code"] == -32700


def test_stdio_end_to_end(tmp_path):
    """真实 stdio 管道：子进程跑 server，走 initialize→tools/call 全程。"""
    ev = tmp_path / "ev"
    lines = [
        _j({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        _j({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "tdca:echo", "arguments": {"text": "hello tdca"}}}),
        _j({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "nca:chain", "arguments": {}}}),
    ]
    p = subprocess.run([sys.executable, "-m", "mcp_bridge", "--evidence", str(ev)],
                       input="\n".join(lines) + "\n", capture_output=True, text=True,
                       cwd=str(TOOLS), timeout=30)
    outs = [json.loads(x) for x in p.stdout.strip().splitlines() if x.strip()]
    assert [o["id"] for o in outs] == [1, 2, 3]
    assert "hello tdca" in outs[1]["result"]["content"][0]["text"]
    assert "NCA-MCP" in outs[2]["result"]["content"][0]["text"]


# ---- A-2 NCA 自动落链 ----

def test_echo_auto_nca(srv, tmp_path):
    srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "tdca:echo", "arguments": {"text": "存证我"}}}))
    files = list((tmp_path / "evidence").glob("NCA-MCP-*.yaml"))
    assert len(files) == 1
    doc = yaml.safe_load(files[0].read_text(encoding="utf-8"))
    for k in ("NCA-ID", "Operation-Type", "Operator", "Timestamp", "Scope",
              "Post-State", "payload_ref", "data_provenance"):
        assert k in doc, f"存证缺字段 {k}"
    assert doc["data_provenance"] == "simulated"


def test_chain_continuity(srv):
    for i in range(3):
        srv.handle_line(_j({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                            "params": {"name": "tdca:echo", "arguments": {"text": f"m{i}"}}}))
    chain = srv.wm.chain()
    assert len(chain) == 3
    assert len({c["Hash"] for c in chain}) == 3  # 哈希各异 = 链式演进


# ---- A-3 NSFL 熔断 ----

def test_fuse_reject(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "tdca:echo",
                                       "arguments": {"text": "我们计划发币募资"}}}))
    assert r["result"]["isError"] is True
    assert srv.fuse_log.is_file()  # 熔断日志已落
    assert "发币" in srv.fuse_log.read_text(encoding="utf-8")


def test_fuse_reject_also_stamped(srv, tmp_path):
    srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "tdca:echo", "arguments": {"text": "搞个代币"}}}))
    doc = srv.wm.get("NCA-MCP-" + __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).strftime("%Y%m%d") + "-001")
    assert doc["Operation-Type"] == "FuseReject"


def test_fuse_negation_exempt(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "tdca:echo",
                                       "arguments": {"text": "我们承诺不发币、不代币化"}}}))
    assert "isError" not in r["result"]


def test_precheck_unit(tmp_path):
    ok, hits = precheck({"text": "不发币"}, tmp_path / "f.log")
    assert ok and not hits and not (tmp_path / "f.log").exists()
    ok, hits = precheck({"text": "密谋公售"}, tmp_path / "f.log")
    assert not ok and "公售" in hits


# ---- A-4 存证可查 ----

def test_nca_get(srv):
    srv.handle_line(_j({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "tdca:echo", "arguments": {"text": "x"}}}))
    nid = srv.wm.chain()[-1]["NCA-ID"]
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                            "params": {"name": "nca:get", "arguments": {"nca_id": nid}}}))
    assert nid in r["result"]["content"][0]["text"]


def test_nca_get_missing(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                            "params": {"name": "nca:get", "arguments": {"nca_id": "NOPE"}}}))
    assert "存证不存在" in r["result"]["content"][0]["text"]


def test_unknown_tool(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                            "params": {"name": "evil:tool", "arguments": {}}}))
    assert r["error"]["code"] == -32602


# ---- 模块 5 TDCA_CORE ----

def test_core_load():
    core = load_core()
    assert core["core_id"] == "TDCA_CORE"
    assert set(core["protocols"]) == {"TDCA-CONST", "NSFL-V0.2",
                                      "TDCA-WORKING-SPEC-001", "TDCA-OPC-COMMUNITY-001"}
    assert "不发币" in core["hard_rules"]


def test_core_tool(srv):
    r = srv.handle_line(_j({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                            "params": {"name": "tdca:core", "arguments": {}}}))
    assert "TDCA-CONST" in r["result"]["content"][0]["text"]
