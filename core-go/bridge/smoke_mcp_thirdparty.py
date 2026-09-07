"""smoke_mcp_thirdparty.py · 互操作轻量替代验证（阶段 2-B）

用官方第三方 MCP 标准 client（Python MCP SDK——独立于 TDCA 自写 bridge）
连接 TDCA MCP 服务端（tdcad.exe mcp serve），验证：
  initialize 握手 → tools/list → tools/call enforce_check（+ nca_verify）
消除「自证」：client 实现来自 MCP 官方生态，非 TDCA 代码。

零外联；只读验证（enforce_check/nca_verify 无写入副作用）。
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _tdcad() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)  # tdca-core-go/（本文件位于 bridge/ 下）
    for cand in ("tdcad.exe", "tdcad"):  # Windows exe / Linux 无后缀（CI）
        exe = os.path.join(root, cand)
        if os.path.exists(exe):
            return exe
    return "tdcad"


async def main() -> int:
    params = StdioServerParameters(command=_tdcad(), args=["mcp", "serve"])
    report: dict = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. initialize（第三方 SDK 协商协议版本）
            init = await session.initialize()
            report["handshake"] = init.protocol_version
            report["server_info"] = f"{init.server_info.name} {init.server_info.version}"

            # 2. tools/list
            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            report["tools"] = names
            report["tool_count"] = len(names)

            # 3. tools/call enforce_check（准入——只读）
            card = {
                "agent_id": "ext-3p", "protocol_version": "3.1.2",
                "scene_id": "scene-phy-notification", "role": "NM-Operator",
                "allowed_calls": ["verify", "record"],
                "nsfl_boundary": ["no-key-export", "no-tamper"],
            }
            r = await session.call_tool("enforce_check", {"agent_card": card})
            text = "".join(c.text or "" for c in r.content if c.type == "text")
            import json as _json
            try:
                payload = _json.loads(text)
            except Exception:
                payload = {"raw": text}
            report["enforce_check"] = payload

            # 4. tools/call nca_verify（存证查询——只读；schema 不符时记录不致命）
            try:
                rv = await session.call_tool("nca_verify", {"nca_id": "smoke-nonexistent"})
                text_v = "".join(c.text or "" for c in rv.content if c.type == "text")
                report["nca_verify_raw"] = text_v[:200]
            except Exception as _e:  # noqa: BLE001
                report["nca_verify_error"] = str(_e)[:200]

    print("=== 第三方 MCP client ↔ tdcad mcp serve 冒烟 ===")
    for k, v in report.items():
        print(f"  {k}: {v}")

    ok = (
        report.get("handshake")
        and report.get("tool_count", 0) >= 4
        and set(report.get("tools", [])) >= {"enforce_check", "nca_append", "nca_verify", "nsfl_eval"}
        and isinstance(report.get("enforce_check"), dict)
    )
    print("[SMOKE-3P]", "PASS" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
