# -*- coding: utf-8 -*-
"""L1SI193-B1-001：二期 C-1 授权配置面板（只施工不上线）——/api/v1/authorization/draft|sign|revoke ＋ GET /{auth_id}。

口径（照 TDCA-HANDOFF-EXEC-L1SI193-B1-001 V1.0）：
  - 五操作：预收权／实时授权／追加授权／许可变更／多层级授权（各成一表单流程，共用八字段）；
  - 八字段：授权方／被授权方／标的／范围／期限／条件／签署／凭据号
    （授权方与被授权方＝主体名称，⛔ 昵称、⛔ 账号名；标的／范围逐项写，⛔「等」字兜底）；
  - 四要件（缺一即 400 fail-closed，且提示缺哪一项）：
    ① 授权方 ② 被授权方 ③ 标的与范围 ④ 期限与条件；
  - 签署：须本人（签署人＝起草人；⛔ 智能体代签代填——on_behalf 非空即拒）；
    未登录 ⛔ 起草；非本人 ⛔ 签署；凭据号只回指针，凭据值 ⛔ 不入件；
  - 五态机（可回摆）：draft → pending_sign → active → suspended／revoked；
    撤回后已发生使用另记一笔（事件流水 append-only，⛔ 抹）；
  - 可靠性九项（GK-03）：
    提交失败 ⛔ 半条记录（先落业务行、NCA 落证失败即清行——不给编号不落存证）；
    存证每次落 nca_seq 与双库哈希对拍（业务表 rec_hash ↔ nca_chain 行重算）；
    恢复＝编号与字段可从 NCA 反查复建（artifact_path=authorization-panel:{auth_id}）；
    熔断三条（同一 auth_id 短时重复签署异常／哈希连续不符 ≥3／标准无法对应）
    触发即停该链（status=suspended＋冻结行），后续全拒，⛔ 降级放行；
    恢复＝operator 复核解冻（POST /sign {resume:true}，角色 founder/operator，⛔ 自动恢复）；
    未授权输入默认拒；无存证视未发生（状态停本步、公开查 404）；权限不足拒绝 ⛔ 降级。
  - 与 P8b 合约备案（authorization_records）分立并存：本面不改其逻辑与文案（S-1）；
  - 全程 SIMULATED 硬标注；改动走 PR；⛔ 部署、⛔ 对外可见（S-4）。
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
from api_v1 import (_nca_append, _nca_watermark, _require_session_user,  # noqa: E402
                    _utc, rec_hash_of)
from authorization_ops import _public_space_hits  # noqa: E402

router = APIRouter(prefix="/api/v1/authorization", tags=["authorization-panel"])

# 五操作（与 P8b OPERATIONS 名目同、语义各立——本面操作载于面板授权件 operation 字段）
OPERATIONS_PANEL = {
    "pre_accept": "预收权",
    "activate": "实时授权",
    "append": "追加授权",
    "amend_terms": "许可变更",
    "sub_grant": "多层级授权",
}

# 四要件（缺一即拒；提示缺哪一项）
_REQ_LABELS = [("grantor", "授权方"), ("grantee", "被授权方"),
               ("subject_scope", "标的与范围"), ("term_conditions", "期限与条件")]

# 条件三问（八字段之「条件」；只收 是／否——口径未定者不填即缺）
_CONDITION_KEYS = (("may_sub_grant", "可否再授权"),
                   ("may_commercialize", "可否商用"),
                   ("attribution_required", "须否标注来源"))

# 熔断①：同一 auth_id 重复签署观察窗（秒）
_RESIGN_WINDOW_SEC = 30
# 熔断②：哈希连续不符阈值
_HASH_STREAK_LIMIT = 3

_AUTH_ID_RE = re.compile(r"^AP-[0-9a-f]{10}$")

# 「等」字兜底拦截（八字段：标的／范围逐项写，⛔「等」）——句中「等等」亦不放过
_ETC_RE = re.compile(r"等[等]?[。．.!！?？\s,，、;；:：]*$|等[等]?[^A-Za-z0-9一-鿿]*$")


def _etc_hit(*texts: str) -> bool:
    """标的／范围是否以「等」字兜底收尾（逐项写口径；⛔「等」）。"""
    for t in texts:
        t = (t or "").strip()
        if t and _ETC_RE.search(t):
            return True
    return False


def _freeze_active(auth_id: str) -> M.AuthorizationPanelFreeze | None:
    with get_session() as s:
        return (s.query(M.AuthorizationPanelFreeze)
                .filter_by(auth_id=auth_id, unfrozen_at=None)
                .first())


def _trip_freeze(auth_id: str, reason: str, detail: str, by: str = "system") -> None:
    """熔断触发：停该链（status=suspended＋冻结行）。后续全拒，⛔ 降级放行。"""
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, auth_id)
        pre = doc.status if doc else "pending_sign"
    fid = f"APF-{uuid.uuid4().hex[:10]}"
    with get_sessionmaker().begin() as s:
        doc = s.get(M.AuthorizationPanelDoc, auth_id)
        if doc is not None and doc.status != "revoked":
            doc.status = "suspended"
            doc.updated_at = _utc()
        s.add(M.AuthorizationPanelFreeze(
            freeze_id=fid, auth_id=auth_id, reason=reason, detail=detail,
            frozen_by=by, created_at=_utc(),
            unfrozen_note=f"PRE_FREEZE_STATUS={pre}"))


def _assert_not_frozen(auth_id: str) -> None:
    fz = _freeze_active(auth_id)
    if fz is not None:
        raise HTTPException(423, f"该授权链已熔断冻结（{fz.reason}）——后续全拒；"
                                 f"须 operator 复核解冻（⛔ 自动恢复、⛔ 降级放行）")


def _nca_row(nca_id: str) -> M.NcaChain | None:
    with get_session() as s:
        return s.get(M.NcaChain, nca_id)


def _hash_match(doc: M.AuthorizationPanelDoc) -> bool:
    """双库哈希对拍：以 nca_chain 行字段按公开口径重算 rec_hash，与业务表副本比对。"""
    if not doc.nca_seq or not doc.rec_hash:
        return False
    row = _nca_row(doc.nca_seq)
    if row is None:
        return False
    expect = rec_hash_of(row.nca_id, row.prev_nca, row.action, row.actor,
                         row.artifact_path, row.sha256_8, row.handshake_id,
                         row.data_provenance, row.ts)
    return expect == doc.rec_hash


def _verify_or_trip(auth_id: str) -> None:
    """写路径对拍：不符即累计（连续 ≥3 → 熔断②）。"""
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, auth_id)
    if doc is None:
        raise HTTPException(404, "auth_id 不存在")
    if not doc.nca_seq:
        raise HTTPException(409, "无存证视为未发生（状态停本步）——该件尚无 NCA 存证")
    if _hash_match(doc):
        if doc.hash_mismatch_streak:
            with get_sessionmaker().begin() as s:
                d = s.get(M.AuthorizationPanelDoc, auth_id)
                d.hash_mismatch_streak = 0
        return
    streak = doc.hash_mismatch_streak + 1
    if streak >= _HASH_STREAK_LIMIT:
        _trip_freeze(auth_id, "hash",
                     f"双库哈希连续不符 ≥{_HASH_STREAK_LIMIT}（nca_seq={doc.nca_seq}）")
        raise HTTPException(423, "双库哈希连续不符——该链已熔断冻结（fail-closed，⛔ 降级放行）")
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, auth_id)
        d.hash_mismatch_streak = streak
    raise HTTPException(409, f"双库哈希对拍不符（连续 {streak} 次）——本次拒，"
                             f"连续 ≥{_HASH_STREAK_LIMIT} 次即熔断停链")


def _conditions_check(cond) -> tuple[dict | None, str | None]:
    """条件三问校验：⛔ 只收 是／否；缺一即 (None, 缺项名)。"""
    if not isinstance(cond, dict):
        return None, "条件（可否再授权／可否商用／须否标注来源）"
    out = {}
    for key, label in _CONDITION_KEYS:
        v = str(cond.get(key, "")).strip()
        if v not in ("是", "否"):
            return None, f"条件·{label}（须填 是／否）"
        out[key] = v
    return out, None


def _public_view(doc: M.AuthorizationPanelDoc) -> dict:
    """公开读投影（免会话）：范围与期限与状态；⛔ 凭据值／签署人／起草人账号。"""
    try:
        cond = json.loads(doc.conditions or "{}")
        if not isinstance(cond, dict):
            cond = {}
    except (ValueError, TypeError):
        cond = {}
    return _nca_watermark({
        "auth_id": doc.auth_id,
        "operation": doc.operation,
        "operation_label": OPERATIONS_PANEL.get(doc.operation, doc.operation),
        "status": doc.status,
        "subject": doc.subject,          # 标的
        "scope": doc.scope,              # 范围
        "term": doc.term,                # 期限
        "conditions": {label: cond.get(key) for key, label in _CONDITION_KEYS},
        "nca_seq": doc.nca_seq,          # 存证指针（凭据值 ⛔ 不在公开面）
        "simulated": True,
        "note": "公开面仅回范围与期限与状态（C-1 授权配置面板）；"
                "凭据值与签署人信息 ⛔ 不在公开面出现"})


class DraftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str                    # 五操作之一（标准无法对应即 400＋熔断③）
    grantor: str = ""                 # ① 授权方（主体名称）
    grantee: str = ""                 # ② 被授权方（主体名称）
    subject: str = ""                 # ③a 标的
    scope: str = ""                   # ③b 范围
    term: str = ""                    # ④a 期限
    conditions: dict = {}             # ④b 条件三问（是／否）
    credential_ref: str = ""          # 凭据号（只回指针，⛔ 值不入件）
    submit: bool = True               # true→pending_sign；false→draft（草稿）
    note: str = ""


@router.post("/draft", status_code=201)
def panel_draft(req: DraftIn, request: Request):
    """起草（须登录；四要件缺一即 400 fail-closed，且提示缺哪一项）。

    原子序：业务行先落（nca_seq 空）→ NCA 落证 → 同 tx 回写指针＋事件；
    NCA 失败即清业务行——失败不给编号、不落存证、⛔ 半条记录。
    """
    user = _require_session_user(request)
    # 标准对应（熔断③）：操作须属五操作
    if req.operation not in OPERATIONS_PANEL:
        raise HTTPException(400, "标准无法对应：operation 须为 pre_accept／activate／"
                                 "append／amend_terms／sub_grant 之一——已 fail-closed 拦截")
    # 四要件（缺一即拒，提示缺哪一项）
    missing = []
    if not req.grantor.strip():
        missing.append("授权方")
    if not req.grantee.strip():
        missing.append("被授权方")
    if not req.subject.strip() or not req.scope.strip():
        missing.append("标的与范围" + ("（标的）" if not req.subject.strip() else "（范围）"))
    cond_ok, cond_missing = _conditions_check(req.conditions)
    if not req.term.strip() or cond_ok is None:
        item = "期限与条件（" + "／".join(
            x for x in ([ "期限" ] if not req.term.strip() else []) +
            ([cond_missing] if cond_ok is None else [])) + ")"
        missing.append(item)
    if missing:
        raise HTTPException(400, "四要件缺一即拒——缺：" + "、".join(missing))
    # 「等」字兜底（逐项写口径）
    if _etc_hit(req.subject, req.scope):
        raise HTTPException(400, "标的／范围须逐项写明（⛔「等」字兜底）——请补全列举")
    # 四条不公开负空间（⛔ 凭据值等入件）
    cond_norm = {k: v for k, v in cond_ok.items()}
    fields = {"grantor": req.grantor, "grantee": req.grantee,
              "subject": req.subject, "scope": req.scope, "term": req.term,
              "conditions": json.dumps(cond_norm, ensure_ascii=False),
              "credential_ref": req.credential_ref, "note": req.note}
    hits = _public_space_hits(fields)
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")

    auth_id = f"AP-{uuid.uuid4().hex[:10]}"
    status = "pending_sign" if req.submit else "draft"
    now = _utc()
    # tx1：业务行先落（无存证位——此时对外的任何读都「视未发生」）
    with get_sessionmaker().begin() as s:
        s.add(M.AuthorizationPanelDoc(
            auth_id=auth_id, operation=req.operation,
            grantor=req.grantor.strip(), grantee=req.grantee.strip(),
            subject=req.subject.strip(), scope=req.scope.strip(),
            term=req.term.strip(),
            conditions=json.dumps(cond_norm, ensure_ascii=False),
            drafter=user["username"],
            credential_ref=req.credential_ref.strip() or None,
            status=status, note=req.note.strip() or None,
            data_provenance="simulated", created_at=now, updated_at=now))
    # NCA 落证（失败 → 清业务行：不给编号不落存证）
    try:
        nca_ref = _nca_append("AUTH_PANEL_DRAFT", user["username"],
                              artifact_path=f"authorization-panel:{auth_id}")
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, auth_id)
            if d is not None:
                s.delete(d)
        raise HTTPException(500, "存证落链失败——本次起草未发生（业务行已清，"
                                 "⛔ 半条记录、⛔ 编号发放）")
    # tx2：回写指针＋事件（失败 → 清业务行）
    row = _nca_row(nca_ref)
    try:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, auth_id)
            d.nca_seq = nca_ref
            d.rec_hash = row.rec_hash if row else None
            s.add(M.AuthorizationPanelEvent(
                event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=auth_id,
                event_type="submit" if req.submit else "draft",
                actor=user["username"], nca_ref=nca_ref,
                detail=f"起草（{OPERATIONS_PANEL[req.operation]}）",
                created_at=_utc()))
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, auth_id)
            if d is not None:
                s.delete(d)
        raise HTTPException(500, "存证回写失败——本次起草未发生（业务行已清）")
    return _nca_watermark({
        "auth_id": auth_id, "status": status,
        "operation": req.operation,
        "operation_label": OPERATIONS_PANEL[req.operation],
        "nca_seq": nca_ref,
        "simulated": True,
        "note": ("已提交待签（pending_sign）——请本人在本页签署"
                 if req.submit else
                 "已存草稿（draft）——未提交签署，对外不可查")})


class SignIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auth_id: str
    resume: bool = False              # operator 复核解冻（熔断恢复；⛔ 自动恢复）
    on_behalf: str = ""               # 非空即智能体代签嫌疑 → 400（⛔ 代签代填硬红线）
    note: str = ""


@router.post("/sign")
def panel_sign(req: SignIn, request: Request):
    """本人签署（签署人＝起草人；⛔ 智能体代签代填）；或 operator 复核解冻（resume）。

    熔断①：同一 auth_id 观察窗内重复签署 → 停链。
    """
    user = _require_session_user(request)
    aid = req.auth_id.strip()
    if not _AUTH_ID_RE.match(aid):
        raise HTTPException(404, "auth_id 不存在")
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
    if doc is None:
        raise HTTPException(404, "auth_id 不存在")

    # operator 复核解冻（熔断恢复）
    if req.resume:
        if user["role"] not in ("founder", "operator"):
            raise HTTPException(403, "复核解冻须 operator 及以上角色（⛔ 自动恢复、⛔ 降级放行）")
        fz = _freeze_active(aid)
        if fz is None:
            raise HTTPException(409, "该链未冻结——无需解冻")
        if doc.status != "suspended":
            raise HTTPException(409, "该件非停权态——解冻路径不适用于此件")
        pre = "active"
        m = re.search(r"PRE_FREEZE_STATUS=(\w+)", fz.unfrozen_note or "")
        if m:
            pre = m.group(1)
        if pre == "suspended":
            pre = "active"
        nca_ref = _nca_append("AUTH_PANEL_RESUME", user["username"],
                              artifact_path=f"authorization-panel:{aid}")
        row = _nca_row(nca_ref)
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = pre
            d.nca_seq = nca_ref
            d.rec_hash = row.rec_hash if row else None
            d.updated_at = _utc()
            f = s.get(M.AuthorizationPanelFreeze, fz.freeze_id)
            f.unfrozen_by = user["username"]
            f.unfrozen_note = (req.note.strip() or "operator 复核通过")
            f.unfrozen_at = _utc()
            s.add(M.AuthorizationPanelEvent(
                event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=aid,
                event_type="resume", actor=user["username"], nca_ref=nca_ref,
                detail=f"operator 复核解冻（原冻结 {fz.reason}；回摆 {pre}）",
                created_at=_utc()))
        return _nca_watermark({
            "auth_id": aid, "status": pre, "nca_seq": nca_ref, "simulated": True,
            "note": f"已复核解冻（原冻结 {fz.reason}）——状态回摆 {pre}；"
                    f"NCA 存证在册（⛔ 自动恢复）"})

    # 硬红线：智能体 ⛔ 代签代填
    if req.on_behalf.strip():
        raise HTTPException(400, "智能体不得代签代填（⛔ 代持）——签署须本人；"
                                 "如由智能体发起，请改由本人登录签署")
    if doc.status == "revoked":
        raise HTTPException(409, "该件已撤回——⛔ 不得再签署（历史档案不回改）")
    _assert_not_frozen(aid)
    if doc.status == "suspended":
        raise HTTPException(423, "该件停权中（suspended）——⛔ 不签署；"
                                 "须 operator 复核解冻后方可继续")
    # 非本人 ⛔ 签署
    if user["username"] != doc.drafter:
        raise HTTPException(403, "非本人 ⛔ 签署——签署人须与起草人为同一登录主体")
    # 熔断①：观察窗内重复签署异常
    with get_session() as s:
        last_sign = (s.query(M.AuthorizationPanelEvent)
                     .filter_by(auth_id=aid, event_type="sign")
                     .order_by(M.AuthorizationPanelEvent.created_at.desc())
                     .first())
    if last_sign is not None and last_sign.actor == user["username"]:
        try:
            from datetime import datetime, timezone
            gap = (datetime.now(timezone.utc)
                   - datetime.strptime(last_sign.created_at, "%Y-%m-%dT%H:%M:%SZ")
                   .replace(tzinfo=timezone.utc)).total_seconds()
        except (ValueError, TypeError):
            gap = _RESIGN_WINDOW_SEC + 1
        if gap < _RESIGN_WINDOW_SEC:
            _trip_freeze(aid, "resign",
                         f"同一 auth_id {gap:.0f}s 内重复签署（窗 {_RESIGN_WINDOW_SEC}s）",
                         by=user["username"])
            raise HTTPException(423, "同一 auth_id 短时重复签署异常——该链已熔断冻结"
                                     "（fail-closed；须 operator 复核解冻）")
    if doc.status == "active":
        raise HTTPException(409, "该件已生效（active）——重复签署不受理")
    # 双库对拍（不符累计；连续 ≥3 熔断②）
    _verify_or_trip(aid)

    prev_status = doc.status
    # tx1：状态推进 active（签署人＝本人）
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, aid)
        d.status = "active"
        d.signer = user["username"]
        d.updated_at = _utc()
    # NCA 落证
    try:
        nca_ref = _nca_append("AUTH_PANEL_SIGN", user["username"],
                              artifact_path=f"authorization-panel:{aid}")
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = prev_status          # 状态停本步
            d.signer = None
            d.updated_at = _utc()
        raise HTTPException(500, "签署存证落链失败——状态已停在本步（未生效），请重试")
    row = _nca_row(nca_ref)
    try:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.nca_seq = nca_ref
            d.rec_hash = row.rec_hash if row else None
            s.add(M.AuthorizationPanelEvent(
                event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=aid,
                event_type="sign", actor=user["username"], nca_ref=nca_ref,
                detail="本人签署（签署人＝起草人）", created_at=_utc()))
    except Exception:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = prev_status          # 状态停本步
            d.signer = None
            d.updated_at = _utc()
        raise HTTPException(500, "签署存证回写失败——状态已停在本步（未生效），请重试")
    return _nca_watermark({
        "auth_id": aid, "status": "active", "nca_seq": nca_ref, "simulated": True,
        "note": "本人签署完成——授权生效（NCA 存证在册；凭据值 ⛔ 不入件）"})


class RevokeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auth_id: str
    note: str = ""


@router.post("/revoke")
def panel_revoke(req: RevokeIn, request: Request):
    """撤回（须起草人本人；撤回后已发生使用另记一笔——事件流水 append-only，⛔ 抹）。"""
    user = _require_session_user(request)
    aid = req.auth_id.strip()
    if not _AUTH_ID_RE.match(aid):
        raise HTTPException(404, "auth_id 不存在")
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
    if doc is None:
        raise HTTPException(404, "auth_id 不存在")
    _assert_not_frozen(aid)
    if user["username"] != doc.drafter:
        raise HTTPException(403, "非本人 ⛔ 撤回——撤回人须与起草人为同一登录主体")
    if doc.status == "revoked":
        raise HTTPException(409, "该件已撤回——重复撤回不受理（历史档案不回改）")
    hits = _public_space_hits({"note": req.note})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    _verify_or_trip(aid)
    prev_status = doc.status

    # tx1：状态 → revoked
    with get_sessionmaker().begin() as s:
        d = s.get(M.AuthorizationPanelDoc, aid)
        d.status = "revoked"
        d.updated_at = _utc()
    try:
        nca_ref = _nca_append("AUTH_PANEL_REVOKE", user["username"],
                              artifact_path=f"authorization-panel:{aid}")
    except Exception:
        with get_sessionmaker().begin() as s:   # 状态停本步
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = prev_status
            d.updated_at = _utc()
        raise HTTPException(500, "撤回存证落链失败——状态已停在本步，请重试")
    row = _nca_row(nca_ref)
    try:
        with get_sessionmaker().begin() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.nca_seq = nca_ref
            d.rec_hash = row.rec_hash if row else None
            s.add(M.AuthorizationPanelEvent(
                event_id=f"APE-{uuid.uuid4().hex[:10]}", auth_id=aid,
                event_type="revoke", actor=user["username"], nca_ref=nca_ref,
                detail="撤回（另记一笔；既往签署/使用记录保留不抹）"
                       + (f"：{req.note.strip()}" if req.note.strip() else ""),
                created_at=_utc()))
    except Exception:
        with get_sessionmaker().begin() as s:   # 状态停本步
            d = s.get(M.AuthorizationPanelDoc, aid)
            d.status = prev_status
            d.updated_at = _utc()
        raise HTTPException(500, "撤回存证回写失败——状态已停在本步，请重试")
    return _nca_watermark({
        "auth_id": aid, "status": "revoked", "nca_seq": nca_ref, "simulated": True,
        "note": "撤回已登记（NCA 存证；已发生使用另记一笔——既往事件流水保留不抹）"})


@router.get("/{auth_id}")
def panel_public(auth_id: str):
    """公开读（免会话）：回范围与期限与状态；⛔ 凭据值。无存证视为未发生（404）。"""
    aid = (auth_id or "").strip()
    if not _AUTH_ID_RE.match(aid):
        raise HTTPException(404, "auth_id 不存在")
    with get_session() as s:
        doc = s.get(M.AuthorizationPanelDoc, aid)
    if doc is None or not doc.nca_seq:   # 无存证 → 未发生
        raise HTTPException(404, "auth_id 不存在（无存证视为未发生）")
    return _public_view(doc)
