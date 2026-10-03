# -*- coding: utf-8 -*-
"""
P4 工具货架（A-15）：/api/v1/toolshelf/* —— 站内工具/模板目录（编译器、适配器等）。

口径：上架工具如实标 requires_grant（配置类工具 = 调用须过 P2 准入闸门）；
      模板区是否加授权件模板为延后定事项，本期不做（如实列未做项）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/toolshelf", tags=["toolshelf"])


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
                   "requires_grant": bool(r.requires_grant), "status": r.status}
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
    with get_sessionmaker().begin() as s:
        s.add(M.ToolItem(
            tool_id=tid, name=req.name.strip(), category=req.category,
            description=req.description or None, version=req.version or None,
            requires_grant=1 if req.requires_grant else 0,
            status="available", created_at=_utc()))
    return _nca_watermark({"tool_id": tid, "name": req.name.strip(),
                           "category": req.category,
                           "requires_grant": req.requires_grant,
                           "note": "工具已上架（配置类调用须凭授权件过准入闸门）"})
