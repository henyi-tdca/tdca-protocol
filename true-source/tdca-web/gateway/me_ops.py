# -*- coding: utf-8 -*-
"""
L1SI214-TOKEN-B1-001 批1只读两端点（A: GET /me/tokens ／ B: GET /me/permissions）。

口径（施工令 TDCA-HANDOFF-EXEC-L1SI214-TOKEN-B1-001）：
- 只返回本人：按会话身份取，⛔ 接受任何 ?user= 之类参数——带任何查询参数即 404
  （越权查他人 ⛔ 403，避免泄露存在性；S-3）。
- 令牌值一律不回显：响应只给 token_hash 前 4 + ****（S-2）；令牌值不入件不入日志。
- 无令牌 → 空数组 ＋ count: 0（⛔ 报错、⛔ 404）。
- 未登录 → 401（_require_session_user fail-closed；S-6）。
- permissions 的 matrix 由 perm_table.build_permissions 从权限点表直接生成（S-4/S-5）。
- 两端点为叠加（⛔ 替换鉴权主流程）；role 沿用三值枚举（⛔ 新造）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_watermark, _require_session_user  # noqa: E402
from me_audit import audit_token_revoke  # noqa: E402
from perm_table import build_permissions  # noqa: E402

router = APIRouter(prefix="/api/v1/me", tags=["me"])


def _reject_query_params(request: Request) -> None:
    """本端点无参数：带任何查询参数（含 ?user= 之类）一律 404（S-3，⛔ 403）。"""
    if request.query_params:
        raise HTTPException(404, "Not Found")


def _tokens_payload(username: str) -> dict:
    """本人名下令牌清单（sessions 表按 username 归属；单会话制下旧会话 revoked=1 照列）。"""
    now = datetime.now(timezone.utc)
    with get_session() as s:
        rows = (s.query(M.AuthSession)
                .filter(M.AuthSession.username == username)
                .order_by(M.AuthSession.created_at).all())
    tokens = []
    for r in rows:
        expired = datetime.fromisoformat(str(r.expires_at).replace("Z", "+00:00")) <= now
        status = "revoked" if r.revoked else ("expired" if expired else "active")
        # ⭐ id 脱敏：token_hash 前 4 + ****；令牌值与全量哈希一律不回显（S-2）
        tokens.append({
            "id": r.token_hash[:4] + "****",
            "kind": "session",
            "issued_at": r.created_at,
            "expires_at": r.expires_at,
            "last_used_at": None,
            "status": status,
            "bound_agents": [],
            "note": None,
        })
    return {"tokens": tokens, "count": len(tokens), "scope": "self"}


@router.get("/tokens")
def me_tokens(request: Request):
    """A 项：列本人名下令牌（⛔ 参数；⛔ 他人；⛔ 令牌值回显）。"""
    _reject_query_params(request)
    v = _require_session_user(request)
    return _nca_watermark(_tokens_payload(v["username"]), nature="real")


@router.get("/permissions")
def me_permissions(request: Request):
    """B 项：列本人权限清单（matrix 由权限点表直接生成；逐项带依据）。"""
    _reject_query_params(request)
    v = _require_session_user(request)
    return _nca_watermark(build_permissions(v["role"]), nature="real")


_MASKED_ID = re.compile(r"[0-9a-f]{4}\*{4}")


@router.delete("/tokens/{tid}")
def me_token_revoke(tid: str, request: Request):
    """批2 A 项：吊销本人令牌（软删 revoked=1，⛔ 物理删除；幂等；越权/不存在一律 404）。

    · 只能吊销本人：按会话身份过滤 username，⛔ 接受任何 user/owner 类参数（带参 404）。
    · {id} 即批 1 脱敏形（token_hash 前 4 + ****）；非此形或不属本人或不存在 ⟹ 404
      （与「令牌不存在」同码，⛔ 403，免泄露存在性）。
    · 幂等：重复吊销同一 id 返回 200、result=already_revoked、行状态保持 revoked=1。
    · 留痕：每次调用写 nca_chain 一条（操作者/被吊销令牌 id 脱敏/时点/结果，⛔ 记值）。
    """
    _reject_query_params(request)
    v = _require_session_user(request)
    me = v["username"]
    if not _MASKED_ID.fullmatch(tid):
        raise HTTPException(404, "Not Found")
    with get_sessionmaker().begin() as s:
        rows = (s.query(M.AuthSession)
                .filter(M.AuthSession.username == me,
                        M.AuthSession.token_hash.like(tid[:4] + "%"))
                .all())
        if not rows:
            raise HTTPException(404, "Not Found")   # 无此令牌或不属本人：同码
        already = all(r.revoked for r in rows)
        for r in rows:
            r.revoked = 1                            # 只软删不硬删
    audit_token_revoke(me, tid, already)
    result = "already_revoked" if already else "revoked"
    return _nca_watermark({"id": tid, "result": result,
                           "revoked_count": len(rows), "scope": "self"},
                          nature="real")


@router.get("/tokens/{tid}")
def me_token_revoke_wrong_method(tid: str, request: Request):
    """读/改路径形态一律 404（fail-closed：⛔ 以 405 泄露路由存在性；S-3 同码口径）。"""
    raise HTTPException(404, "Not Found")
