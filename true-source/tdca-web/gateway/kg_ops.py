# -*- coding: utf-8 -*-
"""
知识图谱公开只读面（L1SI211-KG-SITE-001 · 977 节点／2581 关系版）。

口径（对令 TDCA-HANDOFF-EXEC-L1SI211-KG-SITE-001 及其 AMEND-1）：
  - 匿名只读：仅 GET；写方法一律 405（未定义即 fail-closed）；
  - 静态包四件按 docs/ 族方式直取：/kg/v1/manifest.yaml、nodes.yaml、edges.yaml、
    README.md——件即容器内只读文件，sha256 现算，⛔ 不另建库表副本；
  - 四条只读接口：/api/v1/kg/nodes|node/{id}|subgraph|edges（+ manifest 摘要面）；
  - ⛔ 藏登录墙后、⛔ 与文档库／制度库重复列表；
  - 容器无 PyYAML（实测）⟹ 依赖-free 扁平 YAML 解析器（标量字段、固定结构）；
  - 页面显示数字实读 manifest ⛔ 写死（AMEND-1 §三-1）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from error_codes import with_code

router = APIRouter(tags=["kg-public"])

# ---------------------------------------------------------------------
# 件目录解析：容器内只读目录 /kg/v1 为单一事实源；
# 本地/测试可用 TDCA_KG_DIR 指向等价目录（⛔ 生产不设）
# ---------------------------------------------------------------------
_STATIC_FILES = ("manifest.yaml", "nodes.yaml", "edges.yaml", "README.md")


def _kg_dir() -> Path | None:
    override = os.environ.get("TDCA_KG_DIR", "").strip()
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    for cand in (Path("/kg/v1"),):
        if cand.is_dir():
            return cand
    here = Path(__file__).resolve()
    # parents[0]＝包目录自身（站机部署：kg/v1 随代码目录同挂载）；其余为本地仓回退
    for parent in (here.parents[0], here.parents[3], here.parents[2], here.parents[1]):
        cand = parent / "kg" / "v1"
        if cand.is_dir():
            return cand
    return None


def _read_file(name: str) -> tuple[bytes, str] | None:
    """读包内件（⛔ 绝不越出四件白名单）。"""
    if name not in _STATIC_FILES:
        return None
    d = _kg_dir()
    if d is None:
        return None
    fpath = d / name
    try:
        raw = fpath.read_bytes()
    except OSError:
        return None
    if not fpath.is_file() or fpath.parent != d:  # 纵深防御（防路径穿越）
        return None
    return raw, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------
# 依赖-free 扁平 YAML 解析（nodes/edges 结构固定：顶层单键 → 列表 → 标量键值）
# ---------------------------------------------------------------------
def _parse_flat_yaml(text: str) -> dict:
    top_key = None
    items: list[dict] = []
    cur: dict | None = None
    for ln in text.splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if not ln.startswith(" ") and ln.rstrip().endswith(":"):
            top_key = ln.strip()[:-1]
            continue
        s = ln.strip()
        if s.startswith("- "):
            cur = {}
            items.append(cur)
            s = s[2:].strip()
            if not s:
                continue
        elif not ln.startswith(" ") and ":" in ln:
            # 顶层标量（manifest 用，本解析器只用于 nodes/edges，防御性跳过）
            continue
        if cur is not None and ":" in s:
            k, _, v = s.partition(":")
            cur[k.strip()] = v.strip().strip("'").strip('"')
    return {top_key or "items": items}


_CACHE: dict | None = None


def _load() -> dict | None:
    """载入图谱（进程内缓存；文件缺失/解析失败返回 None，fail-closed）。"""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    n = _read_file("nodes.yaml")
    e = _read_file("edges.yaml")
    if n is None or e is None:
        return None
    try:
        nodes = _parse_flat_yaml(n[0].decode("utf-8", "replace")).get("nodes", [])
        edges = _parse_flat_yaml(e[0].decode("utf-8", "replace")).get("edges", [])
        by_id = {x["id"]: x for x in nodes if "id" in x}
        out = {"nodes": nodes, "edges": edges, "by_id": by_id}
    except Exception:
        return None
    _CACHE = out
    return out


def _unavailable(detail: str) -> JSONResponse:
    return JSONResponse(
        with_code({"error": "KG_SOURCE_UNAVAILABLE", "detail": detail}, 503),
        status_code=503)


# ---------------------------------------------------------------------
# 静态包直取：GET /kg/v1/{name}
# ---------------------------------------------------------------------
@router.get("/kg/v1/{name}")
def kg_static(name: str, request: Request):
    got = _read_file(name)
    if got is None:
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    raw, sha = got
    return PlainTextResponse(
        raw.decode("utf-8", "replace"),
        media_type="application/yaml" if name.endswith(".yaml") else "text/markdown",
        headers={"X-Content-SHA256-16": sha.upper()[:16]},
    )


# ---------------------------------------------------------------------
# 接口一：/api/v1/kg/manifest（摘要；数字实读包内 manifest 件）
# ---------------------------------------------------------------------
@router.get("/api/v1/kg/manifest")
def kg_manifest(request: Request):
    got = _read_file("manifest.yaml")
    if got is None:
        return _unavailable("知识图谱包暂不可读（文档源异常，已按 fail-closed 暂停列出）")
    raw, sha = got
    return JSONResponse({
        "package": "TDCA Knowledge Graph V1 · Public",
        "sha256_16": sha.upper()[:16],
        "files": {n: (_read_file(n)[1].upper()[:16] if _read_file(n) else None)
                  for n in ("nodes.yaml", "edges.yaml", "README.md")},
    })


# ---------------------------------------------------------------------
# 接口二：/api/v1/kg/nodes?layer=&type=&q=&limit=
# ---------------------------------------------------------------------
@router.get("/api/v1/kg/nodes")
def kg_nodes(layer: str = "", type: str = "", q: str = "", limit: int = 200,
             request: Request = None):
    g = _load()
    if g is None:
        return _unavailable("知识图谱数据暂不可读（文档源异常，已按 fail-closed 暂停列出）")
    items = g["nodes"]
    if layer:
        items = [n for n in items if n.get("layer") == layer]
    if type:
        items = [n for n in items if n.get("type") == type]
    if q:
        items = [n for n in items if q.lower() in n.get("label", "").lower()]
    total = len(items)
    items = items[: max(1, min(limit, 1000))]
    return JSONResponse({"count": total, "returned": len(items), "nodes": items})


# ---------------------------------------------------------------------
# 接口三：/api/v1/kg/node/{node_id}
# ---------------------------------------------------------------------
@router.get("/api/v1/kg/node/{node_id}")
def kg_node(node_id: str, request: Request):
    g = _load()
    if g is None:
        return _unavailable("知识图谱数据暂不可读（文档源异常，已按 fail-closed 暂停列出）")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", node_id):
        return JSONResponse(with_code({"detail": "节点不存在"}, 404), status_code=404)
    n = g["by_id"].get(node_id)
    if n is None:
        return JSONResponse(with_code({"detail": "节点不存在"}, 404), status_code=404)
    out = g["edges"]
    rel_out = [e for e in out if e.get("source") == node_id]
    rel_in = [e for e in out if e.get("target") == node_id]
    by_id = g["by_id"]
    return JSONResponse({
        "node": n,
        "out_edges": [{"id": e["id"], "type": e["type"],
                       "target": by_id.get(e["target"], {}).get("label", e["target"])}
                      for e in rel_out],
        "in_edges": [{"id": e["id"], "type": e["type"],
                      "source": by_id.get(e["source"], {}).get("label", e["source"])}
                     for e in rel_in],
    })


# ---------------------------------------------------------------------
# 接口四：/api/v1/kg/subgraph?root=&depth=（depth 限 1~2）
# ---------------------------------------------------------------------
@router.get("/api/v1/kg/subgraph")
def kg_subgraph(root: str, depth: int = 1, request: Request = None):
    g = _load()
    if g is None:
        return _unavailable("知识图谱数据暂不可读（文档源异常，已按 fail-closed 暂停列出）")
    if root not in g["by_id"]:
        return JSONResponse(with_code({"detail": "节点不存在"}, 404), status_code=404)
    depth = 1 if depth not in (1, 2) else depth
    seen = {root}
    frontier = [root]
    sub_edges: list[dict] = []
    for _ in range(depth):
        nxt = []
        for e in g["edges"]:
            s, t = e.get("source"), e.get("target")
            if s in frontier and t not in seen:
                seen.add(t)
                nxt.append(t)
                sub_edges.append(e)
            elif t in frontier and s not in seen:
                seen.add(s)
                nxt.append(s)
                sub_edges.append(e)
        frontier = nxt
    by_id = g["by_id"]
    return JSONResponse({
        "root": root,
        "depth": depth,
        "nodes": [by_id[i] for i in sorted(seen)],
        "edges": sub_edges,
    })


# ---------------------------------------------------------------------
# 接口五：/api/v1/kg/edges?type=
# ---------------------------------------------------------------------
@router.get("/api/v1/kg/edges")
def kg_edges(type: str = "", limit: int = 500, request: Request = None):
    g = _load()
    if g is None:
        return _unavailable("知识图谱数据暂不可读（文档源异常，已按 fail-closed 暂停列出）")
    items = g["edges"]
    if type:
        items = [e for e in items if e.get("type") == type]
    total = len(items)
    items = items[: max(1, min(limit, 3000))]
    return JSONResponse({"count": total, "returned": len(items), "edges": items})
