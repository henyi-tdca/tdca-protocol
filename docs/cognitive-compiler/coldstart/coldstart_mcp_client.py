# -*- coding: utf-8 -*-
"""TDCA 冷启动 · MCP 外部 agent 客户端(stdio 手写帧, 纯标准库)
=========================================================
模拟"自定义连接器"对外部 agent 的真实调用: 启动 server 子进程, 走 MCP stdio JSON-RPC 帧,
调用 load_core(取身份/能力画像) 与 contribute_cop(取贡献物)。
输出: (profile_dict, cop_yaml_str, tool_names)
与 mcp_external_agent_server.py 手写帧同构, 零第三方依赖。
"""
import json
import subprocess
import sys

_PY = "C:/Users/22850/.workbuddy/binaries/python/envs/default/Scripts/python.exe"


def _send_buf(wbuf, msg):
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    wbuf.write(b"Content-Length: %d\r\n\r\n" % len(data))
    wbuf.write(data)
    wbuf.flush()


def _read_frame(rbuf):
    header = b""
    while b"\r\n\r\n" not in header:
        ch = rbuf.read(1)
        if not ch:
            return None
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
        ch = rbuf.read(1)
        if not ch:
            return None
        body += ch
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def connect_external_agent(server_path: str):
    """同步入口: 真实连外部 MCP agent, 返回 (profile, cop_yaml, tool_names)。"""
    proc = subprocess.Popen([_PY, server_path],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    wbuf = proc.stdin
    rbuf = proc.stdout
    try:
        _send_buf(wbuf, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "tdca-coldstart", "version": "0.1"}}})
        _read_frame(rbuf)
        _send_buf(wbuf, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        _send_buf(wbuf, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tl = _read_frame(rbuf)
        tool_names = [t["name"] for t in tl["result"]["tools"]]
        _send_buf(wbuf, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": "load_core", "arguments": {}}})
        lc = _read_frame(rbuf)
        profile = json.loads(lc["result"]["content"][0]["text"])
        _send_buf(wbuf, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                        "params": {"name": "contribute_cop",
                                   "arguments": {"topic": "开源社区冷启动·正和准入"}}})
        cp = _read_frame(rbuf)
        cop_yaml = cp["result"]["content"][0]["text"]
        return profile, cop_yaml, tool_names
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
