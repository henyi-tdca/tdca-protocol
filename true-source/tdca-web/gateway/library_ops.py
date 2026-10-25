# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 内容区文库（/api/v1/library/*）
# 约束矩阵: 站点入站令·甲（whitepapers/papers 批 1 入站）＋乙（cop-library 说明件
#           与代表性子库）——内容区只读面；以在册仓库为唯一权威源，本站只作内部阅读索引
# 口径: 只读（无写端点）；family 闭集机验（whitepaper/paper/terms/kg/cop-library/laws/law-notes）；
#       登录 DID 会话鉴权（与 P3~P9 各面一致）；docs 表缺失即 503 fail-closed
# 匿名放行: TDCA-RULING-SITE-COP-LIB-OPEN-001（2026-10-21，创始人取甲）——
#           仅 cop-library 一族三端点匿名只读；其余族仍须会话；⛔ 不改 _require_session_user 本体
# 匿名放行追加: LAWINGEST-001（2026-10-23，批C-C2）——laws/law-notes 两族并入匿名只读
#           （法律原文属公域材料；适用说明标「本侧解读·非官方意见」）；制度族（regulation）
#           归 /api/site/docs 维持原口径不变，⛔ 借机改动
# =============================================================================
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from api_v1 import _nca_watermark, _require_session_user  # noqa: E402
from db import get_session  # noqa: E402

router = APIRouter(prefix="/api/v1/library", tags=["library"])

# family 闭集：LIB-DOCS-SCOPE-001 新口径——知识库＝理论/白皮书/文献/术语/知识图谱/思维协议产物；
# regulation（制度类）归文档库 /api/site/docs（两闭集各自定义 ⛔ 不互取，零重叠）；
# terms/kg 新族位零行只建位 ⛔ 不造数据
_FAMILIES: dict[str, str] = {
    "whitepaper": "白皮书（理论／白皮书）",
    "paper": "文献（papers）",
    "terms": "术语（terms）",
    "kg": "知识图谱（kg）",
    "cop-library": "思维协议产物（cop-library）",
    "laws": "法律原文（laws）",
    "law-notes": "适用说明（law-notes）",
}

_SEL_LIST = text("SELECT slug, title, synced_at, LENGTH(body_md) AS body_chars"
                 " FROM docs WHERE family = :family ORDER BY slug")
_SEL_DETAIL = text("SELECT slug, title, body_md, source_path, data_nature, synced_at"
                   " FROM docs WHERE family = :family AND slug = :slug")
_SEL_COUNTS = text("SELECT family, COUNT(*) AS n FROM docs GROUP BY family")
_SEL_PAPER_CATALOG = text("SELECT slug, title, body_md, synced_at FROM docs"
                          " WHERE family = 'paper' ORDER BY slug")

# L1SI175-B1 S1-4：匿名摘要面脱敏正则——内部件号/存证指针/凭据措辞/自然人邮箱，
# 命中任一即 fail-closed（摘处置 null 或整件不列）
_CATALOG_SENSITIVE = re.compile(
    r"\b(FC|TL|CI)-[A-Z0-9]|GSEQ-\d+|L1SI\d+|NCA-|TDCA-CRT|TDCA-SES|"
    r"[\w.+-]+@[\w-]+\.[\w.]+|(密码|口令|token|secret|凭据)", re.IGNORECASE)
_SUMMARY_LEN = 200


def _first_prose_paragraph(body_md: str) -> str:
    """取正文首个说明性段落：跳过 Markdown 标题/分隔线/空行，截 200 字。"""
    for block in re.split(r"\n\s*\n", body_md or ""):
        lines = [ln.strip() for ln in block.splitlines()
                 if ln.strip() and not ln.strip().startswith(("#", "---", "```"))]
        if lines:
            return " ".join(lines)[:_SUMMARY_LEN]
    return ""


@router.get("/paper/catalog")
def paper_catalog(request: Request):
    """纸族匿名目录＋摘要（L1SI175-B1 S1-4）。

    匿名只返 slug/title/摘要（正文首段截 200 字）；正文端点 /paper/{slug} 仍 401 不动；
    摘要或标题命中脱敏正则者 fail-closed（摘要置 null 标「待核定」，标题命中整件不列）。"""
    try:
        with get_session() as s:
            rows = s.execute(_SEL_PAPER_CATALOG).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    items = []
    for r in rows:
        if _CATALOG_SENSITIVE.search(r.title or ""):
            continue
        summary = _first_prose_paragraph(r.body_md or "")
        if _CATALOG_SENSITIVE.search(summary):
            items.append({"slug": r.slug, "title": r.title,
                          "summary": None, "summary_note": "摘要待核定"})
        else:
            items.append({"slug": r.slug, "title": r.title, "summary": summary})
    return _nca_watermark(
        {"family": "paper", "count": len(items), "items": items,
         "note": "文献族公开目录＋摘要（正文须登录；摘要不构成全文替代）"},
        nature="real")


# COP-LIB-OPEN-001 + TERMS-OPEN-001：匿名放行两族（2026-10-21 并入同轮）
# LAWINGEST-001（批C-C2）：追加 laws/law-notes 两族匿名只读（法律原文属公域材料）
_OPEN_FAMILIES = ("cop-library", "terms", "laws", "law-notes")


def _session_or_open(request: Request, family: str = "") -> None:
    """会话要求分派：_OPEN_FAMILIES 四族（cop-library/terms/laws/law-notes）匿名放行；
    其余（含未点名）照旧会话鉴权。
    ⛔ 不改 _require_session_user 本体（不动其签名与行为），仅在本族分支不调用之。"""
    if family in _OPEN_FAMILIES:
        return
    _require_session_user(request)


def _counts() -> dict[str, int]:
    try:
        with get_session() as s:
            rows = s.execute(_SEL_COUNTS).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    return {r.family: r.n for r in rows}


def _check_family(family: str) -> None:
    if family not in _FAMILIES:
        raise HTTPException(404, f"FAMILY_UNKNOWN: family 须为 {' / '.join(_FAMILIES)}")


@router.get("/families")
def library_families(request: Request):
    """文库族列表。匿名仅返 _OPEN_FAMILIES 四族（⛔ 泄他族名）；
    会话通过则返全闭集（回归照旧）。"""
    try:
        _require_session_user(request)
        authed = True
    except HTTPException:
        authed = False
    counts = _counts()
    if not authed:
        items = [{"family": f, "name": _FAMILIES[f],
                  "count": counts.get(f, 0)} for f in _OPEN_FAMILIES]
        return _nca_watermark(
            {"items": items, "note": "匿名只读面：cop-library＋terms＋laws＋law-notes 四族开放"
                                     "（COP-LIB-OPEN-001／TERMS-OPEN-001／LAWINGEST-001）"},
            nature="real")
    items = [{"family": k, "name": v, "count": counts.get(k, 0)} for k, v in _FAMILIES.items()]
    return _nca_watermark({"families": items, "note": "内容区只读面；以在册仓库为唯一权威源"},
                          nature="real")


@router.get("/{family}")
def library_list(family: str, request: Request):
    """族内件目（slug/title/synced_at；正文经 /{slug} 读取）。_OPEN_FAMILIES 四族匿名可读。"""
    _session_or_open(request, family)
    _check_family(family)
    try:
        with get_session() as s:
            rows = s.execute(_SEL_LIST, {"family": family}).all()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    return _nca_watermark(
        {"family": family, "name": _FAMILIES[family],
         "items": [{"slug": r.slug, "title": r.title, "synced_at": r.synced_at,
                    "has_content": bool(r.body_chars and r.body_chars > 0)} for r in rows]},
        nature="real")


@router.get("/{family}/{slug}")
def library_detail(family: str, slug: str, request: Request):
    """单件正文（body_md 原文直出；不复制不改写；权威源在册）。_OPEN_FAMILIES 四族匿名可读。"""
    _session_or_open(request, family)
    _check_family(family)
    try:
        with get_session() as s:
            row = s.execute(_SEL_DETAIL, {"family": family, "slug": slug}).first()
    except Exception:
        raise HTTPException(503, "LIBRARY_FAIL_CLOSED: 内容库不可用（docs 表缺失或损坏）")
    if row is None:
        raise HTTPException(404, "DOC_NOT_FOUND: 件不存在或未入站")
    return _nca_watermark(
        {"family": family, "slug": row.slug, "title": row.title, "body_md": row.body_md,
         "source_path": row.source_path, "synced_at": row.synced_at,
         "note": "本站为内部阅读面；⛔ 不复制正文另存、⛔ 不改一字；权威源以在册仓库为准"},
        nature=row.data_nature if row.data_nature in ("real", "simulated") else "real")
