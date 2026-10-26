# -*- coding: utf-8 -*-
"""
批3「门与闸」A块·缔约审核后端（TDCA-HANDOFF-EXEC-L1SI176-B3-GATE-001）：
/api/site/join/list（评审只读队列）。

- 前端契约冻结（/review 页现状）：字段名／五态枚举／路径一律照前端，⛔ 不改；
- 审核身份双通道（A-1 判据）：有效登录会话且角色 founder/operator；或有效 CRT 执行令牌
  ＋ x-tdca-reviewer 审核人标识头。无凭证 401；有凭证非审核身份 403（fail-closed）；
- ⛔ 不返回凭据值；display_name 为面客展示名（自然人敏感信息本就不入库）。

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

import auth
from db import get_session
from db import models as M

router = APIRouter(prefix="/api/site/join", tags=["site-join"])

# 审核人标识之 agent 形态前缀（代签轻防线；命中即拒）——A-2 复用
_AGENT_MARKERS = ("agent:", "agent-", "智能体:")


def reviewer_gate(request: Request) -> str:
    """审核身份闸：返回审核人标识（留痕用）。无凭证 401；非审核身份 403。"""
    raw = request.headers.get("authorization", "").strip()
    reviewer_hdr = request.headers.get("x-tdca-reviewer", "").strip()
    if not raw:
        raise HTTPException(401, "须登录会话（TDCA-SES）或 TDCA-CRT 令牌")
    if raw.startswith(auth.SESSION_PREFIX):
        v = auth.validate_session(raw)
        if not v["ok"]:
            raise HTTPException(401, "会话已过期，请重新登录" if v.get("expired") else "会话无效或已吊销")
        if v.get("role") not in ("founder", "operator"):
            raise HTTPException(403, "非审核身份（须创始人或运营者）")
        return v["username"]
    if auth._valid_crt_token(raw):
        if not reviewer_hdr:
            raise HTTPException(403, "非审核身份（须 x-tdca-reviewer 审核人标识）")
        if any(reviewer_hdr.lower().startswith(m) for m in _AGENT_MARKERS):
            raise HTTPException(403, "审核人标识不得为智能体形态（⛔ 代签）")
        return reviewer_hdr
    raise HTTPException(403, "凭证无效")


@router.get("/list")
def join_list(request: Request):
    """A-1 评审只读队列。未登录 401；非审核身份 403；空队列 200 items:[]。"""
    reviewer_gate(request)
    with get_session() as s:
        rows = (s.query(M.JoinRequest)
                .order_by(M.JoinRequest.id.desc())
                .all())
        items = [{
            "id": r.id,
            "display_name": r.display_name,
            "applicant_kind": r.applicant_kind,
            "channel": r.channel,
            "created_at": r.created_at,
            "status": r.status,
            "nsfl_result": r.nsfl_result,
            "reviewer_note": r.reviewer_note,
        } for r in rows]
    return {"items": items}
