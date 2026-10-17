# -*- coding: utf-8 -*-
"""
手册接口化（TDCA-HANDOFF-OPS-INACCOUNT-DEPLOY-001 块 2）：/api/v1/ops/files/* ——
运维手册与制度改由接口按角色出件，站内渲染直读（撤 /ops/files/ 静态门后唯一取件口）。

- GET /api/v1/ops/files：白名单清单（在册 7 件·带 sha256_16，现读现算可核）；
- GET /api/v1/ops/files/{name}：按名出件——⛔ 防穿越（含 / \\ .. 即 400）／⛔ 只许白名单内件（否则 404）；
- 会话 401 fail-closed＋operator/founder 403（照 /api/v1/ops/* 既有惯例）；
- 文件在容器内只读挂载（OPS_FILES_DIR 环境变量，⛔ 不在 web 根、不经 nginx 静态）；
- md → text/markdown；yaml → application/yaml；charset=utf-8；
- ⛔ 运维件不进公域文库、⛔ 不入主仓（照 GSEQ-5005/5007）；新增件须登记白名单并留痕。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response

from api_v1 import _nca_watermark, _require_session_user  # noqa: E402

router = APIRouter(prefix="/api/v1/ops/files", tags=["ops-files"])

# ── 在册白名单（= /ops/files 固定索引页登记之七件；新增件须同步本清单＋留痕）──
# 键＝服务器件名（逐字节照 ops-files 目录实登）；值＝人读短标签
_WHITELIST: dict[str, str] = {
    "TDCA-MAN-SITE-PHASE2-OPS-001-V1.0-二期站点建设运维手册（定稿·四类运维分则与TLS生命周期·两项主职为主线四类为分类轴·V1.0-FROZEN）.md": "运维手册（人读定稿 V1.0-FROZEN）",
    "TDCA-MAN-SITE-PHASE2-OPS-001-MACHINE-V1.0-二期站点建设运维制度机读版（四类分则与TLS生命周期与十三条归位·V1.0-FROZEN）.md": "运维制度（机读定稿 V1.0-FROZEN）",
    "TDCA-TPL-OPS-LOG-001-运维日志模板（每日填写·四类运维对应·异常三段闭合·人读）.md": "运维日志模板（人读）",
    "TDCA-TPL-OPS-LOG-001-MACHINE-运维日志模板机读版（字段定义与八条校验·供表单化）.md": "运维日志模板（机读）",
    "TDCA-STD-SITE-INGEST-TRAIL-001-内容入站脱敏复扫与拒绝清单每批留痕制度（V1.0-FROZEN·已签批生效·人读版）.md": "入站留痕制度（人读 V1.0-FROZEN）",
    "TDCA-STD-SITE-INGEST-TRAIL-001-内容入站每批留痕制度（V1.0-FROZEN·机读版）.yaml": "入站留痕制度（机读 yaml）",
    "TDCA-SIGNOFF-STD-SITE-INGEST-TRAIL-001-签批落地件（内容入站每批留痕制度V1.0-FROZEN生效·双版本齐·即刻起适用）.md": "入站留痕制度（签批落地件）",
}

_MIME = {".md": "text/markdown", ".yaml": "application/yaml", ".yml": "application/yaml"}
_TRAVERSAL_TAINT = ("/", "\\", "..", "\x00")


def _files_dir() -> Path:
    return Path(os.environ.get("OPS_FILES_DIR", "/var/lib/tdca-ops-files"))


def _require_ops_admin(request: Request) -> dict:
    """运维门内：会话（401 fail-closed）＋ operator/founder（403）——照 /api/v1/ops/* 既有惯例。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可取运维件")
    return user


@router.get("")
def list_files(request: Request):
    """在册七件清单（现读现算 sha256_16；缺件如实标 missing，⛔ 不伪造）。"""
    _require_ops_admin(request)
    d = _files_dir()
    items = []
    for name, label in _WHITELIST.items():
        p = d / name
        if not p.is_file():
            items.append({"name": name, "label": label, "missing": True})
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16].upper()
        items.append({"name": name, "label": label, "sha256_16": digest,
                      "bytes": p.stat().st_size, "missing": False})
    return _nca_watermark({"total": len(_WHITELIST), "files": items,
                           "note": "在册 7 件人工登记（⛔ 不自动列举）；新增件须登记白名单并留痕"})


@router.get("/{name}")
def get_file(name: str, request: Request):
    """按名出件：白名单精确匹配；穿越形串先 400，白名单外 404（⛔ 不泄露目录信息）。"""
    _require_ops_admin(request)
    if any(t in name for t in _TRAVERSAL_TAINT):
        raise HTTPException(400, "非法件名（⛔ 拒绝穿越形串）")
    label = _WHITELIST.get(name)
    if label is None:
        raise HTTPException(404, "件不在白名单（未登记之件不出件）")
    p = _files_dir() / name
    if not p.is_file():
        raise HTTPException(404, "在册件缺失（登记在册但文件不在，报运维负责人补挂）")
    content = p.read_bytes()
    media = _MIME.get(p.suffix.lower(), "application/octet-stream")
    from urllib.parse import quote
    return Response(content, media_type=f"{media}; charset=utf-8",
                    headers={"Content-Disposition":
                             f"inline; filename*=UTF-8''{quote(name)}"})
