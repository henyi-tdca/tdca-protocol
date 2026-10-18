# -*- coding: utf-8 -*-
"""手册接口化测试（/api/v1/ops/files/*——TDCA-HANDOFF-OPS-INACCOUNT-DEPLOY-001 块 2）。

覆盖：未登录 401／viewer 403；清单七件带 sha256_16；按名出件 200＋content-type；
穿越形串（/ \\ ..）400；白名单外 404；在册件缺失 404；yaml 出 application/yaml。
测试件写在 pytest tmp 目录并 monkeypatch OPS_FILES_DIR——⛔ 不触服务器实件。
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from ops_files_ops import _WHITELIST

client = TestClient(app)
_PW = "Opsfiles-2026"
_SEQ = {"n": 0}

# 短名测试件（白名单键在夹内替换，⛔ 不改模块常量本体）
_FAKE = {
    "manual-a.md": "运维手册甲（测试件）",
    "manual-b.md": "运维手册乙（测试件）",
    "spec.yaml": "机读规范（测试件）",
}


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    api_v1._register_hits.clear()
    d = tmp_path / "ops-files"
    d.mkdir()
    for name, body in _FAKE.items():
        (d / name).write_text(body, encoding="utf-8")
    monkeypatch.setenv("OPS_FILES_DIR", str(d))
    for name, label in (("manual-a.md", "运维手册甲（测试件）"),
                        ("manual-b.md", "运维手册乙（测试件）"),
                        ("spec.yaml", "机读规范（测试件）")):
        _WHITELIST[name] = label
    yield
    for name in _FAKE:
        _WHITELIST.pop(name, None)
    api_v1._register_hits.clear()


def _auth(uname=None, role=None):
    if uname is None:
        _SEQ["n"] += 1
        uname = f"opsfile{_SEQ['n']:03d}"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    if role:
        from db import get_sessionmaker
        from db import models as M
        with get_sessionmaker().begin() as s:
            s.get(M.User, uname).role = role
    return {"Authorization": r.json()["data"]["token"]}


# ── 权限面 ──────────────────────────────────────────────
def test_unauthenticated_401_all():
    assert client.get("/api/v1/ops/files").status_code == 401
    assert client.get("/api/v1/ops/files/manual-a.md").status_code == 401


def test_viewer_403():
    h = _auth()
    assert client.get("/api/v1/ops/files", headers=h).status_code == 403
    assert client.get("/api/v1/ops/files/manual-a.md", headers=h).status_code == 403


# ── 清单与出件 ──────────────────────────────────────────
def test_list_whitelist_with_hashes():
    h = _auth(role="operator")
    r = client.get("/api/v1/ops/files", headers=h)
    assert r.status_code == 200
    files = {f["name"]: f for f in r.json()["data"]["files"]}
    for name in _FAKE:
        assert name in files and files[name]["missing"] is False
        assert files[name]["sha256_16"]
    # 既有在册七件（服务器件）在测试库目录缺席 → 如实标 missing，⛔ 不伪造
    assert any(f["missing"] for f in r.json()["data"]["files"])


def test_get_file_md_and_yaml():
    h = _auth(role="operator")
    r = client.get("/api/v1/ops/files/manual-a.md", headers=h)
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "运维手册甲" in r.text
    r = client.get("/api/v1/ops/files/spec.yaml", headers=h)
    assert r.status_code == 200 and "application/yaml" in r.headers["content-type"]


def test_founder_also_allowed():
    h = _auth(role="founder")
    assert client.get("/api/v1/ops/files/manual-b.md", headers=h).status_code == 200


# ── 反例：穿越与白名单外 ─────────────────────────────────
@pytest.mark.parametrize("bad", ["../secret.md", "a/b.md", "a\\b.md", "..%2f.."])
def test_traversal_rejected(bad):
    """穿越形串必拒（400 服务端拒／404 路由拒皆算拒，⛔ 关键是不出件）。"""
    h = _auth(role="operator")
    assert client.get(f"/api/v1/ops/files/{bad}", headers=h).status_code in (400, 404)


def test_not_in_whitelist_404():
    h = _auth(role="operator")
    assert client.get("/api/v1/ops/files/index.html", headers=h).status_code == 404
    assert client.get("/api/v1/ops/files/whatever.md", headers=h).status_code == 404


def test_registered_but_missing_404():
    h = _auth(role="operator")
    # manual-b 在册但夹内文件被删 → 404 如实（不泄目录信息）
    import os
    os.remove(os.path.join(os.environ["OPS_FILES_DIR"], "manual-b.md"))
    assert client.get("/api/v1/ops/files/manual-b.md", headers=h).status_code == 404
