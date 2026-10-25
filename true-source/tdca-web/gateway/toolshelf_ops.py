# -*- coding: utf-8 -*-
"""
P4 工具货架（A-15）：/api/v1/toolshelf/* —— 站内工具/模板目录（编译器、适配器等）。

口径：上架工具如实标 requires_grant（配置类工具 = 调用须过 P2 准入闸门）；
      模板区是否加授权件模板为延后定事项，本期不做（如实列未做项）。
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

router = APIRouter(prefix="/api/v1/toolshelf", tags=["toolshelf"])

# 匿名面脱敏：内部件号/存证指针/凭据措辞，任一命中即不列（fail-closed）
_CATALOG_SENSITIVE = re.compile(
    r"\b(TL|FC|CI)-[A-Z0-9]|GSEQ-\d+|L1SI\d+|NCA-|TDCA-CRT|TDCA-SES|"
    r"(密码|口令|token|secret|凭据)", re.IGNORECASE)
_CATALOG_PURPOSE_LEN = 80


def _one_line_purpose(description: str) -> str:
    """一句用途：取 description 首句（。！？!?换行截断），超 80 字截断。"""
    text = (description or "").strip()
    if not text:
        return ""
    first = re.split(r"[。！？!?；;\n]", text, maxsplit=1)[0].strip()
    return first[:_CATALOG_PURPOSE_LEN]


@router.get("/catalog")
def tool_catalog(request: Request):
    """匿名货架清单（L1SI175-B1 S1-2）：只返 name ＋ 一句用途 ＋ category。

    ⛔ 不含 tool_id / version / requires_grant / nca_ref（内部编号、凭据态与存证指针不出）；
    名称或用途命中脱敏正则者整件不列（fail-closed）。上架与详情仍须登录。"""
    with get_session() as s:
        rows = s.query(M.ToolItem).order_by(M.ToolItem.created_at).all()
    out = []
    for r in rows:
        purpose = _one_line_purpose(r.description)
        if _CATALOG_SENSITIVE.search(r.name or "") or _CATALOG_SENSITIVE.search(purpose):
            continue
        out.append({"name": r.name, "category": r.category, "purpose": purpose})
    return _nca_watermark({
        "count": len(out),
        "tools": out,
        "note": "工具货架公开目录（只列名称、类目与一句用途；"
                "不含内部编号、版本与调用凭据信息）"})


@router.get("/list")
def tool_list(request: Request, category: str = ""):
    """货架列表（可按类目过滤：compiler/adapter/template/other）。"""
    _require_session_user(request)
    with get_session() as s:
        q = s.query(M.ToolItem).order_by(M.ToolItem.created_at)
        if category:
            if category not in ("compiler", "adapter", "template", "other"):
                raise HTTPException(400, "category 过滤值非法")
            q = q.filter_by(category=category)
        rows = q.all()
    return _nca_watermark({
        "count": len(rows),
        "tools": [{"tool_id": r.tool_id, "name": r.name, "category": r.category,
                   "description": r.description, "version": r.version,
                   "requires_grant": bool(r.requires_grant), "status": r.status,
                   "nca_ref": r.nca_ref}
                  for r in rows],
        "note": "工具货架（内部目录；requires_grant=true 的配置类工具须过准入闸门）"})


class ToolRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    category: str = ""            # compiler/adapter/template/other
    description: str = ""
    version: str = ""
    requires_grant: bool = False


@router.post("/register", status_code=201)
def tool_register(req: ToolRegister, request: Request):
    """工具上架（operator/founder；类目闭集机验；配置类如实标记）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可上架工具")
    if not req.name or not req.name.strip():
        raise HTTPException(400, "name 不得为空")
    if req.category not in ("compiler", "adapter", "template", "other"):
        raise HTTPException(400, "category 须为 compiler / adapter / template / other")
    tid = f"TL-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("TOOL_REGISTER", user["username"],
                          artifact_path=f"toolshelf:{tid}")
    with get_sessionmaker().begin() as s:
        s.add(M.ToolItem(
            tool_id=tid, name=req.name.strip(), category=req.category,
            description=req.description or None, version=req.version or None,
            requires_grant=1 if req.requires_grant else 0,
            status="available", nca_ref=nca_ref, created_at=_utc()))
    return _nca_watermark({"tool_id": tid, "name": req.name.strip(),
                           "category": req.category, "nca_ref": nca_ref,
                           "requires_grant": req.requires_grant,
                           "note": "工具已上架（NCA 存证；配置类调用须凭授权件过准入闸门）"})
# 模板区：授权件模板（AMEND-002 更正两件——引用在仓《授权件模板》三件，不复制正文）
# 唯一权威源 = docs/regulations/ 之 TDCA-TEMPLATE-AUTH-001（中／英／机读）；
# ⛔ 与 docs/register-contract/ 之 TDCA-OWNER-CONTRACT-AUTH-001（所有者缔约授权书）
#    名近而用途不同，不可互替——本端不引用后者。
# 版本：读件内真实值（机读版 version 字段，现 V0.1-DRAFT），⛔ 不硬编码；
# 「生效」另以在仓注记件为准（TDCA-TEMPLATE-AUTH-001-生效注记.md → V1.0-FROZEN），
# 两者分别标注来源，⛔ 不得合并成单一字样。
# =====================================================================

from pathlib import Path as _Path  # noqa: E402
import re as _re  # noqa: E402

_TEMPLATE_DIR = _Path(__file__).resolve().parents[3] / "docs" / "regulations"
_TEMPLATE_FILES = (
    ("zh", "TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版V0.1-DRAFT·四要件与固定格式八字段）.md"),
    ("en", "TDCA-TEMPLATE-AUTH-001-授权件模板（英文人读版V0.1-DRAFT）.md"),
    ("machine", "TDCA-TEMPLATE-AUTH-001-授权件模板（机读版V0.1-DRAFT）.yaml"),
)
_EFFECTIVE_NOTE = "TDCA-TEMPLATE-AUTH-001-生效注记.md"


def _version_from_machine(machine_text: str) -> str:
    """读件内真实版本（机读版 version 字段）——⛔ 不硬编码。"""
    m = _re.search(r"^version:\s*(\S+)", machine_text, _re.MULTILINE)
    return m.group(1) if m else "UNKNOWN（机读版缺 version 字段——如实报，不猜）"


def _effective_from_note() -> dict:
    """生效信息取自仓注记件（V1.0-FROZEN·范围期一内部运行）；缺件如实报。"""
    fpath = _TEMPLATE_DIR / _EFFECTIVE_NOTE
    if not fpath.is_file():
        return {"effective": "UNKNOWN", "source": f"docs/regulations/{_EFFECTIVE_NOTE}（缺失）"}
    m = _re.search(r"(V\d+\.\d+-FROZEN)", fpath.read_text(encoding="utf-8"))
    return {"effective": m.group(1) if m else "UNKNOWN",
            "source": f"docs/regulations/{_EFFECTIVE_NOTE}"}


@router.get("/template/auth-contract")
def template_auth_contract(request: Request):
    """授权件模板（四要件＋固定格式八字段）——实时引用在仓三件，可查看/可下载。"""
    _require_session_user(request)
    import hashlib
    files = []
    version = None
    for lang, fname in _TEMPLATE_FILES:
        fpath = _TEMPLATE_DIR / fname
        if not fpath.is_file():
            raise HTTPException(503, f"TEMPLATE_UNAVAILABLE: 在仓件缺失 {fname}"
                                     "（不另存副本——修复仓内件后方可引用）")
        raw = fpath.read_bytes()
        text = raw.decode("utf-8")
        if lang == "machine":
            version = _version_from_machine(text)
        files.append({"lang": lang, "filename": fname, "content": text,
                      "sha256_8": hashlib.sha256(raw).hexdigest()[:8],
                      "bytes": len(raw)})
    effective = _effective_from_note()
    return _nca_watermark({
        "template": "授权件模板（四要件：场景约束／五阶资产形态／全构成已授权／法律主体签名）",
        "version": version,
        "version_source": "机读版件内 version 字段（逐字读取，非硬编码）",
        "effective_status": effective["effective"],
        "effective_source": effective["source"] + "（GSEQ-3626 创始人签批；范围＝期一内部运行）",
        "authority": "docs/regulations/（在仓《授权件模板》TDCA-TEMPLATE-AUTH-001 三件为唯一权威源；"
                     "与 TDCA-OWNER-CONTRACT-AUTH-001 所有者缔约授权书不可互替，本端不引用后者）",
        "files": files,
        "note": "引用在仓、逐字一致；⛔ 不自创字段；智能体不得代签、不得代持代填"})
