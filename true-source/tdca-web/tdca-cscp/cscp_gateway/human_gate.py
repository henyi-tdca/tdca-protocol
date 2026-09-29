# -*- coding: utf-8 -*-
"""
T-CSCP-008 · HumanGate 双签名控制器（真实不可绕过校验）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §2.1 人类签名强制插入点 #1（Step-3 后）/ #2（Step-5 前）
     + H-CSCP-005（人类签名 #1/#2 不可绕过，渗透测试 100% 阻断）+ 红队 #2 N3（模拟级→真实级）
方案: challenge-response + HMAC-SHA256（标准库 hashlib/hmac/secrets）+ 一次性 nonce 防重放
     + 时间窗口防过期 + 动作绑定防错绑 + 服务端密钥防伪造（代码层；合约层校验由 CBDC 合约 T-CSCP-004 承接）
模拟态声明: 本实现为「真实级模拟」——密钥由服务端持有（模拟人类签名设备与通知机交互）；
           生产化时密钥经 KMS/HSM 管理，签名算法可升级（R-CSCP-003 不阻塞）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Dict, Optional, Tuple

# 模拟态密钥（红队 N3: 生产经 KMS/HSM；测试共享同一密钥以签发有效签名）
DEFAULT_SECRET = b"tdca-cscp-humangate-sim-secret-v1"

# 签名动作（与状态机步骤绑定，防跨动作重放）
ACTION_MATCH = "MATCH"          # 人类签名 #1（Step-3 配置权匹配后）
ACTION_DISPATCH = "DISPATCH"    # 人类签名 #2（Step-5 执行前）

NONCE_TTL_SECONDS = 300         # nonce 有效窗口（5min）
MAX_NONCES = 10000              # 红队 FIN-2: 未用 nonce 容量上限（防内存膨胀 DoS）


class HumanGate:
    """双签名控制器：签发 challenge、验证签名（HMAC + 一次性 nonce + TTL + 动作绑定）。"""

    def __init__(self, secret: bytes = DEFAULT_SECRET,
                 nonce_ttl_seconds: int = NONCE_TTL_SECONDS,
                 max_nonces: int = MAX_NONCES,
                 now=time.monotonic):
        self._secret = secret
        self._ttl = nonce_ttl_seconds
        self._max_nonces = max_nonces
        self._now = now
        self._nonces: Dict[str, Tuple[float, bool]] = {}   # nonce -> (expires_at, used)

    # ---- 签发侧（人类签名设备/通知机交互）----

    def issue_challenge(self, handshake_id: str, action: str) -> dict:
        """服务端签发一次性 challenge：注册 nonce（防重放基准）+ 返回给签名设备。"""
        if action not in (ACTION_MATCH, ACTION_DISPATCH):
            raise ValueError(f"非法签名动作: {action}")
        self._gc()                                          # 惰性清理过期项（FIN-2）
        if len(self._nonces) >= self._max_nonces:
            raise OverflowError(f"nonce 池满（上限 {self._max_nonces}），拒绝签发（FIN-2）")
        nonce = secrets.token_hex(16)
        self._nonces[nonce] = (self._now() + self._ttl, False)
        return {"nonce": nonce, "handshake_id": handshake_id, "action": action,
                "expires_in": self._ttl}

    def compute_signature(self, handshake_id: str, action: str, nonce: str) -> str:
        """签名设备签发：对服务端已签发的 nonce 计算 HMAC（纯计算，不注册）。
        返回 token 形如 `{nonce}.{hmac_hex}`。"""
        sig = self._hmac(handshake_id, action, nonce)
        return f"{nonce}.{sig}"

    # ---- 验证侧（HumanGate 控制器）----

    def verify(self, handshake_id: str, action: str, token: str) -> bool:
        """验证签名。fail-closed：任何异常 → False（红队: 不可绕过）。"""
        if not isinstance(token, str):
            return False
        try:
            nonce, sig = token.split(".", 1)
        except ValueError:
            return False
        # 1. nonce 存在且未使用（防重放）
        entry = self._nonces.get(nonce)
        if entry is None or entry[1]:
            return False
        expires_at, _ = entry
        # 2. 时间窗口（防过期）
        if self._now() > expires_at:
            self._nonces.pop(nonce, None)
            return False
        # 3. HMAC 校验（防伪造）+ 动作绑定（防错绑）
        expected = self._hmac(handshake_id, action, nonce)
        if not hmac.compare_digest(expected, sig):
            return False
        # 4. 一次性消费（防重放二次使用）
        self._nonces[nonce] = (expires_at, True)
        return True

    def invalidate(self, handshake_id: str) -> None:
        """会话失败/回滚时清理其全部未用 nonce。"""
        stale = [n for n, (_, used) in self._nonces.items() if not used]
        for n in stale:
            self._nonces.pop(n, None)

    def _gc(self) -> None:
        """惰性清理过期 nonce（FIN-2）。"""
        now = self._now()
        expired = [n for n, (exp, _) in self._nonces.items() if now > exp]
        for n in expired:
            self._nonces.pop(n, None)

    # ---- 内部 ----

    def _hmac(self, handshake_id: str, action: str, nonce: str) -> str:
        msg = f"{handshake_id}:{action}:{nonce}".encode("utf-8")
        return hmac.new(self._secret, msg, hashlib.sha256).hexdigest()
