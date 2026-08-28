"""MCP stdio 桥 → HTTP 门面（仅供测试云门户实测；每次调用子进程跑桥，存证落 /evidence）"""
import json
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="tdca-mcp-http-shim", version="0.1.0")
EV = Path("/evidence")
EV.mkdir(parents=True, exist_ok=True)

ALLOWED = {"tdca:echo", "nca:get", "nca:chain", "tdca:core"}


class CallReq(BaseModel):
    name: str
    arguments: dict = {}


@app.get("/health")
def health():
    return {"ok": True, "bridge": "tdca-mcp-bridge stdio", "tools": sorted(ALLOWED)}


@app.post("/call")
def call(req: CallReq):
    if req.name not in ALLOWED:
        return {"ok": False, "error": f"unknown tool: {req.name}"}
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "cloud-portal", "version": "1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": req.name, "arguments": req.arguments}},
    ]
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_bridge", "--evidence", str(EV), "--caller", "cloud-portal"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8")
        out, _ = proc.communicate("\n".join(json.dumps(m, ensure_ascii=False) for m in msgs) + "\n",
                                  timeout=20)
    except Exception as e:
        return {"ok": False, "error": f"bridge error: {e}"}
    resps = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            try:
                resps.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    result = next((r for r in resps if r.get("id") == 2), None)
    if result is None:
        return {"ok": False, "error": "no response from bridge", "raw": resps}
    return {"ok": True, "result": result.get("result", result.get("error"))}
