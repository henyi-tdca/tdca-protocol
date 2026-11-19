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


# ── A-2 审核写 ─────────────────────────────────────────────────────────────
from pydantic import BaseModel

from api_v1 import _nca_append, _utc  # noqa: E402


class ReviewReq(BaseModel):
    join_request_id: int
    action: str                # approve｜reject
    note: str | None = None


# 负空间敏感词初始清单（内置起步集；词库扩面另批，不影响本端点契约）。
# 每次「放行」复核展示名＋审核备注双扫，命中即 409 拦截、状态不变、NCA 留痕。
_NSFL_WORDS = (
    "洗钱", "诈骗", "赌博", "贩毒", "色情", "暴力催收",
    "传销", "非法集资", "走私", "制假", "盗号", "钓鱼网站",
)

_TRANSITIONS = {
    # 放行两段 pending→sandbox、sandbox→active；谢绝 →rejected（照令 §二 A-2 业务规则①）
    ("pending", "approve"): "sandbox",
    ("sandbox", "approve"): "active",
    ("pending", "reject"): "rejected",
    ("sandbox", "reject"): "rejected",
}


def _nsfl_hit(text: str) -> str | None:
    for w in _NSFL_WORDS:
        if w in (text or ""):
            return w
    return None


@router.post("/review")
def join_review(request: Request, req: ReviewReq):
    """A-2 审核写。每次操作落 NCA 存证（含审核人标识、动作、备注）。

    - 放行两段 pending→sandbox、sandbox→active；谢绝 →rejected；
    - 每次放行复核负空间敏感词清单，触负即 409 拦截：状态不变、NCA 留痕；
    - 重复审核同一单 → 409（本侧取 409 不取幂等：状态机会话已推进，重复即异常，
      理由随回报 R-4）；
    - ⛔ 令牌值不落库明文／不回显（令牌只在请求头校验，本端点不落任何凭据值）。
    """
    reviewer = reviewer_gate(request)
    if req.action not in ("approve", "reject"):
        raise HTTPException(400, "action 仅允许 approve｜reject")
    with get_session() as s:
        row = s.get(M.JoinRequest, req.join_request_id)
        if row is None:
            raise HTTPException(404, "申请单不存在")
        if req.action == "approve":
            hit = _nsfl_hit(row.display_name + "\n" + (req.note or ""))
            if hit:
                nca = _nca_append("join-review-nsfl-blocked", reviewer,
                                  artifact_path=f"join_requests/{row.id}", prov="real")
                row.reviewer_note = req.note
                row.nca_ref = nca
                row.updated_at = _utc()
                s.commit()
                raise HTTPException(409, f"触负拦截：命中负空间敏感词「{hit}」，状态未变")
        new_status = _TRANSITIONS.get((row.status, req.action))
        if new_status is None:
            raise HTTPException(409, f"当前状态 {row.status} 不允许 {req.action}（重复审核或已终态）")
        nca = _nca_append(f"join-review-{req.action}", reviewer,
                          artifact_path=f"join_requests/{row.id}", prov="real")
        row.status = new_status
        row.reviewer_note = req.note
        row.nca_ref = nca
        row.updated_at = _utc()
        s.commit()
        return {"ok": True, "id": row.id, "status": row.status, "nca_ref": nca}
