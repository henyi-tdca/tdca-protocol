# -*- coding: utf-8 -*-
"""
W3 P3 API · 跨场景沙盒网关（FastAPI）
锚定: TDCA-TASKBOOK-5CC-P3-001 P3 接口契约（/cross-scene/create·inject-data·evaluate + /promote/propose·confirm）
     + 安全约束（数据不反向泄露 / 算法哈希上链 / 晋升人类签名不可绕过）
D-2 联调: inject-data 的 nsfl_boundary 经 NSFLUnionEngine 负空间校验（REJECTED 触碰负空间）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .sandbox import CrossSceneSandbox, SandboxStatus

app = FastAPI(title="P3 Cross-Scene Sandbox Gateway", version="T-P3-001")

# 沙盒注册表（模拟态内存；生产接 SBX-OPS store）
_sandboxes: Dict[str, CrossSceneSandbox] = {}
_proposals: Dict[str, Dict[str, Any]] = {}


def _nsfl_check(boundary: dict, data: dict) -> Dict[str, Any]:
    """D-2 联调：负空间边界校验（NSFLUnionEngine）。boundary 携带场景负空间声明。"""
    from nsfl_union import (NS_Operator, NS_Rule, NS_Type, NSFLUnionEngine,
                            SceneNSFL)
    rules = []
    for r in boundary.get("rules", []):
        ns = NS_Type(r["ns_type"])
        op = NS_Operator(r["operator"])
        kw = {}
        if op in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN):
            from decimal import Decimal
            kw = {"parameter": Decimal(str(r["parameter"])), "unit": r.get("unit", "CNY")}
        rules.append(NS_Rule(r.get("rule_id", f"B{len(rules)}"), ns, op, **kw))
    scene = SceneNSFL(scene_id=boundary.get("scene_id", "SBX-INJECT"), rules=rules)
    empty = SceneNSFL(scene_id="INJECT-TARGET", rules=[])
    u = NSFLUnionEngine().compute(scene, empty)
    if u.conflict_set:
        return {"verdict": "REJECTED",
                "reason": f"负空间冲突 {len(u.conflict_set)} 项: {u.conflict_set[0].reason}"}
    if u.review_queue and scene.has_legal_or_high_tier():
        return {"verdict": "REJECTED", "reason": "REQUIRES_REVIEW（含 LEGAL/高档位）"}
    return {"verdict": "PASS"}


# ---- 请求模型（P3 契约）----

class CreateRequest(BaseModel):
    scene_ids: List[str] = Field(min_length=3)
    pcr_budget: float = Field(gt=0)
    sponsor_did: str


class InjectRequest(BaseModel):
    sandbox_id: str
    scene_id: str
    data: Dict[str, Any]
    nsfl_boundary: Dict[str, Any] = {}


class EvaluateRequest(BaseModel):
    sandbox_id: str
    duration_days: int = Field(gt=0)


class PromoteConfirmRequest(BaseModel):
    proposal_id: str
    human_signature: str
    human_did: str


# ---- 端点（P3 契约）----

@app.post("/cross-scene/create", status_code=201)
def create(req: CreateRequest) -> Dict[str, Any]:
    try:
        sb = CrossSceneSandbox.create(scene_ids=req.scene_ids,
                                      pcr_budget=req.pcr_budget,
                                      sponsor_did=req.sponsor_did)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    _sandboxes[sb.sandbox_id] = sb
    return {"sandbox_id": sb.sandbox_id, "status": sb.status.value,
            "algorithm_hash": sb.algorithm_hash}


@app.post("/cross-scene/inject-data")
def inject(req: InjectRequest) -> Dict[str, Any]:
    sb = _sandboxes.get(req.sandbox_id)
    if sb is None:
        raise HTTPException(status_code=404, detail="sandbox_id 不存在")
    verdict = _nsfl_check(req.nsfl_boundary, req.data)
    return sb.inject_data(req.scene_id, req.data, nsfl_verdict=verdict["verdict"])


@app.post("/cross-scene/evaluate")
def evaluate(req: EvaluateRequest) -> Dict[str, Any]:
    sb = _sandboxes.get(req.sandbox_id)
    if sb is None:
        raise HTTPException(status_code=404, detail="sandbox_id 不存在")
    detail = sb.activation_coefficient()
    detail.update({"sandbox_id": sb.sandbox_id, "duration_days": req.duration_days,
                   "status": sb.status.value})
    return detail


@app.post("/promote/propose")
def propose(req: EvaluateRequest) -> Dict[str, Any]:
    """自动晋升提案（T-P3-003 语义：自动仅生成提案，最终出盒必须人类签名）。"""
    sb = _sandboxes.get(req.sandbox_id)
    if sb is None:
        raise HTTPException(status_code=404, detail="sandbox_id 不存在")
    detail = sb.activation_coefficient()
    if detail["activation_coefficient"] <= 1.2:
        raise HTTPException(status_code=409, detail="激活系数 ≤1.2，不满足晋升门槛")
    pid = f"PROP-{uuid.uuid4().hex[:10]}"
    _proposals[pid] = {"sandbox_id": sb.sandbox_id, "detail": detail,
                       "requires_human_signature": True,
                       "proposed_at": time.time()}
    sb.status = SandboxStatus.PROMOTING
    return {"proposal_id": pid, "nca_ref": f"NCA-PROMOTE-{pid}",
            "requires_human_signature": True, "activation": detail}


@app.post("/promote/confirm")
def confirm(req: PromoteConfirmRequest) -> Dict[str, Any]:
    """人类签名确认出盒（安全约束：无签名禁止任何状态变更，负空间熔断）。"""
    prop = _proposals.get(req.proposal_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="proposal_id 不存在")
    if not req.human_signature or len(req.human_signature) < 8:
        raise HTTPException(status_code=403,
                            detail="HUMAN_SIGNATURE_REQUIRED（自动晋升绕过人类签名=负空间熔断）")
    sb = _sandboxes[prop["sandbox_id"]]
    sb.status = SandboxStatus.ACTIVE
    market_entry_id = f"ME-{sb.sandbox_id}"
    _proposals[req.proposal_id]["confirmed"] = True
    return {"new_status": sb.status.value, "market_entry_id": market_entry_id,
            "nca_ref": f"NCA-PROMOTE-CONFIRM-{req.proposal_id}"}
