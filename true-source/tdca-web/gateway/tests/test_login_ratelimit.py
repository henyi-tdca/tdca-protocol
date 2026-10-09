# -*- coding: utf-8 -*-
"""登录口防爆破限流测试（2026-10-10 F-5 小修件）：POST /api/v1/auth/login。

验收映射：
  连续失败超限 → 429        → test_login_ratelimit_429_after_burst
  分键独立（IP|用户名）     → test_login_ratelimit_keyed_per_account
  成功登录不计数            → test_login_success_not_counted
  429 文案不区分账号存在性  → test_login_ratelimit_message_fail_closed
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from auth import hash_password
from db import get_sessionmaker
from db import models as M

client = TestClient(app)
_URL = "/api/v1/auth/login"


@pytest.fixture()
def _rate_limit_setup():
    """调低限流阈值并清空进程内计数，用毕恢复（互不影响其他套件）。"""
    saved_max = api_v1._LOGIN_MAX
    api_v1._LOGIN_MAX = 3
    api_v1._login_hits.clear()
    yield
    api_v1._LOGIN_MAX = saved_max
    api_v1._login_hits.clear()


def _mkuser(username: str) -> None:
    ph, salt, iters = hash_password(f"pw-{username}")
    with get_sessionmaker().begin() as s:
        if s.get(M.User, username) is None:
            s.add(M.User(username=username, password_hash=ph, salt=salt,
                         iterations=iters, role="viewer",
                         created_at="2026-10-10T00:00:00+00:00"))


def test_login_ratelimit_429_after_burst(_rate_limit_setup):
    """同一账号连续失败：前 3 次 401，第 4 次 429。"""
    for i in range(3):
        r = client.post(_URL, json={"username": "rl-burst", "password": f"wrong-{i}9x"})
        assert r.status_code == 401, r.text[:200]
    r = client.post(_URL, json={"username": "rl-burst", "password": "wrong-99x"})
    assert r.status_code == 429, r.text[:200]


def test_login_ratelimit_keyed_per_account(_rate_limit_setup):
    """分键独立（IP|用户名）：A 超限不阻塞 B（同 IP 下同进程）。"""
    api_v1._LOGIN_MAX = 1
    client.post(_URL, json={"username": "rl-a", "password": "wrong1x9"})
    r_a2 = client.post(_URL, json={"username": "rl-a", "password": "wrong2x9"})
    assert r_a2.status_code == 429, r_a2.text[:200]      # A 第二次失败即超限（阈值 1）
    r_b1 = client.post(_URL, json={"username": "rl-b", "password": "wrong1x9"})
    assert r_b1.status_code == 401, r_b1.text[:200]      # B 独立预算，未受 A 影响


def test_login_success_not_counted(_rate_limit_setup):
    """成功登录不耗额度：阈值 1 下连续成功登录均 200。"""
    api_v1._LOGIN_MAX = 1
    _mkuser("rl-ok")
    for _ in range(3):
        r = client.post(_URL, json={"username": "rl-ok", "password": "pw-rl-ok"})
        assert r.status_code == 200, r.text[:200]


def test_login_ratelimit_message_fail_closed(_rate_limit_setup):
    """429 文案不区分账号存在/口令错（fail-closed 口径与 401 一致）。"""
    api_v1._LOGIN_MAX = 1
    client.post(_URL, json={"username": "rl-msg", "password": "wrong1x9"})
    r = client.post(_URL, json={"username": "rl-msg", "password": "wrong2x9"})
    assert r.status_code == 429
    assert "登录尝试过于频繁" in r.json()["detail"]
    assert "用户名或密码错误" not in r.json()["detail"]
