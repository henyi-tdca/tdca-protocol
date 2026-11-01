# -*- coding: utf-8 -*-
"""
P3 形式化与实验线结论入站（A-14）：/api/v1/formal/* —— 只做结论面。

四要件（期一段二追加，逐条机验）：
  1. 只做结论面：不转公式（禁公式符号与 LaTeX 记法）、不引数值（禁 ≥3 位连续数字）、
     不带内部编号（禁井号制编号与内部件号前缀）——三者任一命中即 400 fail-closed；
  2. 数据性质显式标注：formal-proved（形式化已证）/ simulated（有限模型模拟）/
     assessed（评估判断）——闭集外取值即拒；
  3. 条件形态结论须在 scope_note 载明适用边界（不得表述为无条件成立）；
  4. 红线：结论入站 ≠ 入主仓 ≠ 对外——本端点不构成对外发布通道（涉对外即停手）。
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

router = APIRouter(prefix="/api/v1/formal", tags=["formal"])

# 公式符号（Lean/LaTeX/逻辑记法常见面）与数值引用、内部编号制式
_FORMULA_CHARS = re.compile(r"[∀∃∧∨¬→↔λ⊢⊨≡≈≤≥≠∈∑∏∫√∞]|:=|\\\[|\\\(|\\forall|\\exists|\\lambda|\\to|\\leftrightarrow")
_NUMBER_REF = re.compile(r"\d{3,}")
_INTERNAL_ID = re.compile(r"(TDCA-[A-Z]|#[^\s#]{1,20}\b)|\b(C-\d{1,3}|P-\d{1,2}|M-\d{1,2}|COORD-\d)\b")

_MAX_LEN = 2000

# 对外版适用范围追加禁则（SITE-CLAIMFIX-001 A-4）：内部假设标号独立出现
# （A1／B1 类——字母+一至两位数字、前后非字母数字），如「A1 信任链为…」
_SCOPE_LABEL = re.compile(r"(?<![A-Za-z0-9])[A-Z]\d{1,2}(?![A-Za-z0-9])")


def _check_claim_surface(claim_text: str) -> None:
    """结论面机验：公式 / 数值 / 内部编号，任一命中即 400 fail-closed。"""
    if not claim_text or not claim_text.strip():
        raise HTTPException(400, "CLAIM_EMPTY: 结论面文字不得为空")
    if len(claim_text) > _MAX_LEN:
        raise HTTPException(400, f"CLAIM_TOO_LONG: 结论面超 {_MAX_LEN} 字符上限")
    if _FORMULA_CHARS.search(claim_text):
        raise HTTPException(400, "FORMULA_DETECTED: 结论面不得转公式（仅收纯文字结论）")
    if _NUMBER_REF.search(claim_text):
        raise HTTPException(400, "NUMERIC_REF_DETECTED: 结论面不得引用数值")
    if _INTERNAL_ID.search(claim_text):
        raise HTTPException(400, "INTERNAL_ID_DETECTED: 结论面不得带内部编号")


def _check_scope_summary(scope_summary: str) -> None:
    """对外版适用范围机验：同结论面红线全套，另禁内部假设标号独立出现。"""
    if not scope_summary or not scope_summary.strip():
        raise HTTPException(400, "SCOPE_SUMMARY_EMPTY: 对外版适用范围不得为空")
    if len(scope_summary) > _MAX_LEN:
        raise HTTPException(400, f"SCOPE_SUMMARY_TOO_LONG: 对外版适用范围超 {_MAX_LEN} 字符上限")
    if _FORMULA_CHARS.search(scope_summary):
        raise HTTPException(400, "FORMULA_DETECTED: 对外版适用范围不得含公式记法")
    if _NUMBER_REF.search(scope_summary):
        raise HTTPException(400, "NUMERIC_REF_DETECTED: 对外版适用范围不得引用数值")
    if _INTERNAL_ID.search(scope_summary):
        raise HTTPException(400, "INTERNAL_ID_DETECTED: 对外版适用范围不得带内部编号")
    if _SCOPE_LABEL.search(scope_summary):
        raise HTTPException(400, "SCOPE_LABEL_DETECTED: 对外版适用范围不得含内部假设标号")


class ConclusionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_text: str
    data_nature: str = ""          # formal-proved / simulated / assessed
    scope_note: str = ""


@router.post("/conclusion", status_code=201)
def conclusion_register(req: ConclusionIn, request: Request):
    """结论入站（结论面机验 → 性质闭集 → 落库 + NCA 存证）。"""
    user = _require_session_user(request)
    _check_claim_surface(req.claim_text)
    if req.data_nature not in ("formal-proved", "simulated", "assessed"):
        raise HTTPException(400, "DATA_NATURE_INVALID: 须为 formal-proved / simulated / assessed")
    # 条件形态守卫：结论面含条件措辞而 scope_note 为空 → 拒（不得表述为无条件成立）
    if re.search(r"条件|限于|离散情形|有限模型", req.claim_text) and not req.scope_note.strip():
        raise HTTPException(400, "SCOPE_REQUIRED: 条件形态结论须载明适用边界（scope_note）")
    cid = f"FC-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("FORMAL_CONCLUSION", user["username"],
                          artifact_path=f"conclusion:{cid}")
    with get_sessionmaker().begin() as s:
        s.add(M.FormalConclusion(
            conclusion_id=cid, claim_text=req.claim_text.strip(),
            data_nature=req.data_nature,
            scope_note=req.scope_note.strip() or None, nca_ref=nca_ref,
            created_at=_utc()))
    return _nca_watermark({
        "conclusion_id": cid, "data_nature": req.data_nature, "nca_ref": nca_ref,
        "note": "结论已入站（结论面口径）——入站 ≠ 入主仓 ≠ 对外；"
                "数据性质随文显式标注，不得据入站升级主张"})


@router.get("/conclusion/catalog")
def conclusion_catalog(request: Request):
    """匿名结论清单（L1SI175-B1 S1-1；CLAIMFIX-001 A-2/A-3 增补）。

    返回 claim_text ＋ data_nature ＋ scope_summary（对外版适用范围）；
    ⛔ 不含 conclusion_id / nca_ref / scope_note（内部编号与存证指针不出匿名面）；
    分级 fail-closed：data_nature == formal-proved 且 scope_summary 为空 ⟹ 该条不列出；
    simulated 存量豁免（照旧列出，scope_summary 可为空）。
    入站时已机验结论面（公式/数值/内部编号任一命中即 400），此处再挡一道：
    存量行若含内部编号（含 TL- 件号，入站正则未覆盖面），整行不列出（fail-closed）。"""
    with get_session() as s:
        rows = s.query(M.FormalConclusion) \
                .order_by(M.FormalConclusion.created_at).all()
    sensitive = re.compile(r"\bTL-[A-Z0-9]|GSEQ-\d+|L1SI\d+|NCA-|TDCA-CRT|TDCA-SES")
    out = []
    for r in rows:
        if _INTERNAL_ID.search(r.claim_text or "") \
                or sensitive.search(r.claim_text or ""):
            continue                       # 敏感行整行不列（fail-closed，原口径）
        summary = (r.scope_summary or "").strip()
        if _INTERNAL_ID.search(summary) or sensitive.search(summary):
            continue                       # 对外版命中内部编号亦整行不列（fail-closed）
        if r.data_nature == "formal-proved" and not summary:
            continue                       # CLAIMFIX-001 A-3：正式结论无对外版即不列
        out.append({"claim_text": r.claim_text, "data_nature": r.data_nature,
                    "scope_summary": summary})
    return _nca_watermark({
        "count": len(out),
        "conclusions": out,
        "note": "形式化清单（匿名面；只列结论文字、数据性质与对外版适用范围，"
                "不含内部编号、内部适用范围与存证指针；不构成对外发布）"})


class ConclusionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_text: str | None = None       # 可选；提供即过结论面机验（同入站）
    scope_summary: str | None = None    # 可选；提供即过对外版机验（另禁内部假设标号）


@router.patch("/conclusion/{conclusion_id}")
def conclusion_update(conclusion_id: str, req: ConclusionPatch, request: Request):
    """结论更新（SITE-CLAIMFIX-001 A-4）：去前缀/补对外版唯一通道。

    权限：仅 operator/founder（同注册）；机验：与入站同一套红线；
    存证：追加一条 NCA（操作类型＝结论更新，artifact_path 指向同 conclusion_id），
    ⛔ 覆盖原存证；conclusion_id 保留（不删旧增新）；
    幂等：值不变即不写库、不追加存证，返回同形态结果。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可更新结论")
    if req.claim_text is None and req.scope_summary is None:
        raise HTTPException(400, "PATCH_EMPTY: claim_text 与 scope_summary 至少提供一项")
    if req.claim_text is not None:
        _check_claim_surface(req.claim_text)
    if req.scope_summary is not None:
        _check_scope_summary(req.scope_summary)

    with get_sessionmaker().begin() as s:
        row = s.get(M.FormalConclusion, conclusion_id)
        if row is None:
            raise HTTPException(404, "结论不存在")
        new_claim = req.claim_text.strip() if req.claim_text is not None else None
        new_summary = req.scope_summary.strip() if req.scope_summary is not None else None
        changed: list[tuple[str, str]] = []
        if new_claim is not None and new_claim != row.claim_text:
            # 条件形态守卫同入站：条件措辞结论须有适用边界（内部版为准）
            if re.search(r"条件|限于|离散情形|有限模型", new_claim) \
                    and not (row.scope_note or "").strip():
                raise HTTPException(400, "SCOPE_REQUIRED: 条件形态结论须有适用边界（scope_note）")
            changed.append(("claim_text", new_claim))
        if new_summary is not None and new_summary != (row.scope_summary or ""):
            changed.append(("scope_summary", new_summary))
        if not changed:
            return _nca_watermark({
                "conclusion_id": conclusion_id, "updated": False,
                "note": "内容未变，幂等返回（无新增存证）"})
        nca_ref = _nca_append("结论更新", user["username"],
                              artifact_path=f"conclusion:{conclusion_id}")
        for field, value in changed:
            setattr(row, field, value)
        # ⛔ 不动 row.nca_ref：行指针维持创建存证，更新存证以追加行存于 nca_chain
    return _nca_watermark({
        "conclusion_id": conclusion_id, "updated": True,
        "changed": [f for f, _ in changed], "nca_ref": nca_ref,
        "note": "结论已更新（存证追加，原存证未动；conclusion_id 不变）"})


@router.get("/conclusion/list")
def conclusion_list(request: Request, data_nature: str = ""):
    """结论列表（可按数据性质过滤；全量只读可查）。"""
    _require_session_user(request)
    with get_session() as s:
        q = s.query(M.FormalConclusion).order_by(M.FormalConclusion.created_at)
        if data_nature:
            if data_nature not in ("formal-proved", "simulated", "assessed"):
                raise HTTPException(400, "data_nature 过滤值非法")
            q = q.filter_by(data_nature=data_nature)
        rows = q.all()
    return _nca_watermark({
        "count": len(rows),
        "conclusions": [{"conclusion_id": r.conclusion_id,
                         "claim_text": r.claim_text,
                         "data_nature": r.data_nature,
                         "scope_note": r.scope_note,
                         "scope_summary": r.scope_summary,
                         "nca_ref": r.nca_ref} for r in rows],
        "note": "结论入站清单（数据性质显式标注；不构成对外发布）"})
