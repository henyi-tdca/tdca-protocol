"""MCP stdio 桥 → HTTP 门面（仅供测试云门户实测；每次调用子进程跑桥，存证落 /evidence）"""
import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mcp_bridge import official_invoke

app = FastAPI(title="tdca-mcp-http-shim", version="0.1.0")
EV = Path(os.environ.get("TDCA_MCP_EVIDENCE", "/evidence"))  # 可测性：本地测试指临时卷
EV.mkdir(parents=True, exist_ok=True)

# INTERFACE-001 批4：官方能力调用 API 面（复用 tools/mcp_bridge/official_invoke.py 单一判据源）
_svc = official_invoke.OfficialInvokeService(EV)

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
                    "clientInfo": {"name": "anonymous", "version": "1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": req.name, "arguments": req.arguments}},
    ]
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_bridge", "--evidence", str(EV), "--caller", "anonymous"],
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


@app.post("/api/v1/official/invoke")
def official_invoke_api(body: dict = Body(...), request: Request = None):
    """官方能力调用（INTERFACE-001）：全部判据在 official_invoke.handle 内，此处只取头与转发。"""
    status, resp = _svc.handle(
        body,
        card_header=(request.headers.get("X-TDCA-Agent-Card") if request else None),
        contract=(request.headers.get("X-TDCA-Contract") if request else None),
        user_agent=(request.headers.get("user-agent") if request else None),
        source_header=(request.headers.get("X-TDCA-Source") if request else None),
    )
    return JSONResponse(resp, status_code=status)
