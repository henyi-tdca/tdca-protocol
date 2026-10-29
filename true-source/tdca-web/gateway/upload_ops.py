# -*- coding: utf-8 -*-
"""「用」组 U-1 素材上传（USE-U1-001）：/api/v1/use/upload（POST 单文件）＋ /api/v1/use/upload/{id}（GET）。

口径（照开工令）：
  - 存储＝本地目录（容器 /data/uploads 卷，与 tdca.db 同卷、⛔ 不改部署形态）＋逐件哈希清单（本表即清单）；
  - 文件名＝哈希前段（天然防重：同人同件不重复落盘；同人同件重复传 → 返回既有记录）；
  - 归属＝登录账号（_require_session_user，⛔ 匿名不可上传；本面 ⛔ 不做公开匿名面）；
  - 受理＝十类／拒收＝五类（清单为执行侧暂代表：在册清单未于仓面与信箱检得——见回报照报；
    全部集中于 _ACCEPT_CATEGORIES/_REJECT_CATEGORIES 两常量，智库换表只动这两处）；
  - 拒收回一句人话理由（⛔ 只给错误码）；
  - 每次上传落一条站内留痕（谁、何时、多大、哈希）＋NCA 存证回链；
  - 原始报文直读（request.body()）：⛔ 不引 python-multipart（S-2 新增依赖停手线）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import IntegrityError

from db import get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/use", tags=["use-u1-upload"])

# 存储目录：容器内 /data 卷（tdca.db 同卷；宿主机 /var/lib/docker/volumes/deploy_tdca-db/_data/uploads）
UPLOAD_DIR = Path("/data/uploads")

# 单件上限（执行侧裁量；回报载明，待在册口径替换）
MAX_BYTES = 20 * 1024 * 1024

# ─────────────────────────────────────────────────────────────────────
# 受理十类（暂代表；智库在册清单下换只动此处）
# ─────────────────────────────────────────────────────────────────────
_ACCEPT_CATEGORIES = {
    "文本文档": {".md", ".markdown", ".txt"},
    "版式文档": {".pdf"},
    "演示文稿": {".pptx"},
    "数据表格": {".csv", ".tsv"},
    "结构化数据": {".json"},
    "制度配置": {".yaml", ".yml"},
    "图像": {".png", ".jpg", ".jpeg", ".gif", ".webp"},
    "音频": {".mp3", ".wav", ".flac", ".ogg"},
    "压缩包": {".zip"},
    "矢量与字体": {".svg", ".ttf", ".woff", ".woff2"},
}

# 拒收五类（理由必须人话；扩展名判类 fail-closed：不认识的扩展名一律拒收）
_REJECT_RULES = [
    (".exe .dll .com .msi .app .apk", "这类文件不受理：可执行程序存在安全风险，站方不收。"),
    (".sh .bash .bat .cmd .ps1 .py", "这类文件不受理：脚本命令不在素材受理范围。"),
]


def _classify(filename: str, size: int) -> tuple[str | None, str | None]:
    """返回 (受理类别, None) 或 (None, 人话拒收理由)。空件/超限/未知类各自成类。"""
    if size == 0:
        return None, "空文件没有内容——请确认选对了文件再传。"
    if size > MAX_BYTES:
        return None, f"文件超过 {MAX_BYTES // (1024 * 1024)}MB 上限——请先压缩分包，或联系站方人工受理。"
    ext = Path(filename).suffix.lower()
    for category, exts in _ACCEPT_CATEGORIES.items():
        if ext in exts:
            return category, None
    for ext_list, reason in _REJECT_RULES:
        if ext in ext_list.split():
            return None, reason
    if not ext:
        return None, "看不出文件类型——请把文件转成常见格式（文档/数据/图像/音频/压缩包）再传。"
    return None, ("这类文件暂不受理——当前只收十类常见素材（文档、数据、图像、音频、压缩包等）；"
                  "如确需提交此类件，请联系站方人工受理。")


_FILENAME_SAFE = re.compile(r"[^0-9A-Za-z._\-\u4e00-\u9fff（）()]")


def _sanitize_filename(raw: str) -> str:
    """取路径末段（⛔ 目录穿越）：先解百分号编码（前端 encodeURIComponent），
    只留基名，剔不安全字符，限长。"""
    from urllib.parse import unquote
    name = unquote(raw or "")
    name = name.replace("\\", "/").rsplit("/", 1)[-1].strip() or "unnamed"
    name = _FILENAME_SAFE.sub("_", name)
    return name[:128]


def _view(r: M.UploadRecord) -> dict:
    return {
        "upload_id": r.upload_id,
        "sha256": r.sha256,
        "sha256_16": r.sha256_16,
        "size_bytes": r.size_bytes,
        "original_filename": r.original_filename,
        "accept_category": r.accept_category,
        "owner": r.username,            # 归属＝登录账号（本面登录可见；⛔ 公开匿名面）
        "stored_name": Path(r.stored_path).name,
        "nca_ref": r.nca_ref,
        "uploaded_at": r.created_at,
    }


@router.post("/upload")
async def use_upload(request: Request):
    """交素材（单文件直传：请求体＝文件字节；文件名走 X-Upload-Filename 头）。

    幂等：同哈希同归属 → 返回既有记录（duplicate=true，⛔ 不多落一条）。
    """
    user = _require_session_user(request)  # 未登录 401（fail-closed）
    body = await request.body()
    filename = _sanitize_filename(request.headers.get("x-upload-filename", ""))
    category, reject_reason = _classify(filename, len(body))
    if reject_reason:
        raise HTTPException(400, reject_reason)  # 人话理由（⛔ 只给码）

    sha = hashlib.sha256(body).hexdigest()
    sha16 = sha.upper()[:16]
    ext = Path(filename).suffix.lower()
    stored_path = UPLOAD_DIR / f"{sha16}{ext}"

    try:
        with get_sessionmaker().begin() as s:
            existing = s.query(M.UploadRecord).filter_by(sha256=sha, username=user["username"]).one_or_none()
            if existing is not None:
                # 幂等返回：同哈希同归属不重复落盘、不多一条
                return _nca_watermark({**_view(existing), "duplicate": True,
                                       "note": "同一件已收过——返回既有记录，未重复落盘。"}, nature="real")
            upload_id = f"UPL-{uuid.uuid4().hex[:12].upper()}"
            nca_ref = _nca_append("USE_U1_UPLOAD", user["username"],
                                  artifact_path=f"upload:{upload_id}/sha256:{sha16}",
                                  prov="real")
            s.add(M.UploadRecord(
                upload_id=upload_id, username=user["username"],
                sha256=sha, sha256_16=sha16, size_bytes=len(body),
                original_filename=filename, accept_category=category,
                stored_path=str(stored_path), nca_ref=nca_ref,
                data_provenance="real", created_at=_utc()))
    except IntegrityError:
        # D-1 同式：并发同件提交期撞 uq(sha256,username) → 归一幂等返回既有记录
        with get_sessionmaker().begin() as s:
            existing = s.query(M.UploadRecord).filter_by(sha256=sha, username=user["username"]).one()
            return _nca_watermark({**_view(existing), "duplicate": True,
                                   "note": "同一件已收过——返回既有记录，未重复落盘。"}, nature="real")

    # 磁盘防重：同人同件已写过则跳过（不同人同件共用同一哈希文件，天然防重）
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        if not stored_path.exists():
            stored_path.write_bytes(body)
    except OSError as e:
        raise HTTPException(500, f"落盘失败：{e.__class__.__name__}（已留痕，请联系站方核查）")

    with get_sessionmaker().begin() as s:
        rec = s.get(M.UploadRecord, upload_id)
        return _nca_watermark({**_view(rec), "duplicate": False,
                               "note": "已收到——下一步：提交登记材料（权属/授权登记）。"},
                              nature="real")


@router.get("/upload/{upload_id}")
def use_upload_get(upload_id: str, request: Request):
    """回读一件：哈希、大小、归属、时间（上传者本人或 founder/operator 可见）。"""
    user = _require_session_user(request)
    with get_sessionmaker().begin() as s:
        rec = s.get(M.UploadRecord, upload_id)
        if rec is None:
            raise HTTPException(404, "没有这件——请核对编号（或它还没传上来）。")
        if rec.username != user["username"] and user["role"] not in ("founder", "operator"):
            raise HTTPException(403, "只能回读自己传的件。")
        return _nca_watermark(_view(rec), nature="real")


# GET /upload 路径方法守卫：裸 GET 集合面本令未开（⛔ 不做列表公开面）
@router.get("/upload")
def use_upload_get_method_guard():
    raise HTTPException(404, "该端点未上线或不存在")
