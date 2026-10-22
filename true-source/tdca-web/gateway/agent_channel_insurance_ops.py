# -*- coding: utf-8 -*-
"""
A-30 智能体通道 对外补齐 D（L1SI166-CHANNEL-GAP-001 项 D）：履约保证保险挂接
（保单登记 ＋ 转正前置校验 ＋ 漏洞损失申报入口）。

制度口径（裁定 TDCA-RULING-L1SI166-GUEST-THREE-001 项三／五条 ＋ 原令硬约束）：
  - 履约保证保险挂接：登记主体须持**有效保单**方可转正——无有效保单 ⟹
    fail-closed 拒转正（⛔ 告警放行、⛔ 默认通过）；
  - 有效保单口径：status=active 且 保障期（period_start..period_end）覆盖当前时点
    （期满即拒，fail-closed）；status 闭集 active／expired／revoked；
  - 转正端双重前置（fail-closed，缺一即拒）：①有效转正令牌在册（site_agent_promo_token
    active）＋②有效保单在册；成功落 NCA AGENT_CHANNEL_PROMOTED；
    ⛔ 不改 channel_type（转正只作事件记录，通道定性裁定不动）；
  - 漏洞损失申报入口：loss_type 闭集 制度漏洞／技术漏洞；提交即落 NCA
    （AGENT_CHANNEL_INSURANCE_CLAIM）；状态口径照在册保险规则
    （TDCA-INSURANCE-RULES-001）：INSURED＝事件触发态（定损→池兑付 NCA 留痕→
    追偿回补由在册保险金机制承接，本表只记触发态）；
  - 人类签名权不可绕：保单登记／转正／申报均须人类会话内且仅登记主体本人，
    ⛔ 智能体不得代办；保额／损失额一律 MOU 折算。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark,  # noqa: E402
                    _require_session_user, _utc)
from agent_channel_ops import gate_assert  # noqa: E402

router = APIRouter(prefix="/api/v1/agent-channel", tags=["agent-channel-insurance"])


def _policy_no() -> str:
    """保单号：SIP-＋12 位大写十六进制（同 SPT-/SUD- 体例，⛔ 非新编号体例）。"""
    return "SIP-" + uuid.uuid4().hex[:12].upper()


def _claim_no() -> str:
    """申报号：SIC-＋12 位大写十六进制（同上体例）。"""
    return "SIC-" + uuid.uuid4().hex[:12].upper()


def active_policy(s, reg_no: str):
    """当前有效保单（fail-closed 读态）：status=active 且保障期覆盖当前时点。"""
    now = _utc()
    return (s.query(M.SiteAgentInsurancePolicy)
            .filter(M.SiteAgentInsurancePolicy.reg_no == reg_no,
                    M.SiteAgentInsurancePolicy.status == "active",
                    M.SiteAgentInsurancePolicy.period_start <= now,
                    M.SiteAgentInsurancePolicy.period_end >= now)
            .order_by(M.SiteAgentInsurancePolicy.created_at.desc())
            .first())


class InsurancePolicyReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    insurer: str = ""            # 承保方（人类可读名）
    coverage_mou: int = 0        # 保额（MOU 折算，正整数）
    period_start: str = ""       # 保障期起（ISO 串）
    period_end: str = ""         # 保障期止（ISO 串）


@router.post("/{reg_no}/insurance-policies", status_code=201)
def register_policy(reg_no: str, req: InsurancePolicyReq, request: Request):
    """履约保证保险保单登记（人类会话内；仅登记主体本人；fail-closed 入参校验）。"""
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可登记其履约保单"
                                     "（⛔ 智能体不得代办）")
        missing = [k for k, val in (("承保方（insurer）", req.insurer),
                                    ("保障期起（period_start）", req.period_start),
                                    ("保障期止（period_end）", req.period_end))
                   if not val.strip()]
        if missing:
            raise HTTPException(400, "保单要件不齐，缺：" + "／".join(missing)
                                + "（fail-closed）")
        if req.coverage_mou <= 0:
            raise HTTPException(400, "保额须为正整数（MOU 计量，fail-closed）")
        if req.period_end.strip() <= req.period_start.strip():
            raise HTTPException(400, "保障期止须晚于保障期起（fail-closed）")
    policy_no = _policy_no()
    nca_ref = _nca_append("AGENT_CHANNEL_INSURANCE_POLICY_REGISTER", actor,
                          artifact_path=f"agent-channel:{reg_no}/policy:{policy_no}",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentInsurancePolicy(
            policy_no=policy_no, reg_no=reg_no, insurer=req.insurer.strip(),
            coverage_mou=req.coverage_mou,
            period_start=req.period_start.strip(), period_end=req.period_end.strip(),
            status="active", nca_ref=nca_ref,
            data_provenance="real", created_at=now))
    return _nca_watermark({
        "registered": True, "policy_no": policy_no, "reg_no": reg_no,
        "insurer": req.insurer.strip(), "coverage_mou": req.coverage_mou,
        "period_start": req.period_start.strip(), "period_end": req.period_end.strip(),
        "status": "active", "nca_ref": nca_ref,
        "note": "履约保证保险保单在册：转正前置校验读 active＋保障期覆盖（fail-closed）"},
        nature="real")


@router.post("/{reg_no}/promotion", status_code=201)
def promote(reg_no: str, request: Request):
    """转正（fail-closed 双重前置：有效转正令牌 ＋ 有效保单；⛔ 不改 channel_type）。

    成功只作事件记录：落 NCA AGENT_CHANNEL_PROMOTED；通道定性裁定不动。
    """
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可申报转正"
                                     "（⛔ 智能体不得代报）")
        # 前置①：有效转正令牌在册（对外补齐 B）
        tok = (s.query(M.SiteAgentPromoToken)
               .filter_by(reg_no=reg_no, status="active").first())
        if tok is None:
            raise HTTPException(403, "无有效转正令牌——拒转正（fail-closed：转正须先持"
                                     " active 转正令牌在册）")
        # 前置②：有效保单在册（对外补齐 D；期满/吊销即拒）
        pol = active_policy(s, reg_no)
        if pol is None:
            raise HTTPException(403, "无有效保单——拒转正（fail-closed：履约保证保险"
                                     "未在册或保障期未覆盖当前时点）")
        # 重复转正拦截（GO-LIVE-001 步2 状态位）：promoted_at 非空即已转正
        if row.promoted_at is not None:
            raise HTTPException(409, "TDCA-E-ASSET-STATE-002: 已转正"
                                     "（promoted_at 见列；⛔ 重复发令牌 ⛔ 重复落 NCA）")
    nca_ref = _nca_append("AGENT_CHANNEL_PROMOTED", actor,
                          artifact_path=f"agent-channel:{reg_no}/promotion",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        r2 = s.get(M.SiteAgentRegistry, reg_no)
        if r2 is None or r2.promoted_at is not None:   # 竞态护栏：重复转正事务回滚
            raise HTTPException(409, "TDCA-E-ASSET-STATE-002: 已转正"
                                     "（promoted_at 见列；⛔ 重复发令牌 ⛔ 重复落 NCA）")
        r2.promoted_at = now
        r2.promotion_nca_ref = nca_ref
    return _nca_watermark({
        "promoted": True, "reg_no": reg_no, "event_only": True,
        "promoted_at": now,
        "token_no": tok.token_no, "policy_no": pol.policy_no,
        "channel_type_unchanged": row.channel_type, "nca_ref": nca_ref,
        "note": "转正事件已落 NCA（AGENT_CHANNEL_PROMOTED）；promoted_at/promotion_nca_ref"
                " 已写登记表；⛔ 不改 channel_type——通道定性裁定不动，转正只作事件记录"},
        nature="real")


class InsuranceClaimReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    loss_type: str = ""          # 制度漏洞|技术漏洞
    description: str = ""        # 损失情述明文
    amount_mou: int = 0          # 申报损失额（MOU 折算，正整数）


@router.post("/{reg_no}/claims", status_code=201)
def file_claim(reg_no: str, req: InsuranceClaimReq, request: Request):
    """漏洞损失申报（人类会话内；仅登记主体本人；提交即落 NCA；状态 INSURED）。

    状态口径照在册保险规则（TDCA-INSURANCE-RULES-001）：INSURED＝事件触发态；
    定损→池兑付→追偿回补由在册保险金机制承接。
    """
    v = _require_session_user(request)
    actor = v["username"]
    loss_type = req.loss_type.strip()
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可申报漏洞损失"
                                     "（⛔ 智能体不得代报）")
        if loss_type not in ("制度漏洞", "技术漏洞"):
            raise HTTPException(400, "loss_type 仅接受 制度漏洞／技术漏洞（fail-closed）")
        if not req.description.strip():
            raise HTTPException(400, "损失情述（description）必填（fail-closed）")
        if req.amount_mou <= 0:
            raise HTTPException(400, "申报损失额须为正整数（MOU 计量，fail-closed）")
    claim_no = _claim_no()
    nca_ref = _nca_append("AGENT_CHANNEL_INSURANCE_CLAIM", actor,
                          artifact_path=f"agent-channel:{reg_no}/claim:{claim_no}",
                          prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentInsuranceClaim(
            claim_no=claim_no, reg_no=reg_no, loss_type=loss_type,
            description=req.description.strip(), amount_mou=req.amount_mou,
            status="INSURED", actor=actor, nca_ref=nca_ref,
            data_provenance="real", created_at=now))
    return _nca_watermark({
        "filed": True, "claim_no": claim_no, "reg_no": reg_no,
        "loss_type": loss_type, "amount_mou": req.amount_mou,
        "status": "INSURED", "nca_ref": nca_ref,
        "note": "漏洞损失申报已落 NCA（AGENT_CHANNEL_INSURANCE_CLAIM）；状态 INSURED"
                "＝事件触发态（定损→池兑付 NCA 留痕→追偿回补照在册保险金机制）"},
        nature="real")
