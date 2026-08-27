# -*- coding: utf-8 -*-
"""MCP / 连接器候选源 —— 真实全网接入点
=========================================================
设计要点:
  1. 本 Provider 实现 CandidateProvider 接口, 与 LocalProvider 完全同构
     -> 引擎无需改动即可热插拔到真实全网。
  2. 若配置声明的 MCP 工具可用, 经 stdio MCP 客户端调用它拉取真实主体;
  3. 若不可用 (未连接/无权限/抛错), 自动回退 LocalProvider, 保证引擎可运行。
  4. _call_mcp 是真实接入契约: 把"tdca-wan-registry 类连接器"暴露的
     list_entities 工具接入即可启用真实全网源 (见 _MCPStdioClient)。
"""
import os
import sys
import json
import subprocess

from .base import Candidate, CandidateProvider
from .local_provider import LocalProvider

_THIS = os.path.dirname(os.path.abspath(__file__))          # providers/
_SERVER_DEFAULT = os.path.join(os.path.dirname(_THIS),
                               "wan_registry_mcp_server.py")  # 同目录的演示 server


# ------------------------------------------------------------
# 最小 MCP stdio 客户端 (JSON-RPC over stdio, Content-Length 帧)
# 仅依赖标准库, 不需要 mcp SDK; 与 wan_registry_mcp_server 同协议。
# ------------------------------------------------------------
class _MCPStdioClient:
    def __init__(self, command, args, stderr_to=None):
        self.proc = subprocess.Popen(
            [command] + list(args),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=(stderr_to or subprocess.DEVNULL))
        self._id = 0

    def _send(self, msg):
        data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(data))
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def _recv_frame(self):
        """严格按帧读: 头部逐字节读到 \\r\\n\\r\\n, 正文按 Content-Length 精确读满。
        注意: 管道上 read(N) 会阻塞到读满 N 字节, 故不可用 read(4096) 猜长度。"""
        header = b""
        while b"\r\n\r\n" not in header:
            ch = self.proc.stdout.read(1)
            if not ch:
                return None                       # server EOF
            header += ch
        length = None
        for line in header.decode("utf-8", "replace").split("\r\n"):
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
        if length is None:
            return None
        body = b""
        while len(body) < length:
            chunk = self.proc.stdout.read(length - len(body))
            if not chunk:
                return None
            body += chunk
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def _recv(self, want_id):
        while True:
            msg = self._recv_frame()
            if msg is None:
                return None
            if msg.get("id") == want_id:          # 只认匹配 id 的响应 (忽略通知)
                return msg

    def initialize(self):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "tdca-sm-test", "version": "0.1"}}})
        resp = self._recv(want_id=self._id)
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return resp

    def list_tools(self):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "tools/list", "params": {}})
        return self._recv(want_id=self._id)

    def call_tool(self, name, arguments):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}})
        return self._recv(want_id=self._id)

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.kill()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=2)
        except Exception:
            pass


class MCPProvider(CandidateProvider):
    def __init__(self, connector_cfg: dict = None):
        self.cfg = connector_cfg or {}
        self._fallback = LocalProvider(
            path=self.cfg.get("local_fallback_path"),
            scale=self.cfg.get("local_fallback_scale", 0))

    @property
    def source_name(self):
        return "mcp:" + self.cfg.get("connector_name", "unbound")

    def load(self, dims, task_id=""):
        tool = self.cfg.get("tool_name") or "list_entities"
        try:
            if tool:
                rows = self._call_mcp(tool, dims=dims, task_id=task_id,
                                      query=self.cfg.get("query", ""))
                cands = [self._to_candidate(r, dims) for r in rows]
                if cands:
                    print(f"[MCP] 连接器 '{tool}' 拉取真实主体 {len(cands)} 个 (全网源已接入)")
                    return cands
        except Exception as e:   # 连接器不可用 -> 优雅回退, 不中断引擎
            print(f"[MCP] 连接器 '{tool}' 不可用 ({type(e).__name__}: {e}); 回退本地源")
        return self._fallback.load(dims, task_id)

    # ---- 真实接入: 经 stdio MCP 客户端调用连接器 ----
    def _call_mcp(self, tool_name, **kwargs):
        cmd = self.cfg.get("server_command") or sys.executable
        srv = self.cfg.get("server_args") or [_SERVER_DEFAULT]
        client = _MCPStdioClient(cmd, srv)
        try:
            client.initialize()
            tools = client.list_tools() or {}
            tool_names = [t.get("name") for t in
                          tools.get("result", {}).get("tools", [])]
            if tool_name not in tool_names:
                raise RuntimeError(
                    f"连接器未暴露工具 '{tool_name}'; 可用: {tool_names}")
            result = client.call_tool(tool_name, {
                "query": kwargs.get("query", ""),
                "dims": list(kwargs.get("dims", [])),
            })
            content = (result or {}).get("result", {}).get("content", [])
            text = "".join(c.get("text", "") for c in content
                           if c.get("type") == "text")
            rows = json.loads(text)
            return rows
        finally:
            client.close()

    def _to_candidate(self, row, dims):
        return Candidate(
            id=str(row["id"]), name=str(row.get("name", "")), cop=str(row.get("cop", "")),
            res={d: float(row.get("res", {}).get(d, 0.0)) for d in dims},
            batna=float(row.get("batna", 0)), source=self.source_name)
