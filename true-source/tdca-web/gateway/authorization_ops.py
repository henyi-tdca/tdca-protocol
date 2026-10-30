# -*- coding: utf-8 -*-
"""
P8b 授权登记管理（一期段）：/api/v1/authorization/* —— 登记／变更／注销／查询／操作（授权侧）。

口径（组四 P8b 要件，制度唯一权威源＝《TDCA 注册登记制度》V1.0-FROZEN）：
  - 登记二分：权属登记＝归谁（P8a）；授权登记＝谁能怎么用（本面）；
  - 四要件（登记自证，缺一即 400 fail-closed，⛔ 不得代填代证）：
      ① 场景约束（授权场景已载明且属在册范围）
      ② 五阶资产形态（全阶资产构成已列明）
      ③ 全构成已授权（无保留构成）
      ④ 法律主体签名（电子签名与授权码，⛔ 皆须本人；智能体不代持、不代填；
         授权码值 ⛔ 不入件、不入仓、不入册、不入对话）；
  - 授权件模板（V1.0-FROZEN 固定格式八字段）以 template_fields 透传登记——
    本端 ⛔ 不代定任何未裁取值（费率／期限／层级上限照在册已裁者，未裁者不填）；
  - 公开面四字段＝权属信息／授权信息／授权状态／获取方式（GET /public/{record_id} 免会话，
    仅回此四字段＋记录键与状态）；不公开四条负空间（内部编号／凭据密钥／自然人敏感信息／
    负空间词面）写入时 fail-closed 拦截（400），读取时兜底脱敏（⛔ 不回显命中内容）；
  - 授权件仅内部存证，⛔ 不入主仓；
  - 全程 SIMULATED 硬标注；改动走 PR；⛔ 不重写制度正文、⛔ 不复制另存。
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

router = APIRouter(prefix="/api/v1/authorization", tags=["authorization"])

# 公开面四字段（授权件模板 V1.0-FROZEN 公开投影；初始条件必公开）
PUBLIC_FIELD_KEYS = ("权属信息", "授权信息", "授权状态", "获取方式")

# 五操作（授权管理操作面板；授权状态随操作实时同步；NCA 逐笔存证）
OPERATIONS = {
    "pre_accept": {"label": "预收权", "to_status": "pre-accepted",
                   "note": "预收权：授权件已预收、待生效确认（状态→pre-accepted）"},
    "activate": {"label": "实时授权", "to_status": "active",
                 "note": "实时授权：授权即时生效（状态→active）"},
    "append": {"label": "追加授权", "to_status": "active",
               "note": "追加授权：范围／构成追加（状态保持 active，NCA 逐笔留痕）"},
    "amend_terms": {"label": "许可变更", "to_status": "amended",
                    "note": "许可变更：许可条款变更（状态→amended）"},
    "sub_grant": {"label": "多层级授权", "to_status": "active",
                  "note": "多层级授权：再授权层级操作（状态保持 active，"
                          "⛔ 可否再授权以在册授权件载明为准，本端不代判）"},
}

# 四条不公开负空间（写入拦截／读取兜底脱敏；命中只报类别，⛔ 不回显内容）
_PUBLIC_SPACE_PATTERNS = [
    ("凭据密钥形态", re.compile(
        r"(?i)(password|passwd|secret|token|api[_-]?key|access[_-]?token|"
        r"authorization|credential)\s*[:=]")),
    ("凭据密钥形态", re.compile(r"(?i)bearer\s+[a-z0-9._\-]{8,}")),
    ("自然人敏感信息", re.compile(r"\b\d{17}[\dXx]\b")),
    ("自然人敏感信息", re.compile(r"\b1[3-9]\d{9}\b")),
    ("内部编号词面", re.compile(
        r"(?i)\b(GSEQ-\d+|L\d+SI\d+|KIMI-L\d+SI\d+|NCA-WEB-[0-9a-f]{6,})\b")),
    ("负空间词面", re.compile(r"NSFL|负空间")),
]


def _public_space_hits(fields: dict) -> list:
    """四条不公开负空间扫描：返回命中类别（去重；⛔ 不含命中内容）。"""
    hits = []
    for name, pat in _PUBLIC_SPACE_PATTERNS:
        for value in fields.values():
            if value and pat.search(str(value)) and name not in hits:
                hits.append(name)
    return hits


def _redact(fields: dict) -> dict:
    """读取兜底脱敏：命中字段以占位符替换（不公开面不回显）。"""
    out = {}
    for key, value in fields.items():
        text = "" if value is None else str(value)
        if any(pat.search(text) for _, pat in _PUBLIC_SPACE_PATTERNS):
            out[key] = "[不公开·已按四条负空间脱敏]"
        else:
            out[key] = value
    return out


def _or_aligned(asset_ref: str) -> bool:
    """P3 软校验：asset_ref 是否命中在册权属登记号（只查存在性；不阻断、不改写）。"""
    with get_session() as s:
        return (s.query(M.OwnershipRecord.record_id)
                .filter(M.OwnershipRecord.record_id == (asset_ref or ""))
                .first()) is not None


def _record_view(r: M.AuthorizationRecord) -> dict:
    redacted = _redact({
        "asset_ref": r.asset_ref, "grantee_ref": r.grantee_ref,
        "scene": r.scene, "scope_note": r.scope_note, "term_note": r.term_note,
        "template_fields": r.template_fields, "note": r.note,
    })
    return {
        "record_id": r.record_id, "status": r.status,
        "asset_ref_aligned": _or_aligned(r.asset_ref),
        "four_requirements": {
            "scene_ok": r.req_scene, "five_forms_ok": r.req_five_forms,
            "full_grant_ok": r.req_full_grant, "legal_signature_ok": r.req_legal_signature},
        "operations_available": list(OPERATIONS),
        "nca_ref": r.nca_ref, "data_provenance": r.data_provenance,
        "created_at": r.created_at, "updated_at": r.updated_at,
        **redacted,
    }


def _public_view(r: M.AuthorizationRecord) -> dict:
    """公开面：仅四字段投影（权属信息／授权信息／授权状态／获取方式）＋记录键与状态。"""
    try:
        tpl = json.loads(r.template_fields or "{}")
        if not isinstance(tpl, dict):
            tpl = {}
    except (ValueError, TypeError):
        tpl = {}
    projected = {k: tpl.get(k) for k in PUBLIC_FIELD_KEYS}
    projected = _redact(projected)  # 读取兜底脱敏（公开面亦不例外）
    extra = _redact({  # P1 扩项同走兜底脱敏（S-2：公开面不得出凭据／敏感信息／内部编号）
        "scope_note": r.scope_note or "未提供",
        "term_note": r.term_note or "未提供",
        "是否嵌套": tpl.get("是否嵌套") or "未提供",
        "调用对象": tpl.get("调用对象") or "未提供",
    })
    return _nca_watermark({
        "record_id": r.record_id, "status": r.status,
        "public_fields": dict(zip(PUBLIC_FIELD_KEYS,
                                  ["权属信息", "授权信息", "授权状态", "获取方式"])),
        "权属信息": projected["权属信息"], "授权信息": projected["授权信息"],
        "授权状态": projected["授权状态"] or r.status, "获取方式": projected["获取方式"],
        "初始条件": {"scene_ok": bool(r.req_scene),
                      "five_forms_ok": bool(r.req_five_forms),
                      "full_grant_ok": bool(r.req_full_grant),
                      "legal_signature_ok": bool(r.req_legal_signature),
                      "scope_note": extra["scope_note"]},
        "期限": extra["term_note"],
        "是否嵌套与调用对象": {"是否嵌套": extra["是否嵌套"],
                               "调用对象": extra["调用对象"]},
        "simulated": True,
        "note": "公开面仅四字段（初始条件必公开）；不公开四条负空间读取兜底脱敏；"
                "授权码值与内部编号 ⛔ 不在公开面出现"})


@router.get("/rules")
def authorization_rules(request: Request):
    """授权登记口径（登记二分·四要件·五操作·公开四字段·四条不公开负空间）。"""
    _require_session_user(request)
    return _nca_watermark({
        "registry_split": {
            "ownership": "权属登记＝归谁（P8a）",
            "authorization": "合约备案＝协作配置中双方约定的权利义务（⛔ 非确权）"},
        "four_requirements": [
            {"key": "scene_ok", "label": "① 场景约束", "rule": "授权场景已载明且属在册范围"},
            {"key": "five_forms_ok", "label": "② 五阶资产形态", "rule": "全阶资产构成已列明"},
            {"key": "full_grant_ok", "label": "③ 全构成已授权", "rule": "无保留构成"},
            {"key": "legal_signature_ok", "label": "④ 法律主体签名",
             "rule": "电子签名与授权码皆须本人；智能体不代持、不代填；值不入件入仓入册"}],
        "template": "授权件模板 V1.0-FROZEN 固定格式八字段——以 template_fields 透传登记；"
                    "本端 ⛔ 不代定未裁取值（费率／期限／层级上限照在册已裁者）",
        "operations": [{"op": k, **{kk: vv for kk, vv in v.items()}}
                       for k, v in OPERATIONS.items()],
        "public_four_fields": list(PUBLIC_FIELD_KEYS),
        "non_public_four": ["内部编号", "凭据密钥", "自然人敏感信息", "负空间词面"],
        "storage": "授权件仅内部存证，⛔ 不入主仓",
        "authority": "《TDCA 注册登记制度》（V1.0-FROZEN）为唯一权威源——"
                     "本端只列名目与索引入口（/api/v1/regulations/index），"
                     "⛔ 不重写正文、⛔ 不复制另存",
        "simulated": True,
        "note": "期一内部真跑：「全网可查」仅为内部呈现；对外另须创始人明示"})


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_ref: str                    # 授权对象引用（如五族资产）
    grantee_ref: str                  # 被授权方引用
    scene: str = ""               # 场景（四要件①载体；空 → 400 fail-closed）
    req_scene: bool = False           # 四要件① 场景约束自证
    req_five_forms: bool = False      # 四要件② 五阶资产形态自证
    req_full_grant: bool = False      # 四要件③ 全构成已授权自证
    req_legal_signature: bool = False  # 四要件④ 法律主体签名自证
    scope_note: str = ""              # 权限范围说明（⛔ 不代定取值）
    term_note: str = ""               # 期限说明（⛔ 不代定取值）
    template_fields: dict = {}        # 授权件模板八字段（JSON；本端不代填未裁项）
    note: str = ""


@router.post("/register", status_code=201)
def authorization_register(req: RegisterIn, request: Request):
    """授权登记（四要件缺一即 400 fail-closed——⛔ 不代填代证）。"""
    user = _require_session_user(request)
    missing = [k for k in ("asset_ref", "grantee_ref", "scene")
               if not str(getattr(req, k)).strip()]
    if missing:
        raise HTTPException(400, f"{'／'.join(missing)} 为必填（合约备案）")
    if not all([req.req_scene, req.req_five_forms, req.req_full_grant,
                req.req_legal_signature]):
        raise HTTPException(400, "四要件（场景约束／五阶资产形态／全构成已授权／"
                                 "法律主体签名）须全部自证为真——缺一即 fail-closed 拦截"
                                 "（⛔ 智能体不代持、不代填）")
    if not isinstance(req.template_fields, dict):
        raise HTTPException(400, "template_fields 须为 JSON 对象（授权件模板八字段）")
    tpl = json.dumps(req.template_fields, ensure_ascii=False)
    fields = {"asset_ref": req.asset_ref, "grantee_ref": req.grantee_ref,
              "scene": req.scene, "scope_note": req.scope_note,
              "term_note": req.term_note, "template_fields": tpl, "note": req.note}
    hits = _public_space_hits(fields)
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    rid = f"AR-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("AUTHORIZATION_REGISTER", user["username"],
                          artifact_path=f"authorization:{rid}")
    with get_sessionmaker().begin() as s:
        s.add(M.AuthorizationRecord(
            record_id=rid, asset_ref=req.asset_ref.strip(),
            grantee_ref=req.grantee_ref.strip(), scene=req.scene.strip(),
            req_scene=req.req_scene, req_five_forms=req.req_five_forms,
            req_full_grant=req.req_full_grant,
            req_legal_signature=req.req_legal_signature,
            scope_note=req.scope_note.strip() or None,
            term_note=req.term_note.strip() or None,
            template_fields=tpl, note=req.note.strip() or None,
            status="active", nca_ref=nca_ref,
            created_at=_utc(), updated_at=_utc()))
    aligned = _or_aligned(req.asset_ref.strip())
    payload = {
        "record_id": rid, "status": "active", "nca_ref": nca_ref,
        "asset_ref_aligned": aligned,
        "simulated": True,
        "note": "合约备案已入册（NCA 存证；四要件自证齐全；"
                "授权件仅内部存证，⛔ 不入主仓）"}
    if not aligned:
        payload["warn"] = ("asset_ref 未命中在册权属登记号（未对齐）——"
                           "软校验照收不阻断；读回标「未对齐」")
    return _nca_watermark(payload)


class AmendIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    scene: str = ""
    scope_note: str = ""
    term_note: str = ""
    template_fields: dict | None = None
    note: str = ""


@router.post("/amend")
def authorization_amend(req: AmendIn, request: Request):
    """授权变更（已注销者 409；变更须载明事项；⛔ 不代定未裁取值）。"""
    user = _require_session_user(request)
    if not any([req.scene.strip(), req.scope_note.strip(), req.term_note.strip(),
                req.template_fields is not None, req.note.strip()]):
        raise HTTPException(400, "变更须至少载明一项（scene／scope_note／"
                                 "term_note／template_fields／note）")
    tpl = (json.dumps(req.template_fields, ensure_ascii=False)
           if req.template_fields is not None else "")
    hits = _public_space_hits({"scene": req.scene, "scope_note": req.scope_note,
                               "term_note": req.term_note,
                               "template_fields": tpl, "note": req.note})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    with get_session() as s:
        row = s.get(M.AuthorizationRecord, req.record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    if row.status == "cancelled":
        raise HTTPException(409, "该记录已注销——⛔ 不得变更（历史档案不回改）")
    nca_ref = _nca_append("AUTHORIZATION_AMEND", user["username"],
                          artifact_path=f"authorization:{row.record_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.AuthorizationRecord, req.record_id)
        if req.scene.strip():
            r.scene = req.scene.strip()
        if req.scope_note.strip():
            r.scope_note = req.scope_note.strip()
        if req.term_note.strip():
            r.term_note = req.term_note.strip()
        if req.template_fields is not None:
            r.template_fields = tpl
        if req.note.strip():
            r.note = req.note.strip()
        r.status = "amended"
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    return _nca_watermark({"record_id": row.record_id, "status": "amended",
                           "nca_ref": nca_ref, "simulated": True,
                           "note": "授权变更已登记（NCA 存证）"})


class CancelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    note: str = ""


@router.post("/cancel")
def authorization_cancel(req: CancelIn, request: Request):
    """授权注销（协作终结留痕口径；已注销者 409）。"""
    user = _require_session_user(request)
    hits = _public_space_hits({"note": req.note})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    with get_session() as s:
        row = s.get(M.AuthorizationRecord, req.record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    if row.status == "cancelled":
        raise HTTPException(409, "该记录已注销——重复注销不受理（历史档案不回改）")
    nca_ref = _nca_append("AUTHORIZATION_CANCEL", user["username"],
                          artifact_path=f"authorization:{row.record_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.AuthorizationRecord, req.record_id)
        r.status = "cancelled"
        r.note = ((r.note or "") + (" ｜ " if r.note else "")
                  + (req.note.strip() or "注销（无附言）"))
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    return _nca_watermark({"record_id": row.record_id, "status": "cancelled",
                           "nca_ref": nca_ref, "simulated": True,
                           "note": "授权注销已登记（NCA 存证；记录留存为历史档案）"})


class OperateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    op: str                           # pre_accept／activate／append／amend_terms／sub_grant
    note: str = ""


@router.post("/operate")
def authorization_operate(req: OperateIn, request: Request):
    """授权操作面板（五操作：预收权／实时授权／追加授权／许可变更／多层级授权；
    授权状态随操作实时同步；逐笔落 NCA 存证）。"""
    user = _require_session_user(request)
    if req.op not in OPERATIONS:
        raise HTTPException(400, "op 须为 pre_accept／activate／append／"
                                 "amend_terms／sub_grant 之一")
    hits = _public_space_hits({"note": req.note})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    with get_session() as s:
        row = s.get(M.AuthorizationRecord, req.record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    if row.status == "cancelled":
        raise HTTPException(409, "该记录已注销——⛔ 不得再操作（历史档案不回改）")
    meta = OPERATIONS[req.op]
    nca_ref = _nca_append(f"AUTHORIZATION_OP_{req.op.upper()}", user["username"],
                          artifact_path=f"authorization:{row.record_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.AuthorizationRecord, req.record_id)
        r.status = meta["to_status"]
        stamp = f"{meta['label']}（{req.op}）" + (f"：{req.note.strip()}"
                                                 if req.note.strip() else "")
        r.note = ((r.note or "") + (" ｜ " if r.note else "") + stamp)
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    return _nca_watermark({
        "record_id": row.record_id, "op": req.op, "op_label": meta["label"],
        "status": meta["to_status"], "nca_ref": nca_ref, "simulated": True,
        "note": f"{meta['note']}（NCA 存证；授权状态已实时同步）"})


@router.get("/query")
def authorization_query(request: Request, status: str = "", grantee_ref: str = ""):
    """授权查询（内部呈现；输出经四条不公开负空间兜底脱敏）。"""
    _require_session_user(request)
    if status and status not in ("pre-accepted", "active", "amended", "cancelled"):
        raise HTTPException(400, "status 过滤值非法")
    with get_session() as s:
        q = s.query(M.AuthorizationRecord).order_by(M.AuthorizationRecord.created_at)
        if status:
            q = q.filter_by(status=status)
        if grantee_ref:
            q = q.filter_by(grantee_ref=grantee_ref)
        rows = q.all()
    return _nca_watermark({
        "simulated": True, "count": len(rows),
        "records": [_record_view(r) for r in rows],
        "note": "授权查询（登记二分之授权侧；输出已按四条不公开负空间兜底脱敏）"})


@router.get("/query/{record_id}")
def authorization_query_one(record_id: str, request: Request):
    """授权单条查询（内部呈现；输出兜底脱敏）。"""
    _require_session_user(request)
    with get_session() as s:
        row = s.get(M.AuthorizationRecord, record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    return _nca_watermark({"simulated": True, "record": _record_view(row)})


@router.get("/public/{record_id}")
def authorization_public(record_id: str):
    """公开查（免会话）：仅回公开面四字段——权属信息／授权信息／授权状态／获取方式；
    初始条件必公开；⛔ 不含内部编号／凭据值／授权码值／NCA 引用。"""
    with get_session() as s:
        row = s.get(M.AuthorizationRecord, record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    return _public_view(row)
