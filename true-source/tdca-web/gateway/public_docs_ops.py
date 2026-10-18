# -*- coding: utf-8 -*-
"""
公开只读制度件取得面（丙案 · L1SI151-PUBLIC-ROUTE-001）。

口径（入站判据 P-1~P-5之前置 · TDCA-RULING-SITE-INGEST-DEFINITION-001）：
  - 入站＝公网可取得件：本面即「可发现（P-1）＋可取得（P-2）」之公开承载面；
  - 匿名只读：仅 GET；写方法一律不开放（未定义即 405 fail-closed）；
  - 只列已入站公开件：以在册公开清单（甲类 8 件 · L1SI151 批1段二）为准，
    ⛔ 未入站件不出现、⛔ 乙类存证件永不出现（fail-closed：越界取件 404，
    ⛔ 不借 404/200 之差泄露在仓与否之外的信息——统一 404）；
  - 单一事实源：件即容器内只读文件（docs/regulations/），sha256 由文件现算，
    ⛔ 不另建库表副本、⛔ 不双源各算；
  - 不带私域：⛔ 内部编号（件内若残留编号属内容本身，照实返回——入站核验另扫）、
    ⛔ 运维字段、⛔ 他人数据、⛔ 计量与额度；
  - 限流：60 次/分/IP（滑动窗口，防枚举）；
  - 别名：旧 /api/site/docs/* 指向同一实现（⛔ 不双实现），仅为前端不改。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from error_codes import with_code  # L1SI153 段一：拒绝体仅增设 code 字段

router = APIRouter(prefix="/api/public", tags=["public-docs"])
# 别名路由：与主路由同一实现（同一处理函数），仅为前端不改（施工令 §二）
alias_router = APIRouter(prefix="/api/site", tags=["public-docs-alias"])

# ---------------------------------------------------------------------
# 在册公开清单（甲类 8 件 · L1SI151 批1段二 · main e9b4309a）
# ⛔ 未入站件与乙类 2 件（签批记录／生效注记）一律不得列入；
# 更新本清单须另有在册依据（入站批次放行件），⛔ 不得随代码静默扩面。
# ---------------------------------------------------------------------
_FAMILY = "regulation"
_PUBLIC_DOCS = (
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V0.1-DRAFT）.yaml",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V0.1-DRAFT）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V0.1-DRAFT）.yaml",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（人读版·V0.9-DRAFT·待签批）.md",
    "TDCA-STD-SCENE-ENCOUNTER-001-场景线·相遇专章（机读版·V0.9-DRAFT）.yaml",
)
_PUBLIC_SET = frozenset(_PUBLIC_DOCS)

_RATE_LIMIT_PER_MIN = 60

# ---------------------------------------------------------------------
# 限流（进程内滑动窗口；单 worker 部署下足够，防枚举非防攻击）
# ---------------------------------------------------------------------
_hits: dict[str, list] = {}
_hits_lock = threading.Lock()


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    with _hits_lock:
        lst = _hits.setdefault(ip, [])
        cutoff = now - 60.0
        while lst and lst[0] < cutoff:
            lst.pop(0)
        if len(lst) >= _RATE_LIMIT_PER_MIN:
            return True
        lst.append(now)
        return False


# ---------------------------------------------------------------------
# 件目录解析：容器内只读挂载（/docs/regulations）为单一事实源；
# 本地/测试可用 TDCA_PUBLIC_DOCS_DIR 指向等价目录（⛔ 生产不设）
# ---------------------------------------------------------------------
def _docs_dir() -> Path | None:
    override = os.environ.get("TDCA_PUBLIC_DOCS_DIR", "").strip()
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    here = Path(__file__).resolve()
    for parent in (here.parents[3], here.parents[2], here.parents[1]):
        cand = parent / "docs" / "regulations"
        if cand.is_dir():
            return cand
    return None


def _read_doc(filename: str) -> tuple[bytes, str] | None:
    """读在册公开件（⛔ 绝不越出清单）；返回 (bytes, sha256) 或 None。"""
    if filename not in _PUBLIC_SET:
        return None
    d = _docs_dir()
    if d is None:
        return None
    fpath = d / filename
    try:
        raw = fpath.read_bytes()
    except OSError:
        return None
    if not fpath.is_file() or fpath.parent != d:  # 纵深防御（防路径穿越）
        return None
    return raw, hashlib.sha256(raw).hexdigest()


_VERSION_RE = re.compile(r"V\d+\.\d+(?:-[A-Z0-9.]+)*")
_YAML_VERSION_RE = re.compile(r"^version:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.M)


def _version_of(filename: str, text: str) -> str | None:
    """版本读件内真实值（best-effort；⛔ 不硬编码）。"""
    if filename.endswith(".yaml"):
        m = _YAML_VERSION_RE.search(text[:2000])
        if m:
            return m.group(1).strip()
    head = "\n".join(text.splitlines()[:30])
    m = _VERSION_RE.search(head)
    return m.group(0) if m else None


def _entry(filename: str, raw: bytes, sha: str) -> dict:
    text = raw.decode("utf-8", "replace")
    return {
        "family": _FAMILY,
        "slug": filename,
        "filename": filename,
        "version": _version_of(filename, text),
        "bytes": len(raw),
        "sha256": sha,
        "sha256_16": sha.upper()[:16],
    }


def _list_docs() -> JSONResponse:
    entries = []
    for name in _PUBLIC_DOCS:
        got = _read_doc(name)
        if got is None:
            # 已入站件缺失＝容器件异常：不静默减项，明示 fail-closed
            # L1SI153 段三②：error 机器字段设过渡期（两存：error＋detail＋code）——
            # DEPRECATED，下版删除；新判据一律读 code，⛔ 勿为新代码依赖 error
            return JSONResponse(
                with_code({"error": "DOC_SOURCE_UNAVAILABLE",
                           "detail": f"在册公开件暂不可读：{name}（文档源异常，已按 fail-closed 暂停列出）"}, 503),
                status_code=503)
        raw, sha = got
        entries.append(_entry(name, raw, sha))
    return JSONResponse({
        "family": _FAMILY,
        "count": len(entries),
        "source": "docs/regulations（只读容器件·单一事实源）",
        "principle": "只列已入站公开件；未入站与存证件不出现（fail-closed）",
        "documents": entries,
    })


def _get_doc(slug: str) -> JSONResponse:
    got = _read_doc(slug)
    if got is None:
        # 统一 404：未入站件／乙类件／不存在件，对外不可分辨（fail-closed）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    raw, sha = got
    entry = _entry(slug, raw, sha)
    entry["content"] = raw.decode("utf-8", "replace")
    return JSONResponse(entry)


def _guard(request: Request) -> JSONResponse | None:
    if _rate_limited(request.client.host if request.client else "unknown"):
        # L1SI153 段二②：裸英文退役 → 码表口径中文短句（RES-RES-001）
        return JSONResponse(with_code({"detail": "操作过于频繁，请稍后再试（限流 60 次/分钟/同一地址）"}, 429), status_code=429)
    return None


# ---------------------------------------------------------------------
# 主路由：GET /api/public/docs[/regulation[/slug]]
# ---------------------------------------------------------------------
@router.get("/docs")
def public_docs_list(request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    return _list_docs()


@router.get("/docs/{family}")
def public_docs_family(family: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family != _FAMILY:
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _list_docs()


@router.get("/docs/{family}/{slug:path}")
def public_docs_get(family: str, slug: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family != _FAMILY:
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _get_doc(slug)


# ---------------------------------------------------------------------
# 别名：旧 /api/site/docs/* —— 同一实现，⛔ 不双实现（施工令 §二）
# ---------------------------------------------------------------------
@alias_router.get("/docs")
def alias_docs_list(request: Request):
    return public_docs_list(request)


@alias_router.get("/docs/{family}")
def alias_docs_family(family: str, request: Request):
    return public_docs_family(family, request)


@alias_router.get("/docs/{family}/{slug:path}")
def alias_docs_get(family: str, slug: str, request: Request):
    return public_docs_get(family, slug, request)
