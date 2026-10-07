# -*- coding: utf-8 -*-
"""
配置权市场「管理」面：/api/v1/market-admin/* —— 挂出／查询／状态变更／下架。

口径（两件在册件；制度面以《配置权市场规范》V1.0-FROZEN 为准，本件不增删制度语义）：
  - 四操作（与已建登记面同粒度，不增设第五项）：
      A-1 挂出——先有成件：权属登记成件（本人为权属登记人）＋授权登记成件
            ＋授权四要件齐（场景约束／五阶资产形态／全构成已授权／法律主体签名）方准挂；
            例外仅沙盒／演练（可先挂、显式标记 sandbox_flag=1、出盒仍须授权）；
            初始条件必公开（空则拒）；
      A-2 查询——本人查全量（含已下架）；公开面四字段（权属信息／授权信息／
            授权状态／获取方式），⛔ 不公开四条负空间照守（写入 fail-closed 拦截）；
      A-3 状态变更——暂停／恢复；原态与新态双留痕（事件表＋NCA 各一笔）；
      A-4 下架——不溯及已生成／已生效授权件（授权登记记录一字不动，存续至其期限）；
  - 权限：挂出／状态变更／下架限权属登记人本人（⛔ 不设代理人、⛔ 管理方不入本面）；
  - fail-closed：判据取不到／校验异常一律拦，⛔ 不默认放行；
  - 每操作落 NCA 存证（无存证不执行）；公开面随操作同步（下架即撤出公开面）；
  - ⛔ 不做：定价／费率／估值／撮合／结算／争议／推送排行（属规范运营面）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402
from authorization_ops import _public_space_hits  # noqa: E402  负空间词面复用（⛔ 不另造判据）

router = APIRouter(prefix="/api/v1/market-admin", tags=["market-admin"])

# 状态机：active ↔ paused；delisted 终态（不溯及授权件）
_STATUSES = ("active", "paused", "delisted")
_ACTIONS = {"pause": ("active", "paused"), "resume": ("paused", "active")}


def _view(r: M.MarketListing) -> dict:
    """内部全量视图（本人面）。"""
    return {"listing_id": r.listing_id, "owner_ref": r.owner_ref,
            "ownership_record_id": r.ownership_record_id,
            "authorization_record_id": r.authorization_record_id,
            "asset_summary": r.asset_summary, "scene": r.scene,
            "scope_note": r.scope_note, "term_note": r.term_note,
            "initial_conditions": r.initial_conditions,
            "sandbox_flag": bool(r.sandbox_flag), "status": r.status,
            "nca_ref": r.nca_ref, "data_provenance": r.data_provenance,
            "published_at": r.published_at, "updated_at": r.updated_at}


def _public_view(r: M.MarketListing) -> dict:
    """公开面四字段（照授权面公开投影之形；⛔ 不公开四条不入面）。"""
    return {"listing_id": r.listing_id,
            "权属信息": {"ownership_record_id": r.ownership_record_id,
                        "owner_alias": r.owner_ref},
            "授权信息": {"scene": r.scene, "scope_note": r.scope_note,
                        "term_note": r.term_note,
                        "sandbox": bool(r.sandbox_flag)},
            "授权状态": {"listing_status": r.status,
                        "data_provenance": r.data_provenance},
            "获取方式": {"initial_conditions": r.initial_conditions},
            "published_at": r.published_at}


def _ownership_gate(s, username: str, ownership_record_id: str) -> M.OwnershipRecord:
    """身份与权属校验（流程①）：权属登记成件须存在、本人为权属登记人、未注销。
    取不到／不符一律 fail-closed（403），⛔ 不默认放行。"""
    ow = s.get(M.OwnershipRecord, ownership_record_id.strip())
    if ow is None or ow.owner_ref != username or ow.status == "cancelled":
        raise HTTPException(403, "挂出前置未过：须权属登记成件且本人为权属登记人（fail-closed）")
    return ow


def _authorization_gate(s, authorization_record_id: str) -> M.AuthorizationRecord:
    """合规前置闸门（流程②）：授权登记成件须存在＋四要件齐＋未注销。
    缺一即 403 fail-closed（⛔ 不代填代证）。"""
    ar = s.get(M.AuthorizationRecord, authorization_record_id.strip())
    if ar is None:
        raise HTTPException(403, "挂出前置未过：授权登记成件不存在（fail-closed）")
    if not (ar.req_scene and ar.req_five_forms and ar.req_full_grant
            and ar.req_legal_signature):
        raise HTTPException(403, "挂出前置未过：授权四要件未齐（fail-closed）")
    if ar.status == "cancelled":
        raise HTTPException(403, "挂出前置未过：授权登记已注销（fail-closed）")
    return ar


def _events(s, listing_id: str) -> list:
    rows = (s.query(M.MarketListingEvent)
            .filter_by(listing_id=listing_id)
            .order_by(M.MarketListingEvent.created_at).all())
    return [{"event_id": r.event_id, "action": r.action,
             "from_status": r.from_status, "to_status": r.to_status,
             "operator": r.operator, "nca_ref": r.nca_ref,
             "created_at": r.created_at} for r in rows]


def _event(s, listing_id: str, action: str, frm: str, to: str,
           operator: str, nca_ref: str) -> None:
    s.add(M.MarketListingEvent(
        event_id=f"MLE-{uuid.uuid4().hex[:10]}", listing_id=listing_id,
        action=action, from_status=frm, to_status=to, operator=operator,
        nca_ref=nca_ref, created_at=_utc()))


# ---------------------------------------------------------------- 口径回读


@router.get("/rules")
def market_admin_rules(request: Request):
    """管理面口径回读（四操作·闸门·权限·留痕）。"""
    _require_session_user(request)
    return _nca_watermark({
        "four_operations": [
            {"key": "publish", "label": "挂出",
             "rule": "先有成件：权属成件（本人）＋授权成件＋四要件齐；例外仅沙盒演练（出盒须授权）；初始条件必公开"},
            {"key": "query", "label": "查询",
             "rule": "本人查全量；公开面四字段（权属信息／授权信息／授权状态／获取方式）"},
            {"key": "status", "label": "状态变更",
             "rule": "暂停／恢复；原态与新态双留痕（事件表＋NCA）"},
            {"key": "delist", "label": "下架",
             "rule": "不溯及已生成／已生效授权件（授权记录一字不动，存续至其期限）"}],
        "permission": "挂出／状态变更／下架限权属登记人本人（无代理人、管理方不入面）",
        "four_requirements": ["场景约束", "五阶资产形态", "全构成已授权", "法律主体签名"],
        "public_four_fields": ["权属信息", "授权信息", "授权状态", "获取方式"],
        "non_public_four": ["内部编号", "凭据密钥", "自然人敏感信息", "负空间词面"],
        "sandbox_exception": "仅沙盒／演练可先挂（sandbox_flag 显式标记；出盒仍须授权）",
        "not_doing": ["定价", "费率", "估值", "撮合", "结算", "争议", "推送排行"],
        "note": "与已建登记面同粒度；制度面以《配置权市场规范》为准，本面不增删制度语义"},
        nature="real")


# ---------------------------------------------------------------- A-1 挂出


class ListingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ownership_record_id: str                 # 权属登记成件（本人）
    authorization_record_id: str = ""        # 授权登记成件（沙盒例外可空）
    asset_summary: str                       # 标的（五阶资产形态说明）
    scene: str                               # 场景
    scope_note: str = ""                     # 权限范围（照授权件载明，⛔ 不代定）
    term_note: str = ""                      # 期限（照在册已裁者；未裁者不填）
    initial_conditions: str                  # 初始条件（必公开；空则拒）
    sandbox: bool = False                    # 沙盒／演练例外（显式标记）


@router.post("/listings", status_code=201)
def listing_publish(req: ListingIn, request: Request):
    """挂出（A-1）：成件＋四要件合取闸门；沙盒例外显式标记；落 NCA＋事件留痕。"""
    user = _require_session_user(request)
    username = user["username"]

    fields = {"asset_summary": req.asset_summary, "scene": req.scene,
              "scope_note": req.scope_note, "term_note": req.term_note,
              "initial_conditions": req.initial_conditions}
    for k, v in fields.items():
        if not v or not v.strip():
            raise HTTPException(400, f"{k} 不得为空（初始条件必公开）")
    hits = _public_space_hits({k: v for k, v in fields.items()})
    if hits:
        raise HTTPException(400, f"含不公开负空间词面（{','.join(hits)}），fail-closed 拒收")

    with get_session() as s:
        _ownership_gate(s, username, req.ownership_record_id)
        if not req.sandbox:
            _authorization_gate(s, req.authorization_record_id)

    lid = f"ML-{uuid.uuid4().hex[:10]}"
    prov = "simulated" if req.sandbox else "real"
    nca_ref = _nca_append("MARKETADMIN_PUBLISH", username,
                          artifact_path=f"market-admin:{lid}", prov=prov)
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.MarketListing(
            listing_id=lid, owner_ref=username,
            ownership_record_id=req.ownership_record_id.strip(),
            authorization_record_id=(req.authorization_record_id.strip()
                                     if not req.sandbox else ""),
            asset_summary=req.asset_summary.strip(), scene=req.scene.strip(),
            scope_note=req.scope_note.strip(), term_note=req.term_note.strip(),
            initial_conditions=req.initial_conditions.strip(),
            sandbox_flag=1 if req.sandbox else 0,
            status="active", nca_ref=nca_ref, data_provenance=prov,
            published_at=now, updated_at=now))
        _event(s, lid, "publish", "", "active", username, nca_ref)
    return _nca_watermark({"listing": _view_from(lid),
                           "note": "挂出成功（"
                                   + ("沙盒／演练例外，显式标记；出盒仍须授权"
                                      if req.sandbox else
                                      "成件＋四要件齐") + "）"},
                          nature=prov)


def _view_from(listing_id: str) -> dict:
    with get_session() as s:
        r = s.get(M.MarketListing, listing_id)
    return _view(r) if r else {}


# ---------------------------------------------------------------- A-2 查询


@router.get("/listings")
def listing_list_mine(request: Request, status: str = ""):
    """本人全量（含已下架；可按 status 过滤）。"""
    user = _require_session_user(request)
    if status and status not in _STATUSES:
        raise HTTPException(400, "status 过滤值非法")
    with get_session() as s:
        q = (s.query(M.MarketListing)
             .filter_by(owner_ref=user["username"]))
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(M.MarketListing.published_at.desc()).all()
    return _nca_watermark({"count": len(rows),
                           "listings": [_view(r) for r in rows],
                           "note": "本人面全量（含已下架；公开面见 /public/listings）"},
                          nature="real")


@router.get("/listings/{listing_id}")
def listing_one_mine(listing_id: str, request: Request):
    """本人单件全量＋留痕（非本人 403）。"""
    user = _require_session_user(request)
    with get_session() as s:
        r = s.get(M.MarketListing, listing_id)
        if r is None:
            raise HTTPException(404, "listing_id 不存在")
        if r.owner_ref != user["username"]:
            raise HTTPException(403, "仅权属登记人本人可查全量（fail-closed）")
        return _nca_watermark({"listing": _view(r), "events": _events(s, listing_id),
                               "note": "本人面全量＋事件留痕"}, nature="real")


@router.get("/public/listings")
def listing_list_public():
    """公开面（免会话）：仅 active／paused；下架即撤出公开面；四字段投影。"""
    with get_session() as s:
        rows = (s.query(M.MarketListing)
                .filter(M.MarketListing.status.in_(("active", "paused")))
                .order_by(M.MarketListing.published_at.desc()).all())
    return _nca_watermark({"count": len(rows),
                           "listings": [_public_view(r) for r in rows],
                           "note": "公开面四字段（权属信息／授权信息／授权状态／获取方式）；"
                                   "不公开四条照守"}, nature="real")


@router.get("/public/listings/{listing_id}")
def listing_one_public(listing_id: str):
    """公开面单件（下架件 404——公开面随操作同步）。"""
    with get_session() as s:
        r = s.get(M.MarketListing, listing_id)
        if r is None or r.status == "delisted":
            raise HTTPException(404, "listing 不存在或已下架")
        return _nca_watermark({"listing": _public_view(r)}, nature="real")


# ------------------------------------------------------- A-3 状态变更 / A-4 下架


class StatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str                              # pause / resume


@router.post("/listings/{listing_id}/status")
def listing_status(listing_id: str, req: StatusIn, request: Request):
    """状态变更（A-3）：暂停／恢复；原态新态双留痕；限本人。"""
    user = _require_session_user(request)
    if req.action not in _ACTIONS:
        raise HTTPException(400, "action 仅 pause／resume")
    frm_expected, to = _ACTIONS[req.action]
    with get_session() as s:
        r = s.get(M.MarketListing, listing_id)
        if r is None:
            raise HTTPException(404, "listing_id 不存在")
        if r.owner_ref != user["username"]:
            raise HTTPException(403, "仅权属登记人本人可操作（fail-closed）")
        if r.status != frm_expected:
            raise HTTPException(409, f"当前状态 {r.status} 不可 {req.action}"
                                     f"（须 {frm_expected}）")
        prov = r.data_provenance
    nca_ref = _nca_append(f"MARKETADMIN_{req.action.upper()}", user["username"],
                          artifact_path=f"market-admin:{listing_id}",
                          prov=prov)
    with get_sessionmaker().begin() as s:
        r = s.get(M.MarketListing, listing_id)
        frm = r.status
        r.status, r.updated_at = to, _utc()
        _event(s, listing_id, req.action, frm, to, user["username"], nca_ref)
    return _nca_watermark({"listing_id": listing_id, "from": frm, "to": to,
                           "nca_ref": nca_ref, "note": "状态变更双留痕（事件表＋NCA）"},
                          nature=prov)


@router.post("/listings/{listing_id}/delist")
def listing_delist(listing_id: str, request: Request):
    """下架（A-4）：不溯及已生成／已生效授权件——授权登记记录一字不动。"""
    user = _require_session_user(request)
    with get_session() as s:
        r = s.get(M.MarketListing, listing_id)
        if r is None:
            raise HTTPException(404, "listing_id 不存在")
        if r.owner_ref != user["username"]:
            raise HTTPException(403, "仅权属登记人本人可操作（fail-closed）")
        if r.status == "delisted":
            raise HTTPException(409, "已下架，不可重复下架")
        prov = r.data_provenance
    nca_ref = _nca_append("MARKETADMIN_DELIST", user["username"],
                          artifact_path=f"market-admin:{listing_id}",
                          prov=prov)
    with get_sessionmaker().begin() as s:
        r = s.get(M.MarketListing, listing_id)
        frm = r.status
        r.status, r.updated_at = "delisted", _utc()
        _event(s, listing_id, "delist", frm, "delisted", user["username"], nca_ref)
        # ⛔ 不溯及：authorization_records 一字不动（已生效授权件存续至其期限）。
    return _nca_watermark({"listing_id": listing_id, "from": frm, "to": "delisted",
                           "nca_ref": nca_ref,
                           "note": "下架完成；已生成／已生效授权件不受影响（不溯及）"},
                          nature=prov)
