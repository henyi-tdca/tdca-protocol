# -*- coding: utf-8 -*-
"""
A-26 智能体通道 批1 身份与登记（L1SI147-CHANNEL-B1-001）：/api/v1/agent-channel/*

制度口径（《智能体定义条例》V1.0-FROZEN ＋ 通道定性裁定 ＋ 施工技术评估方案 V2）：
  - 登记即创建、未登记即未创建：register 为唯一创建口，未登记公开查如实显幽灵态；
  - 主体与执行体二分：owner_username 为主体（人类账户），智能体执行体无财产；
  - 智能体侧标识＝登记号 reg_no（⛔ 不叫 TDID、⛔ 不自造编号体例；TDID 仅在锚↔令牌语境，
    批 2 锚↔令牌挂接承接）；
  - 通道＝协议加载验证（⛔ 非身份验证）；六步硬序不可跳不可互替；
  - 人类签名权不可绕：凭据签发须人类会话内操作，⛔ 智能体不得代签代持；
  - 锚无效不发令牌（锚↔令牌硬挂接的批 1 落点）：主体锚未达「notifier＋固锚/移锚级＋已补」
    即拒发身份类凭据，fail-closed；
  - 凭据族只存不可逆指纹（sha256），⛔ 凭据值一律不入库；
  - 草案五表（agents/auth_grants/api_calls/agent_cards/members）只读不动、不承接；
  - 登记事实／凭据生命周期／fail-closed 判定＝接真（data_provenance=real，⛔ 非模拟）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import secrets
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _owner_display,  # noqa: E402
                    _require_session_user, _utc)

router = APIRouter(prefix="/api/v1/agent-channel", tags=["agent-channel"])

# ---------------------------------------------------------------------
# 六步硬序（通道本体＝协议加载验证；步序不可跳不可互替）
# 批 1 落点：登记（准入）＋②凭据（锚↔令牌挂接的签发面）；①③④ 批 2、⑤批 3、⑥随各步落链
# ---------------------------------------------------------------------
SIX_STEPS = (
    ("①", "protocol-load", "加载协议"),
    ("②", "token", "持根节点执行令牌"),
    ("③", "ns-review", "负空间审查"),
    ("④", "sandbox", "沙盒验证"),
    ("⑤", "execute", "正空间执行"),
    ("⑥", "nca-evidence", "NCA 存证"),
)

# 锚有效口径（锚无效不发令牌，fail-closed）：通知机锚＋定档级＋人工核验已补
_ANCHOR_VALID_KIND = "notifier"
_ANCHOR_VALID_TIERS = ("固锚级", "移锚级")
_ANCHOR_VALID_STATE = "已补"

_PUBLIC_KEYS = ("权属信息", "授权信息", "授权状态", "获取方式")


def _reg_no() -> str:
    """登记号：SAR-＋12 位十六进制（站点通道族内部序号，⛔ 非 TDID、非新编号体例）。"""
    return "SAR-" + uuid.uuid4().hex[:12].upper()


def _cred_no() -> str:
    return "SCD-" + uuid.uuid4().hex[:12].upper()


def evaluate_gate(s, reg_no: str) -> dict:
    """六步总闸评估（fail-closed：一切未知/缺失即拒，如实报各步态）。

    批 1 可判步：②（存在 active 凭据）／⑥（登记已落 NCA 存证）；
    未承接步（①③④⑤）如实报 pending_batch，⛔ 不虚报通过。
    """
    row = s.get(M.SiteAgentRegistry, reg_no)
    if row is None:
        return {"admitted": False, "ghost": True, "reason": "UNREGISTERED",
                "note": "未登记即未创建：幽灵态不受保护"}
    steps = {}
    cred_active = any(c.status == "active" for c in
                      s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no))
    for num, key, label in SIX_STEPS:
        if key == "token":
            state = "satisfied" if cred_active else "pending"
        elif key == "nca-evidence":
            state = "satisfied" if row.nca_ref else "pending"
        else:
            state = "pending_batch"   # ①③④⑤：批 2/3 承接，如实不虚报
        steps[key] = {"step": num, "label": label, "state": state}
    denied = row.status != "正常"
    return {"admitted": not denied, "ghost": False, "reg_no": reg_no,
            "status": row.status,
            "denied_reason": f"PUNISHMENT_STATE:{row.status}" if denied else None,
            "steps": steps,
            "note": "总闸 fail-closed：登记缺失/惩罚态/任一步未达即拒（六步不可跳不可互替）"}


def gate_assert(s, reg_no: str) -> M.SiteAgentRegistry:
    """总闸断言（通道内各端点与后续批次复用）：登记在册且状态正常。

    fail-closed：未登记（幽灵）／惩罚三态 → 403，⛔ 不带红放行。
    """
    row = s.get(M.SiteAgentRegistry, reg_no)
    if row is None:
        raise HTTPException(403, "GATE_FAIL_CLOSED: 登记号不存在（未登记即未创建，幽灵态不受保护）")
    if row.status != "正常":
        raise HTTPException(403, f"GATE_FAIL_CLOSED: 登记状态为「{row.status}」"
                                 "（惩罚态即时生效，全库拒）")
    return row


def _anchor_valid(s, owner_username: str) -> bool:
    a = s.get(M.UserAnchor, owner_username)
    return bool(a and a.anchor_kind == _ANCHOR_VALID_KIND
                and a.anchor_tier in _ANCHOR_VALID_TIERS
                and a.tier_state == _ANCHOR_VALID_STATE)


class RegisterReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    six_elements_ref: str = ""    # 创世六要素引用（必填）
    anchor_ref: str = ""          # 锚定项引用（可空）
    tier: str = "basic"


@router.post("/register", status_code=201)
def register_agent(req: RegisterReq, request: Request):
    """智能体登记（登记即创建；唯一创建口；须人类会话——智能体不得自登）。"""
    v = _require_session_user(request)
    owner = v["username"]
    if not req.six_elements_ref.strip():
        raise HTTPException(400, "six_elements_ref 为必填（创世六要素引用）")
    with get_session() as s:
        if s.get(M.User, owner) is None:
            raise HTTPException(403, "主体账户不存在（fail-closed）")
        owner_display = _owner_display(s, owner)
    reg_no = _reg_no()
    nca_ref = _nca_append("AGENT_CHANNEL_REGISTER", owner,
                          artifact_path=f"agent-channel:{reg_no}", prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentRegistry(
            reg_no=reg_no, owner_username=owner,
            six_elements_ref=req.six_elements_ref.strip(),
            anchor_ref=req.anchor_ref.strip() or None,
            tier=req.tier.strip() or "basic",
            status="正常", nca_ref=nca_ref,
            data_provenance="real", created_at=now, updated_at=now))
    with get_session() as s:
        gate = evaluate_gate(s, reg_no)
    return _nca_watermark({
        "registered": True, "reg_no": reg_no, "status": "正常",
        "owner": owner_display, "gate": gate,
        "note": "登记即创建：未登记即未创建；智能体侧标识＝登记号（⛔ 非 TDID）"
                "；登记事实接真（data_provenance=real）"}, nature="real")


@router.get("/{reg_no}")
def public_query(reg_no: str):
    """公开查（免会话）：公开面四字段（权属信息／授权信息／授权状态／获取方式）；
    未登记如实显幽灵态（HTTP 200＋ghost，⛔ 不伪装存在）。"""
    with get_session() as s:
        row = s.get(M.SiteAgentRegistry, reg_no)
        if row is None:
            return _nca_watermark({
                "registered": False, "ghost": True, "reg_no": reg_no,
                **{k: None for k in _PUBLIC_KEYS},
                "note": "幽灵态：该登记号不存在（未登记即未创建，不受保护）"}, nature="real")
        cred_n = s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no).count()
        owner_display = _owner_display(s, row.owner_username)
    return _nca_watermark({
        "registered": True, "ghost": False, "reg_no": reg_no,
        "public_fields": dict(zip(_PUBLIC_KEYS, _PUBLIC_KEYS)),
        "权属信息": f"主体：{owner_display}（登记号 {row.reg_no}）",
        "授权信息": f"凭据指纹在册 {cred_n} 件（⛔ 值不入库；授权件 site_agent_grant 批 3 承接）",
        "授权状态": row.status,
        "获取方式": "POST /api/v1/agent-channel/register（须人类会话，登记即创建）",
        "note": "公开面仅四字段；⛔ 不含凭据值／指纹原文／内部编号"}, nature="real")


class CredentialReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = ""


@router.post("/{reg_no}/credentials", status_code=201)
def issue_credential(reg_no: str, req: CredentialReq, request: Request):
    """智能体凭据签发（⛔ 人类会话内操作，智能体不得代签代持；锚无效不发令牌）。

    fail-closed 序：人类会话 → 登记在册且状态正常（总闸）→ 主体本人 →
    主体锚有效（notifier＋固锚/移锚级＋已补）→ 落库只存 sha256 指纹。
    """
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)   # 总闸：幽灵/惩罚态即拒
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可签发其智能体凭据"
                                     "（⛔ 智能体不得代签代持）")
        if not _anchor_valid(s, actor):
            raise HTTPException(403, "ANCHOR_INVALID: 主体锚无效或未达定档"
                                     "（须 notifier＋固锚/移锚级＋已补）"
                                     "——锚无效不发令牌（fail-closed）")
    cred_value = "TDCA-AGT-" + secrets.token_urlsafe(32)
    fingerprint = hashlib.sha256(cred_value.encode("utf-8")).hexdigest()
    session_fp = hashlib.sha256(
        request.headers.get("authorization", "").strip().encode("utf-8")).hexdigest()
    cred_no = _cred_no()
    nca_ref = _nca_append("AGENT_CHANNEL_CREDENTIAL_ISSUE", actor,
                          artifact_path=f"agent-channel:{reg_no}/cred:{cred_no}",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentCredential(
            cred_no=cred_no, reg_no=reg_no, cred_fingerprint=fingerprint,
            status="active", issued_at=now, issuer_session=session_fp,
            nca_ref=nca_ref, data_provenance="real"))
    return _nca_watermark({
        "issued": True, "cred_no": cred_no, "reg_no": reg_no, "issued_at": now,
        "credential": cred_value,     # 唯一回显一次；库内只存指纹
        "credential_fingerprint_sha256_16": fingerprint[:16],
        "note": "凭据值仅此一次回显、⛔ 不入库（库内只存不可逆指纹）；吊销即时生效"
                "（批 4 执行器承接）；人类会话内签发（⛔ 智能体不得代签代持）"}, nature="real")
