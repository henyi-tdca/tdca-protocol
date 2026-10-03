# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 内容区文库（/api/v1/library/*）
# 约束矩阵: 站点入站令·甲（whitepapers/papers 批 1 入站）＋乙（cop-library 说明件
#           与代表性子库）——内容区只读面；以在册仓库为唯一权威源，本站只作内部阅读索引
# 口径: 只读（无写端点）；family 闭集机验（whitepaper/paper/cop-library）；
#       登录 DID 会话鉴权（与 P3~P9 各面一致）；docs 表缺失即 503 fail-closed
# =============================================================================
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from api_v1 import _nca_watermark, _require_session_user  # noqa: E402
from db import get_session  # noqa: E402

router = APIRouter(prefix="/api/v1/library", tags=["library"])

# family 闭集：名目照入站令（甲＝whitepaper/paper；乙＝cop-library）；
# 2026-10-04 创始人明示：规范栏目须看全文 ⟹ 增列 regulation（docs 表 regulation 族实读）
_FAMILIES: dict[str, str] = {
    "whitepaper": "白皮书（whitepapers）",
    "paper": "论文与实证（papers）",
    "cop-library": "产物库（cop-library）",
    "regulation": "制度规范（regulations）",
}

_SEL_LIST = text("SELECT slug, title, synced_at, LENGTH(body_md) AS body_chars"
                 " FROM docs WHERE family = :family ORDER BY slug")
_SEL_DETAIL = text("SELECT slug, title, body_md, source_path, data_nature, synced_at"
                   " FROM docs WHERE family = :family AND slug = :slug")
_SEL_COUNTS = text("SELECT family, COUNT(*) AS n FROM docs GROUP BY family")


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
    """文库族列表（闭集＋各族件数；登录 DID）。"""
    _require_session_user(request)
    counts = _counts()
    items = [{"family": k, "name": v, "count": counts.get(k, 0)} for k, v in _FAMILIES.items()]
    return _nca_watermark({"families": items, "note": "内容区只读面；以在册仓库为唯一权威源"},
                          nature="real")


@router.get("/{family}")
def library_list(family: str, request: Request):
    """族内件目（slug/title/synced_at；正文经 /{slug} 读取）。"""
    _require_session_user(request)
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
    """单件正文（body_md 原文直出；不复制不改写；权威源在册）。"""
    _require_session_user(request)
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
