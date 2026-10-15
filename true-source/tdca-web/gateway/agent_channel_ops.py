# -*- coding: utf-8 -*-
"""
A-26 智能体通道 批1 身份与登记（L1SI147-CHANNEL-B1-001）＋ 批2 通道本体（-B2）：/api/v1/agent-channel/*

制度口径（《智能体定义条例》V1.0-FROZEN ＋ 通道定性裁定 ＋ 施工技术评估方案 V2）：
  - 登记即创建、未登记即未创建：register 为唯一创建口，未登记公开查如实显幽灵态；
  - 主体与执行体二分：owner_username 为主体（人类账户），智能体执行体无财产；
  - 智能体侧标识＝登记号 reg_no（⛔ 不叫 TDID、⛔ 不自造编号体例；TDID 仅在锚↔令牌语境）；
  - 通道＝协议加载验证（⛔ 非身份验证）；六步硬序不可跳不可互替；
  - 人类签名权不可绕：凭据/令牌签发、轮换、吊销须人类会话内操作，⛔ 智能体不得代签代持；
  - 锚无效不发令牌（锚↔令牌硬挂接）：主体锚未达「notifier＋固锚/移锚级＋已补」
    即拒发身份类凭据，fail-closed；
  - 凭据族只存不可逆指纹（sha256），⛔ 凭据值一律不入库、至多一次性回显；
  - 轮换口径（默认）：签发即轮换——新签自动置同智能体旧 active 为 revoked；
  - 草案五表（agents/auth_grants/api_calls/agent_cards/members）只读不动、不承接；
  - 登记事实／凭据生命周期／六步状态机／fail-closed 判定＝接真（data_provenance=real）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _owner_display,  # noqa: E402
                    _require_session_user, _utc)
from api_v1 import (CONTRACT_ID, CONTRACT_VERSION,  # noqa: E402
                    CONTRACT_ZH_SHA256, CONTRACT_EN_SHA256, CONTRACT_JSON_SHA256)

router = APIRouter(prefix="/api/v1/agent-channel", tags=["agent-channel"])

# ---------------------------------------------------------------------
# 六步硬序（通道本体＝协议加载验证；步序不可跳不可互替）
# 批 1 落点：登记（准入）＋②凭据签发面；批 2 落点：①③④（闸步表 site_agent_admission）
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

# ①③④ 之状态机落点＝site_agent_admission 闸步表（批 2 接真）；⑤execute 批 3 承接
# ②token 步状态由凭据表 active 指纹派生，⛔ 不在闸步表落行（单一事实源）

# 协议包在册哈希（缔约协议三语分量，sha256_16 闭集——⛔ 不认可闭集外哈希）
_REGISTERED_PACKAGE_HASHES_16 = tuple(sorted({
    CONTRACT_ZH_SHA256[:16], CONTRACT_EN_SHA256[:16], CONTRACT_JSON_SHA256[:16]}))

_PUBLIC_KEYS = ("权属信息", "授权信息", "授权状态", "获取方式")

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NSFL_COMPILER = "true-source/tdca-web/tdca-nsfl-compiler/nsfl_compiler"


def _reg_no() -> str:
    """登记号：SAR-＋12 位十六进制（站点通道族内部序号，⛔ 非 TDID、非新编号体例）。"""
    return "SAR-" + uuid.uuid4().hex[:12].upper()


def _cred_no() -> str:
    return "SCD-" + uuid.uuid4().hex[:12].upper()


# =====================================================================
# 六步总闸（批 1 立、批 2 复核；后续批次只复用，⛔ 不另造旁路）
# =====================================================================

def _step_state(s, reg_no: str, step: str) -> str | None:
    """闸步表读态：passed/failed/pending；无行＝None（未达）。"""
    a = s.get(M.SiteAgentAdmission, (reg_no, step))
    return a.state if a else None


def _admission_set(reg_no: str, step: str, state: str, result_ref: str = "",
                   detail: str = "", nca_ref: str = "", actor: str = "") -> None:
    """闸步表落态（upsert，每（登记号,步）一行；fail-closed 非 passed 即未达）。"""
    now = _utc()
    with get_sessionmaker().begin() as s:
        a = s.get(M.SiteAgentAdmission, (reg_no, step))
        if a is None:
            s.add(M.SiteAgentAdmission(
                reg_no=reg_no, step=step, state=state, result_ref=result_ref or None,
                detail=detail or None, nca_ref=nca_ref or None, actor=actor or None,
                data_provenance="real", created_at=now, updated_at=now))
        else:
            a.state = state
            a.result_ref = result_ref or a.result_ref
            a.detail = detail or a.detail
            a.nca_ref = nca_ref or a.nca_ref
            a.actor = actor or a.actor
            a.updated_at = now


def _has_active_credential(s, reg_no: str) -> bool:
    return any(c.status == "active" for c in
               s.query(M.SiteAgentCredential).filter_by(reg_no=reg_no))


def _require_prior_steps(s, reg_no: str, need_token: bool = True) -> None:
    """六步硬序断言（不可跳不可互替）：①须 passed；need_token 时②须 active 凭据。

    fail-closed：未达即 403 并指明缺口——⛔ 不带红放行后续步。
    """
    if _step_state(s, reg_no, "protocol-load") != "passed":
        raise HTTPException(403, "STEP_ORDER: ① 协议未加载（protocol-load 未达）"
                                 "——未加载一切后续不可（fail-closed）")
    if need_token and not _has_active_credential(s, reg_no):
        raise HTTPException(403, "STEP_ORDER: ② 无有效执行令牌（无 active 凭据指纹）"
                                 "——六步不可跳（fail-closed）")


def evaluate_gate(s, reg_no: str) -> dict:
    """六步总闸评估（fail-closed：一切未知/缺失即拒，如实报各步态）。

    语义（B2-FIX-001 补正①：名实相符）：`admitted` ＝ **登记正常 且 六步全 satisfied**；
    登记面另留判据 `registry_ok`（在册且状态正常）；`unsatisfied_steps` 如实列缺口。
    批 2 复核：①③④ 读闸步表（⛔ 不再报 pending_batch）；②由凭据表 active 指纹派生；
    ⑤execute 批 3 接真读闸步表（passed→satisfied，⛔ 不再报 pending_batch）；
    ⑥登记存证已落链即 satisfied。
    状态闭集 satisfied/pending/failed。
    """
    row = s.get(M.SiteAgentRegistry, reg_no)
    if row is None:
        return {"admitted": False, "ghost": True, "reason": "UNREGISTERED",
                "note": "未登记即未创建：幽灵态不受保护"}
    steps = {}
    for num, key, label in SIX_STEPS:
        derived = None
        if key == "token":
            state = "satisfied" if _has_active_credential(s, reg_no) else "pending"
            derived = "凭据表 active 指纹派生（单一事实源）"
        elif key == "nca-evidence":
            state = "satisfied" if row.nca_ref else "pending"
            derived = "登记存证回链派生（⑥随各步落链）"
        else:
            st = _step_state(s, reg_no, key)   # ①③④⑤ 批 3 起同读闸步表（⛔ 不再特判 pending_batch）
            state = {"passed": "satisfied", "failed": "failed"}.get(st, "pending")
        step_info = {"step": num, "label": label, "state": state}
        if derived:
            step_info["derived"] = derived
        steps[key] = step_info
    denied = row.status != "正常"
    unsatisfied = [k for k, v in steps.items() if v["state"] != "satisfied"]
    admitted = (not denied) and not unsatisfied
    return {"admitted": admitted, "ghost": False, "reg_no": reg_no,
            "status": row.status,
            "registry_ok": not denied,   # 登记面判据（独立于六步）
            "denied_reason": f"PUNISHMENT_STATE:{row.status}" if denied else None,
            "unsatisfied_steps": unsatisfied or None,
            "steps": steps,
            "note": "总闸 fail-closed：admitted＝登记正常且六步全 satisfied（名实相符）；"
                    "登记面判据另列 registry_ok；登记缺失/惩罚态/任一步未达即拒"
                    "（六步不可跳不可互替）"}


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
    """智能体凭据签发（批 1 面；⛔ 人类会话内操作，智能体不得代签代持；锚无效不发令牌）。

    通道内完整签发/轮换/吊销见 POST /api/v1/agent-channel/token（批 2，含六步前置）。
    B2-FIX-001 补正③（取甲·复用轮换）：本端点新签**自动置同智能体旧 active 为
    revoked**（rotated_at 落时点），与 /token 同口径——⛔ 同智能体至多一 active 指纹。
    fail-closed 序：人类会话 → 总闸 → 主体本人 → 锚有效 → 旧证轮换 → 落新指纹。
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
        old_actives = [c for c in s.query(M.SiteAgentCredential)
                       .filter_by(reg_no=reg_no, status="active")]
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
        for c in old_actives:   # 复用轮换（B2-FIX-001③）：旧 active 全置 revoked
            c2 = s.get(M.SiteAgentCredential, c.cred_no)
            if c2 is None:
                raise HTTPException(409, "CONFLICT: 旧凭据行竞态消失（轮换中止，事务回滚）")
            c2.status = "revoked"
            c2.rotated_at = now
        s.add(M.SiteAgentCredential(
            cred_no=cred_no, reg_no=reg_no, cred_fingerprint=fingerprint,
            status="active", issued_at=now, issuer_session=session_fp,
            nca_ref=nca_ref, data_provenance="real"))
    return _nca_watermark({
        "issued": True, "cred_no": cred_no, "reg_no": reg_no, "issued_at": now,
        "rotated": len(old_actives),
        "credential": cred_value,     # 唯一回显一次；库内只存指纹
        "credential_fingerprint_sha256_16": fingerprint[:16],
        "note": "凭据值仅此一次回显、⛔ 不入库（库内只存不可逆指纹）；签发即轮换"
                "（同智能体至多一 active，B2-FIX-001③）；吊销即时生效"
                "（批 4 执行器承接）；人类会话内签发（⛔ 智能体不得代签代持）"
                "；通道内六步前置签发/吊销走 /token（批 2）"}, nature="real")


# =====================================================================
# 批 2（L1SI147-CHANNEL-B1-002）：通道本体——①protocol-load ②token ③ns-review ④sandbox
# 四端点均走批 1 总闸（gate_assert/_require_prior_steps），⛔ 不造旁路；
# 六步硬序：不可跳不可互替；凭据/令牌 ⛔ 值不入库、至多一次性回显。
# =====================================================================

def _subject_gate(reg_no: str, request: Request):
    """批 2 公共前置：人类会话 → 总闸（登记在册且正常）→ 主体本人。返回 (actor, session)。"""
    v = _require_session_user(request)
    actor = v["username"]
    s = get_session()
    row = gate_assert(s, reg_no)
    if row.owner_username != actor:
        s.close()
        raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可操作其智能体通道"
                                 "（⛔ 智能体不得代持代操作）")
    return actor, s


class ProtocolLoadReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""
    contract_version: str = ""       # 须等于在册缔约协议版本
    package_sha256_16: str = ""      # 协议包哈希（B2-FIX-001 建议④：升完整 64 位；16 位短值兼容）
    package_component: str = ""      # 可选分量标识 zh|en|json（如声明须与在册分量一致）


# 在册协议分量全量哈希（分量标识 → sha256-64）
_REGISTERED_PACKAGE_COMPONENTS = {
    "zh": CONTRACT_ZH_SHA256, "en": CONTRACT_EN_SHA256, "json": CONTRACT_JSON_SHA256}


def _match_package_hash(claimed: str, component: str) -> tuple[str, str] | None:
    """协议包哈希在册核验：64 位全量比对（或 16 位短值前缀比对）；返回 (分量, 全量哈希) 或 None。"""
    for comp, full in _REGISTERED_PACKAGE_COMPONENTS.items():
        if component and comp != component:
            continue
        if len(claimed) == 64 and claimed == full:
            return comp, full
        if len(claimed) == 16 and full.startswith(claimed):
            return comp, full
    return None


@router.post("/protocol-load")
def protocol_load(req: ProtocolLoadReq, request: Request):
    """① 通道本体＝协议加载验证：版本登记＋协议包哈希校验＋回执可机验凭证。

    通道定性（裁定）：通道＝协议加载验证，⛔ 非身份验证。
    fail-closed：版本不符/哈希不符/分量声明不符 → 403（未加载/哈希不符，⛔ 一切后续不可）。
    """
    actor, s = _subject_gate(req.reg_no, request)
    s.close()
    if req.contract_version != CONTRACT_VERSION:
        raise HTTPException(403, "PROTOCOL_VERSION_UNKNOWN: 协议版本未在册"
                                 "（fail-closed，未加载一切后续不可）")
    claimed = req.package_sha256_16.strip().lower()
    matched = _match_package_hash(claimed, req.package_component.strip().lower())
    if matched is None:
        raise HTTPException(403, "PROTOCOL_HASH_MISMATCH: 协议包哈希不在册"
                                 "（哈希不符/分量声明不符 → ⛔ 一切后续不可）")
    matched_comp, full_hash = matched
    nca_ref = _nca_append("AGENT_CHANNEL_PROTOCOL_LOAD", actor,
                          artifact_path=(f"agent-channel:{req.reg_no}"
                                         f"/protocol:{CONTRACT_ID}:{CONTRACT_VERSION}"),
                          prov="real")
    receipt_core = {"loaded": True, "channel": "协议加载验证（⛔ 非身份验证）",
                    "contract_id": CONTRACT_ID, "contract_version": CONTRACT_VERSION,
                    "verified_component": matched_comp,
                    "verified_sha256": full_hash,
                    "verified_sha256_16": full_hash[:16],
                    "nca_ref": nca_ref, "ts": _utc()}
    receipt = "sha256:" + hashlib.sha256(json.dumps(
        receipt_core, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:32]
    _admission_set(req.reg_no, "protocol-load", "passed",
                   result_ref=f"sha256:{full_hash}",
                   detail=json.dumps({"contract_id": CONTRACT_ID,
                                      "contract_version": CONTRACT_VERSION,
                                      "component": matched_comp},
                                     ensure_ascii=False, sort_keys=True),
                   nca_ref=nca_ref, actor=actor)
    return _nca_watermark({**receipt_core, "receipt_sha256_32": receipt,
                           "note": "协议加载验证通过：版本、分量与协议包哈希（64 位全量）在册"
                                   "核验一致；回执哈希＋NCA 存证双件可机验；"
                                   "⛔ 身份验证不在通道本体"},
                          nature="real")


class TokenReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""
    action: str = "issue"     # issue（签发）| rotate（轮换）| revoke（吊销）


@router.post("/token")
def token_manage(req: TokenReq, request: Request):
    """② 执行令牌：签发／轮换／吊销（人类会话内；锚无效不发令牌；吊销即时生效）。

    轮换口径（默认）：签发即轮换——新签自动置同智能体旧 active 凭据为 revoked。
    锚↔令牌挂接：签发之存证引用载锚口径（kind/tier/state），回执载锚口径。
    """
    actor, s = _subject_gate(req.reg_no, request)
    try:
        if req.action not in ("issue", "rotate", "revoke"):
            raise HTTPException(400, "action 仅接受 issue|rotate|revoke")
        # ②首签只要求 ①已加载（need_token=False——②自身是令牌步，⛔ 不自要求）
        _require_prior_steps(s, req.reg_no, need_token=False)
        if req.action == "revoke":
            actives = [c for c in s.query(M.SiteAgentCredential)
                       .filter_by(reg_no=req.reg_no, status="active")]
            nca_ref = _nca_append("AGENT_CHANNEL_TOKEN_REVOKE", actor,
                                  artifact_path=f"agent-channel:{req.reg_no}/token:revoke",
                                  prov="real")
            now = _utc()
            n = len(actives)
            with get_sessionmaker().begin() as s2:
                for c in actives:
                    c2 = s2.get(M.SiteAgentCredential, c.cred_no)
                    if c2 is None:
                        raise HTTPException(409, "CONFLICT: 凭据行竞态消失"
                                                 "（吊销中止，事务回滚）")
                    c2.status = "revoked"
                    c2.revoked_at = now
            return _nca_watermark({
                "action": "revoke", "revoked": n, "immediate": True,
                "nca_ref": nca_ref,
                "note": "吊销即时生效：全库即时拒（无 active 指纹即②步未达，六步总闸即闭）"},
                nature="real")
        # issue / rotate（签发即轮换）
        anchor = s.get(M.UserAnchor, actor)
        if anchor is None:
            raise HTTPException(403, "ANCHOR_INVALID: 主体无锚记录"
                                     "——锚无效不发令牌（fail-closed）")
        if not _anchor_valid(s, actor):
            raise HTTPException(403, "ANCHOR_INVALID: 主体锚无效或未达定档"
                                     "（须 notifier＋固锚/移锚级＋已补）"
                                     "——锚无效不发令牌（fail-closed）")
        old_actives = [c for c in s.query(M.SiteAgentCredential)
                       .filter_by(reg_no=req.reg_no, status="active")]
        cred_value = "TDCA-AGT-" + secrets.token_urlsafe(32)
        fingerprint = hashlib.sha256(cred_value.encode("utf-8")).hexdigest()
        session_fp = hashlib.sha256(
            request.headers.get("authorization", "").strip().encode("utf-8")).hexdigest()
        cred_no = _cred_no()
        anchor_seg = (f"anchor://{anchor.anchor_kind}/{anchor.anchor_tier}"
                      f"/{anchor.tier_state}")   # 锚↔令牌挂接：存证引用载锚口径
        nca_ref = _nca_append("AGENT_CHANNEL_TOKEN_ISSUE", actor,
                              artifact_path=(f"agent-channel:{req.reg_no}"
                                             f"/token:{cred_no}/{anchor_seg}"),
                              prov="real")
        now = _utc()
        with get_sessionmaker().begin() as s2:
            for c in old_actives:   # 签发即轮换（默认口径）：旧 active 全置 revoked
                c2 = s2.get(M.SiteAgentCredential, c.cred_no)
                if c2 is None:
                    raise HTTPException(409, "CONFLICT: 旧凭据行竞态消失"
                                             "（轮换中止，事务回滚）")
                c2.status = "revoked"
                c2.rotated_at = now
            s2.add(M.SiteAgentCredential(
                cred_no=cred_no, reg_no=req.reg_no, cred_fingerprint=fingerprint,
                status="active", issued_at=now, issuer_session=session_fp,
                nca_ref=nca_ref, data_provenance="real"))
    finally:
        s.close()
    return _nca_watermark({
        "action": req.action, "issued": True, "cred_no": cred_no,
        "reg_no": req.reg_no, "issued_at": now,
        "rotated": len(old_actives),   # 签发即轮换：被轮换的旧凭据数
        "credential": cred_value,      # 至多一次性回显；库内只存指纹
        "credential_fingerprint_sha256_16": fingerprint[:16],
        "anchor": {"kind": anchor.anchor_kind, "tier": anchor.anchor_tier,
                   "state": anchor.tier_state},
        "nca_ref": nca_ref,
        "note": "锚↔令牌挂接：存证引用与回执均载锚口径；签发即轮换（默认口径，创始人可改）；"
                "吊销即时生效"}, nature="real")


class NsReviewReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""
    boundary_ref: str = ""          # NSFL 边界函数声明引用
    adversarial_set_ref: str = ""   # 对抗集引用
    scene_scope: str = ""           # 场景约束范围
    note: str = ""


@router.post("/ns-review")
def ns_review(req: NsReviewReq, request: Request):
    """③ 负空间审查：申报与判定（fail-closed：不过 → ⛔ 拒绝入网）。

    判定分两层：结构要件机验（闭集内确定性）＋深度对抗判定归 NSFL 引擎
    （组件在位如实报，⛔ 不冒充已跑对抗）。结构要件不齐＝不过，如实记 failed。
    """
    actor, s = _subject_gate(req.reg_no, request)
    try:
        _require_prior_steps(s, req.reg_no)   # ①②须达（fail-closed：未达拒入网）
        missing = [k for k, v in (("boundary_ref", req.boundary_ref),
                                  ("adversarial_set_ref", req.adversarial_set_ref),
                                  ("scene_scope", req.scene_scope)) if not v.strip()]
        申报来源 = "人类会话内申报（登记主体本人）"
        机验层级_过 = ("结构要件层（闭集内机验通过）；引擎层未跑——NSFL 深度对抗判定归引擎"
                       "（⛔ passed 不等于已过对抗）")
        机验层级_拒 = "结构要件层未过（要件缺失）——拒绝入网；引擎层未跑"
        if missing:
            nca_ref = _nca_append("AGENT_CHANNEL_NS_REVIEW_FAIL", actor,
                                  artifact_path=f"agent-channel:{req.reg_no}/ns-review:rejected",
                                  prov="real")
            _admission_set(req.reg_no, "ns-review", "failed",
                           detail=json.dumps({"missing": missing,
                                              "申报来源": 申报来源,
                                              "机验层级": 机验层级_拒},
                                             ensure_ascii=False),
                           nca_ref=nca_ref, actor=actor)
            raise HTTPException(400, f"NS_REVIEW_REJECTED: 负空间审查不过（要件缺失："
                                     f"{','.join(missing)}）——拒绝入网（fail-closed）")
        payload = {"boundary_ref": req.boundary_ref.strip(),
                   "adversarial_set_ref": req.adversarial_set_ref.strip(),
                   "scene_scope": req.scene_scope.strip(),
                   "note": req.note.strip() or None,
                   "申报来源": 申报来源, "机验层级": 机验层级_过}
        nca_ref = _nca_append("AGENT_CHANNEL_NS_REVIEW", actor,
                              artifact_path=f"agent-channel:{req.reg_no}/ns-review:passed",
                              prov="real")
        _admission_set(req.reg_no, "ns-review", "passed",
                       result_ref=req.boundary_ref.strip(),
                       detail=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                       nca_ref=nca_ref, actor=actor)
    finally:
        s.close()
    return _nca_watermark({
        "verdict": "passed", "admitted_to_sandbox": True,
        "申报来源": 申报来源, "机验层级": 机验层级_过,
        "components": {"nsfl_compiler": "PRESENT" if (_REPO_ROOT / _NSFL_COMPILER).is_dir()
                       else "MISSING"},
        "nca_ref": nca_ref,
        "note": "结构要件机验通过（闭集内确定性判定）；深度对抗判定归 NSFL 引擎，"
                "组件在位如实报、⛔ 不冒充已跑对抗（passed ≠ 已过对抗）；"
                "未过即拒绝入网"}, nature="real")


class SandboxReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""
    sea_elements_ref: str = ""     # SEA 要件绑定引用
    sandbox_run_ref: str = ""      # 沙盒运行号引用
    result: str = ""               # passed|failed


@router.post("/sandbox")
def sandbox_verify(req: SandboxReq, request: Request):
    """④ 沙盒验证：要件绑定与结果登记（fail-closed：未过 → ⛔ 不得正空间执行）。"""
    actor, s = _subject_gate(req.reg_no, request)
    try:
        _require_prior_steps(s, req.reg_no)            # ①②须达
        if _step_state(s, req.reg_no, "ns-review") != "passed":
            raise HTTPException(403, "STEP_ORDER: ③ 负空间审查未过——"
                                     "未过即拒绝入网，⛔ 不得进沙盒（fail-closed）")
        if req.result not in ("passed", "failed"):
            raise HTTPException(400, "result 仅接受 passed|failed")
        missing = [k for k, v in (("sea_elements_ref", req.sea_elements_ref),
                                  ("sandbox_run_ref", req.sandbox_run_ref)) if not v.strip()]
        if missing:
            raise HTTPException(400, f"沙盒要件缺失：{','.join(missing)}（fail-closed）")
        passed = req.result == "passed"
        申报来源 = "人类会话内申报（登记主体本人）"
        机验层级 = ("结果系申报（沙盒运行号引用绑定，⛔ 非站内实跑；"
                    "passed ≠ 已实跑沙盒）")
        nca_ref = _nca_append(
            "AGENT_CHANNEL_SANDBOX_PASS" if passed else "AGENT_CHANNEL_SANDBOX_FAIL",
            actor, artifact_path=f"agent-channel:{req.reg_no}/sandbox:{req.result}",
            prov="real")
        _admission_set(req.reg_no, "sandbox", "passed" if passed else "failed",
                       result_ref=req.sandbox_run_ref.strip(),
                       detail=json.dumps({"sea_elements_ref": req.sea_elements_ref.strip(),
                                          "sandbox_run_ref": req.sandbox_run_ref.strip(),
                                          "申报来源": 申报来源, "机验层级": 机验层级},
                                         ensure_ascii=False, sort_keys=True),
                       nca_ref=nca_ref, actor=actor)
    finally:
        s.close()
    return _nca_watermark({
        "bound": True, "result": req.result, "executable": passed,
        "申报来源": 申报来源, "机验层级": 机验层级,
        "nca_ref": nca_ref,
        "note": ("沙盒验证申报登记通过（结果系申报，⛔ 非站内实跑）："
                 "可进正空间执行（批 3 承接 execute＋计量）"
                 if passed else
                 "沙盒未过（结果系申报）：⛔ 不得正空间执行（fail-closed，闸步表已记 failed）")},
        nature="real")


# =====================================================================
# 批 3（L1SI147-CHANNEL-B1-003）：交易接线——授权件四要件机验＋execute 正空间执行＋计量落账
# 授权件表 site_agent_grant＋计量表 site_agent_call_ledger（迁移 0010）；
# 四要件依在册《授权件模板》（R1 场景约束/R2 五阶资产形态/R3 全构成已授权/R4 法律主体签名）；
# 核心 fail-closed：无授权件⟹拒（配置即侵权）、④未过⟹⛔不得执行、存证失败⟹操作不生效。
# =====================================================================

def _grant_no() -> str:
    return "SGR-" + uuid.uuid4().hex[:12].upper()


# R2 五阶资产形态闭集（《授权件模板》R2：未列明之阶不得据本件主张）
_GRANT_TIERS = ("一阶", "二阶", "三阶", "四阶", "五阶")

# 计量聚合窗口（方案 V2 §九 只要求设窗未定值：施工取 60 秒；窗口起点按 ISO 分钟截断）
_LEDGER_WINDOW_MINUTES = 1
_LEDGER_ENDPOINT_EXECUTE = "execute"


def _ledger_window(ts: str) -> str:
    """聚合窗口起点：ISO 分钟截断（ts 形如 YYYY-MM-DDTHH:MM:SSZ）。"""
    return ts[:16]


class GrantReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_constraint: str = ""       # R1 场景（必填；未列明场景不在授权范围；多场景逗号分隔）
    tiers_covered: str = ""          # R2 五阶清单（必填；如「一阶,三阶」，逐项须在五阶闭集）
    full_composition: bool = False   # R3 全构成已授权声明（须 true；有保留即未达全构成）
    legal_signer: str = ""           # R4 法律主体签名者（本人；⛔ 智能体不代签代持）
    signature_ref: str = ""          # R4 签名事件引用（须落 NCA 的引用串）
    parent_grant_no: str = ""        # 转授上层件号（可空）


@router.post("/{reg_no}/grants", status_code=201)
def issue_grant(reg_no: str, req: GrantReq, request: Request):
    """授权件登记（四要件机验，缺一不成立；人类会话内，⛔ 智能体不代签代持）。

    fail-closed 序：人类会话 → 总闸 → 主体本人 → 四要件逐条机验（缺件逐条拒）
    → 存证（先存证后落表：存证失败⟹操作不生效）→ 落表 active＋机验明细 detail。
    场景闭集口径：未列明场景不在授权范围（R1）；五阶未列明之阶不得据本件主张（R2）。
    """
    actor, s = _subject_gate(reg_no, request)
    try:
        missing = []
        if not req.scene_constraint.strip():
            missing.append("R1 场景约束缺失（scene_constraint 必填）")
        tiers = [t.strip() for t in req.tiers_covered.replace("，", ",").split(",") if t.strip()]
        if not tiers:
            missing.append("R2 五阶清单缺失（tiers_covered 必填）")
        else:
            bad = [t for t in tiers if t not in _GRANT_TIERS]
            if bad:
                missing.append(f"R2 五阶清单越闭集：{','.join(bad)}")
        if not req.full_composition:
            missing.append("R3 全构成已授权声明缺失（有保留即未达全构成，须显式声明 true）")
        if not req.legal_signer.strip():
            missing.append("R4 法律主体签名者缺失（legal_signer 必填，⛔ 智能体不代签）")
        if not req.signature_ref.strip():
            missing.append("R4 签名事件引用缺失（signature_ref 必填，签名事件须落 NCA）")
        if req.parent_grant_no.strip():
            parent = s.get(M.SiteAgentGrant, req.parent_grant_no.strip())
            if parent is None or parent.status != "active":
                raise HTTPException(403, "GRANT_PARENT_INVALID: 转授上层件不存在或非 active"
                                         "（多层转授逐层皆须件，任一环失效下游全失效）")
        if missing:
            raise HTTPException(400, "GRANT_REJECTED: 授权件四要件缺一不成立——"
                                     + "；".join(missing) + "（fail-closed：无件不得配置）")
        grant_no = _grant_no()
        nca_ref = _nca_append("AGENT_CHANNEL_GRANT_ISSUE", actor,
                              artifact_path=f"agent-channel:{reg_no}/grant:{grant_no}",
                              prov="real")   # 先存证：写入失败⟹操作不生效（⛔ 不落半条）
        detail = json.dumps({
            "R1 场景约束": req.scene_constraint.strip(),
            "R2 五阶资产形态": tiers,
            "R3 全构成已授权": True,
            "R4 法律主体签名": {"signer": req.legal_signer.strip(),
                              "signature_ref": req.signature_ref.strip()},
            "四要件判": {k: True for k in ("R1", "R2", "R3", "R4")},
            "parent_grant_no": req.parent_grant_no.strip() or None,
        }, ensure_ascii=False, sort_keys=True)
        now = _utc()
        with get_sessionmaker().begin() as s2:
            s2.add(M.SiteAgentGrant(
                grant_no=grant_no, reg_no=reg_no,
                scene_constraint=req.scene_constraint.strip(),
                legal_signer=req.legal_signer.strip(),
                signature_ref=req.signature_ref.strip(),
                parent_grant_no=req.parent_grant_no.strip() or None,
                status="active", detail=detail, nca_ref=nca_ref, actor=actor,
                data_provenance="real", created_at=now, updated_at=now))
    finally:
        s.close()
    return _nca_watermark({
        "granted": True, "grant_no": grant_no, "reg_no": reg_no, "status": "active",
        "four_requirements": {"R1 场景约束": True, "R2 五阶资产形态": True,
                              "R3 全构成已授权": True, "R4 法律主体签名": True},
        "nca_ref": nca_ref,
        "note": "授权件四要件机验通过（照在册《授权件模板》，缺一不成立）；"
                "人类会话内登记（⛔ 智能体不代签代持）；生效≠部署≠上线≠对外；"
                "无有效授权件即不得执行（配置即侵权口径）"}, nature="real")


def _active_grant(s, reg_no: str, scene: str) -> "M.SiteAgentGrant | None":
    """有效授权件机验（execute 前置）：active 且在册＋场景命中（R1：未列明场景不在授权范围）。"""
    for g in s.query(M.SiteAgentGrant).filter_by(reg_no=reg_no, status="active"):
        scenes = [x.strip() for seg in g.scene_constraint.replace("，", ",").split(";")
                  for x in seg.split(",") if x.strip()]
        if scene in scenes:
            return g
    return None


class ExecuteReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""        # 登记号
    scene: str = ""         # 本次执行场景（须在授权件场景约束列明范围内）
    action: str = ""        # 正空间动作（如实记录于闸步明细）
    units: int = 1          # 计量单位（数值按方案标模拟，SIMULATED 水印）


@router.post("/execute")
def execute(req: ExecuteReq, request: Request):
    """⑤ 正空间执行＋计量落账（fail-closed 全序：⛔ 不可跳不可互替）。

    硬序：人类会话 → 总闸 → 主体本人 → ①②（须达）→ ③须过 → ④须过（未过⟹⛔不得执行）
    → 授权件机验（无有效件⟹拒，配置即侵权；场景越界⟹拒，R1 未列明不在授权范围）
    → 存证（先存证后落账：写入失败⟹操作不生效）→ 计量聚合落账（窗口内一行累计，
    ⛔ 不高频直写致锁）→ 闸步表 execute 记 passed。
    计量数值按方案标模拟（SIMULATED 水印）；执行事实／状态机／存证接真。
    """
    actor, s = _subject_gate(req.reg_no, request)
    try:
        _require_prior_steps(s, req.reg_no)      # ①②须达（吊销即时：无 active 凭据即拒）
        if _step_state(s, req.reg_no, "ns-review") != "passed":
            raise HTTPException(403, "STEP_ORDER: ③ 负空间审查未过——拒绝入网，"
                                     "⛔ 不得正空间执行（fail-closed）")
        if _step_state(s, req.reg_no, "sandbox") != "passed":
            raise HTTPException(403, "STEP_ORDER: ④ 沙盒验证未过——⛔ 不得正空间执行（fail-closed）")
        if not req.scene.strip():
            raise HTTPException(403, "GRANT_SCENE_REQUIRED: 执行须声明场景"
                                     "（R1 场景约束：未列明场景不在授权范围）")
        grant = _active_grant(s, req.reg_no, req.scene.strip())
        if grant is None:
            raise HTTPException(403, "GRANT_REQUIRED: 无有效授权件（或无覆盖本场景的授权件）"
                                     "——配置即侵权，无授权不得执行（fail-closed）")
        申报来源 = "人类会话内发起（登记主体本人）"
        机验层级 = ("授权件四要件机验层（结构要件闭集机验通过）；计量聚合落账层接真；"
                    "实际算力执行不在站内（如实标注）")
        nca_ref = _nca_append("AGENT_CHANNEL_EXECUTE", actor,
                              artifact_path=(f"agent-channel:{req.reg_no}"
                                             f"/execute:{grant.grant_no}:{req.scene.strip()}"),
                              prov="real")   # 先存证：写入失败⟹操作不生效（⛔ 不落半条）
        now = _utc()
        window = _ledger_window(now)
        with get_sessionmaker().begin() as s2:
            row = s2.get(M.SiteAgentCallLedger,
                         (req.reg_no, _LEDGER_ENDPOINT_EXECUTE, window))
            if row is None:
                s2.add(M.SiteAgentCallLedger(
                    reg_no=req.reg_no, endpoint=_LEDGER_ENDPOINT_EXECUTE, ts=window,
                    units=req.units, nca_anchor=nca_ref,
                    data_provenance="mixed", created_at=now, updated_at=now))
            else:
                row.units += req.units
                row.nca_anchor = nca_ref
                row.updated_at = now
        _admission_set(req.reg_no, "execute", "passed",
                       result_ref=grant.grant_no,
                       detail=json.dumps({"scene": req.scene.strip(),
                                          "action": req.action.strip() or None,
                                          "grant_no": grant.grant_no,
                                          "ledger_window": window, "units": req.units,
                                          "申报来源": 申报来源, "机验层级": 机验层级},
                                         ensure_ascii=False, sort_keys=True),
                       nca_ref=nca_ref, actor=actor)
        with get_session() as s3:
            gate = evaluate_gate(s3, req.reg_no)
    finally:
        s.close()
    return _nca_watermark({
        "executed": True, "reg_no": req.reg_no, "scene": req.scene.strip(),
        "action": req.action.strip() or None, "grant_no": grant.grant_no,
        "ledger": {"endpoint": _LEDGER_ENDPOINT_EXECUTE, "window": window,
                   "units": req.units, "data_nature": "simulated",
                   "note": "SIMULATED 水印：计量数值按方案标模拟（聚合窗口 "
                           f"{_LEDGER_WINDOW_MINUTES} 分钟）"},
        "申报来源": 申报来源, "机验层级": 机验层级,
        "admission": "execute:passed", "gate": gate, "nca_ref": nca_ref,
        "note": "正空间执行登记通过：六步硬序①②③④全达＋授权件四要件机验＋存证落链；"
                "计量数值 SIMULATED（方案 §六），执行事实／状态机／存证接真；"
                "生效≠部署≠上线≠对外"}, nature="mixed")
