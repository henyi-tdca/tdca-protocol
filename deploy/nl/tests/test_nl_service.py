# -*- coding: utf-8 -*-
"""SITE-SEC-001 A 段锁测试（nl 意图边车）：会话核验 / IP 限流 / 单日配额 / 成本不外露 / 供应商中性。"""
import json

import pytest
from fastapi.testclient import TestClient

import nl_service as M
from nl_service import app

client = TestClient(app)
HDR = {"Authorization": "TDCA-SES-testtoken-0001"}


@pytest.fixture()
def clean(monkeypatch, tmp_path):
    """隔离证据文件与会话核验；默认核验通过。"""
    monkeypatch.setattr(M, "COST_FILE", tmp_path / "cost.json")
    monkeypatch.setattr(M, "CALLS_LOG", tmp_path / "calls.log")
    monkeypatch.setattr(M, "QUOTA_FILE", tmp_path / "quota.json")
    monkeypatch.setattr(M, "FUSE_LOG", tmp_path / ".nsfl-fuse.log")
    monkeypatch.setattr(M, "_verify_cache", {})
    monkeypatch.setattr(M, "_rate_hits", {})
    async def _ok(token):
        return {"ok": True, "username": "tester", "role": "viewer"}
    monkeypatch.setattr(M, "_verify_session", _ok)
    return tmp_path


# ── A-1 会话令牌 ──────────────────────────────────────────────

def test_no_token_401(clean):
    r = client.get("/api/v1/intent?q=查税收")
    assert r.status_code == 401
    assert r.json()["code"] == "TDCA-E-NL-AUTH-001"
    assert "data" not in r.json()          # ⛔返回结果


def test_invalid_token_401(clean, monkeypatch):
    async def _bad(token):
        return {"ok": False, "username": "", "role": ""}
    monkeypatch.setattr(M, "_verify_session", _bad)
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 401
    assert r.json()["code"] == "TDCA-E-NL-AUTH-002"


def test_gateway_unreachable_503(clean, monkeypatch):
    async def _down(token):
        return {"ok": False, "unreachable": True}
    monkeypatch.setattr(M, "_verify_session", _down)
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 503            # fail-closed


def test_session_survives_s1(clean, monkeypatch):
    """S-1 回归：持有效会话 → 服务可用（降级路也算可用）。"""
    monkeypatch.setattr(M, "DS_KEY", "")
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 200


# ── A-1 IP 限流 ───────────────────────────────────────────────

def test_rate_limit_429(clean, monkeypatch):
    monkeypatch.setattr(M, "RATE_PER_MIN", 2)
    monkeypatch.setattr(M, "DS_KEY", "")
    assert client.get("/api/v1/intent?q=查税收", headers=HDR).status_code == 200
    assert client.get("/api/v1/intent?q=查账单", headers=HDR).status_code == 200
    r = client.get("/api/v1/intent?q=查审计", headers=HDR)
    assert r.status_code == 429
    assert r.json()["code"] == "TDCA-E-NL-RATE-001"


# ── A-1 单日配额（仅计真实 LLM 调用）──────────────────────────

def test_quota_429(clean, monkeypatch):
    monkeypatch.setattr(M, "QUOTA_DAY", 1)
    monkeypatch.setattr(M, "DS_KEY", "sk-test")

    class _FakeResp:
        def __init__(self, payload):
            self._p = payload
        def raise_for_status(self):
            pass
        def json(self):
            return self._p

    class _FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def get(self, *a, **k):
            raise RuntimeError("no gateway in test")
        async def post(self, *a, **k):
            return _FakeResp({"choices": [{"message": {"content":
                        json.dumps({"route": "/tax", "action": "查询",
                                    "guide": ["a", "b", "c"], "reply": "好的"})}}],
                              "usage": {"prompt_tokens": 10, "completion_tokens": 5}})

    monkeypatch.setattr(M.httpx, "AsyncClient", _FakeClient)
    assert client.get("/api/v1/intent?q=查税收", headers=HDR).status_code == 200
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 429
    assert r.json()["code"] == "TDCA-E-NL-QUOTA-001"


# ── A-2 成本不外露 ＋ A-3 供应商中性 ──────────────────────────

def test_billed_response_has_no_cost_no_brand(clean, monkeypatch):
    monkeypatch.setattr(M, "DS_KEY", "sk-test")

    class _FakeResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"message": {"content":
                        json.dumps({"route": "/tax", "action": "查询",
                                    "guide": ["打开税收页"], "reply": "好的"})}}],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 10}}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def get(self, *a, **k):
            raise RuntimeError("no gateway in test")
        async def post(self, *a, **k):
            return _FakeResp()

    monkeypatch.setattr(M.httpx, "AsyncClient", _FakeClient)
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 200
    body = r.json()
    assert body["data_nature"] == "real"
    note = body["data"]["note"]
    assert note == "真实外部模型调用（real 水印）"
    text = json.dumps(body, ensure_ascii=False)
    assert "DeepSeek" not in text
    assert "累计" not in text
    assert "¥" not in text
    # A-2：明细入内日志
    log = (clean / "calls.log").read_text(encoding="utf-8")
    rec = json.loads(log.strip().splitlines()[-1])
    assert rec["user"] == "tester" and rec["spend"] > 0 and "day_spend" in rec


def test_fuse_response_has_no_amount(clean, monkeypatch):
    """熔断降级路：响应体只有口径，没有金额。"""
    monkeypatch.setattr(M, "DS_KEY", "sk-test")
    monkeypatch.setattr(M, "CAP_DAY", 0.0)

    class _FakeResp:
        def json(self):
            return {"data": {"note": "意图导航（规则表匹配）", "matched": True,
                             "route": "/tax", "title": "税收仪表盘", "action": "查询",
                             "guide": ["x"], "alternatives": []},
                    "nca_watermark": "sha256:abc", "data_nature": "simulated"}
        def raise_for_status(self):
            pass

    class _FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def get(self, *a, **k):
            return _FakeResp()

    monkeypatch.setattr(M.httpx, "AsyncClient", _FakeClient)
    r = client.get("/api/v1/intent?q=查税收", headers=HDR)
    assert r.status_code == 200
    text = json.dumps(r.json(), ensure_ascii=False)
    assert "¥" not in text and "累计" not in text


def test_health_keeps_internal_cost(clean):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["lock"] == {"session": "required", "rate_per_min": M.RATE_PER_MIN,
                         "quota_day": M.QUOTA_DAY}
    assert "cap_day" in d["cost"]        # 预算可见在内网 health，不在响应体
