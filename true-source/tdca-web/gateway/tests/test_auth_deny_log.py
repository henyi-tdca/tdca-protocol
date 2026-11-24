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
    monkeypatch.setenv("AUTH_DENY_LOG_DROPPED", str(tmp_path / "dropped.json"))
    import auth_deny_log
    monkeypatch.setattr(auth_deny_log, "_DEFAULT_PATH", str(p))
    return p


def _dropped(tmp_path, monkeypatch):
    p = Path(os.environ["AUTH_DENY_LOG_DROPPED"])
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


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


def test_rotate_on_size_limit(denylog, monkeypatch, tmp_path):
    """R-1/R-2/R-4：达限轮转——现档 → .1，新行只进轮转后现档；轮转件同 JSONL。"""
    import auth_deny_log
    monkeypatch.setattr(auth_deny_log, "_SIZE_LIMIT", 64)
    old_lines = [{"ts": "t0", "path": "/x", "method": "GET", "http_code": 401,
                  "subject": "anonymous", "code": "C", "source": "s"}]
    denylog.write_text("".join(json.dumps(x) + "\n" for x in old_lines) + "p" * 80,
                       encoding="utf-8")
    auth_deny_log.log_deny(path="/api/v1/auth/me", method="GET", http_code=401,
                           subject="", code="TDCA-E-IDENT-PERM-001",
                           source="http_exception", ts="2026-11-24T00:00:00+00:00")
    rot = denylog.with_name(denylog.name + ".1")
    assert rot.exists(), "达限未轮转出 .1"
    assert json.loads(rot.read_text(encoding="utf-8").splitlines()[0]) == old_lines[0]
    cur = _read_lines(denylog)
    assert len(cur) == 1 and cur[0]["path"] == "/api/v1/auth/me"
    assert denylog.stat().st_size < 64 + 4096  # 轮转后现档只剩新行


def test_write_failure_degrades_with_counter(denylog, monkeypatch, tmp_path, capsys):
    """R-3/R-5：写失败不抛异常、不反转裁决；计数文件 +1 且 stderr 告警一行。"""
    import auth_deny_log
    # 指向父目录不存在的路径 → open() 必失败（跨平台 FileNotFoundError/NotADirectory）
    monkeypatch.setenv("AUTH_DENY_LOG", str(tmp_path / "no_such_dir" / "x.log"))
    auth_deny_log.log_deny(path="/p", method="GET", http_code=401, subject="",
                           code="C", source="middleware")
    d = _dropped(tmp_path, monkeypatch)
    assert d is not None, "写失败未产出计数文件"
    assert d["dropped"] >= 1 and "last_reason" in d and "last_ts" in d
    assert "AUTH_DENY_LOG_DEGRADED" in capsys.readouterr().err


def test_rotate_failure_alerts_not_raises(denylog, monkeypatch, tmp_path, capsys):
    """R-1 补网：轮转失败（现档被置为目录占位）不阻断、不抛，降级告警。"""
    import auth_deny_log
    monkeypatch.setattr(auth_deny_log, "_SIZE_LIMIT", 8)
    denylog.mkdir()  # 同名目录 → stat 成功但轮转 rename 必失败
    auth_deny_log.log_deny(path="/p", method="GET", http_code=401, subject="",
                           code="C", source="middleware")
    d = _dropped(tmp_path, monkeypatch)
    assert d is not None and d["dropped"] >= 1
    assert "AUTH_DENY_LOG_DEGRADED" in capsys.readouterr().err
