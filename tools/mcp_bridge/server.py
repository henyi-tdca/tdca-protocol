# FC-ID: DCD-MCP-BRIDGE-001 | 模块 3+4 MCP 协议（stdio JSON-RPC 2.0）+ 存证查询工具
from __future__ import annotations

import json
from pathlib import Path

from .core import load_core
from .fuse import precheck
from .watermark import Watermark
from . import trispace

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {"name": "tdca:echo",
     "description": "演示业务工具：回显输入（写路：须随调用提交 agent_card"
                    "（双轨身份§三）→ 四判出 NSFL-CERT → 落 SBX 分卷存证；"
                    "匿名调用零消耗拒绝）[SIMULATED]",
     "inputSchema": {"type": "object",
                     "properties": {"text": {"type": "string"},
                                    "agent_card": {"type": "object"}},
                     "required": ["text"]}},
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
        # TRISPACE-001：三空间流水线件（A3~A7）；CHAIN-DECLARATION（A8 分链登记）
        self.config = trispace.load_config()
        self.state = trispace.TriSpaceState(evidence_dir)
        self.limiter = trispace.RateLimiter(self.config)
        trispace.ensure_chain_declaration(evidence_dir)

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

    # ---- TRISPACE-001 写路三段流水线（A1/A2/A3/A5/A7） ----
    def _write_pipeline(self, rid, args: dict) -> dict:
        """tdca:echo 写路：agent_card → 状态闸门 → 限流 → 熔断预检/越界 → 四判 → SBX。

        零消耗口径（A2）：未持卡/被禁/被停/超限 ⟹ 不落存证、不写状态、不记熔断日志。
        """
        card = args.pop("agent_card", None)
        if card is None:
            return self._err(rid, trispace.CODE_NO_CARD, trispace.MSG_NO_CARD)
        shape_err = trispace.validate_card_shape(card)
        if shape_err:
            return self._err(rid, trispace.CODE_NO_CARD,
                             trispace.MSG_NO_CARD + f"（受理失败：{shape_err}）")
        fp = trispace.card_fingerprint(card)

        ok, st, why = self.state.check_writable(fp)
        if not ok:
            code = (trispace.CODE_BANNED if st == trispace.ST_SBX_BANNED
                    else trispace.CODE_SUSPENDED)
            return self._err(rid, code, why)

        ok, why = self.limiter.allow(fp)
        if not ok:
            return self._err(rid, trispace.CODE_RATE_LIMITED, why)

        # 轻量前置（保留，⛔充作四判）：命中 = 触碰法律负空间 ⟹ SBX-BANNED（A7）
        ok, hits = precheck(args, self.fuse_log)
        if not ok:
            self.state.ban(fp)
            self.wm.stamp(self.caller, "tdca:echo", args,
                          f"REJECTED-BANNED {hits}", rejected=True,
                          space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_BANNED)
            return self._ok(rid, {"isError": True, "content": [{"type": "text",
                "text": f"NSFL 熔断：触碰法律负空间 {hits}，已封禁（SBX-BANNED）并存证 [SIMULATED]"}]})

        # 越界（A7）：实参触及卡声明的场景限制/需审批档 ⟹ 降级 SBX-SUSPENDED + 熔断 NCA
        ns = card.get("ns_types", {})
        text = json.dumps(args, ensure_ascii=False)
        crossed = [str(x) for k in ("scene_limited", "approval_required")
                   for x in ns.get(k, []) if str(x) and str(x) in text]
        if crossed:
            a = self.state.suspend(fp, self.config["suspend_hours"])
            self.wm.stamp(self.caller, "tdca:echo", args,
                          f"REJECTED-SUSPENDED crossed={crossed}", rejected=True,
                          space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_SUSPENDED)
            return self._ok(rid, {"isError": True, "content": [{"type": "text",
                "text": f"越界：触及声明边界 {crossed}，已降级 SBX-SUSPENDED"
                        f"（限期重整至 {a['suspended_until']}），熔断 NCA 已落 [SIMULATED]"}]})

        # 四判（A3）：全过才出 NSFL-CERT 升 SBX；未过零消耗拒绝（无 CERT 不升 SBX）
        j = trispace.run_four_judgments(card, args, [], self.config)
        if not j["passed"]:
            return self._err(rid, trispace.CODE_JUDGMENT_FAIL,
                             trispace.MSG_JUDGMENT_FAIL.format(detail=j["detail"]))
        cert = trispace.issue_cert(fp, j, self.config)
        self.state.admit_sbx(fp, cert)
        out = f"[SIMULATED] echo: {args.get('text', '')}"
        nca = self.wm.stamp(self.caller, "tdca:echo", args, out,
                            space_id=trispace.SPACE_SBX, status=trispace.ST_SBX_ACTIVE)
        self.state.data["agents"][fp]["writes"] += 1
        self.state.save()
        return self._ok(rid, {"content": [{"type": "text", "text":
            f"{out}\n（存证 {nca['NCA-ID']} space_id=SBX status=SBX-ACTIVE；"
            f"NSFL-CERT {cert['cert_id']} 有效期至 {cert['expires_at']}；"
            f"输出哈希 {nca['Post-State']['Hash'][:24]}…）"}]})

    def _call(self, rid, params: dict) -> dict:
        name = params.get("name", "")
        args = params.get("arguments") or {}
        known = {t["name"] for t in TOOLS}
        if name not in known:
            return self._err(rid, -32602, f"Unknown tool: {name}")
        if name == "tdca:echo":
            return self._write_pipeline(rid, dict(args))
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
