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
    """匿名结论清单（L1SI175-B1 S1-1）：只返 claim_text ＋ data_nature。

    ⛔ 不含 conclusion_id / nca_ref / scope_note（内部编号与存证指针不出匿名面）；
    入站时已机验结论面（公式/数值/内部编号任一命中即 400），此处再挡一道：
    存量行若含内部编号（含 TL- 件号，入站正则未覆盖面），整行不列出（fail-closed）。"""
    with get_session() as s:
        rows = s.query(M.FormalConclusion) \
                .order_by(M.FormalConclusion.created_at).all()
    sensitive = re.compile(r"\bTL-[A-Z0-9]|GSEQ-\d+|L1SI\d+|NCA-|TDCA-CRT|TDCA-SES")
    out = [{"claim_text": r.claim_text, "data_nature": r.data_nature}
           for r in rows
           if not _INTERNAL_ID.search(r.claim_text or "")
           and not sensitive.search(r.claim_text or "")]
    return _nca_watermark({
        "count": len(out),
        "conclusions": out,
        "note": "形式化清单（匿名面；只列结论文字与数据性质，"
                "不含内部编号与存证指针；不构成对外发布）"})


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
                         "nca_ref": r.nca_ref} for r in rows],
        "note": "结论入站清单（数据性质显式标注；不构成对外发布）"})
