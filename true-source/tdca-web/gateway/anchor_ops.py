# -*- coding: utf-8 -*-
"""
P6 模拟外部锚与版权事件（A-17）：/api/v1/anchor/* —— 三锚全 SIMULATED 硬标注。

口径（组三 P6）：
  - 版权事件一律收为「权属登记事件」＝登记／变更／注销（模板＝在册
    docs/contracts/copyright-event-templates-v1.0.yaml，先立之事件模板）；
    ⛔ 转让／许可不在一期（归 8b）——请求即 400 fail-closed；
  - 跑在版权链模拟锚上：事件落 NCA 链（nca_chain）＋ 组件在位核查
    （nca-generator / AXIOM6 审计引擎 / notary / NCA 模板集——如实报在位与否，不冒充接入）；
  - 三锚：版权链＝NCA 链（站内模拟）／结算＝站内积分模拟／税务＝金税四期功能模拟；
    全程 SIMULATED 硬标注，⛔ 零外部依赖、⛔ 不冒充真实 e-CNY／真实结算／真实税务申报。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/anchor", tags=["anchor"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVENT_TEMPLATE = "docs/contracts/copyright-event-templates-v1.0.yaml"

_ANCHORS = {
    "copyright_chain": "SIMULATED（NCA 链·站内模拟；事件落 nca_chain 存证）",
    "settlement": "SIMULATED（站内积分模拟数字人民币结算功能）",
    "tax": "SIMULATED（金税四期功能模拟）",
}
_EVENT_TYPES = {"register": "CRIGHT-EVENT-001", "amend": "CRIGHT-EVENT-002",
                "cancel": "CRIGHT-EVENT-003"}


def _component_presence() -> dict:
    """组件在位核查（如实报，不冒充接入）。"""
    return {
        "event_template": _EVENT_TEMPLATE if (_REPO_ROOT / _EVENT_TEMPLATE).is_file()
                          else "MISSING",
        "nca_generator": "docs/cognitive-compiler/cop-compiler/compiler_src/nca_generator.py"
                         if (_REPO_ROOT / "docs/cognitive-compiler/cop-compiler/compiler_src"
                             / "nca_generator.py").is_file() else "MISSING",
        "axiom6_audit": "core-go/pkg/enforce/axiom6.go"
                        if (_REPO_ROOT / "core-go/pkg/enforce/axiom6.go").is_file()
                        else "MISSING",
        "notary": "tools/dca_sandbox/notary.py"
                  if (_REPO_ROOT / "tools/dca_sandbox/notary.py").is_file() else "MISSING",
        "nca_template_set": "docs/contracts/contract-templates-v1.0.yaml"
                            if (_REPO_ROOT / "docs/contracts/contract-templates-v1.0.yaml")
                            .is_file() else "MISSING",
    }


@router.get("/status")
def anchor_status(request: Request):
    """三锚状态（全 SIMULATED 硬标注＋组件在位核查）。"""
    _require_session_user(request)
    return _nca_watermark({
        "simulated": True,
        "anchors": _ANCHORS,
        "components": _component_presence(),
        "note": "三类外部锚均为站内模拟；⛔ 不冒充真实 e-CNY／真实结算／真实税务申报"
                "（永久范围外）"})


class CopyrightEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str = ""        # register / amend / cancel
    work_title: str = ""
    owner_ref: str = ""
    source_lineage: str = ""    # 生成来源谱系（8a 口径；cancel/amend 可空）
    note: str = ""


@router.post("/copyright-event", status_code=201)
def copyright_event(req: CopyrightEvent, request: Request):
    """权属登记事件（登记／变更／注销）→ 落库＋NCA 链存证（版权链模拟锚载体）。"""
    user = _require_session_user(request)
    if req.event_type in ("transfer", "license"):
        raise HTTPException(400, "OUT_OF_SCOPE: 转让／许可属权利处分，⛔ 本期不做（归 8b 后续）")
    if req.event_type not in _EVENT_TYPES:
        raise HTTPException(400, "EVENT_TYPE_INVALID: 仅受理 登记(register)／"
                                 "变更(amend)／注销(cancel)")
    if not req.work_title.strip() or not req.owner_ref.strip():
        raise HTTPException(400, "work_title 与 owner_ref 为必填（权属登记事件）")
    if req.event_type == "register" and not req.source_lineage.strip():
        raise HTTPException(400, "登记事件须载生成来源谱系 source_lineage（8a 口径）")
    eid = f"CE-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append(f"CRIGHT_{req.event_type.upper()}",
                          user["username"], artifact_path=f"copyright:{eid}")
    with get_sessionmaker().begin() as s:
        s.add(M.CopyrightEvent(
            event_id=eid, event_type=req.event_type,
            work_title=req.work_title.strip(), owner_ref=req.owner_ref.strip(),
            source_lineage=req.source_lineage.strip() or None,
            note=req.note.strip() or None, template_ref=_EVENT_TYPES[req.event_type],
            nca_ref=nca_ref, created_at=_utc()))
    return _nca_watermark({
        "event_id": eid, "event_type": req.event_type,
        "template_ref": _EVENT_TYPES[req.event_type], "nca_ref": nca_ref,
        "simulated": True, "anchors": _ANCHORS,
        "note": "权属登记事件已落 NCA 链（版权链模拟锚）；"
                "三锚全 SIMULATED——⛔ 不冒充真实锚"})


@router.get("/copyright-events")
def copyright_events(request: Request, event_type: str = ""):
    _require_session_user(request)
    with get_session() as s:
        q = s.query(M.CopyrightEvent).order_by(M.CopyrightEvent.created_at)
        if event_type:
            if event_type not in _EVENT_TYPES:
                raise HTTPException(400, "event_type 过滤值非法")
            q = q.filter_by(event_type=event_type)
        rows = q.all()
    return _nca_watermark({
        "simulated": True, "count": len(rows),
        "events": [{"event_id": r.event_id, "event_type": r.event_type,
                    "work_title": r.work_title, "owner_ref": r.owner_ref,
                    "template_ref": r.template_ref, "nca_ref": r.nca_ref}
                   for r in rows],
        "note": "权属登记事件清单（登记／变更／注销；⛔ 不含转让／许可）"})
