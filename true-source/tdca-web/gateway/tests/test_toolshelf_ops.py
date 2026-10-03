# -*- coding: utf-8 -*-
"""P4 工具货架测试（/api/v1/toolshelf/*——A-15）。

验收映射：① 会话鉴权 fail-closed（无登录 401）
          ② 上架权限（viewer 403；operator 201）
          ③ 类目闭集机验（越界 400）
          ④ 落库 + list 类目过滤（配置类 requires_grant 如实标记）
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()

client = TestClient(app)

_PW = "Ts-pass-2026"


def _auth(uname, role=None):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    if role:
        with get_sessionmaker().begin() as s:
            s.get(M.User, uname).role = role
    return {"Authorization": r.json()["data"]["token"]}


def test_no_session_401():
    r = client.get("/api/v1/toolshelf/list")
    assert r.status_code == 401


def test_viewer_register_403():
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "编译器X", "category": "compiler"},
                    headers=_auth("tstester01"))
    assert r.status_code == 403


def test_category_closed_set_400():
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "某工具", "category": "weapon"},
                    headers=_auth("tstester02", role="operator"))
    assert r.status_code == 400


def test_register_and_list_filter_201():
    h = _auth("tstester03", role="operator")
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "双协议编译器", "category": "compiler",
                          "description": "协议包编译为可执行形态",
                          "version": "0.1", "requires_grant": True},
                    headers=h)
    assert r.status_code == 201, r.text
    tid = r.json()["data"]["tool_id"]
    with get_sessionmaker().begin() as s:
        row = s.get(M.ToolItem, tid)
        assert row is not None and row.requires_grant == 1
    r2 = client.get("/api/v1/toolshelf/list",
                    params={"category": "compiler"}, headers=h)
    assert r2.status_code == 200
    names = [t["name"] for t in r2.json()["data"]["tools"]]
    assert "双协议编译器" in names
    r3 = client.get("/api/v1/toolshelf/list",
                    params={"category": "adapter"}, headers=h)
    assert all(t["category"] == "adapter" for t in r3.json()["data"]["tools"])
# -*- coding: utf-8 -*-
"""P4 工具货架测试（/api/v1/toolshelf/*——A-15）。

验收映射：① 会话鉴权 fail-closed（无登录 401）
          ② 上架权限（viewer 403；operator 201）
          ③ 类目闭集机验（越界 400）
          ④ 落库 + list 类目过滤（配置类 requires_grant 如实标记）
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()

client = TestClient(app)

_PW = "Ts-pass-2026"


def _auth(uname, role=None):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    if role:
        with get_sessionmaker().begin() as s:
            s.get(M.User, uname).role = role
    return {"Authorization": r.json()["data"]["token"]}


def test_no_session_401():
    r = client.get("/api/v1/toolshelf/list")
    assert r.status_code == 401


def test_viewer_register_403():
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "编译器X", "category": "compiler"},
                    headers=_auth("tstester01"))
    assert r.status_code == 403


def test_category_closed_set_400():
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "某工具", "category": "weapon"},
                    headers=_auth("tstester02", role="operator"))
    assert r.status_code == 400


def test_register_and_list_filter_201():
    h = _auth("tstester03", role="operator")
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "双协议编译器", "category": "compiler",
                          "description": "协议包编译为可执行形态",
                          "version": "0.1", "requires_grant": True},
                    headers=h)
    assert r.status_code == 201, r.text
    tid = r.json()["data"]["tool_id"]
    with get_sessionmaker().begin() as s:
        row = s.get(M.ToolItem, tid)
        assert row is not None and row.requires_grant == 1
    r2 = client.get("/api/v1/toolshelf/list",
                    params={"category": "compiler"}, headers=h)
    assert r2.status_code == 200
    names = [t["name"] for t in r2.json()["data"]["tools"]]
    assert "双协议编译器" in names
    r3 = client.get("/api/v1/toolshelf/list",
                    params={"category": "adapter"}, headers=h)
    assert all(t["category"] == "adapter" for t in r3.json()["data"]["tools"])


def test_template_auth_contract_200():
    """AMEND-002 更正两件：引用源＝在仓三件；版本读件内（V0.1-DRAFT）；生效读注记件（V1.0-FROZEN）。"""
    h = _auth("tstester10")
    r = client.get("/api/v1/toolshelf/template/auth-contract", headers=h)
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    # 更正②：版本不硬编码——读件内真实值
    assert d["version"] == "V0.1-DRAFT"
    assert "机读版件内" in d["version_source"]
    # 生效另源标注（不合并成单一字样）
    assert d["effective_status"] == "V1.0-FROZEN"
    assert "生效注记" in d["effective_source"]
    assert d["effective_source"] != d["version_source"]
    # 更正①：权威源＝在仓三件（docs/regulations），非所有者缔约授权书
    assert "docs/regulations" in d["authority"]
    assert "TDCA-OWNER-CONTRACT-AUTH-001" in d["authority"]  # 仅作「不可互替」声明出现
    assert "唯一权威源" in d["authority"]
    assert len(d["files"]) == 3
    assert {f["lang"] for f in d["files"]} == {"zh", "en", "machine"}
    for f in d["files"]:
        assert len(f["content"]) > 0 and len(f["sha256_8"]) == 8
    # 在仓路径逐件核对
    names = {f["filename"] for f in d["files"]}
    assert any("中文人读版" in n for n in names)
    assert any("英文人读版" in n for n in names)
    assert any("机读版" in n for n in names)
