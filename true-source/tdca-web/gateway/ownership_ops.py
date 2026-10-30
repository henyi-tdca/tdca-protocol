# -*- coding: utf-8 -*-
"""
P8a 权属登记管理（一期段）：/api/v1/ownership/* —— 登记／变更／注销／查询（权属侧）。

口径（组四 P8a 要件）：
  - 登记二分（《TDCA 注册登记制度》V1.0-FROZEN）：权属登记＝归谁／授权登记＝谁能怎么用；
    本面只做权属侧四操作；转让／许可属权利处分，⛔ 一期不做（归 8b）；
  - 入口＝凡具表达形式者皆可登记；每件须载生成来源谱系（与 P2 谱系账本口径互通）；
  - 场景 ⛔ 非必须——载明适用时从宽，⛔ 不得因无场景拒登记；
  - 法域四支仅为索引分支（表达形式→著作权／发明→专利法／数字结构化→数据法／标识→商标法），
    ⛔ 不代作法律判定、⛔ 不就权利归属下结论；
  - 公开面守四条不公开负空间：内部编号／凭据密钥／自然人敏感信息／负空间词面——
    写入时 fail-closed 拦截（400），读取时兜底脱敏（⛔ 不回显命中内容）；
  - 全程 SIMULATED 硬标注；改动走 PR；⛔ 不重写制度正文、⛔ 不复制另存。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402
from rights_bundle import rb_parse  # noqa: E402

router = APIRouter(prefix="/api/v1/ownership", tags=["ownership"])

# 法域四支（索引分支，⛔ 不代作法律判定）
JURISDICTION_BRANCHES = {
    "copyright": {"branch": "著作权", "entry": "表达形式"},
    "patent": {"branch": "专利法", "entry": "发明"},
    "data": {"branch": "数据法", "entry": "数字结构化"},
    "trademark": {"branch": "商标法", "entry": "标识"},
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


def _record_view(r: M.OwnershipRecord) -> dict:
    redacted = _redact({
        "work_title": r.work_title, "owner_ref": r.owner_ref,
        "expression_form": r.expression_form, "source_lineage": r.source_lineage,
        "scene": r.scene, "note": r.note,
    })
    return {
        "record_id": r.record_id, "status": r.status,
        "jurisdiction_branch": r.jurisdiction_branch,
        "jurisdiction_index": JURISDICTION_BRANCHES.get(r.jurisdiction_branch),
        "nca_ref": r.nca_ref, "data_provenance": r.data_provenance,
        "created_at": r.created_at, "updated_at": r.updated_at,
        **redacted,
    }


@router.get("/rules")
def ownership_rules(request: Request):
    """权属登记口径（登记二分·入口·法域四支·四条不公开负空间）。"""
    _require_session_user(request)
    return _nca_watermark({
        "registry_split": {
            "ownership": "权属登记＝归谁（本面四操作：登记／变更／注销／查询）",
            "authorization": "合约备案＝协作配置中双方约定的权利义务（⛔ 非确权）"},
        "entry": "凡具表达形式者皆可登记",
        "lineage_required": "每件须载生成来源谱系（登记必填；与 P2 谱系账本口径互通）",
        "scene_optional": "场景非必须——⛔ 不得因无场景拒登记",
        "jurisdiction_branches": [
            {"key": k, **v} for k, v in JURISDICTION_BRANCHES.items()],
        "no_legal_judgement": "法域四支仅为索引分支：⛔ 不代作法律判定、⛔ 不就权利归属下结论",
        "out_of_scope": "转让／许可属权利处分，⛔ 一期不做（归 8b 后续）；"
                        "所有权转让属交易合约，可备案存档（⛔ 非确权）",
        "non_public_four": ["内部编号", "凭据密钥", "自然人敏感信息", "负空间词面"],
        "authority": "《TDCA 注册登记制度》（V1.0-FROZEN）为唯一权威源——"
                     "本端只列名目与索引入口（/api/v1/regulations/index），"
                     "⛔ 不重写正文、⛔ 不复制另存",
        "simulated": True,
        "note": "期一内部真跑：「全网可查」仅为内部呈现；对外另须创始人明示"})


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    work_title: str
    owner_ref: str
    source_lineage: str = ""     # 生成来源谱系（登记必填；空 → 400 fail-closed）
    expression_form: str = ""
    jurisdiction_branch: str = "unspecified"
    scene: str = ""              # ⛔ 非必须
    note: str = ""


@router.post("/register", status_code=201)
def ownership_register(req: RegisterIn, request: Request):
    """权属登记（入口＝凡具表达形式者皆可登记；场景非必须）。"""
    user = _require_session_user(request)
    if req.jurisdiction_branch not in (*JURISDICTION_BRANCHES, "unspecified"):
        raise HTTPException(400, "jurisdiction_branch 须为 copyright/patent/data/"
                                 "trademark 之一；不预判法域可省略或取 unspecified")
    if not req.work_title.strip() or not req.owner_ref.strip():
        raise HTTPException(400, "work_title 与 owner_ref 为必填（权属登记）")
    if not req.source_lineage.strip():
        raise HTTPException(400, "登记须载生成来源谱系 source_lineage（⛔ 不得空缺）")
    try:
        note_norm, _rb, rb_anomaly = rb_parse(req.note)
    except ValueError as e:
        raise HTTPException(400, str(e))
    fields = {"work_title": req.work_title, "owner_ref": req.owner_ref,
              "expression_form": req.expression_form, "source_lineage": req.source_lineage,
              "scene": req.scene, "note": note_norm}
    hits = _public_space_hits(fields)
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    rid = f"OR-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("OWNERSHIP_REGISTER", user["username"],
                          artifact_path=f"ownership:{rid}")
    with get_sessionmaker().begin() as s:
        s.add(M.OwnershipRecord(
            record_id=rid, work_title=req.work_title.strip(),
            owner_ref=req.owner_ref.strip(),
            expression_form=req.expression_form.strip() or None,
            jurisdiction_branch=req.jurisdiction_branch,
            source_lineage=req.source_lineage.strip(),
            scene=req.scene.strip() or None, note=note_norm.strip() or None,
            status="registered", nca_ref=nca_ref, created_at=_utc(), updated_at=_utc()))
    payload = {
        "record_id": rid, "status": "registered", "nca_ref": nca_ref,
        "simulated": True,
        "scene_recorded": bool(req.scene.strip()),
        "note": "权属登记已入册（NCA 存证）；场景非必须——未载明不影响登记"}
    if rb_anomaly:
        payload["rb_anomaly"] = rb_anomaly
    return _nca_watermark(payload)


class AmendIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    expression_form: str = ""
    jurisdiction_branch: str = ""
    scene: str = ""
    note: str = ""


@router.post("/amend")
def ownership_amend(req: AmendIn, request: Request):
    """权属变更（已注销者 409；变更须载明事项）。"""
    user = _require_session_user(request)
    if req.jurisdiction_branch and req.jurisdiction_branch not in JURISDICTION_BRANCHES:
        raise HTTPException(400, "jurisdiction_branch 须为 copyright/patent/data/"
                                 "trademark 之一（变更不提供则保留原值）")
    if not any([req.expression_form.strip(), req.jurisdiction_branch.strip(),
                req.scene.strip(), req.note.strip()]):
        raise HTTPException(400, "变更须至少载明一项（expression_form／"
                                 "jurisdiction_branch／scene／note）")
    try:
        note_norm, _rb, rb_anomaly = rb_parse(req.note)
    except ValueError as e:
        raise HTTPException(400, str(e))
    hits = _public_space_hits({"expression_form": req.expression_form,
                               "scene": req.scene, "note": note_norm})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    with get_session() as s:
        row = s.get(M.OwnershipRecord, req.record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    if row.status == "cancelled":
        raise HTTPException(409, "该记录已注销——⛔ 不得变更（历史档案不回改）")
    nca_ref = _nca_append("OWNERSHIP_AMEND", user["username"],
                          artifact_path=f"ownership:{row.record_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.OwnershipRecord, req.record_id)
        if req.expression_form.strip():
            r.expression_form = req.expression_form.strip()
        if req.jurisdiction_branch.strip():
            r.jurisdiction_branch = req.jurisdiction_branch.strip()
        if req.scene.strip():
            r.scene = req.scene.strip()
        if note_norm.strip():
            r.note = note_norm.strip()
        r.status = "amended"
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    payload = {"record_id": row.record_id, "status": "amended",
               "nca_ref": nca_ref, "simulated": True,
               "note": "权属变更已登记（NCA 存证）"}
    if rb_anomaly:
        payload["rb_anomaly"] = rb_anomaly
    return _nca_watermark(payload)


class CancelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str
    note: str = ""


@router.post("/cancel")
def ownership_cancel(req: CancelIn, request: Request):
    """权属注销（协作终结留痕口径；已注销者 409）。"""
    user = _require_session_user(request)
    hits = _public_space_hits({"note": req.note})
    if hits:
        raise HTTPException(400, f"PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间之 "
                                 f"{'／'.join(hits)}——已 fail-closed 拦截（⛔ 内容不回显）")
    with get_session() as s:
        row = s.get(M.OwnershipRecord, req.record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    if row.status == "cancelled":
        raise HTTPException(409, "该记录已注销——重复注销不受理（历史档案不回改）")
    nca_ref = _nca_append("OWNERSHIP_CANCEL", user["username"],
                          artifact_path=f"ownership:{row.record_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.OwnershipRecord, req.record_id)
        r.status = "cancelled"
        r.note = ((r.note or "") + (" ｜ " if r.note else "")
                  + (req.note.strip() or "注销（无附言）"))
        r.nca_ref = nca_ref
        r.updated_at = _utc()
    return _nca_watermark({"record_id": row.record_id, "status": "cancelled",
                           "nca_ref": nca_ref, "simulated": True,
                           "note": "权属注销已登记（NCA 存证；记录留存为历史档案）"})


@router.get("/query")
def ownership_query(request: Request, status: str = "",
                    jurisdiction_branch: str = "", owner_ref: str = ""):
    """权属查询（内部呈现；输出经四条不公开负空间兜底脱敏）。"""
    _require_session_user(request)
    if status and status not in ("registered", "amended", "cancelled"):
        raise HTTPException(400, "status 过滤值非法")
    if jurisdiction_branch and jurisdiction_branch not in (*JURISDICTION_BRANCHES,
                                                           "unspecified"):
        raise HTTPException(400, "jurisdiction_branch 过滤值非法")
    with get_session() as s:
        q = s.query(M.OwnershipRecord).order_by(M.OwnershipRecord.created_at)
        if status:
            q = q.filter_by(status=status)
        if jurisdiction_branch:
            q = q.filter_by(jurisdiction_branch=jurisdiction_branch)
        if owner_ref:
            q = q.filter_by(owner_ref=owner_ref)
        rows = q.all()
    return _nca_watermark({
        "simulated": True, "count": len(rows),
        "records": [_record_view(r) for r in rows],
        "note": "权属查询（登记二分之权属侧；⛔ 不含授权侧 8b；"
                "输出已按四条不公开负空间兜底脱敏）"})


@router.get("/query/{record_id}")
def ownership_query_one(record_id: str, request: Request):
    """权属单条查询（内部呈现；输出兜底脱敏）。"""
    _require_session_user(request)
    with get_session() as s:
        row = s.get(M.OwnershipRecord, record_id)
    if row is None:
        raise HTTPException(404, "record_id 不存在")
    return _nca_watermark({"simulated": True, "record": _record_view(row)})
