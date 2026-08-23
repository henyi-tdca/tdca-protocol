"""tdca_mcp_bridge · 挂载模式 E2E 客户端（DCD-CORE-GO-001 §三 / TDCA-OPEN-COLLAB-001 §二）

外部 Agent（如 DeepSeek Harness / OpenAI Codex Harness）通过 MCP stdio 挂载 TDCA 核心引擎：
  enforce_check / nca_append / nca_verify / nsfl_eval

只赋能不改码（BIDIR-001）：TDCA 仅增加协议层，不修改外部源码。
接口熵=0：工具输出与 tdcad CLI / Go pkg 输出 JSON 100% 同构。

用法:
  from tdca_mcp_bridge import TdcaMcpClient
  client = TdcaMcpClient()          # 自动定位 tdcad.exe 并启动 MCP 服务
  client.initialize()
  tools = client.list_tools()
  res = client.call_tool("enforce_check", {...})
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

# ---- 定位 tdcad.exe（MCP 服务端）----

def _find_tdcad() -> str:
    """优先工作区根 tdcad.exe；否则 PATH。"""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)  # tdca-core-go/（本文件位于 bridge/ 下）
    exe = os.path.join(root, "tdcad.exe")
    if os.path.exists(exe):
        return exe
    return "tdcad"


class TdcaMcpClient:
    """外部 Agent 视角的 MCP 客户端（stdio JSON-RPC 2.0）。"""

    def __init__(self, tdcad_path: Optional[str] = None, debug: bool = False):
        exe = tdcad_path or _find_tdcad()
        self._proc = subprocess.Popen(
            [exe, "mcp", "serve"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1,
        )
        self._seq = 0
        self._debug = debug

    # ---- 底层 JSON-RPC ----

    def _send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._seq += 1
        req = {"jsonrpc": "2.0", "id": self._seq, "method": method}
        if params is not None:
            req["params"] = params
        line = json.dumps(req, ensure_ascii=False)
        if self._debug:
            print(">>", line)
        self._proc.stdin.write(line + "\n")
        self._proc.stdin.flush()
        resp = json.loads(self._proc.stdout.readline())
        if self._debug:
            print("<<", json.dumps(resp, ensure_ascii=False))
        return resp

    # ---- MCP 会话 ----

    def initialize(self) -> Dict[str, Any]:
        """握手：协议版本 + serverInfo。"""
        resp = self._send("initialize", {
            "protocolVersion": "2025-06-18",
            "clientInfo": {"name": "ext-agent", "version": "0.1"},
            "capabilities": {},
        })
        return resp["result"]

    def list_tools(self) -> List[Dict[str, Any]]:
        resp = self._send("tools/list")
        return resp["result"]["tools"]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具；返回解析后的 result（MCP 文本内容）。"""
        resp = self._send("tools/call", {"name": name, "arguments": arguments})
        if "error" in resp:
            raise RuntimeError(f"[MCP-ERROR] {name}: {resp['error']['message']}")
        text = resp["result"]["content"][0]["text"]
        return json.loads(text)

    def close(self) -> None:
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass

    def __enter__(self) -> "TdcaMcpClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ---- 演示 / 挂载模式 E2E ----

def run_e2e() -> Dict[str, Any]:
    """挂载模式 E2E：外部 Agent 全链（准入 → 存证 → 熔断）。"""
    report: Dict[str, Any] = {}
    with TdcaMcpClient() as c:
        info = c.initialize()
        report["handshake"] = info["protocolVersion"]

        tools = {t["name"] for t in c.list_tools()}
        report["tools"] = sorted(tools)

        # ① 准入 PASS
        card = {
            "agent_id": "NM-001", "protocol_version": "3.1.2",
            "scene_id": "scene-phy-notification", "role": "NM-Operator",
            "allowed_calls": ["verify", "record"],
            "nsfl_boundary": ["no-key-export", "no-tamper"],
        }
        report["enforce_pass"] = c.call_tool("enforce_check", {"agent_card": card})["status"]

        # ② 注入拒绝（破坏性）
        bad_card = dict(card, agent_id="<script>alert(1)</script>")
        try:
            c.call_tool("enforce_check", {"agent_card": bad_card})
            report["injection"] = "ALLOWED(FAIL)"
        except RuntimeError:
            report["injection"] = "BLOCKED"

        # ③ 存证追加 + 伪造拒绝（破坏性）
        rec = {
            "nca_id": "e2e-001", "type": "fact", "hash": "",
            "ts": "2026-08-23T00:00:00Z", "signer": "TDCA-PUBKEY-01",
            "payload_ref": "FactHash_0", "prev_hash": "sha256:genesis",
            "nsfl": {"version": "V0.2"},
        }
        report["nca_append"] = c.call_tool("nca_append", {"record": rec})["status"]
        forged = dict(rec, prev_hash="sha256:forged")
        try:
            c.call_tool("nca_append", {"record": forged})
            report["nca_forge"] = "APPENDED(FAIL)"
        except RuntimeError:
            report["nca_forge"] = "REJECTED"

        # ④ 熔断 WARN / FUSED（破坏性）
        report["nsfl_warn"] = c.call_tool("nsfl_eval", {"trigger_id": "t1", "signal": "suspicious-pattern"})["action"]["status"]
        report["nsfl_fused"] = c.call_tool("nsfl_eval", {"trigger_id": "t1", "signal": "nsfl-bypass-attempt"})["action"]["status"]
    return report


if __name__ == "__main__":  # pragma: no cover
    r = run_e2e()
    print("=== TDCA MCP 挂载模式 E2E（外部 Agent → tdcad mcp serve）===")
    for k, v in r.items():
        print(f"  {k}: {v}")
    ok = (r.get("handshake") == "2025-06-18"
          and r.get("enforce_pass") == "PASS"
          and r.get("injection") == "BLOCKED"
          and r.get("nca_append") == "appended"
          and r.get("nca_forge") == "REJECTED"
          and r.get("nsfl_warn") == "WARN"
          and r.get("nsfl_fused") == "FUSED")
    print("[E2E]", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 2)
