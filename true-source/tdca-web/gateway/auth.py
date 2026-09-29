# -*- coding: utf-8 -*-
"""
TDCA 统一网关鉴权中间件（B-4 → M3 会话化，F-2 关闭）

设计原则:
- 默认宽松（不启用）→ 向后兼容既有测试/前端（6 tests 无鉴权）
- 环境变量 TDCA_GATEWAY_AUTH=1 启用 → 写操作（POST/PUT/DELETE）须携带有效凭证
- 双凭证族（M3）:
  * TDCA-SES-{随机}  会话令牌（login 签发，sessions 表存 sha256 哈希，2h 固定期）
  * TDCA-CRT-{token} 静态令牌（保留为降级开关，对齐 tdca-bridge IRP-PROD-BLOCKED 预埋点 1）
- 读操作（GET/HEAD/OPTIONS）默认放行（制度即公开 BV-3：审计透明页任意可查）
- 治理路径（/governance、/api/v1/governance/*）无论读写均须鉴权（HUF 敏感）
- /api/v1/auth/login 与 /api/v1/auth/logout 豁免（否则无法登录/过期后无法登出）
- fail-closed: 启用状态下无 token → 401；token 不符 → 403；会话过期 → 401 + session_expired 标记
- 密码: PBKDF2-HMAC-SHA256（stdlib，免装 bcrypt），salt 16B 随机，120,000 迭代
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

SESSION_PREFIX = "TDCA-SES-"
CRT_PREFIX = "TDCA-CRT-"
SESSION_TTL_HOURS = 2
_PBKDF2_ITERATIONS = 120000

# 写操作豁免路径（登录/登出/注册自身）
_AUTH_EXEMPT = ("/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/register")
_SENSITIVE_PREFIXES = ("/governance", "/api/v1/governance")
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ---------------------------------------------------------------------
# 密码哈希（PBKDF2-HMAC-SHA256，stdlib）
# ---------------------------------------------------------------------

def hash_password(password: str, salt: Optional[bytes] = None,
                  iterations: int = _PBKDF2_ITERATIONS) -> Tuple[str, str, int]:
    """返回 (hash_hex, salt_hex, iterations)。salt 缺省随机 16B。"""
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return h.hex(), salt.hex(), iterations


def verify_password(password: str, salt_hex: str, iterations: int, expected_hex: str) -> bool:
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                            bytes.fromhex(salt_hex), iterations)
    return secrets.compare_digest(h.hex(), expected_hex)


# ---------------------------------------------------------------------
# 会话（token 只存 sha256 哈希；单会话制）
# ---------------------------------------------------------------------

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(username: str) -> Tuple[str, str]:
    """签发会话：吊销该用户全部旧会话（防会话固定/挤下线），返回 (token, expires_at)。"""
    from db import get_sessionmaker
    from db import models as M
    token = SESSION_PREFIX + secrets.token_urlsafe(32)
    now = _utcnow()
    expires = _iso(now + timedelta(hours=SESSION_TTL_HOURS))
    with get_sessionmaker().begin() as s:
        for old in s.query(M.AuthSession).filter_by(username=username, revoked=0).all():
            old.revoked = 1
        s.add(M.AuthSession(token_hash=_token_hash(token), username=username,
                            expires_at=expires, revoked=0, created_at=_iso(now),
                            data_provenance="real"))
    return token, expires


def revoke_session(token: str) -> bool:
    """吊销会话（logout）。命中即吊销，返回是否命中。"""
    from db import get_sessionmaker
    from db import models as M
    with get_sessionmaker().begin() as s:
        row = s.get(M.AuthSession, _token_hash(token))
        if row is not None and not row.revoked:
            row.revoked = 1
            return True
    return False


def validate_session(token: str) -> dict:
    """校验会话。返回 {ok, expired, username, role, expires_at}。"""
    from db import get_session
    from db import models as M
    with get_session() as s:
        row = s.get(M.AuthSession, _token_hash(token))
        if row is None or row.revoked:
            return {"ok": False, "expired": False}
        expired = datetime.fromisoformat(row.expires_at) <= _utcnow()
        if expired:
            return {"ok": False, "expired": True}
        user = s.get(M.User, row.username)
        return {"ok": True, "expired": False, "username": row.username,
                "role": user.role if user else "viewer", "expires_at": row.expires_at}


# ---------------------------------------------------------------------
# 中间件
# ---------------------------------------------------------------------

def _auth_enabled() -> bool:
    return os.environ.get("TDCA_GATEWAY_AUTH", "0") == "1"


def _bare_token(s: str) -> str:
    """归一化为裸 token（剥掉全部 TDCA-CRT- 前缀）。两侧都归一，面板填带前缀/裸串均可。"""
    s = s.strip()
    while s.startswith(CRT_PREFIX):
        s = s[len(CRT_PREFIX):]
    return s.strip()


def _valid_crt_token(token: str) -> bool:
    """静态 TDCA-CRT 令牌（降级开关，配置 TDCA_GATEWAY_TOKEN，生产须替换）。
    口径①：环境变量与调用方（HTTP 头 / WS query）均可带/不带 TDCA-CRT- 前缀，比较前双侧归一。
    口径②（防缺省）：未设 TDCA_GATEWAY_TOKEN 时 CRT 通道整体关闭——宁可降级通道失灵，
    不可「忘设变量 = 公开一把人尽皆知的默认钥匙」。"""
    raw_expected = os.environ.get("TDCA_GATEWAY_TOKEN", "")
    if not raw_expected.strip():
        return False
    expected = _bare_token(raw_expected)
    return bool(expected) and secrets.compare_digest(_bare_token(token), expected)


# 向后兼容别名：ws_events.py（B-5 握手联动）引用旧名
_valid_token = _valid_crt_token


def _check_credential(raw: str) -> Tuple[bool, Optional[dict]]:
    """凭证统一校验。返回 (放行, 拒绝响应体 or None)。"""
    if not raw:
        return False, {"error": "UNAUTHORIZED", "detail": "须登录会话（TDCA-SES）或 TDCA-CRT token"}
    if raw.startswith(SESSION_PREFIX):
        v = validate_session(raw)
        if v["ok"]:
            return True, None
        if v.get("expired"):
            return False, {"error": "UNAUTHORIZED", "session_expired": True,
                           "detail": "会话已过期或被挤下线，请重新登录（未提交内容已保留在本地草稿）"}
        return False, {"error": "FORBIDDEN", "detail": "会话无效或已吊销"}
    token = raw.strip()
    if token and _valid_crt_token(token):
        return True, None
    return False, {"error": "FORBIDDEN", "detail": "token 无效"}


class TDCAGatewayAuthMiddleware(BaseHTTPMiddleware):
    """网关鉴权中间件（B-4 → M3 会话化）。"""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        if not _auth_enabled():
            return await call_next(request)

        path = request.url.path
        method = request.method

        # 登录/登出豁免（否则无法建立/终结会话）
        if path in _AUTH_EXEMPT:
            return await call_next(request)

        needs_auth = (path.startswith(_SENSITIVE_PREFIXES)      # 治理路径读写均须鉴权
                      or method not in _SAFE_METHODS)            # 写操作 fail-closed
        if needs_auth:
            ok, deny = _check_credential(request.headers.get("authorization", "").strip())
            if not ok:
                return JSONResponse(deny, status_code=401 if deny["error"] == "UNAUTHORIZED" else 403)

        return await call_next(request)
