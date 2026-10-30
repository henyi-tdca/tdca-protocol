# -*- coding: utf-8 -*-
"""「用」组 U-1 素材上传（USE-U1-001）：/api/v1/use/upload（POST 单文件）＋ /api/v1/use/upload/{id}（GET）。

口径（照开工令）：
  - 存储＝本地目录（容器 /data/uploads 卷，与 tdca.db 同卷、⛔ 不改部署形态）＋逐件哈希清单（本表即清单）；
  - 文件名＝哈希前段（天然防重：同人同件不重复落盘；同人同件重复传 → 返回既有记录）；
  - 归属＝登录账号（_require_session_user，⛔ 匿名不可上传；本面 ⛔ 不做公开匿名面）；
  - 受理＝十类／拒收＝五类（清单照录在册：TDCA-HANDOFF-EXEC-L1SI182-USE-U2-001 §三／§四——
    此前暂代表由本令补齐原文替换；⛔ 自行增删十类／五类）；
  - 拒收回一句人话理由（⛔ 只给错误码）；
  - 通用硬约束照在册：件名 ≤ 110 字符／⛔ 路径穿越（..）／⛔ 绝对路径／文本类须 UTF-8 可解；
  - 拒收第 3 类（加密包）以 stdlib 启发检测（zip 加密位／PDF /Encrypt），检不出则收并照记非完备；
  - 拒收第 5 类（未脱敏个人信息）对文本类件做成批模式粗检（身份证／手机号 ≥3 处即退），照记非完备；
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

# ─────────────────────────────────────────────────────────────────────
# 受理十类（照录在册 USE-U2-001 §三；⛔ 增删；上限＝在册单件上限）
# 注：机读件类（.yaml/.json machine 类）与结构化类扩展名重叠，机读规范件仓面未检得——
#     收件层按结构化数据受理，规范到后换表（差额照报）；「大件走分片」为处理管线层，非收件层。
# ─────────────────────────────────────────────────────────────────────
_MB = 1024 * 1024
_ACCEPT_CATEGORIES: dict[str, tuple[set[str], int]] = {
    "文本文档": ({".md", ".txt", ".rtf", ".html"}, 20 * _MB),
    "办公文档": ({".docx", ".doc", ".odt", ".pdf"}, 50 * _MB),
    "表格": ({".csv", ".tsv", ".xlsx", ".xls"}, 50 * _MB),
    "结构化数据": ({".json", ".yaml", ".yml", ".xml"}, 20 * _MB),
    "代码／规范": ({".py", ".ts", ".js", ".go", ".lean", ".sol", ".sql", ".sh"}, 20 * _MB),
    "图片": ({".png", ".jpg", ".jpeg", ".webp", ".gif"}, 20 * _MB),
    "音频": ({".mp3", ".wav", ".m4a"}, 200 * _MB),
    "视频": ({".mp4", ".mov", ".webm"}, 500 * _MB),
    "数据集": ({".zip", ".tar.gz"}, 2 * 1024 * _MB),
}

# 文本类（须 UTF-8 可解＋个人信息粗检的扩展名，⛔ 二进制不解码）
_TEXT_EXTS = ({".md", ".txt", ".rtf", ".html", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml",
               ".py", ".ts", ".js", ".go", ".lean", ".sol", ".sql", ".sh"})

# 拒收五类（照录在册 USE-U2-001 §四；理由必人话；扩展名判类 fail-closed：不认识的扩展名一律拒收）
# 第 4 类（外链下载式）无扩展名可判——属语义层，由 U-2 代办机器人收件步拦（只给链接不给件 → 人话退回）。
_REJECT_RULES = [
    ({".exe", ".dll", ".so", ".msi", ".apk", ".scr", ".bat", ".cmd", ".ps1"},
     "这类文件不受理：可执行程序存在安全风险，站内不执行任何上传物。"),
    ({".docm", ".xlsm", ".pptm"},
     "这类文件不受理：带宏文档的宏就是可执行代码，站方不收。"),
]

# 在册通用硬约束
_NAME_MAX = 110           # 件名 ≤ 110 字符
_PII_PATTERNS = (re.compile(r"\b\d{17}[\dXx]\b"), re.compile(r"\b1[3-9]\d{9}\b"))  # 身份证／手机号
_PII_BATCH_MIN = 3        # 成批：≥3 处即退（照「成批」口径的执行侧判据，照报）


def _ext_of(filename: str) -> str:
    name = filename.lower()
    return ".tar.gz" if name.endswith(".tar.gz") else Path(name).suffix


def _classify(filename: str, body: bytes) -> tuple[str | None, str | None]:
    """返回 (受理类别, None) 或 (None, 人话拒收理由)。空件／超限／拒收类／未知类各自成类。"""
    size = len(body)
    if size == 0:
        return None, "空文件没有内容——请确认选对了文件再传。"
    ext = _ext_of(filename)
    category: str | None = None
    cap = 0
    for cat, (exts, cap_bytes) in _ACCEPT_CATEGORIES.items():
        if ext in exts:
            category, cap = cat, cap_bytes
            break
    if category is not None and size > cap:
        return None, (f"这件属于「{category}」，单件上限 {cap // _MB}MB——"
                      f"超了的请先压缩分包，或联系站方人工受理。")
    # 拒收第 1／2 类（扩展名直判）
    for exts, reason in _REJECT_RULES:
        if ext in exts:
            return None, reason
    # 拒收第 3 类（加密／密码保护包，stdlib 启发检测，检不出则收——非完备照报）
    if category is not None:
        if ext in (".zip", ".tar.gz") and _looks_encrypted_archive(body):
            return None, "这类文件不受理：加密或密码保护的压缩包无法校验内容，就无法存证。"
        if ext == ".pdf" and _looks_encrypted_pdf(body):
            return None, "这类文件不受理：加密或密码保护的 PDF 无法校验内容，就无法存证。"
        # 拒收第 5 类（成批未脱敏个人信息，仅文本类粗检——非完备照报）
        if ext in _TEXT_EXTS:
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                return None, ("这件按「{}」受理，但内容不是 UTF-8 编码——请转成 UTF-8 再传。".format(category))
            hits = sum(len(p.findall(text)) for p in _PII_PATTERNS)
            if hits >= _PII_BATCH_MIN:
                return None, ("这件里似乎有成批的身份证号／手机号——请先脱敏（删掉或打码）再传。")
        return category, None
    # 不在十类内
    if not ext:
        return None, "看不出文件类型——请把文件转成常见格式（文档、数据、图像、音频、压缩包）再传。"
    return None, ("这类文件暂不受理——当前只收十类常见素材（文档、办公件、表格、数据、代码、图像、音频、视频、数据集）；"
                  "如确需提交此类件，请联系站方人工受理。")


def _looks_encrypted_archive(body: bytes) -> bool:
    """zip 加密位（通用标志 bit0）检测；tar.gz 不解包不判（交处理管线层）。"""
    if body[:4] != b"PK\x03\x04":
        return False  # 非 zip（含伪 zip）不据_extension 误判
    try:
        flag = int.from_bytes(body[6:8], "little")
    except Exception:
        return False
    return bool(flag & 0x1)


def _looks_encrypted_pdf(body: bytes) -> bool:
    """PDF /Encrypt 条粗扫（首 8KB＋尾 8KB）。"""
    if not body.startswith(b"%PDF"):
        return False
    head, tail = body[:8192], body[-8192:] if len(body) > 8192 else body
    return b"/Encrypt" in head or b"/Encrypt" in tail


_FILENAME_SAFE = re.compile(r"[^0-9A-Za-z._\-\u4e00-\u9fff（）()]")


def _check_and_clean_filename(raw: str) -> tuple[str | None, str | None]:
    """在册通用硬约束 fail-closed：件名 ≤ 110 字符／⛔ 路径穿越（..）／⛔ 绝对路径。
    返回 (净名, None)；违例返回 (None, 人话理由)。先解百分号编码（前端 encodeURIComponent）。"""
    from urllib.parse import unquote
    name = unquote(raw or "").strip()
    if not name:
        return "unnamed", None
    # 路径穿越／绝对路径：任何分隔符或 .. 段都拒（不取末段放过——在册口径是拒，不是截）
    if "/" in name or "\\" in name:
        return None, "文件名里带路径——请只填文件本身的名称（不要带目录）。"
    if ".." in name:
        return None, "文件名含「..」——为防路径穿越，请改名后再传。"
    if len(name) > _NAME_MAX:
        return None, f"文件名超过 {_NAME_MAX} 字符——请改短后再传。"
    return _FILENAME_SAFE.sub("_", name), None


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
    filename, name_error = _check_and_clean_filename(request.headers.get("x-upload-filename", ""))
    if name_error:
        raise HTTPException(400, name_error)  # 人话理由（⛔ 只给码）
    category, reject_reason = _classify(filename or "unnamed", body)
    if reject_reason:
        raise HTTPException(400, reject_reason)  # 人话理由（⛔ 只给码）

    sha = hashlib.sha256(body).hexdigest()
    sha16 = sha.upper()[:16]
    ext = _ext_of(filename or "")
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
