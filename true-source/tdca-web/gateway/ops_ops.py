# -*- coding: utf-8 -*-
"""
P7 站点运维端（A-18）：/api/v1/ops/* —— 应用测试期运维工作台。

流程（组三 P7 要件 1）：问题反馈 → 红线分类器 → 诊断/变更提案 → 沙盒验证
（simulated=True 先行）→ 回归（走 P5 CI 手动入口 /api/v1/ci/run）→ 上线登记
（NCA 存证＋reconcile 对账·可回滚）。
红线八项（写死，⛔ 不改名、不增删）：触碰即升 ESCALATED_DCD，运维端无权处置。
第八项「登记制度」以在册《TDCA 注册登记制度》（V1.0-FROZEN）为唯一权威源——
本端只列名目与索引入口；该制度件物理落位不在本仓（如实标注，不重写、不复制）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402
# P9 同源一致：红线第八项（登记制度）索引入口与 /api/v1/regulations/index 同 helper
from regulations_ops import regulation_index_entry  # noqa: E402

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])

# 红线八项（写死；名目照在册交办件，⛔ 不改写/增删）——分类器关键词仅作命中线索
RED_LINES = [
    {"key": "constitution", "name": "宪法十六条",
     "keywords": ["宪法"]},
    {"key": "contract3", "name": "缔约三件套",
     "keywords": ["缔约三件套", "注册即缔约"]},
    {"key": "nca6", "name": "NCA 六要素语义",
     "keywords": ["NCA 六要素"]},
    {"key": "nsfl", "name": "NSFL 根本负空间",
     "keywords": ["NSFL", "根本负空间"]},
    {"key": "config3", "name": "配置权三层结构",
     "keywords": ["配置权三层"]},
    {"key": "mou", "name": "MOU 税收锚定下限",
     "keywords": ["MOU 税收锚定", "税收锚定下限"]},
    {"key": "posum", "name": "协作须正和效用",
     "keywords": ["正和效用"]},
    {"key": "registry", "name": "登记制度",
     "keywords": ["登记制度", "注册登记制度"],
     "index": "在册《TDCA 注册登记制度》（V1.0-FROZEN）为唯一权威源——"
              "索引入口与 /api/v1/regulations/index 同源"
              "（docs/regulations/ 收录状态动态读取）；"
              "本端只列名目与索引入口，⛔ 不重写正文、⛔ 不复制另存"},
]
_REDLINE_INDEX = {r["key"]: r for r in RED_LINES}


def _redline_index(r: dict) -> str:
    """索引入口：第八项（登记制度）与规范索引区同源动态读取（⛔ 不硬编码收录状态）。"""
    if r["key"] == "registry":
        entry = regulation_index_entry("registration_registry")
        return (f"在册《TDCA 注册登记制度》（V1.0-FROZEN）为唯一权威源——"
                f"索引入口与 /api/v1/regulations/index 同源"
                f"（docs/regulations/ 收录状态：{'已收录' if entry['present'] else '未收录'}）；"
                f"本端只列名目与索引入口，⛔ 不重写正文、⛔ 不复制另存")
    return r.get("index", "名目在册（本端只列名目与索引入口）")


@router.get("/redlines")
def redlines(request: Request):
    """红线八项目录（名目＋索引入口；第八项与规范索引区同源，不重写正文）。"""
    _require_session_user(request)
    return _nca_watermark({
        "count": len(RED_LINES),
        "red_lines": [{"key": r["key"], "name": r["name"],
                       "index": _redline_index(r)} for r in RED_LINES],
        "note": "触碰任一红线即升 DCD，运维端无权处置（⛔ 名目写死，不改增删）"})


def _classify(text: str) -> list:
    """红线分类器：命中任一红线关键词即返回红线名目（升 DCD 依据）。"""
    hits = []
    for r in RED_LINES:
        if any(k in text for k in r["keywords"]):
            hits.append(r["name"])
    return hits


class FeedbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    description: str = ""


@router.post("/feedback", status_code=201)
def feedback(req: FeedbackIn, request: Request):
    """问题反馈入口（登录用户皆可；落库即入 INTAKE）。"""
    user = _require_session_user(request)
    if not req.title.strip():
        raise HTTPException(400, "title 不得为空")
    tid = f"OPS-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("OPS_FEEDBACK", user["username"],
                          artifact_path=f"ops:{tid}")
    with get_sessionmaker().begin() as s:
        s.add(M.OpsTicket(
            ticket_id=tid, title=req.title.strip(),
            description=req.description.strip() or None,
            status="INTAKE", nca_ref=nca_ref, created_at=_utc(),
            updated_at=_utc()))
    return _nca_watermark({"ticket_id": tid, "status": "INTAKE", "nca_ref": nca_ref,
                           "note": "反馈已入池（待红线分类）"})


class TicketRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str


@router.post("/classify")
def classify(req: TicketRef, request: Request):
    """红线分类器（operator/founder）：命中红线 → 升 ESCALATED_DCD，运维端无权处置。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可分类")
    with get_session() as s:
        row = s.get(M.OpsTicket, req.ticket_id)
    if row is None:
        raise HTTPException(404, "ticket_id 不存在")
    text = f"{row.title}\n{row.description or ''}"
    hits = _classify(text)
    if hits:
        nca_ref = _nca_append("OPS_ESCALATE_DCD", user["username"],
                              artifact_path=f"ops:{row.ticket_id}")
        with get_sessionmaker().begin() as s:
            r = s.get(M.OpsTicket, req.ticket_id)
            r.status = "ESCALATED_DCD"
            r.redline_hit = "；".join(hits)
            r.classifier_note = "触碰根本制度红线——升 DCD，运维端无权处置"
            r.nca_ref = nca_ref
            r.updated_at = _utc()
        return _nca_watermark({"ticket_id": row.ticket_id, "status": "ESCALATED_DCD",
                               "redline_hit": hits, "nca_ref": nca_ref,
                               "note": "触碰红线即停手上报（运维端不处置制度层事项）"})
    with get_sessionmaker().begin() as s:
        r = s.get(M.OpsTicket, req.ticket_id)
        r.status = "CLASSIFIED"
        r.classifier_note = "未触碰八项红线（分类器关键词全否）"
        r.updated_at = _utc()
    return _nca_watermark({"ticket_id": row.ticket_id, "status": "CLASSIFIED",
                           "redline_hit": [],
                           "note": "未触碰红线——可进入诊断/变更提案流程"})


class ProposalIn(TicketRef):
    proposal: str = ""


@router.post("/propose")
def propose(req: ProposalIn, request: Request):
    """变更提案（operator/founder；仅 CLASSIFIED 可提案）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可提案")
    if not req.proposal.strip():
        raise HTTPException(400, "proposal 不得为空")
    with get_session() as s:
        row = s.get(M.OpsTicket, req.ticket_id)
    if row is None:
        raise HTTPException(404, "ticket_id 不存在")
    if row.status == "ESCALATED_DCD":
        raise HTTPException(403, "已升 DCD——运维端无权处置，⛔ 不得提案")
    with get_sessionmaker().begin() as s:
        r = s.get(M.OpsTicket, req.ticket_id)
        r.status = "PROPOSED"
        r.proposal = req.proposal.strip()
        r.updated_at = _utc()
    return _nca_watermark({"ticket_id": row.ticket_id, "status": "PROPOSED",
                           "note": "变更提案已登记（下一步：沙盒验证 simulated=True 先行）"})


@router.post("/sandbox")
def sandbox(req: TicketRef, request: Request):
    """沙盒验证登记（simulated=True 先行；PROPOSED 方可进入）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可登记")
    with get_session() as s:
        row = s.get(M.OpsTicket, req.ticket_id)
    if row is None:
        raise HTTPException(404, "ticket_id 不存在")
    if row.status != "PROPOSED":
        raise HTTPException(409, f"当前状态 {row.status} 不可进沙盒（须 PROPOSED）")
    with get_sessionmaker().begin() as s:
        r = s.get(M.OpsTicket, req.ticket_id)
        r.status = "SANDBOXED"
        r.classifier_note = (r.classifier_note or "") + " ｜ 沙盒验证 simulated=True 先行"
        r.updated_at = _utc()
    return _nca_watermark({"ticket_id": row.ticket_id, "status": "SANDBOXED",
                           "simulated": True,
                           "note": "沙盒验证（模拟态先行；回归走 P5 CI 手动入口 /api/v1/ci/run）"})


@router.post("/release")
def release(req: TicketRef, request: Request):
    """上线登记（SANDBOXED 方可；NCA 存证＋对账留痕·可回滚）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可登记上线")
    with get_session() as s:
        row = s.get(M.OpsTicket, req.ticket_id)
    if row is None:
        raise HTTPException(404, "ticket_id 不存在")
    if row.status != "SANDBOXED":
        raise HTTPException(409, f"当前状态 {row.status} 不可上线（须 SANDBOXED）")
    nca_ref = _nca_append("OPS_RELEASE", user["username"],
                          artifact_path=f"ops:{row.ticket_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.OpsTicket, req.ticket_id)
        r.status = "RELEASED"
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    return _nca_watermark({"ticket_id": row.ticket_id, "status": "RELEASED",
                           "nca_ref": nca_ref,
                           "note": "上线已登记（NCA 存证；对账走 deploy/reconcile.py --ledger，可回滚）"})


@router.get("/tickets")
def tickets(request: Request, status: str = ""):
    _require_session_user(request)
    with get_session() as s:
        q = s.query(M.OpsTicket).order_by(M.OpsTicket.created_at)
        if status:
            q = q.filter_by(status=status)
        rows = q.all()
    return _nca_watermark({"count": len(rows), "tickets": [
        {"ticket_id": r.ticket_id, "title": r.title, "status": r.status,
         "redline_hit": r.redline_hit, "updated_at": r.updated_at} for r in rows]})
