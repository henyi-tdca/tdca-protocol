# -*- coding: utf-8 -*-
"""T-CSCP-008 HumanGate 渗透测试（H-CSCP-005: 空/伪造/重放/过期/错绑 → 100% 阻断）。"""
import pytest

from cscp_gateway.human_gate import (ACTION_DISPATCH, ACTION_MATCH, DEFAULT_SECRET,
                                     HumanGate)


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def advance(self, s):
        self.t += s

    def __call__(self):
        return self.t


@pytest.fixture()
def gate():
    return HumanGate(secret=DEFAULT_SECRET, now=FakeClock())


def _token(g, hs, action, nonce=None):
    if nonce is None:
        nonce = g.issue_challenge(hs, action)["nonce"]
    return g.compute_signature(hs, action, nonce)


# ---- 正向 ----

def test_valid_signature_accepted(gate):
    hs = "HS-ABC123"
    token = _token(gate, hs, ACTION_MATCH)
    assert gate.verify(hs, ACTION_MATCH, token) is True


# ---- 空 / 伪造 / 非法格式 ----

def test_empty_signature_rejected(gate):
    assert gate.verify("HS-1", ACTION_MATCH, "") is False


def test_fake_signature_rejected(gate):
    """伪造（无密钥随机串）→ REJECTED。"""
    hs = "HS-ABC123"
    gate.issue_challenge(hs, ACTION_MATCH)
    assert gate.verify(hs, ACTION_MATCH, f"deadbeef.0123456789abcdef" * 2) is False
    assert gate.verify(hs, ACTION_MATCH, "no-separator-here") is False
    assert gate.verify(hs, ACTION_MATCH, 12345) is False  # 非字符串


# ---- 重放（一次性 nonce）----

def test_replay_rejected(gate):
    """同一 token 使用两次 → 第二次 REJECTED（一次性消费）。"""
    hs = "HS-REPLAY"
    token = _token(gate, hs, ACTION_MATCH)
    assert gate.verify(hs, ACTION_MATCH, token) is True
    assert gate.verify(hs, ACTION_MATCH, token) is False  # 重放 → 阻断


# ---- 过期（时间窗口）----

def test_expired_nonce_rejected(gate):
    clock = gate._now
    hs = "HS-EXP"
    nonce = gate.issue_challenge(hs, ACTION_MATCH)["nonce"]
    token = gate.compute_signature(hs, ACTION_MATCH, nonce)
    clock.advance(301)  # 超过 TTL 300s
    assert gate.verify(hs, ACTION_MATCH, token) is False


# ---- 动作错绑（跨动作重放）----

def test_wrong_action_rejected(gate):
    """MATCH 的签名用于 DISPATCH → REJECTED（动作绑定）。"""
    hs = "HS-ACT"
    token = _token(gate, hs, ACTION_MATCH)
    assert gate.verify(hs, ACTION_DISPATCH, token) is False


# ---- 会话错绑 ----

def test_wrong_handshake_rejected(gate):
    hs = "HS-OWNER"
    token = _token(gate, hs, ACTION_MATCH)
    assert gate.verify("HS-OTHER", ACTION_MATCH, token) is False


# ---- 未签发 nonce（服务端无记录）----

def test_unissued_nonce_rejected(gate):
    """攻击者自造 nonce（服务端未签发）→ REJECTED（HMAC 可计算但 nonce 不在注册表）。"""
    hs = "HS-UNISS"
    token = gate.compute_signature(hs, ACTION_MATCH, "ffff" * 8)
    assert gate.verify(hs, ACTION_MATCH, token) is False


# ---- invalidate ----

def test_invalidate_clears_unused(gate):
    hs = "HS-INV"
    gate.issue_challenge(hs, ACTION_MATCH)
    gate.invalidate(hs)
    assert gate._nonces == {}  # 未用 nonce 全部清理


# ---- challenge 动作合法性 ----

def test_issue_challenge_invalid_action(gate):
    with pytest.raises(ValueError):
        gate.issue_challenge("HS-1", "HACK")


# ---- 红队 FIN-2: nonce 池容量上限 ----

def test_nonce_pool_capacity_limit():
    gate = HumanGate(max_nonces=5, now=FakeClock())
    for _ in range(5):
        gate.issue_challenge("HS-CAP", ACTION_MATCH)
    with pytest.raises(OverflowError):
        gate.issue_challenge("HS-CAP", ACTION_MATCH)   # 超上限拒绝签发


def test_lazy_gc_reclaims_expired(gate):
    clock = gate._now
    gate.issue_challenge("HS-GC", ACTION_MATCH)
    assert len(gate._nonces) == 1
    clock.advance(301)
    gate.issue_challenge("HS-GC", ACTION_MATCH)   # 触发 _gc
    assert len(gate._nonces) == 1                  # 过期项已清理，新签发占 1 个槽
