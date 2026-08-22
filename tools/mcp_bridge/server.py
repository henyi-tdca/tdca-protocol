# FC-ID: DCD-MCP-BRIDGE-001 | 模块 3+4 MCP 协议（stdio JSON-RPC 2.0）+ 存证查询工具
from __future__ import annotations

import json
from pathlib import Path

from .core import load_core
from .fuse import precheck
from .watermark import Watermark

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {"name": "tdca:echo",
     "description": "演示业务工具：回显输入（每次调用自动落 NCA 存证 + NSFL 熔断预检）[SIMULATED]",
     "inputSchema": {"type": "object",
                     "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "nca:get",
     "description": "按 NCA-ID 查询存证全文",
     "inputSchema": {"type": "object",
                     "properties": {"nca_id": {"type": "string"}}, "required": ["nca_id"]}},
    {"name": "nca:chain",
     "description": "查询存证链尾（默认 20 条）",
     "inputSchema": {"type": "object",
                     "properties": {"limit": {"type": "integer"}}}},
    {"name": "tdca:core",
     "description": "读取 TDCA_CORE 基协议声明（接入即加载）",
     "inputSchema": {"type": "object", "properties": {}}},
]


class BridgeServer:
    """最小 MCP server：stdio 行分隔 JSON-RPC。零外部依赖。"""

    def __init__(self, evidence_dir: Path, caller: str = "mcp-client"):
        self.wm = Watermark(evidence_dir)
        self.fuse_log = Path(evidence_dir) / ".nsfl-fuse.log"
        self.caller = caller
        self.core = load_core()
        self.initialized = False

    # ---- JSON-RPC 骨架 ----
    def handle_line(self, line: str) -> dict | None:
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            return self._err(None, -32700, "Parse error")
        rid = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}
        if rid is None:  # notification（如 initialized）不回包
            return None
        if method == "initialize":
            self.initialized = True
            return self._ok(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "tdca-mcp-bridge", "version": "0.1.0"},
                "instructions": "TDCA 制度层挂载：全部调用自动落 NCA 存证 + NSFL 熔断预检 [SIMULATED]；"
                                "基协议见 tdca:core"})
        if method == "ping":
            return self._ok(rid, {})
        if method == "tools/list":
            return self._ok(rid, {"tools": TOOLS})
        if method == "tools/call":
            return self._call(rid, params)
        return self._err(rid, -32601, f"Method not found: {method}")

    def _call(self, rid, params: dict) -> dict:
        name = params.get("name", "")
        args = params.get("arguments") or {}
        known = {t["name"] for t in TOOLS}
        if name not in known:
            return self._err(rid, -32602, f"Unknown tool: {name}")
        # 熔断预检（查询类工具豁免——只读不产生业务语义）
        if name == "tdca:echo":
            ok, hits = precheck(args, self.fuse_log)
            if not ok:
                self.wm.stamp(self.caller, name, args, f"REJECTED {hits}", rejected=True)
                return self._ok(rid, {"isError": True, "content": [
                    {"type": "text",
                     "text": f"NSFL 熔断：参数含负空间禁项 {hits}，调用已拒绝并存证 [SIMULATED]"}]})
            out = f"[SIMULATED] echo: {args.get('text', '')}"
            nca = self.wm.stamp(self.caller, name, args, out)
            return self._ok(rid, {"content": [{"type": "text", "text":
                f"{out}\n（存证 {nca['NCA-ID']}，输出哈希 {nca['Post-State']['Hash'][:24]}…）"}]})
        if name == "nca:get":
            doc = self.wm.get(str(args.get("nca_id", "")))
            text = json.dumps(doc, ensure_ascii=False) if doc else "存证不存在"
            return self._ok(rid, {"content": [{"type": "text", "text": text}]})
        if name == "nca:chain":
            chain = self.wm.chain(int(args.get("limit", 20)))
            return self._ok(rid, {"content": [{"type": "text",
                "text": json.dumps(chain, ensure_ascii=False)}]})
        if name == "tdca:core":
            return self._ok(rid, {"content": [{"type": "text",
                "text": json.dumps(self.core, ensure_ascii=False)}]})
        return self._err(rid, -32602, f"Unreachable: {name}")

    @staticmethod
    def _ok(rid, result) -> dict:
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    @staticmethod
    def _err(rid, code, msg) -> dict:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}


def serve_stdio(evidence_dir: Path, caller: str = "mcp-client"):
    """stdio 主循环：行分隔 JSON-RPC（MCP stdio 传输）。"""
    import sys
    srv = BridgeServer(Path(evidence_dir), caller)
    print("[SIMULATED] tdca-mcp-bridge stdio server 就绪", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        resp = srv.handle_line(line)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
