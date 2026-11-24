# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# CASENORM-K3-001 B部（K-3 留证补强）验收：人类面 401/403 入专档＋code 落档＋隐私口径
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

_DENY_LOG = Path(os.environ.get("AUTH_DENY_LOG",
                                "/data/auth_deny.log"))


@pytest.fixture()
def denylog(tmp_path, monkeypatch):
    p = tmp_path / "auth_deny.log"
    monkeypatch.setenv("AUTH_DENY_LOG", str(p))
    import auth_deny_log
    monkeypatch.setattr(auth_deny_log, "_DEFAULT_PATH", str(p))
    return p


def _read_lines(p: Path):
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_endpoint_401_anonymous_logged(denylog):
    """端点层拒绝（_require_session_user）：专档行四字段齐，主体 anonymous，code 落档。"""
    from app import app
    c = TestClient(app)
    r = c.get("/api/v1/me/dashboard")  # 无会话 → 401
    assert r.status_code == 401
    lines = _read_lines(denylog)
    assert len(lines) >= 1
    rec = lines[-1]
    assert rec["path"] == "/api/v1/me/dashboard"
    assert rec["method"] == "GET"
    assert rec["http_code"] == 401
    assert rec["subject"] == "anonymous"
    assert rec["code"] == "TDCA-E-IDENT-PERM-001"
    assert rec["source"] == "http_exception"


def test_middleware_write_deny_logged(denylog, monkeypatch):
    """中间件层拒绝（写操作 fail-closed）：无凭据 POST → 401 落档，source=middleware。
    （测试态 TDCA_GATEWAY_AUTH 缺省 0=关，本用例显式拨 1 直测中间件层。）"""
    monkeypatch.setenv("TDCA_GATEWAY_AUTH", "1")
    from app import app
    c = TestClient(app)
    r = c.post("/api/v1/governance/probe-deny-log", json={})
    assert r.status_code == 401
    lines = _read_lines(denylog)
    recs = [x for x in lines if x["source"] == "middleware"]
    assert recs, "中间件层拒绝未落档"
    assert recs[-1]["http_code"] == 401
    assert recs[-1]["subject"] == "anonymous"
    assert recs[-1]["code"].startswith("TDCA-E-")


def test_privacy_no_credential_in_log(denylog):
    """隐私口径：所呈会话令牌值不得出现在专档任何字段。"""
    from app import app
    c = TestClient(app)
    fake = "TDCA-SES-fakecredentialvalue123"
    r = c.get("/api/v1/me/dashboard", headers={"Authorization": fake})
    assert r.status_code == 401
    blob = denylog.read_text(encoding="utf-8") if denylog.exists() else ""
    assert "fakecredentialvalue123" not in blob


def test_fields_allowlist(denylog):
    """字段清单白名单：仅 ts/path/method/http_code/subject/code/source 七键。"""
    from app import app
    c = TestClient(app)
    c.get("/api/v1/me/dashboard")
    lines = _read_lines(denylog)
    assert lines
    assert set(lines[-1].keys()) == {
        "ts", "path", "method", "http_code", "subject", "code", "source",
    }
