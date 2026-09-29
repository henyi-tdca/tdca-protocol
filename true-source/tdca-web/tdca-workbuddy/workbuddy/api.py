# -*- coding: utf-8 -*-
"""
P5 Workbuddy API（FastAPI）
锚定: TDCA-TASKBOOK-5CC-P5-WB P5 接口契约（/workflow/create·execute·status + /signature/request·confirm）
     + 绝对负空间（L 级不直接跨场景 / 签名不可绕过 / WORM 日志）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import CrossSceneWorkflowEngine, WorkflowDSL

app = FastAPI(title="P5 Workbuddy", version="T-P5-001")

_engine = CrossSceneWorkflowEngine()
_workflows: Dict[str, WorkflowDSL] = {}
_signature_requests: Dict[str, Dict[str, Any]] = {}


class CreateRequest(BaseModel):
    cscp_handshake_id: str
    workflow_template: Dict[str, Any]


class ExecuteRequest(BaseModel):
    workflow_id: str
    human_signature: str


class SignatureRequest(BaseModel):
    workflow_id: str
    gate_id: str
    description: str = ""


class SignatureConfirm(BaseModel):
    request_id: str
    biometric_proof: str = ""
    hardware_signature: str


@app.post("/workflow/create", status_code=201)
def workflow_create(req: CreateRequest) -> Dict[str, Any]:
    try:
        wf = WorkflowDSL.from_dict(req.workflow_template)
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"DSL 无效: {exc}")
    _workflows[wf.workflow_id] = wf
    return _engine.create(wf)


@app.post("/workflow/execute")
def workflow_execute(req: ExecuteRequest) -> Dict[str, Any]:
    wf = _workflows.get(req.workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="workflow_id 不存在")
    try:
        ex = _engine.execute(wf, req.human_signature)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"DSL 依赖错误: {exc}")
    return {"execution_id": ex.execution_id, "workflow_id": wf.workflow_id,
            "status": ex.status, "current_step": ex.current_step,
            "nsfl_status": ex.nsfl_status, "nca_refs": ex.nca_refs}


@app.get("/workflow/status")
def workflow_status(execution_id: str) -> Dict[str, Any]:
    try:
        ex = _engine.status(execution_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="execution_id 不存在")
    return {"workflow_id": ex.workflow_id, "status": ex.status,
            "current_step": ex.current_step, "nsfl_status": ex.nsfl_status,
            "nca_refs": ex.nca_refs, "results": list(ex.results.keys())}


@app.post("/signature/request", status_code=201)
def signature_request(req: SignatureRequest) -> Dict[str, Any]:
    rid = f"SR-{uuid.uuid4().hex[:10]}"
    _signature_requests[rid] = {"workflow_id": req.workflow_id, "gate_id": req.gate_id,
                                "description": req.description}
    return {"signature_request_id": rid, "notification_sent": True}


@app.post("/signature/confirm")
def signature_confirm(req: SignatureConfirm) -> Dict[str, Any]:
    """硬件级签名确认（模拟：hardware_signature 非空 + 长度 ≥8 视为有效硬件签名）。"""
    sr = _signature_requests.get(req.request_id)
    if sr is None:
        raise HTTPException(status_code=404, detail="request_id 不存在")
    if not req.hardware_signature or len(req.hardware_signature) < 8:
        raise HTTPException(status_code=403,
                            detail="HARDWARE_SIGNATURE_INVALID（检测到自动化签名尝试 → 熔断）")
    return {"verified": True, "tx_hash": f"0xSIG-{req.request_id}",
            "gate_id": sr["gate_id"]}


@app.get("/workflow/log-integrity")
def log_integrity() -> Dict[str, Any]:
    """WORM 日志完整性（P5 绝对负空间 3：日志不可篡改）。"""
    return {"integrity": _engine.verify_log_integrity(), "log_entries": len(_engine._log)}
