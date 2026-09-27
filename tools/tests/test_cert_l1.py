# -*- coding: utf-8 -*-
"""tools/cert/cert_l1.py 测试套件（B2 测试补缺）

被测行为清单（先清单后用例）：
  L-1 _find_tdcad：tdcad.exe 存在 → 绝对路径；否则 → 字符串 "tdcad"
  L-2 _card：默认五字段 + allowed_calls/nsfl_boundary 默认值；关键字覆盖生效
  L-3 _mcp_call：JSON-RPC 单行成帧；对端关闭（无响应行）→ RuntimeError("MCP 无响应…")
  L-4 run(endpoint=stub)：① 四工具名全集合判定 ② 三态（PASS/REJECT/BLOCK，REJECT/BLOCK 走 error 信号）
      ③ nca_append → appended ④ nsfl_eval 三信号 WARN/BLOCK/FUSED ⑤ axiom6 完备性（checks==5）
  L-5 verdict：全 ok → passed=True；note 含 SIMULATED 标注；tests 计数正确
  L-6 边界（D1 修复后）：空 _results 时 verdict().passed 为 False（fail-closed，没跑≠通过）
      —— 随 cert_l1 三处缺陷修补单案更新（原「现状钉住」语义已修正）
"""
import importlib.util
import io
import json
import os
import sys
import textwrap
from pathlib import Path

import pytest

CERT_L1 = Path(__file__).resolve().parent.parent / "cert" / "cert_l1.py"

_spec = importlib.util.spec_from_file_location("cert_l1", CERT_L1)
cert_l1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cert_l1)

STUB_SRC = textwrap.dedent("""
    import json, sys

    def result(payload):
        return {"jsonrpc": "2.0", "id": 1,
                "result": {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}}

    for line in sys.stdin:
        req = json.loads(line)
        m = req.get("method")
        if m == "tools/list":
            tools = [{"name": n} for n in ("enforce_check", "nca_append", "nca_verify", "nsfl_eval")]
            print(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": tools}}), flush=True)
        elif m == "tools/call":
            name = req["params"]["name"]
            args = req["params"].get("arguments", {})
            if name == "enforce_check":
                card = args.get("agent_card", {})
                if card.get("protocol_version") == "9.9.9":
                    print(json.dumps({"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "reject"}}), flush=True)
                elif not card.get("nsfl_boundary"):
                    print(json.dumps({"jsonrpc": "2.0", "id": 1, "error": {"code": -32001, "message": "block"}}), flush=True)
                else:
                    print(json.dumps(result({"status": "PASS", "checks": [{"k": i} for i in range(5)]})), flush=True)
            elif name == "nca_append":
                print(json.dumps(result({"status": "appended", "hash": "sha256:x"})), flush=True)
            elif name == "nsfl_eval":
                sig = args.get("signal", "")
                action = {"suspicious-pattern": "WARN", "unauthenticated": "BLOCK",
                          "nsfl-bypass-attempt": "FUSED"}.get(sig, "WARN")
                print(json.dumps(result({"action": {"status": action}})), flush=True)
        # tools/call 其它/未知方法：不回（客户端将超时——不在本 stub 使用）
""")


class _FakeProc:
    """最小假进程：只服务 _mcp_call 的 stdin/stdout 交互。"""
    def __init__(self, response_lines):
        self.stdin = io.StringIO()
        self._lines = list(response_lines)

    class _Out:
        def __init__(self, lines):
            self._lines = lines

        def readline(self):
            return self._lines.pop(0) if self._lines else ""

    @property
    def stdout(self):
        return self._Out(self._lines)


# ---------- L-1 ----------

def test_find_tdcad_fallback():
    out = cert_l1._find_tdcad()
    if (CERT_L1.parent.parent / "tdca-core-go" / "tdcad.exe").exists():
        assert os.path.isabs(out)
    else:
        assert out == "tdcad"


# ---------- L-2 ----------

def test_card_defaults_and_override():
    c = cert_l1.CertL1(tdcad_path="x")._card()
    assert c["agent_id"] == "NM-001" and c["protocol_version"] == "3.1.2"
    assert c["allowed_calls"] == ["verify", "record"]
    assert c["nsfl_boundary"] == ["no-key-export", "no-tamper"]
    c2 = cert_l1.CertL1(tdcad_path="x")._card(agent_id="A-9", protocol_version="9.9.9")
    assert c2["agent_id"] == "A-9" and c2["protocol_version"] == "9.9.9"


# ---------- L-3 ----------

def test_mcp_call_roundtrip():
    cert = cert_l1.CertL1(tdcad_path="x")
    proc = _FakeProc([json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": 1}}) + "\n"])
    resp = cert._mcp_call(proc, "tools/list", {"a": 1})
    assert resp["result"]["ok"] == 1
    sent = json.loads(proc.stdin.getvalue())
    assert sent["method"] == "tools/list" and sent["params"] == {"a": 1}


def test_mcp_call_no_response_raises():
    cert = cert_l1.CertL1(tdcad_path="x")
    proc = _FakeProc([])  # 对端立即关闭 → 空行
    with pytest.raises(RuntimeError, match="MCP 无响应"):
        cert._mcp_call(proc, "tools/list")


# ---------- L-4 / L-5（stub 端点全链） ----------

@pytest.fixture
def stub_endpoint(tmp_path):
    p = tmp_path / "stub_mcp.py"
    p.write_text(STUB_SRC, encoding="utf-8")
    return f"{sys.executable} {p}"


def test_run_full_pass_against_stub(stub_endpoint):
    cert = cert_l1.CertL1(tdcad_path="x")
    results = cert.run(endpoint=stub_endpoint)
    assert set(results) == {"①mcp_connect", "②enforce_compat", "③nca_compat", "④nsfl_compat", "⑤axiom6_audit"}
    assert all(r["ok"] for r in results.values())
    assert results["②enforce_compat"]["detail"] == {"PASS": "PASS", "REJECT": "REJECT", "BLOCK": "BLOCK"}
    assert results["④nsfl_compat"]["detail"] == {
        "suspicious-pattern": "WARN", "unauthenticated": "BLOCK", "nsfl-bypass-attempt": "FUSED"}
    v = cert.verdict()
    assert v["passed"] is True and v["tests"] == 5
    assert "SIMULATED" in v["note"]


def test_run_fails_when_endpoint_silent(tmp_path):
    quiet = tmp_path / "quiet.py"
    quiet.write_text("import sys; sys.exit(0)\n", encoding="utf-8")  # 立即退出 → 无响应行
    cert = cert_l1.CertL1(tdcad_path="x")
    results = cert.run(endpoint=f"{sys.executable} {quiet}")
    assert results["①mcp_connect"]["ok"] is False
    assert not cert.verdict()["passed"]


# ---------- L-6（D1 修复后语义：fail-closed；原「现状钉住」用例随改法更新） ----------

def test_verdict_empty_results_fail_closed():
    # D1（cert_l1 三处缺陷修补单案）：空结果 = 检查未跑，绝不等于通过
    cert = cert_l1.CertL1(tdcad_path="x")
    v = cert.verdict()
    assert v["passed"] is False
    assert v["tests"] == 0
    # 返回结构字段名不变（passed/tests/detail/note），仅取值正确性修正
    assert set(v) == {"cert_level", "passed", "tests", "detail", "note"}
