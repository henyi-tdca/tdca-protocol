# -*- coding: utf-8 -*-
"""
A-23 公告栏：/api/v1/announcements/* —— 站点对外公告区。

口径（创始人 2026-10-04 明示）：
  - 本区只授权【建公告栏这一功能】；初始状态【空栏】——⛔ 不预置内容、
    ⛔ 不预置示例公告冒充正式公告；
  - 公告内容须创始人逐次明示后才可发布；发布入口仅 operator／founder，
    发布落 NCA 存证链（data_provenance=real）；
  - 对外纪律：零内部编号、零凭据值、零人名、零自然人敏感信息；
  - 公开读取（对外可见，无需登录）；写入口会话鉴权 fail-closed。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _nature_of, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])


@router.get("/list")
def announcements_list():
    """公告栏公开列表（对外可见；按发布时间倒序；初始空栏如实报 count=0）。"""
    with get_session() as s:
        rows = (s.query(M.Announcement)
                .order_by(M.Announcement.published_at.desc()).all())
    nature = _nature_of([r.data_provenance for r in rows]) if rows else "simulated"
    return _nca_watermark({
        "count": len(rows),
        "announcements": [{"announcement_id": r.announcement_id, "title": r.title,
                           "body": r.body, "published_at": r.published_at}
                          for r in rows],
        "note": "公告栏（对外公告区）——公告内容须经创始人明示后由运营发布；"
                "空栏为常态，不预置内容"},
        nature=nature)


class AnnouncementPublish(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    body: str


@router.post("/publish", status_code=201)
def announcement_publish(req: AnnouncementPublish, request: Request):
    """发布公告（operator／founder；落 NCA 存证链。⛔ 内容未经创始人明示不得发布）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可发布公告")
    title = req.title.strip() if req.title else ""
    body = req.body.strip() if req.body else ""
    if not title or not body:
        raise HTTPException(400, "title / body 不得为空")
    aid = f"AN-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("SiteAnnounce",
                          f"gateway:announcements/publish:{aid}",
                          artifact_path=f"announcements:{aid}", prov="real")
    with get_sessionmaker().begin() as s:
        s.add(M.Announcement(announcement_id=aid, title=title, body=body,
                             published_by=user.get("username"), nca_ref=nca_ref,
                             data_provenance="real", published_at=_utc()))
    return _nca_watermark({"announcement_id": aid, "title": title,
                           "nca_ref": nca_ref,
                           "note": "公告已发布并入存证链；对外纪律：零内部编号、"
                                   "零凭据值、零人名、零自然人敏感信息"},
                          nature="real")
