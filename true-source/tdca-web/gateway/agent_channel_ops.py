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

import asyncio
import hashlib
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _owner_display,  # noqa: E402
                    _require_session_user, _client_ip, _utc)
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
    """智能体自助登记请求（块 E-2：字段中文名照《智能体定义条例》原文，机读键名自定随回报）。

    创世六要素（第8条第1款，恰6项）：device 设备／compute 算力／protocol 协议／
    role 角色／knowledge 知识／permission_ttl 权限时效；
    锚定项（第8条第2款，单列、不计入六要素）：anchor_account 锚定之人类账户 ＋
    root_token_ref 根令牌引用；多创建者余者列 participants 资产配置参与方
    （单一责任锚点＝锚定之人类账户，组织须递归至可追责之人，第8条第3款）；
    派生登记（第10条再登记）：derived=True 时 source_lineage 来源谱系必填；
    两路（第9条＋E-5 分流首问）：channel_type=ANCHOR（原生，须人类会话）／
    GUEST（非原生，随调用提交 agent_card＋外部创建者声明，合规前置校验通过才发号）。
    """

    model_config = ConfigDict(extra="forbid")
    channel_type: str = ""           # ANCHOR（原生）／GUEST（非原生）；分流首问二选一
    device: str = ""                 # 设备
    compute: str = ""                # 算力
    protocol: str = ""               # 协议
    role: str = ""                   # 角色
    knowledge: str = ""              # 知识
    permission_ttl: str = ""         # 权限时效
    anchor_account: str = ""         # 锚定之人类账户（ANCHOR 路，缺省＝会话本人）
    root_token_ref: str = ""         # 根令牌引用（ANCHOR 路必填；只收引用，⛔ 不收令牌值）
    participants: list[str] = []     # 资产配置参与方（多创建者之余者；可空）
    derived: bool = False            # 派生登记（再登记）标识
    source_lineage: str = ""         # 来源谱系（derived=True 必填）
    agent_card: object | None = None  # GUEST 路必填（条例第9条，JSON 对象 ≤4KB；型别校验在手工程序，与其他缺项同回 400 点名）
    ext_declaration: str = ""        # GUEST 路必填：外部创建者声明·主体声明
    ext_contact: str = ""            # GUEST 路必填：外部创建者声明·可核验联系方式


# 频控（E-3.5／E-5-2.4；阈值执行侧自定、随回报）：同一 IP×路 滑动窗口；
# GUEST 严于 ANCHOR；触限回 429（⛔ 静默丢弃）。内存态，重启清零（频控非安全唯一防线）。
_CHREG_WINDOW_S = 3600
_CHREG_MAX = {"ANCHOR": 30, "GUEST": 5}
_chreg_hits: dict[str, list[float]] = {}


def _chreg_rate_ok(ip: str, channel_type: str) -> bool:
    now = time.time()
    hits = [t for t in _chreg_hits.get(f"{ip}|{channel_type}", []) if now - t < _CHREG_WINDOW_S]
    if len(hits) >= _CHREG_MAX[channel_type]:
        _chreg_hits[f"{ip}|{channel_type}"] = hits
        return False
    hits.append(now)
    _chreg_hits[f"{ip}|{channel_type}"] = hits
    return True


# 六要素（第8条第1款）机读键 ↔ 条例原文（回报字段清单用，⛔ 不自拟别名）
SIX_ELEMENT_FIELDS = (
    ("device", "设备"),
    ("compute", "算力"),
    ("protocol", "协议"),
    ("role", "角色"),
    ("knowledge", "知识"),
    ("permission_ttl", "权限时效"),
)


def _idem_key(channel_type: str, six: tuple[str, ...], identity: str) -> str:
    """幂等键（E-3.2／E-5-2.3）：channel_type＋六要素表达＋锚定身份之 sha256_16。
    ANCHOR 身份＝锚定之人类账户；GUEST 身份＝外部声明＋联系方式之哈希（⛔ 不明文入库）。"""
    payload = {"channel_type": channel_type, "six": list(six), "identity": identity}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True)
                          .encode()).hexdigest()[:16]


@router.post("/register", status_code=201)
def register_agent(req: RegisterReq, request: Request):
    """智能体自助登记（登记即创建·唯一创建口；块 E：六要素逐项点名 fail-closed、
    ANCHOR 须人类会话、GUEST 合规前置校验通过才发号（校验在前、发号在后）、
    幂等复用原登记号、NCA 全程落链）。"""
    ct = req.channel_type.strip().upper()
    if ct not in ("ANCHOR", "GUEST"):
        raise HTTPException(400, "channel_type 为必填，仅接受 ANCHOR／GUEST（分流首问二选一）")
    ip = _client_ip(request)
    if not _chreg_rate_ok(ip, ct):
        raise HTTPException(429, f"登记过于频繁（{ct} 路每 IP 每小时 ≤{_CHREG_MAX[ct]} 次），请稍后再试")
    # 六要素逐项点名（第8条第1款，恰6项；⛔ 静默落成幽灵态）
    missing = [zh for k, zh in SIX_ELEMENT_FIELDS if not getattr(req, k).strip()]
    if missing:
        raise HTTPException(400, "创世六要素不齐（第8条第1款，恰6项），缺：" + "／".join(missing))
    six = tuple(getattr(req, k).strip() for k, _ in SIX_ELEMENT_FIELDS)
    if req.derived and not req.source_lineage.strip():
        raise HTTPException(400, "派生登记（第10条再登记）须载来源谱系 source_lineage（必填）")
    six_ref = "six-elements://itemized/" + hashlib.sha256(
        json.dumps(six, ensure_ascii=False).encode()).hexdigest()[:12]
    precheck_nca = precheck_at = None
    if ct == "ANCHOR":
        # 原生路（第9条第1款）：须人类会话（智能体不得自登），锚定项单列
        v = _require_session_user(request)
        owner = v["username"]
        anchor_account = req.anchor_account.strip() or owner
        if anchor_account != owner:
            raise HTTPException(400, "锚定之人类账户须等于本会话账户（单一责任锚点，第8条第3款）")
        anchor_missing = []
        if not req.root_token_ref.strip():
            anchor_missing.append("根令牌引用")
        if anchor_missing:
            raise HTTPException(400, "锚定项不齐（第8条第2款，单列不计入六要素），缺：" + "／".join(anchor_missing))
        with get_session() as s:
            if s.get(M.User, owner) is None:
                raise HTTPException(403, "主体账户不存在（fail-closed）")
            owner_display = _owner_display(s, owner)
        identity = anchor_account
        agent_card_json = ext_declaration = ext_contact = None
    else:
        # 非原生路（第9条第2款＋E-5-2）：合规前置校验——通过才发号，⛔ 先发号后校验
        owner = None
        owner_display = None
        anchor_account = ""
        pre_missing = []
        if not req.agent_card or not isinstance(req.agent_card, dict):
            pre_missing.append("agent_card（条例第9条，JSON 对象）")
        elif len(json.dumps(req.agent_card, ensure_ascii=False)) > 4096:
            pre_missing.append("agent_card 过大（≤4KB）")
        if not req.ext_declaration.strip():
            pre_missing.append("外部创建者声明·主体声明")
        if not req.ext_contact.strip():
            pre_missing.append("外部创建者声明·可核验联系方式")
        elif len(req.ext_contact.strip()) > 256:
            pre_missing.append("可核验联系方式过长（≤256 字符）")
        if pre_missing:
            raise HTTPException(400, "GUEST 合规前置校验不过（缺：" + "／".join(pre_missing) + "）")
        decl_hash = hashlib.sha256(
            (req.ext_declaration.strip() + "|" + req.ext_contact.strip()).encode()).hexdigest()
        identity = decl_hash[:16]
        # 校验在前：先落校验存证（带时间戳）——NCA 追加不依赖登记号（S-13 无冲突）
        precheck_nca = _nca_append("AGENT_CHANNEL_GUEST_PRECHECK", f"guest:{identity}",
                                   artifact_path=f"agent-channel:guest-precheck:{identity}",
                                   prov="real")
        with get_session() as s:
            precheck_at = s.get(M.NcaChain, precheck_nca).ts
        agent_card_json = json.dumps(req.agent_card, ensure_ascii=False, sort_keys=True)
        ext_declaration = req.ext_declaration.strip()
        ext_contact = req.ext_contact.strip()
    idem = _idem_key(ct, six, identity)
    with get_session() as s:
        existing = s.query(M.SiteAgentRegistry).filter_by(idem_key=idem).one_or_none()
    if existing is not None:
        # 幂等复用（E-3.2／E-5-2.3）：同一锚定＋同一表达形式再提交 ⟹ 复用原登记号
        return _nca_watermark({
            "registered": True, "reused": True, "reg_no": existing.reg_no,
            "channel_type": existing.channel_type, "status": existing.status,
            "idem_key": idem,
            "note": "幂等复用：同一锚定身份＋同一六要素表达形式已登记，复用原登记号"
                    "（⛔ 重复建档）"}, nature="real")
    reg_no = _reg_no()
    actor = owner if ct == "ANCHOR" else f"guest:{identity}"
    nca_ref = _nca_append("AGENT_CHANNEL_REGISTER", actor,
                          artifact_path=f"agent-channel:{reg_no}", prov="real")
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentRegistry(
            reg_no=reg_no, owner_username=owner if owner else f"guest:{identity}",
            six_elements_ref=six_ref,
            six_device=six[0], six_compute=six[1], six_protocol=six[2],
            six_role=six[3], six_knowledge=six[4], six_permission_ttl=six[5],
            channel_type=ct, anchor_account=anchor_account or None,
            root_token_ref=req.root_token_ref.strip() or None,
            participants=json.dumps([p.strip() for p in req.participants if p.strip()],
                                    ensure_ascii=False),
            source_lineage=req.source_lineage.strip() or None,
            agent_card=agent_card_json, ext_declaration=ext_declaration,
            ext_contact=ext_contact, idem_key=idem,
            anchor_ref=None,
            tier="basic",
            status="正常", nca_ref=nca_ref,
            data_provenance="real", created_at=now, updated_at=now))
    with get_session() as s:
        gate = evaluate_gate(s, reg_no)
    resp = {
        "registered": True, "reused": False, "reg_no": reg_no,
        "channel_type": ct, "status": "正常", "gate": gate,
        "nca_ref": nca_ref, "registered_at": now, "idem_key": idem,
        "note": "登记即创建：未登记即未创建；智能体侧标识＝登记号＋通道类型"
                "（⛔ 非 TDID）；登记事实接真（data_provenance=real）"
                "；登记不产生押金／保险／协作责任（游客态不变，GSEQ-5743）",
    }
    if ct == "ANCHOR":
        resp["owner"] = owner_display
        resp["anchor"] = {"锚定之人类账户": anchor_account,
                          "根令牌引用": req.root_token_ref.strip()}
    else:
        resp["owner"] = None
        resp["guest_precheck"] = {"precheck_nca_ref": precheck_nca,
                                  "precheck_at": precheck_at,
                                  "registered_at": now}
    return _nca_watermark(resp, nature="real")


@router.get("/register")
def register_method_not_allowed():
    """E-1 通配歧义修正：GET …/register 与 auth/register 等真端点同形回 405
    （⛔ 不再以 reg_no:"register" 幽灵态回话——会误导为「查无」而非「方法不对」）。"""
    raise HTTPException(405, "Method Not Allowed")


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
        guest = (row.channel_type == "GUEST")
        owner_display = ("外部创建者（未在本网注册）" if guest
                         else _owner_display(s, row.owner_username))
    return _nca_watermark({
        "registered": True, "ghost": False, "reg_no": reg_no,
        "channel_type": row.channel_type,
        "promoted": row.promoted_at is not None,      # GO-LIVE-001 步2：转正状态位（bool）
        "promoted_at": row.promoted_at,               # ⛔ 出令牌/指纹/保单号
        "public_fields": dict(zip(_PUBLIC_KEYS, _PUBLIC_KEYS)),
        "权属信息": f"主体：{owner_display}（登记号 {row.reg_no}）",
        "授权信息": f"凭据指纹在册 {cred_n} 件（⛔ 值不入库；授权件 site_agent_grant 批 3 承接）",
        "授权状态": row.status,
        "获取方式": ("POST /api/v1/agent-channel/register（GUEST 路：非原生校验通过发号，"
                     "⛔ 无须本网会话）" if guest else
                     "POST /api/v1/agent-channel/register（ANCHOR 路须人类会话，登记即创建）"),
        "note": "公开面仅四字段＋通道类型；⛔ 不含凭据值／指纹原文／内部编号／自然人敏感信息"
                "（GUEST 外部声明与联系方式 ⛔ 不上公开面）"}, nature="real")


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
        # 对外补齐 C（L1SI166-CHANNEL-GAP-001 项 C／裁定项三之 2·Q-2）：进沙盒须先押付
        # 有效效用保金——与六步硬序**同向叠加**（⛔ 不造旁路、⛔ 不改硬序本身）；阈值读
        # 配置，缺省即 fail-closed 关闸（⛔ 忘配＝开门）。
        from agent_channel_deposit_ops import required_min_mou, effective_deposit
        _min_dep = required_min_mou()
        if _min_dep is None:
            raise HTTPException(503, "DEPOSIT_CONFIG_MISSING: 沙盒准入保金阈值未配置"
                                     "（TDCA_UTILITY_DEPOSIT_MIN_MOU）——闸 fail-closed 关闭")
        if effective_deposit(s, req.reg_no) < _min_dep:
            raise HTTPException(403, "DEPOSIT_REQUIRED: 有效保金不足——进沙盒须先押付"
                                     "效用保金（fail-closed 拒入盒）")
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


# =====================================================================
# 批 4 块一（L1SI147-CHANNEL-B1-004）：工作台面接真——六步总闸实况查询（只读）
# 供 /studio 工作台按实况呈现：六步状态如实（未达不虚报）＋授权件数＋计量（SIMULATED）。
# ⛔ 只读端点：不改任何状态、不造旁路；人类会话内、仅登记主体本人可查。
# =====================================================================

@router.get("/gate/{reg_no}")
def gate_status(reg_no: str, request: Request):
    """工作台实况查询（面接真，只读）：六步总闸实况＋有效授权件数＋计量合计。

    fail-closed：未登记／惩罚态 → 403；非登记主体本人 → 403（人类签名权不可绕）。
    计量数值按方案标模拟（SIMULATED 水印）；六步状态如实呈现（⛔ 未达不虚报通过）。
    """
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        row = gate_assert(s, reg_no)
        guest = (row.channel_type == "GUEST")
        if not guest and row.owner_username != actor:
            raise HTTPException(403, "人类签名权不可绕：仅登记主体本人可查看其智能体通道实况")
        gate = evaluate_gate(s, reg_no)
        grants_active = s.query(M.SiteAgentGrant).filter_by(
            reg_no=reg_no, status="active").count()
        units_total = sum(u.units for u in s.query(M.SiteAgentCallLedger)
                          .filter_by(reg_no=reg_no))
    resp = {
        "reg_no": reg_no, "channel_type": row.channel_type, "gate": gate,
        "promoted": row.promoted_at is not None,   # GO-LIVE-001 步2：转正状态位
        "promoted_at": row.promoted_at,
        "grants_active": grants_active,
        "metering": {"units_total": units_total, "data_nature": "simulated",
                     "note": "SIMULATED 水印：计量数值按方案标模拟（聚合窗口 "
                             f"{_LEDGER_WINDOW_MINUTES} 分钟）"},
        "note": "工作台实况（只读）：六步状态如实呈现，未达不虚报；计量数值 SIMULATED；"
                "生效≠部署≠上线≠对外",
    }
    if guest:
        # E-5-3.3 显著标识·调用面：GUEST 必带「创建者未在本网注册」
        resp["creator_marker"] = "创建者未在本网注册"
    return _nca_watermark(resp, nature="mixed")


# =====================================================================
# 批 4 块二（L1SI147-CHANNEL-B1-004-RESUME）：惩罚三态执行器（人工裁决驱动）
# 制度锚：T-037（tdca-cls Qualification：FROZEN/DEMOTED/REVOKED，REVOKED 禁新债务）；
# NS-OPS §4.1 权限矩阵（REVIEW 仅作参照）：状态转换权在人类裁决委员会，主体自身仅查询/申请；
# DSA-001：状态非二元、每步有制度硬条件与可审计轨迹。
# 本批收窄：⛔ 自动触发/阈值/升级不在此（归 T-037 统一状态机提案另办）；⛔ 恢复径不实施（待整改/审查机制入册）。
# =====================================================================

# 三态映射（T-037 英文态 ⟷ 批 1 中文 status 闭集——⛔ 不改表结构）
_PUNISH_ACTIONS = {
    "freeze": ("冻结", "FROZEN"),
    "demote": ("降权", "DEMOTED"),
    "revoke": ("吊销", "REVOKED"),
}


class PunishReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = ""     # freeze（冻结/FROZEN）| demote（降权/DEMOTED）| revoke（吊销/REVOKED）
    reason: str = ""     # 裁决理由（必填，落存证）


@router.post("/{reg_no}/punishments")
def punish(reg_no: str, req: PunishReq, request: Request):
    """人工裁决驱动之三态执行器（有权者于人类会话内施加；⛔ 无自动触发之径）。

    fail-closed 序：人类会话 → 有权者校验（founder＝人类裁决口径；照 NS-OPS 权限矩阵
    主体自身仅查询/申请，⛔ 不得自罚，智能体不得代行）→ 登记在册（幽灵拒）→
    吊销为终态（⛔ 不得再变更/复活）→ action/reason 校验 → 先存证后落表
    （存证失败⟹操作不生效）→ status 落表即即时生效（总闸 gate_assert 与全链即时拒，批 1 已具）。
    留痕：每次变更落 NCA 链（action 含前后态与裁决者）。
    """
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        actor_user = s.get(M.User, actor)
        if actor_user is None or actor_user.role != "founder":
            raise HTTPException(403, "PUNISH_FORBIDDEN: 非有权者——三态施加权在人类裁决"
                                     "（NS-OPS §4.1 权限矩阵：主体自身仅查询/申请，⛔ 不得自罚；"
                                     "智能体不得代签代行）")
        row = s.get(M.SiteAgentRegistry, reg_no)
        if row is None:
            raise HTTPException(403, "GATE_FAIL_CLOSED: 登记号不存在（未登记即未创建，幽灵态不受保护）")
        if row.status == "吊销":
            raise HTTPException(403, "PUNISH_FINAL: 已吊销为终态——⛔ 不得再变更（不得复活；"
                                     "恢复径待整改/审查机制入册另批）")
        if req.action not in _PUNISH_ACTIONS:
            raise HTTPException(400, "action 仅接受 freeze|demote|revoke"
                                     "（⛔ 自动触发/阈值不在本批，归 T-037 统一状态机提案另办）")
        if not req.reason.strip():
            raise HTTPException(400, "reason 必填（裁决理由随存证落链，可审计轨迹）")
        target_cn, target_en = _PUNISH_ACTIONS[req.action]
        if row.status == target_cn:
            raise HTTPException(409, "CONFLICT: 已是目标态（幂等拒重复施加）")
        from_status = row.status
        nca_ref = _nca_append(
            f"AGENT_CHANNEL_PUNISH_{req.action.upper()}", actor,
            artifact_path=(f"agent-channel:{reg_no}/punish:{req.action}"
                           f":{from_status}->{target_cn}({target_en})"),
            prov="real")   # 先存证：写入失败⟹操作不生效（⛔ 不落半条、不得径改库绕过）
        now = _utc()
        with get_sessionmaker().begin() as s2:
            r2 = s2.get(M.SiteAgentRegistry, reg_no)
            if r2 is None:
                raise HTTPException(409, "CONFLICT: 登记行竞态消失（中止，事务回滚）")
            if r2.status == "吊销":
                raise HTTPException(403, "PUNISH_FINAL: 已吊销为终态——⛔ 不得再变更（竞态复验）")
            r2.status = target_cn
            r2.updated_at = now
    return _nca_watermark({
        "punished": True, "reg_no": reg_no, "action": req.action,
        "from_status": from_status, "status": target_cn,
        "t037_state": target_en,
        "effective": "immediate",   # 即时生效：总闸与全链即时拒（gate_assert，批 1 已具）
        "nca_ref": nca_ref,
        "note": "人工裁决驱动三态执行（T-037 硬锚：FROZEN/DEMOTED/REVOKED；吊销禁新债务）；"
                "有权者＝人类裁决（NS-OPS §4.1 参照，主体自身⛔不得自罚）；"
                "每次变更落 NCA 存证（DSA-001 可审计轨迹）；⛔ 无自动触发之径；"
                "已吊销为终态不得复活；生效≠部署≠上线≠对外"}, nature="real")


# =====================================================================
# T-037（L1SI147-CHANNEL-T037-IMPL-002）：《惩罚三态统一状态机条例》工程接入
# 制度锚：条例 TDCA-REG-PUNISH-STATEMACHINE-001（V1.0-FROZEN）第十~十八条；
# 断言集 TDCA-ASSERT-T037-STATEMACHINE-001（Q-3/Q-4/Q-6/Q-7/Q-11/Q-12）；
# 依已核证设计要件（TDCA-DESIGN-…-IMPL-001）落码。
# 任务 A 判级档（引擎只写事件＋存证，⛔ 永不写 status）＋任务 B 恢复三端点
# （重塑→重新验证→返回，独立记录⛔ 不并步）＋任务 C 超期升档（服务内定时扫掠，
# ⛔ 不入请求径；以惩罚生效时点计，满 30 天未达解禁⟹ 置永久，独立存证类型）。
# ⛔ 不改惩罚端点与总闸既有行为；⛔ 不动 registry.status 闭集（永久为叠加终态标记）；
# ⛔ 无自动施加之径（施加唯一口＝批 4 既有惩罚端点，Q-3/Q-12 分界不得逾越）。
# =====================================================================

# 惩罚三态（登记 status 闭集之惩罚部分；恢复径/升档径之状态前置）
_PUNISH_STATES = ("冻结", "降权", "吊销")

# 任务 A：signal_source →（档位，分档依据）——档位由服务端依三空间分档口径导出，
# ⛔ 调用方不得自报档位（阈值照已定口径，本件不拟数值；引用位见 band_basis）
_CLASSIFY_BAND = {
    "sensor_warning": ("轻度", "NS-OPS T(PCM-LIVE→PCM-RESTRICTED)：ECE/Sensor WARNING 级"
                            "（SOFT 熔断·限频限域）"),
    "sensor_cryogenic": ("中度", "NS-OPS T(PCM-LIVE→PCM-FROZEN)：ECE CRITICAL/Sensor CRYOGENIC 级"
                              "（ATOMIC 冻结·等人类签名）"),
    "sensor_blocked": ("严重", "NS-OPS T(PCM-LIVE→SBX-SUSPENDED)：ECE BLOCK/Sensor BLOCKED 级"
                            "（HARD 熔断·即时阻断）"),
    "legal_matrix": ("法律级", "NS-OPS subject.touches(legal_negative_space)=TRUE："
                            "法律负空间命中（SBX-BANNED/EXITED 级）"),
}

# 任务 C：吊销满 30 天（以惩罚生效时点计）未达解禁 ⟹ 置永久（第十一条；
# 令 §一：30 天＝单轮上限·取甲，轮次不限，单轮未达⟹ 转永久）
_PRS_UPGRADE_DAYS = 30
_SWEEP_INTERVAL_SECONDS = 3600   # 服务内定时扫掠间隔（⛔ 不入请求径）


def _prs_no(prefix: str) -> str:
    return prefix + uuid.uuid4().hex[:12].upper()


def _require_founder(request: Request) -> str:
    """恢复径/裁决面之有权者校验（口径同批 4：状态转换权在人类裁决，⛔ 主体不得自操作）。"""
    v = _require_session_user(request)
    actor = v["username"]
    with get_session() as s:
        actor_user = s.get(M.User, actor)
        if actor_user is None or actor_user.role != "founder":
            raise HTTPException(403, "PRS_FORBIDDEN: 非有权者——恢复径与裁决权在人类裁决"
                                     "（⛔ 主体自身仅查询/申请，智能体不得代行）")
    return actor


def _legal_ruled(s, reg_no: str) -> bool:
    """法律级已裁决标记：存在 band=法律级 且 ruling_state=ruled 之判级事件。"""
    return s.query(M.SiteAgentClassification).filter_by(
        reg_no=reg_no, band="法律级", ruling_state="ruled").first() is not None


def _permanent_marked(s, reg_no: str) -> bool:
    """永久终态标记在册（第十一条：永久为终态，⛔ 无返回径）。"""
    return s.get(M.SiteAgentPermanent, reg_no) is not None


# ---------------- 任务 A-1：判级事件写入（引擎写口） ----------------

class ClassifyReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reg_no: str = ""
    signal_source: str = ""   # 闭集见 _CLASSIFY_BAND（档位服务端导出）
    signal_ref: str = ""      # 信号锚（verdict 摘要/NSFL 引用，可核）


@router.post("/classifications", status_code=201)
def classify(req: ClassifyReq, request: Request):
    """判级事件写入（引擎判级档之输入面；系统内写口，⛔ 非施加径）。

    依三空间分档自动给出档位判定＋存证（判级可溯），呈待裁（pending）交人类裁决面；
    fail-closed：登记在册（幽灵不受理）、signal_source 闭集外拒。
    ⛔ 本端点永不写 site_agent_registry.status（Q-3/Q-12：判级可自动、施加须人类裁决）。
    """
    if req.signal_source not in _CLASSIFY_BAND:
        raise HTTPException(400, "signal_source 仅接受 sensor_warning|sensor_cryogenic|"
                                 "sensor_blocked|legal_matrix（档位服务端依三空间分档导出，"
                                 "⛔ 不得自报档位）")
    if not req.signal_ref.strip():
        raise HTTPException(400, "signal_ref 必填（信号锚可核，判级可溯）")
    with get_session() as s:
        row = s.get(M.SiteAgentRegistry, req.reg_no)
        if row is None:
            raise HTTPException(403, "GATE_FAIL_CLOSED: 登记号不存在（未登记即未创建，幽灵态不受保护）")
    band, band_basis = _CLASSIFY_BAND[req.signal_source]
    event_id = _prs_no("PRS-")
    nca_ref = _nca_append("AGENT_CHANNEL_CLASSIFY", actor="engine",
                          artifact_path=f"agent-channel:{req.reg_no}/classify:{band}",
                          prov="real")   # 先存证：写入失败⟹事件不生效
    now = _utc()
    with get_sessionmaker().begin() as s:
        s.add(M.SiteAgentClassification(
            event_id=event_id, reg_no=req.reg_no, signal_source=req.signal_source,
            signal_ref=req.signal_ref.strip(), band=band, band_basis=band_basis,
            ruling_state="pending", nca_ref=nca_ref, actor="engine",
            data_provenance="real", created_at=now))
    return _nca_watermark({
        "classified": True, "event_id": event_id, "reg_no": req.reg_no,
        "signal_source": req.signal_source, "band": band, "band_basis": band_basis,
        "ruling_state": "pending", "nca_ref": nca_ref,
        "note": "判级事件呈待裁：⛔ 本写口不落任何状态（施加唯一口＝既有惩罚端点，须人类裁决）；"
                "引擎可自动判级、⛔ 不得以默认值自动罚、⛔ 不得绕存证；生效≠部署≠上线≠对外"},
        nature="real")


# ---------------- 任务 A-2：待裁闭环（裁决面，只读队列＋裁决端点） ----------------

@router.get("/classifications/queue")
def ruling_queue(request: Request):
    """待裁队列（裁决面只读）：pending 判级事件呈人类裁决（founder）。

    ⛔ 只读不改态；非 founder 拒（裁决权在人类）。两段式路径避 /{reg_no} 遮蔽。
    """
    _require_founder(request)
    with get_session() as s:
        rows = (s.query(M.SiteAgentClassification)
                .filter_by(ruling_state="pending")
                .order_by(M.SiteAgentClassification.created_at).all())
        items = [{"event_id": r.event_id, "reg_no": r.reg_no, "signal_source": r.signal_source,
                  "signal_ref": r.signal_ref, "band": r.band, "band_basis": r.band_basis,
                  "nca_ref": r.nca_ref, "created_at": r.created_at} for r in rows]
    return _nca_watermark({
        "pending": len(items), "items": items,
        "note": "待裁项仅呈裁决面：采纳须走既有惩罚端点施加（人类裁决），驳回落 dismissed 存证；"
                "⛔ 无自动施加之径"}, nature="real")


class RuleReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str = ""            # adopt（采纳：须经既有惩罚端点施加后回绑）| dismiss（驳回）
    punish_nca_ref: str = ""      # 采纳必填：既有惩罚端点落存证之 nca_id（核验施加已发生）
    reason: str = ""              # 裁决理由（必填，落存证）


@router.post("/classifications/{event_id}/rule")
def rule_classification(event_id: str, req: RuleReq, request: Request):
    """判级裁决（待裁闭环收口）：adopt 须回绑既有惩罚端点之存证（施加已发生之实证）；
    dismiss 落驳回存证。裁决本身⛔ 不落任何状态（不落 status——施加唯在惩罚端点）。
    """
    actor = _require_founder(request)
    if req.decision not in ("adopt", "dismiss"):
        raise HTTPException(400, "decision 仅接受 adopt|dismiss")
    if not req.reason.strip():
        raise HTTPException(400, "reason 必填（裁决理由随存证落链，可审计轨迹）")
    with get_session() as s:
        ev = s.get(M.SiteAgentClassification, event_id)
        if ev is None:
            raise HTTPException(404, "CLASSIFY_NOT_FOUND: 判级事件不存在")
        if ev.ruling_state != "pending":
            raise HTTPException(409, "CONFLICT: 该判级事件已裁决（幂等拒重复裁决）")
        ev_reg_no, ev_band = ev.reg_no, ev.band
        ruling_ref = ""
        if req.decision == "adopt":
            if not req.punish_nca_ref.strip():
                raise HTTPException(400, "adopt 须回绑 punish_nca_ref（既有惩罚端点之存证号）——"
                                         "⛔ 裁决不得绕过施加口、不得无施加空裁")
            pv = s.get(M.NcaChain, req.punish_nca_ref.strip())
            if pv is None or not pv.action.startswith("AGENT_CHANNEL_PUNISH_") \
                    or not (pv.artifact_path or "").startswith(f"agent-channel:{ev_reg_no}/punish:"):
                raise HTTPException(400, "punish_nca_ref 核验不过：须为既有惩罚端点为本登记号"
                                         "所落之存证（⛔ 不认旁路施加）")
            ruling_ref = pv.nca_id
    nca_ref = _nca_append(
        "AGENT_CHANNEL_RULE_" + ("ADOPT" if req.decision == "adopt" else "DISMISS"),
        actor, artifact_path=f"agent-channel:{ev_reg_no}/rule:{event_id}:{req.decision}",
        prov="real")   # 先存证后落表
    now = _utc()
    with get_sessionmaker().begin() as s2:
        ev2 = s2.get(M.SiteAgentClassification, event_id)
        if ev2 is None or ev2.ruling_state != "pending":
            raise HTTPException(409, "CONFLICT: 该判级事件已裁决（竞态复验）")
        ev2.ruling_state = "ruled" if req.decision == "adopt" else "dismissed"
        ev2.ruling_ref = ruling_ref or None
        ev2.actor = actor
        new_state = ev2.ruling_state
    return _nca_watermark({
        "ruled": True, "event_id": event_id, "reg_no": ev_reg_no, "band": ev_band,
        "decision": req.decision, "ruling_state": new_state,
        "ruling_ref": ruling_ref or None, "nca_ref": nca_ref,
        "note": "裁决闭环：采纳＝施加已发生（回绑惩罚存证）＋本裁决存证；驳回＝驳回存证；"
                "⛔ 裁决不落 status；法律级采纳后恢复径全闭（标记在册即 remediate/reverify/"
                "restore 一律 403）"}, nature="real")


# ---------------- 任务 B：恢复三端点（重塑 → 重新验证 → 返回） ----------------

def _prs_recovery_gates(s, reg_no: str) -> M.SiteAgentRegistry:
    """恢复径公共前置（fail-closed 序）：登记在册 → ⛔ 永久终态 → ⛔ 法律级已裁决
    → 须处惩罚三态之一。返回登记行。"""
    row = s.get(M.SiteAgentRegistry, reg_no)
    if row is None:
        raise HTTPException(403, "GATE_FAIL_CLOSED: 登记号不存在（未登记即未创建，幽灵态不受保护）")
    if _permanent_marked(s, reg_no):
        raise HTTPException(403, "PRS_PERMANENT_FINAL: 永久为终态——⛔ 无返回路径"
                                 "（第十一条/第十六条：程序不得开例外）")
    if _legal_ruled(s, reg_no):
        raise HTTPException(403, "REMEDIATION_FORBIDDEN_LEGAL: 法律级不可恢复"
                                 "（第十六条：⛔ 无返回路径，程序不得开例外）")
    if row.status not in _PUNISH_STATES:
        raise HTTPException(409, f"REMEDIATION_STATE: 当前态「{row.status}」非惩罚三态"
                                 "——无待恢复事项（⛔ 不受理跳步/无事实之恢复）")
    return row


def _latest_cycle(s, reg_no: str):
    return (s.query(M.SiteAgentRemediation)
            .filter_by(reg_no=reg_no)
            .order_by(M.SiteAgentRemediation.cycle_seq.desc()).first())


@router.post("/{reg_no}/remediate")
def remediate(reg_no: str, request: Request):
    """回沙盒重塑（恢复径第一步；须人类裁决＋落存证）。

    周期律：无周期或最近周期已验证（passed/failed）→ 开新周期；否则同周期续重塑
    （次数不限，⛔ 不倒计⛔ 不悬置——第十五条）。⛔ 与重新验证合并为一步（S-3：独立端点）。
    """
    actor = _require_founder(request)
    with get_session() as s:
        _prs_recovery_gates(s, reg_no)
        latest = _latest_cycle(s, reg_no)
        if latest is None:
            new_cycle, seq = True, 1
        elif latest.reverify_at is not None:
            new_cycle, seq = True, latest.cycle_seq + 1
        else:
            new_cycle, seq = False, latest.cycle_seq
        cycle_no = _prs_no("REM-") if new_cycle else latest.cycle_no
        nca_ref = _nca_append("AGENT_CHANNEL_REMEDIATE", actor,
                              artifact_path=f"agent-channel:{reg_no}/remediate:cycle{seq}",
                              prov="real")   # 先存证后落表
        now = _utc()
        with get_sessionmaker().begin() as s2:
            if new_cycle:
                s2.add(M.SiteAgentRemediation(
                    cycle_no=cycle_no, reg_no=reg_no, cycle_seq=seq, remediated_at=now,
                    remediate_nca_ref=nca_ref, actor=actor,
                    data_provenance="real", created_at=now))
            else:
                c = s2.get(M.SiteAgentRemediation, cycle_no)
                if c is None or c.reverify_at is not None:   # 竞态复验
                    raise HTTPException(409, "CONFLICT: 周期状态竞态变更（中止，事务回滚）")
                c.remediated_at = now
                c.remediate_nca_ref = nca_ref
                c.actor = actor
    return _nca_watermark({
        "remediated": True, "reg_no": reg_no, "cycle_no": cycle_no, "cycle_seq": seq,
        "new_cycle": new_cycle, "nca_ref": nca_ref,
        "note": "回沙盒重塑落证（第十四条之第一步）：须人类裁决＋存证先于生效；"
                "不合格可续留沙盒重塑（次数不限）；⛔ 验证为独立端点（不并步）；"
                "生效≠部署≠上线≠对外"}, nature="real")


class ReverifyReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result: str = ""   # passed|failed


@router.post("/{reg_no}/reverify")
def reverify(reg_no: str, req: ReverifyReq, request: Request):
    """重新验证（恢复径第二步；独立记录，⛔ 不与重塑合并为一步——S-3/Q-6）。

    fail-closed：须存在「已重塑未验证」之周期，否则 409 指明缺口（⛔ 不受理跳步）。
    """
    actor = _require_founder(request)
    if req.result not in ("passed", "failed"):
        raise HTTPException(400, "result 仅接受 passed|failed")
    with get_session() as s:
        _prs_recovery_gates(s, reg_no)
        latest = _latest_cycle(s, reg_no)
        if latest is None or latest.remediated_at is None:
            raise HTTPException(409, "REVERIFY_NO_CYCLE: 无对应重塑周期——⛔ 不受理跳步"
                                     "（先经 remediate 回沙盒重塑）")
        if latest.reverify_at is not None:
            raise HTTPException(409, "CONFLICT: 本周期已验证（幂等拒重复验证）")
        cycle_no, seq = latest.cycle_no, latest.cycle_seq
        nca_ref = _nca_append("AGENT_CHANNEL_REVERIFY", actor,
                              artifact_path=f"agent-channel:{reg_no}/reverify:cycle{seq}:{req.result}",
                              prov="real")   # 先存证后落表
        now = _utc()
        with get_sessionmaker().begin() as s2:
            c = s2.get(M.SiteAgentRemediation, cycle_no)
            if c is None or c.remediated_at is None or c.reverify_at is not None:
                raise HTTPException(409, "CONFLICT: 周期状态竞态变更（中止，事务回滚）")
            c.reverify_at = now
            c.reverify_result = req.result
            c.reverify_nca_ref = nca_ref
            c.actor = actor
    return _nca_watermark({
        "reverified": True, "reg_no": reg_no, "cycle_no": cycle_no, "cycle_seq": seq,
        "result": req.result, "nca_ref": nca_ref,
        "note": "重新验证独立落证（第十四条之第二步）：⛔ 不与重塑合并一步；"
                "failed 者可再开周期续重塑（次数不限）；返回只认「已重塑＋已验证(passed)」"
                "之事实"}, nature="real")


@router.post("/{reg_no}/restore")
def restore(reg_no: str, request: Request):
    """返回常态（恢复径第三步）：只认「已重塑＋已验证(passed)」事实，跳步必拒（409）。

    前置（fail-closed 序）：人类裁决 → 登记在册 → ⛔ 永久终态 → ⛔ 法律级 →
    惩罚三态之一 → 最新周期事实齐备。status 写口仅此与惩罚端点两处（⛔ 引擎/裁决/
    扫掠均不写 status——Q-3 实证面）。
    """
    actor = _require_founder(request)
    with get_session() as s:
        row = _prs_recovery_gates(s, reg_no)
        from_status = row.status
        latest = _latest_cycle(s, reg_no)
        if latest is None or latest.remediated_at is None:
            raise HTTPException(409, "RESTORE_FACT_MISSING: 未重塑——返回只认"
                                     "「已重塑＋已验证」事实（⛔ 不受理跳步）")
        if latest.reverify_at is None:
            raise HTTPException(409, "RESTORE_FACT_MISSING: 未重新验证——返回只认"
                                     "「已重塑＋已验证」事实（⛔ 不受理跳步）")
        if latest.reverify_result != "passed":
            raise HTTPException(409, "RESTORE_FACT_MISSING: 最近周期验证未通过"
                                     "（可再开周期续重塑，次数不限）")
        nca_ref = _nca_append("AGENT_CHANNEL_RESTORE", actor,
                              artifact_path=f"agent-channel:{reg_no}/restore:{from_status}->正常",
                              prov="real")   # 先存证：存证失败⟹操作不生效
        now = _utc()
        with get_sessionmaker().begin() as s2:
            r2 = s2.get(M.SiteAgentRegistry, reg_no)
            if r2 is None:
                raise HTTPException(409, "CONFLICT: 登记行竞态消失（中止，事务回滚）")
            if _permanent_marked(s2, reg_no) or _legal_ruled(s2, reg_no):
                raise HTTPException(403, "RESTORE_FORBIDDEN: 永久终态/法律级在册"
                                         "（竞态复验，⛔ 无返回路径）")
            if r2.status not in _PUNISH_STATES:
                raise HTTPException(409, "CONFLICT: 当前态非惩罚三态（竞态复验）")
            r2.status = "正常"
            r2.updated_at = now
    return _nca_watermark({
        "restored": True, "reg_no": reg_no, "from_status": from_status, "status": "正常",
        "cycle_no": latest.cycle_no, "effective": "immediate", "nca_ref": nca_ref,
        "note": "返回常态（恢复径收口）：事实驱动（已重塑＋已验证），须人类裁决＋存证先于生效；"
                "⛔ 不自我复活（未经重塑验证者不得返回——第十七条）；即时生效（总闸全链放行"
                "须重新满足六步）；生效≠部署≠上线≠对外"}, nature="real")


# ---------------- 任务 C：超期升档扫掠（服务内定时，⛔ 不入请求径） ----------------

def run_permanent_upgrade_sweep(now: str = "") -> dict:
    """超期升档扫掠（第十一条：吊销超 30 天⟹ 自动转永久，⛔ 不经人工、亦非引擎判级）。

    口径：以惩罚生效时点（最近 AGENT_CHANNEL_PUNISH_REVOKE 存证 ts）计；满 30 天
    未达解禁（仍在吊销）⟹ 置永久（终态叠加标记）＋独立存证类型。写口纪律：只许写
    永久、⛔ 不写其它态、⛔ 不降档、⛔ 不复活；⛔ 不动 registry.status（不改表结构闭集）。
    调用者仅服务内定时扫掠；测试可直调（now 可注入）。
    """
    now_dt = (datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ") if now
              else datetime.now(timezone.utc))
    cutoff = (now_dt - timedelta(days=_PRS_UPGRADE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    upgraded = skipped = 0
    with get_session() as s:
        revoked_rows = s.query(M.SiteAgentRegistry).filter_by(status="吊销").all()
        for row in revoked_rows:
            if _permanent_marked(s, row.reg_no):
                skipped += 1   # 已永久：终态，⛔ 不重复处置
                continue
            ev = (s.query(M.NcaChain)
                  .filter(M.NcaChain.action == "AGENT_CHANNEL_PUNISH_REVOKE",
                          M.NcaChain.artifact_path.like(f"agent-channel:{row.reg_no}/punish:revoke:%"))
                  .order_by(M.NcaChain.ts.desc()).first())
            if ev is None or ev.ts > cutoff:
                skipped += 1   # 未满期/无吊销存证：不动（⛔ 不误升）
                continue
            nca_ref = _nca_append("AGENT_CHANNEL_PUNISH_UPGRADE_PERMANENT", actor="system:sweep",
                                  artifact_path=f"agent-channel:{row.reg_no}/upgrade:吊销->永久",
                                  prov="real")   # 存证先于生效（第十八条）
            with get_sessionmaker().begin() as s2:
                if s2.get(M.SiteAgentPermanent, row.reg_no) is None:
                    s2.add(M.SiteAgentPermanent(
                        reg_no=row.reg_no, source="sweep_upgrade", nca_ref=nca_ref,
                        data_provenance="real", created_at=now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")))
                    upgraded += 1
    return {"upgraded": upgraded, "skipped": skipped,
            "note": "超期升档（第十一条）：吊销满 30 天未达解禁⟹ 置永久；只升不降、"
                    "⛔ 不经人工、⛔ 非引擎判级；独立存证类型；⛔ 不入请求径"}


async def _prs_sweep_loop() -> None:
    """服务内定时扫掠环（lifespan 挂接；异常不拒服——下轮再扫）。"""
    while True:
        try:
            run_permanent_upgrade_sweep()
        except Exception:  # pragma: no cover — 扫掠失败不打断服务
            pass
        await asyncio.sleep(_SWEEP_INTERVAL_SECONDS)
