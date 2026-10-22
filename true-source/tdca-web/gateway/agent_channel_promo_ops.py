# -*- coding: utf-8 -*-
"""
A-27 智能体通道 对外补齐 B（L1SI166-CHANNEL-GAP-001 项 B）：转正令牌（签发＋验伪＋吊销）。

制度口径（裁定 TDCA-RULING-L1SI166-GUEST-THREE-001 项二 ＋ 原令硬约束八条）：
  - 出盒凭证定名「转正令牌」，与在册「执行令牌」（根节点令牌）不同物，⛔ 名称不得撞词；
  - 与身份凭据族物理分离：独立表 site_agent_promo_token／独立前缀 SPT-／独立存证类型
    （⛔ 不共用 site_agent_credential 表、⛔ 不共用 SCD- 前缀）；
  - 只存 sha256 不可逆指纹：令牌值至多一次性回显，⛔ 入库、⛔ 入日志；
  - 签发即轮换（同登记号旧 active 自动 revoked）；吊销即时生效（status=revoked 全库拒）；
  - 人类签名权不可绕：签发须人类会话内、且仅登记主体本人，⛔ 智能体不得代签代持；
  - 签发前置（fail-closed，缺一即拒）：沙盒签批四要件（人／时／物／意）逐项齐——
    人须等于本会话主体；物须绑定在册沙盒签批记录（闸步表 sandbox 行 result_ref）；
    且出盒判据达标（③负空间审查与④沙盒验证皆 passed）；
  - ⛔ 转授、⛔ 复合、⛔ 跨场景复用；⛔ 作身份凭证使用；
  - 验伪端只判「此转正令牌」之真伪与态（active 方有效），fail-closed：一切不明即 invalid。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import secrets
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark,  # noqa: E402
                    _require_session_user, _client_ip, _utc)
from agent_channel_ops import gate_assert, _step_state  # noqa: E402

router = APIRouter(prefix="/api/v1/agent-channel", tags=["agent-channel-promo"])


def _token_no() -> str:
    """转正令牌号：SPT-＋12 位大写十六进制（⛔ 非 SCD-；非新编号体例外之体例）。"""
    return "SPT-" + uuid.uuid4().hex[:12].upper()


# 验伪端轻量防滥用（内存滑窗，每 IP 每小时 ≤60 次；⛔ 静默丢弃不区分有无）
_VERIFY_WINDOW_S = 3600
_VERIFY_MAX = 60
_verify_hits: dict[str, list[float]] = {}


def _verify_rate_ok(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _verify_hits.get(ip, []) if now - t < _VERIFY_WINDOW_S]
    if len(hits) >= _VERIFY_MAX:
        _verify_hits[ip] = hits
        return False
    hits.append(now)
    _verify_hits[ip] = hits
    return True


class PromoTokenIssueReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approver: str = ""                 # 四要件·人（须＝本会话主体，单一责任锚点）
    approved_at: str = ""              # 四要件·时（签批时点，ISO 串）
    sandbox_approval_ref: str = ""     # 四要件·物（沙盒签批记录引用＝闸步表 sandbox 行 result_ref）
    approval_intent: str = ""          # 四要件·意（签批意旨明文）


@router.post("/{reg_no}/promotion-token", status_code=201)
def issue_promo_token(reg_no: str, req: PromoTokenIssueReq, request: Request):
    """转正令牌签发（官方沙盒签批口径；fail-closed：四要件不齐／出盒判据未达即拒）。"""
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)      # 总闸：幽灵/惩罚态即拒
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可为其智能体"
                                     "申领转正令牌（⛔ 智能体不得代签代持）")
        missing = [k for k, val in (("人（approver）", req.approver),
                                    ("时（approved_at）", req.approved_at),
                                    ("物（sandbox_approval_ref）", req.sandbox_approval_ref),
                                    ("意（approval_intent）", req.approval_intent))
                   if not val.strip()]
        if missing:
            raise HTTPException(400, "沙盒签批四要件不齐（人／时／物／意），缺："
                                     + "／".join(missing) + "（fail-closed）")
        if req.approver.strip() != actor:
            raise HTTPException(400, "四要件·人须等于本会话主体（单一责任锚点）："
                                     f"approver={req.approver.strip()!r} ≠ {actor!r}")
        # 物：沙盒签批记录须真实在册（闸步表 sandbox 行 result_ref 引用绑定）
        sb = s.get(M.SiteAgentAdmission, (reg_no, "sandbox"))
        if sb is None or sb.state != "passed" or not sb.result_ref:
            raise HTTPException(403, "无在册沙盒签批记录（④沙盒验证未过或无运行号引用）"
                                     "——⛔ 签转正令牌（fail-closed）")
        if req.sandbox_approval_ref.strip() != sb.result_ref:
            raise HTTPException(400, "四要件·物与在册沙盒签批记录不符："
                                     f"须等于闸步表 sandbox 行 result_ref（{sb.result_ref}）")
        # 出盒判据达标：③负空间审查 与 ④沙盒验证 皆 passed（六步硬序同向叠加，⛔ 旁路）
        if _step_state(s, reg_no, "ns-review") != "passed":
            raise HTTPException(403, "出盒判据未达：③负空间审查未过"
                                     "（⛔ 签转正令牌，fail-closed）")
        if sb.state != "passed":
            raise HTTPException(403, "出盒判据未达：④沙盒验证未过"
                                     "（⛔ 签转正令牌，fail-closed）")
        old_actives = [t for t in s.query(M.SiteAgentPromoToken)
                       .filter_by(reg_no=reg_no, status="active")]
    token_value = "TDCA-PRT-" + secrets.token_urlsafe(32)
    fingerprint = hashlib.sha256(token_value.encode("utf-8")).hexdigest()
    session_fp = hashlib.sha256(
        request.headers.get("authorization", "").strip().encode("utf-8")).hexdigest()
    token_no = _token_no()
    nca_ref = _nca_append("AGENT_CHANNEL_PROMO_TOKEN_ISSUE", actor,
                          artifact_path=f"agent-channel:{reg_no}/promo:{token_no}",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        for t in old_actives:   # 签发即轮换：旧 active 全置 revoked
            t2 = s.get(M.SiteAgentPromoToken, t.token_no)
            if t2 is None:
                raise HTTPException(409, "CONFLICT: 旧令牌行竞态消失（轮换中止，事务回滚）")
            t2.status = "revoked"
            t2.rotated_at = now
        s.add(M.SiteAgentPromoToken(
            token_no=token_no, reg_no=reg_no, token_fingerprint=fingerprint,
            status="active", approver=actor, approved_at=req.approved_at.strip(),
            sandbox_approval_ref=req.sandbox_approval_ref.strip(),
            approval_intent=req.approval_intent.strip(),
            issued_at=now, issuer_session=session_fp, nca_ref=nca_ref,
            data_provenance="real", created_at=now))
    return _nca_watermark({
        "issued": True, "token_no": token_no, "reg_no": reg_no, "status": "active",
        "fingerprint_sha256_16": fingerprint[:16],
        "token_value": token_value,   # 至多一次性回显（⛔ 不入库不入日志）
        "四要件": {"人": actor, "时": req.approved_at.strip(),
                  "物": req.sandbox_approval_ref.strip(), "意": req.approval_intent.strip()},
        "rotated": [t.token_no for t in old_actives],
        "nca_ref": nca_ref,
        "note": "转正令牌（沙盒签批）：⛔ 非执行令牌；⛔ 转授／复合／跨场景复用；"
                "⛔ 作身份凭证；只存指纹；签发即轮换；吊销即时"},
        nature="real")


class PromoTokenVerifyReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token_value: str = ""


@router.post("/promotion-token/verify")
def verify_promo_token(req: PromoTokenVerifyReq, request: Request):
    """转正令牌验伪（fail-closed：不明即 invalid；active 方有效；每 IP 限流）。"""
    v = _require_session_user(request)
    ip = _client_ip(request)
    if not _verify_rate_ok(ip):
        raise HTTPException(429, "验伪过于频繁（每 IP 每小时 ≤60 次），请稍后再试",
                            )
    valid = False
    token_no = None
    reg_no = None
    status = None
    if req.token_value.strip():
        fp = hashlib.sha256(req.token_value.strip().encode("utf-8")).hexdigest()
        with get_session() as s:
            row = (s.query(M.SiteAgentPromoToken)
                   .filter_by(token_fingerprint=fp).order_by(
                       M.SiteAgentPromoToken.issued_at.desc()).first())
            if row is not None:
                token_no, reg_no, status = row.token_no, row.reg_no, row.status
                valid = row.status == "active"
    return _nca_watermark({
        "valid": valid, "token_no": token_no, "reg_no": reg_no, "status": status,
        "verified_by": v["username"],
        "note": ("验伪通过：转正令牌 active 在册" if valid else
                 "验伪不过：无此令牌／已轮换／已吊销（fail-closed）")},
        nature="real")


@router.post("/{reg_no}/promotion-token/{token_no}/revoke")
def revoke_promo_token(reg_no: str, token_no: str, request: Request):
    """转正令牌吊销（即时生效：status=revoked 即全库拒；仅登记主体本人）。"""
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可吊销其转正令牌")
        t = s.get(M.SiteAgentPromoToken, token_no)
        if t is None or t.reg_no != reg_no:
            raise HTTPException(404, "该转正令牌不存在（⛔ 不透露在册他号信息）")
        if t.status == "revoked":
            raise HTTPException(409, "该转正令牌已吊销（吊销即时，⛔ 重复吊销）")
    nca_ref = _nca_append("AGENT_CHANNEL_PROMO_TOKEN_REVOKE", actor,
                          artifact_path=f"agent-channel:{reg_no}/promo:{token_no}:revoke",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        t2 = s.get(M.SiteAgentPromoToken, token_no)
        if t2 is None or t2.status == "revoked":
            raise HTTPException(409, "CONFLICT: 吊销竞态（令牌已不存在或已吊销）")
        t2.status = "revoked"
        t2.revoked_at = now
        t2.nca_ref = nca_ref
    return _nca_watermark({
        "revoked": True, "token_no": token_no, "reg_no": reg_no,
        "revoked_at": now, "nca_ref": nca_ref,
        "note": "吊销即时生效：此后验伪端对该令牌一律 invalid（fail-closed）"},
        nature="real")
