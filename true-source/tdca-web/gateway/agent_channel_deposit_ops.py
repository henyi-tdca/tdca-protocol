# -*- coding: utf-8 -*-
"""
A-29 智能体通道 对外补齐 C（L1SI166-CHANNEL-GAP-001 项 C）：效用保金
（押付／冻结／没收／退还四态账 ＋ 沙盒准入前置 fail-closed）。

制度口径（裁定 TDCA-RULING-L1SI166-GUEST-THREE-001 项三之 2／Q-2 ＋ 原令硬约束）：
  - 进沙盒须先抵押效用保金：无有效保金 ⟹ fail-closed 拒入盒
    （与六步硬序**同向叠加**，⛔ 不造旁路、⛔ 不改六步硬序本身）；
  - 四态：押付 paid／冻结 frozen／没收 confiscated／退还 refunded——事件账逐笔落行，
    当前有效保金＝Σ押付 − Σ没收 − Σ退还（冻结单列记账、不计减；fail-closed 读态）；
  - 违规没收 ⟹ 入**保险金池**（在册保险金机制同向，⛔ 另起一套）；没收权在人类裁决
    （founder 会话），⛔ 主体自身不得自操作；
  - 金额计量**按 MOU 折算**：参数一律读配置（TDCA_UTILITY_DEPOSIT_MIN_MOU），
    ⛔ 硬编码；配置缺省 ⟹ 沙盒准入闸 fail-closed 关闭（⛔ 忘配＝开门）；
  - 押付须载 MOU 折算依据引用（mou_ref），逐笔 NCA 落链；凭据值口径不涉及（保金非凭据）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark,  # noqa: E402
                    _require_session_user, _utc)
from agent_channel_ops import gate_assert, _require_founder  # noqa: E402

router = APIRouter(prefix="/api/v1/agent-channel", tags=["agent-channel-deposit"])

# 沙盒准入所需最低有效保金（MOU 单位）——⛔ 硬编码：一律读配置；
# 缺省（未配置/不可解析）⟹ required_min_mou() 返回 None ⟹ 沙盒闸 fail-closed 关闭。
_MIN_MOU_ENV = "TDCA_UTILITY_DEPOSIT_MIN_MOU"


def required_min_mou() -> int | None:
    """读配置之最低保金；未配置或非法 ⟹ None（fail-closed：闸保持关闭）。"""
    raw = os.environ.get(_MIN_MOU_ENV, "").strip()
    if not raw:
        return None
    try:
        v = int(raw)
    except ValueError:
        return None
    return v if v > 0 else None


def effective_deposit(s, reg_no: str) -> int:
    """当前有效保金（MOU）＝Σ押付 − Σ没收 − Σ退还（冻结单列、不减有效额）。"""
    q = s.query(M.SiteAgentUtilityDeposit.action,
                func.coalesce(func.sum(M.SiteAgentUtilityDeposit.amount_mou), 0))
    sums = {a: n for a, n in q.filter(M.SiteAgentUtilityDeposit.reg_no == reg_no)
            .group_by(M.SiteAgentUtilityDeposit.action)}
    return sums.get("paid", 0) - sums.get("confiscated", 0) - sums.get("refunded", 0)


def frozen_amount(s, reg_no: str) -> int:
    q = s.query(func.coalesce(func.sum(M.SiteAgentUtilityDeposit.amount_mou), 0))
    return q.filter(M.SiteAgentUtilityDeposit.reg_no == reg_no,
                    M.SiteAgentUtilityDeposit.action == "frozen").scalar() or 0


def _event_no() -> str:
    return "SUD-" + uuid.uuid4().hex[:12].upper()


def _add_event(s, reg_no: str, action: str, amount_mou: int, actor: str,
               mou_ref: str, pool: str, note: str, nca_action: str) -> dict:
    """四态事件落账（共用）：存证先于生效（fail-closed：存证失败操作不生效）。

    GO-LIVE-001 收口附页 §三：无收款通道 ⟹ 押付实为记账——data_provenance
    一律 simulated（⛔ real），NCA 存证同标 simulated；mou_ref 留空／INTERNAL-DEMO，
    ⛔ 编造流水号；对外口径只称「已记账」，⛔ 称「已收押金」。
    """
    nca_ref = _nca_append(nca_action, actor,
                          artifact_path=f"agent-channel:{reg_no}/deposit:{action}",
                          prov="simulated")
    now = _utc()
    event_no = _event_no()
    s.add(M.SiteAgentUtilityDeposit(
        event_no=event_no, reg_no=reg_no, action=action, amount_mou=amount_mou,
        mou_ref=mou_ref or None, pool=pool or None, note=note or None, actor=actor,
        nca_ref=nca_ref, data_provenance="simulated", created_at=now))
    return {"event_no": event_no, "nca_ref": nca_ref, "ts": now}


class DepositPayReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount_mou: int = 0
    mou_ref: str = ""        # MOU 折算依据引用（无收款通道：留空／INTERNAL-DEMO，⛔ 编造流水号）


@router.post("/{reg_no}/deposits", status_code=201)
def pay_deposit(reg_no: str, req: DepositPayReq, request: Request):
    """效用保金押付（人类会话内；仅登记主体本人；⛔ 智能体不得代付代持）。

    记账口径（收口附页 §三）：无收款通道 ⟹ 押付记 simulated 账，⛔ 称已收押金。
    """
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可押付其效用保金")
        if req.amount_mou <= 0:
            raise HTTPException(400, "押付金额须为正整数（MOU 计量，fail-closed）")
    with get_sessionmaker().begin() as s:
        ev = _add_event(s, reg_no, "paid", req.amount_mou, actor,
                        req.mou_ref.strip(), "", "", "AGENT_CHANNEL_DEPOSIT_PAID")
    with get_session() as s:
        bal = effective_deposit(s, reg_no)
    return _nca_watermark({
        "paid": True, "reg_no": reg_no, "amount_mou": req.amount_mou,
        "effective_mou": bal, **ev,
        "note": "押付记账（SIMULATED 水印：无收款通道，押付为记账 ⛔ 称已收押金）："
                "有效保金＝Σ押付−Σ没收−Σ退还；沙盒准入判据读配置"
                f"（{_MIN_MOU_ENV}）"}, nature="simulated")


class DepositActionReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = ""           # frozen／confiscated／refunded
    amount_mou: int = 0
    note: str = ""


@router.post("/{reg_no}/deposit-actions", status_code=201)
def deposit_action(reg_no: str, req: DepositActionReq, request: Request):
    """保金处置（四态之 frozen／confiscated／refunded；fail-closed：越权与超额即拒）。

    权限：冻结／退还＝登记主体本人或 founder；没收＝founder 独有（人类裁决，
    违规没收入**保险金池**）。超额（>当前有效）一律 400 拒绝。
    """
    action = req.action.strip()
    if action not in ("frozen", "confiscated", "refunded"):
        raise HTTPException(400, "action 仅接受 frozen／confiscated／refunded"
                                 "（押付请走 POST …/deposits；fail-closed）")
    v = _require_session_user(request)
    actor = v["username"]
    if action == "confiscated":
        actor = _require_founder(request)     # 没收权在人类裁决（⛔ 主体不得自操作）
    with get_session() as s:
        row = gate_assert(s, reg_no)
        if action != "confiscated" and row.owner_username != actor:
            with get_session() as s2:
                u = s2.get(M.User, actor)
            if u is None or u.role != "founder":
                raise HTTPException(403, "仅登记主体本人或 founder 可冻结／退还保金"
                                         "（人类签名权不可绕）")
        if req.amount_mou <= 0:
            raise HTTPException(400, "处置金额须为正整数（MOU 计量，fail-closed）")
        eff = effective_deposit(s, reg_no)
        if req.amount_mou > eff:
            raise HTTPException(400, f"处置超额：当前有效保金 {eff} MOU "
                                     f"< 请求 {req.amount_mou}（fail-closed）")
        pool = "保险金池" if action == "confiscated" else ""
        nca_action = {"frozen": "AGENT_CHANNEL_DEPOSIT_FROZEN",
                      "confiscated": "AGENT_CHANNEL_DEPOSIT_CONFISCATED",
                      "refunded": "AGENT_CHANNEL_DEPOSIT_REFUNDED"}[action]
    with get_sessionmaker().begin() as s:
        ev = _add_event(s, reg_no, action, req.amount_mou, actor,
                        "", pool, req.note.strip(), nca_action)
    with get_session() as s:
        bal = effective_deposit(s, reg_no)
    zh = {"frozen": "冻结", "confiscated": "没收（入保险金池）", "refunded": "退还"}[action]
    return _nca_watermark({
        "action": action, "zh": zh, "reg_no": reg_no, "amount_mou": req.amount_mou,
        "effective_mou": bal, **ev,
        "note": f"保金{zh}记账（SIMULATED 水印）；" + ("没收金额入保险金池（在册保险金机制同向）"
                                              if action == "confiscated" else "冻结单列记账不减有效额")},
        nature="simulated")


@router.get("/{reg_no}/deposits")
def deposit_state(reg_no: str, request: Request):
    """保金实况（会话用户可查）：逐笔事件＋有效额＋冻结额＋准入阈值（读配置）。"""
    _require_session_user(request)
    with get_session() as s:
        row = gate_assert(s, reg_no)
        events = [{"event_no": e.event_no, "action": e.action,
                   "amount_mou": e.amount_mou, "pool": e.pool,
                   "actor": e.actor, "nca_ref": e.nca_ref, "created_at": e.created_at}
                  for e in s.query(M.SiteAgentUtilityDeposit)
                  .filter_by(reg_no=reg_no).order_by(M.SiteAgentUtilityDeposit.created_at)]
        eff = effective_deposit(s, reg_no)
        frz = frozen_amount(s, reg_no)
    return _nca_watermark({
        "reg_no": reg_no, "channel_type": row.channel_type,
        "effective_mou": eff, "frozen_mou": frz,
        "events": events, "required_min_mou": required_min_mou(),
        "note": "有效保金＝Σ押付−Σ没收−Σ退还；冻结单列；阈值读配置（None=闸关）；"
                "本表记账为 SIMULATED 口径（无收款通道，⛔ 称已收押金）"},
        nature="simulated")
