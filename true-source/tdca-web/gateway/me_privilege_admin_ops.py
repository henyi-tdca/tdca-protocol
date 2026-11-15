# -*- coding: utf-8 -*-
"""
L1SI214-CONSOLE-A2-001 件二：任免私域管理员端点接线（功能追平公告）。

背景：audit_privilege_admin_change 在册、单测绿，但全仓无生产调用方、无路由——
公告「任免自己私域的管理员会自动留痕」此前不成立；本件只做最小接线（⛔ 扩大）。

端点（/api/v1/me/privilege-admin/appoint|revoke，一收一放）：
- 第 1 把锁 · 本人真身：须登录会话（上游 _require_session_user fail-closed）；
  智能体（user_identities.identity_type=external）⛔ 代任免（403）；
  on_behalf 非空即拒（代签代填硬红线，同面板签署口径）。
- 第 2 把锁 · 权属：只能任免 ⭐ 自己私域 ⭐ 的管理员——权属资产须为
  ownership_records 在册、owner_ref=本人、status != cancelled；
  他人私域／查无登记／已注销 ⟹ 一律 404（与「不存在」同码同文案，⛔ 区分、⛔ 泄露）。
- 资格载体：私域管理员以「域内授权关系」表达（perm_table 表头口径，⛔ 角色枚举，
  S-2' 不触发）——任命＝在 authorization_panel_docs 落在册 active 授权件
  （grantee=被任命者、标的含本人权属资产引用，dual_lock 第 2 把锁在册口径同源）；
  撤销＝该件状态推进 revoked（五态机在册，⛔ 新表、⛔ 第二套私域体系）。
- 留痕：任命／撤销各调既有 audit_privilege_admin_change → 既有 nca_chain
  （谁=actor／对谁=subject_ref 脱敏形／哪个私域=actor 本人域／op／结果／ts；
  ⛔ 凭据值、⛔ 新表）。
- 存证：授权件每笔状态推进落 NCA（nca_seq＋rec_hash 对拍副本，面板件可靠性口径），
  无存证视未发生；业务行先落、存证失败即清行（⛔ 半条记录）。
- 越权与探测不审计（最小接线；两把锁拒绝不落痕，与 me 族端点一致口径）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402
from me_audit import audit_privilege_admin_change  # noqa: E402

router = APIRouter(prefix="/api/v1/me/privilege-admin", tags=["me-privilege-admin"])

# 权属资产引用形态（与 dual_lock._ASSET_RE 同口径）
_ASSET_RE = re.compile(r"^OR-[A-Za-z0-9_-]+$")

# 授权件编号形态（面板件同规）
_AUTH_ID_RE = re.compile(r"^AP-[0-9a-f]{10}$")

# 条件三问（面板八字段之「条件」；任免件固定口径：⛔ 再授权／⛔ 商用／须标注来源）
_CONDITIONS = {"may_sub_grant": "否", "may_commercialize": "否",
               "attribution_required": "是"}


def _reject_query_params(request: Request) -> None:
    """本端点无查询参数：带任何查询参数一律 404（/me 族 S-3 同码口径）。"""
    if request.query_params:
        raise HTTPException(404, "Not Found")


def _nca_row(nca_id: str) -> M.NcaChain | None:
    with get_session() as s:
        return s.get(M.NcaChain, nca_id)


def _assert_native_self(user: dict, on_behalf: str) -> str:
    """第 1 把锁 · 本人真身：智能体 ⛔ 代任免；on_behalf 非空即拒（⛔ 代签代填）。

    返回 actor 用户名。拒绝皆 403（本人面不受理＝无此许可，⛔ 用 404 混淆对象存在性）。
    """
    me = user["username"]
    if on_behalf.strip():
        raise HTTPException(403, "智能体不得代任免（⛔ 代设代撤、⛔ 代填代持）——"
                                 "任免须本人登录亲自操作")
    with get_session() as s:
        ident = s.get(M.UserIdentity, me)
    if ident is not None and ident.identity_type == "external":
        raise HTTPException(403, "智能体账号 ⛔ 代任免——任免私域管理员须本人真身操作")
    return me


def _assert_own_domain(me: str, asset_ref: str) -> M.OwnershipRecord:
    """第 2 把锁 · 权属：权属资产须在册、owner_ref=本人、未注销；否则一律 404。

    与他人私域／查无登记／已注销同码同文案（⛔ 区分、⛔ 泄露存在性）。
    """
    if not _ASSET_RE.match(asset_ref or ""):
        raise HTTPException(404, "Not Found")
    with get_session() as s:
        ow = s.get(M.OwnershipRecord, asset_ref)
        if ow is None or ow.owner_ref != me or ow.status == "cancelled":
            raise HTTPException(404, "Not Found")
    return ow


def _active_grant(s, me: str, asset_ref: str, appointee: str):
    """本人就该私域对被任免者在册的 active 授权件（任命幂等／撤销定位之用）。"""
    return (s.query(M.AuthorizationPanelDoc)
            .filter(M.AuthorizationPanelDoc.status == "active",
                    M.AuthorizationPanelDoc.drafter == me,
                    M.AuthorizationPanelDoc.grantee == appointee)
            .all())


def _asset_of(doc: M.AuthorizationPanelDoc) -> str | None:
    m = re.search(r"OR-[A-Za-z0-9_-]+", doc.subject or "")
    return m.group(0) if m else None


def _write_grant(me: str, appointee: str, asset_ref: str) -> tuple[str, str]:
    """任命：业务行先落（active）→ NCA 落证 → 回写指针＋事件；失败即清行（⛔ 半条）。"""
    aid = f"AP-{uuid.uuid4().hex[:10]}"
    now = _utc()
    cond_json = json.dumps(_CONDITIONS, ensure_ascii=False)
    with get_sessionmaker().begin() as s:
        s.add(M.AuthorizationPanelDoc(
            auth_id=aid, operation="activate",
            grantor=me, grantee=appointee,
            subject=f"私域管理员任免·权属资产 {asset_ref}",
            scope="该私域（权属资产）之管理：访问／读／写／删／撤销／上架／发布／可见范围设定",
            term="自本人签署起至本人撤回止",
            conditions=cond_json,
            signer=me, drafter=me,
            credential_ref=None,
            status="active",
            note="L1SI214-CONSOLE-A2-001 任免端点直接生效（本人＝权属人，无需经面板草稿流程）",
            data_provenance="real", created_at=now, updated_at=now))
    try:
        nca_ref = _nca_append("AUTH_PANEL_SIGN", me,
                              artifact_path=f"authorization-panel:{aid}",
                              prov="real")
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            if d is not None:
                s.delete(d)
        raise HTTPException(500, "存证落链失败——本次任命未发生（业务行已清，"
                                 "⛔ 半条记录、⛔ 编号发放）")
    row = _nca_row(nca_ref)
    try:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.nca_seq = nca_ref
            d.rec_hash = row.rec_hash if row else None
            s.add(M.AuthorizationPanelEvent(
                event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=aid,
                event_type="sign", actor=me, nca_ref=nca_ref,
                detail="本人签署（任免端点直接生效·权属人本人操作）",
                created_at=_utc()))
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            if d is not None:
                s.delete(d)
        raise HTTPException(500, "存证回写失败——本次任命未发生（业务行已清）")
    return aid, nca_ref


def _close_grant(me: str, doc: M.AuthorizationPanelDoc) -> str:
    """撤销：状态推进 revoked → NCA 落证 → 回写指针＋事件；失败状态停本步。"""
    aid = doc.auth_id
    prev = doc.status
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, aid)
        d.status = "revoked"
        d.updated_at = _utc()
    try:
        nca_ref = _nca_append("AUTH_PANEL_REVOKE", me,
                              artifact_path=f"authorization-panel:{aid}",
                              prov="real")
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = prev
            d.updated_at = _utc()
        raise HTTPException(500, "撤销存证落链失败——状态已停在本步（未撤回），请重试")
    row = _nca_row(nca_ref)
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, aid)
        d.nca_seq = nca_ref
        d.rec_hash = row.rec_hash if row else None
        s.add(M.AuthorizationPanelEvent(
            event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=aid,
            event_type="revoke", actor=me, nca_ref=nca_ref,
            detail="本人撤回（任免端点·私域管理员撤销）",
            created_at=_utc()))
    return nca_ref


class AppointIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_ref: str                    # 权属资产引用（本人私域；OR-…）
    appointee: str                    # 被任命者（用户名；须为在册用户）
    on_behalf: str = ""               # 非空即智能体代任免嫌疑 → 拒（⛔ 代签代填硬红线）


class RevokeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_ref: str                    # 权属资产引用（本人私域；OR-…）
    appointee: str                    # 被撤销者（用户名）
    on_behalf: str = ""               # 非空即智能体代任免嫌疑 → 拒（⛔ 代签代填硬红线）


@router.post("/appoint", status_code=201)
def privilege_admin_appoint(req: AppointIn, request: Request):
    """任命自己私域的管理员（两把锁：本人真身＋权属；越他域一律 404 同码）。"""
    _reject_query_params(request)
    user = _require_session_user(request)
    me = _assert_native_self(user, req.on_behalf)
    asset_ref = (req.asset_ref or "").strip()
    appointee = (req.appointee or "").strip()
    _assert_own_domain(me, asset_ref)
    with get_session() as s:
        if s.get(M.User, appointee) is None:
            raise HTTPException(404, "Not Found")   # 被任命者不存在：同码（⛔ 泄露）
        for d in _active_grant(s, me, asset_ref, appointee):
            if _asset_of(d) == asset_ref:
                raise HTTPException(409, "该用户已是该私域管理员（active 在册）——"
                                         "重复任命不受理")
    aid, nca_ref = _write_grant(me, appointee, asset_ref)
    audit_privilege_admin_change(me, appointee, "appoint", "ok")
    return _nca_watermark({
        "op": "appoint", "asset_ref": asset_ref, "appointee": appointee,
        "auth_id": aid, "nca_seq": nca_ref, "status": "active", "scope": "self",
        "note": "任命已生效（域内授权关系在册 active；NCA 存证在册；留痕已落链）"},
        nature="real")


@router.post("/revoke")
def privilege_admin_revoke(req: RevokeIn, request: Request):
    """撤销自己私域的管理员（两把锁同任命；未任命过 ⟹ 404 同码）。"""
    _reject_query_params(request)
    user = _require_session_user(request)
    me = _assert_native_self(user, req.on_behalf)
    asset_ref = (req.asset_ref or "").strip()
    appointee = (req.appointee or "").strip()
    _assert_own_domain(me, asset_ref)
    with get_session() as s:
        docs = [d for d in _active_grant(s, me, asset_ref, appointee)
                if _asset_of(d) == asset_ref]
    if not docs:
        raise HTTPException(404, "Not Found")   # 未任命过／已撤回：同码
    nca_ref = _close_grant(me, docs[0])
    audit_privilege_admin_change(me, appointee, "revoke", "ok")
    return _nca_watermark({
        "op": "revoke", "asset_ref": asset_ref, "appointee": appointee,
        "auth_id": docs[0].auth_id, "nca_seq": nca_ref, "status": "revoked",
        "scope": "self",
        "note": "撤销已生效（域内授权关系已撤回 revoked；NCA 存证在册；留痕已落链）"},
        nature="real")
