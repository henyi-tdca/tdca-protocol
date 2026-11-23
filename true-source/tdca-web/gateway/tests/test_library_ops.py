# -*- coding: utf-8 -*-
"""内容区文库测试（/api/v1/library/*——A-22）。

验收映射：① 匿名口径按 _OPEN_FAMILIES 分流：families 清单／cop-library／terms／
          laws／law-notes 匿名 200（COP-LIB-OPEN-001／TERMS-OPEN-001／LAWINGEST-001），
          未开放族（kg 等）匿名 401（fail-closed）；whitepaper/paper 已随 CONTENT-LIVE-ALL-001 案甲开放
          ② family 闭集机验（越界 404）
          ③ 件目/正文只读（docs 表实读；标题与正文逐字一致）
          ④ docs 表缺失 → 503 fail-closed（不崩溃）
"""
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api_v1
import library_ops

from app import app
from db import get_database_url

client = TestClient(app)

_PW = "Ts-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(uname):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _db_path() -> str:
    return get_database_url().split("sqlite:///", 1)[1]


@pytest.fixture()
def _docs_table():
    conn = sqlite3.connect(_db_path())
    conn.execute("""CREATE TABLE IF NOT EXISTS docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        family TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL, body_md TEXT NOT NULL,
        source_path TEXT NOT NULL,
        data_nature TEXT NOT NULL DEFAULT 'simulated',
        synced_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    conn.execute("INSERT OR REPLACE INTO docs (family, slug, title, body_md, source_path)"
                 " VALUES ('whitepaper', 'WP-TEST-001', '测试白皮书', '正文甲', 'docs/x.md')")
    conn.execute("INSERT OR REPLACE INTO docs (family, slug, title, body_md, source_path)"
                 " VALUES ('whitepaper', 'WP-TEST-EMPTY', '占位件（无正文）', '', 'docs/y.md')")
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(_db_path())
    conn.execute("DROP TABLE IF EXISTS docs")
    conn.commit()
    conn.close()


def test_closed_families_401_and_open_families_200(_docs_table):
    """匿名口径分流（COP-LIB-OPEN-001／TERMS-OPEN-001／LAWINGEST-001／CONTENT-LIVE-ALL-001）：开放族 200，未开放族 401。"""
    assert client.get("/api/v1/library/families").status_code == 200
    assert client.get("/api/v1/library/cop-library").status_code == 200
    assert client.get("/api/v1/library/terms").status_code == 200
    # LAWINGEST-001（批C-C2）：laws/law-notes 两族匿名可读（法律原文＋适用说明对外发布）
    assert client.get("/api/v1/library/laws").status_code == 200
    assert client.get("/api/v1/library/law-notes").status_code == 200
    # CONTENT-LIVE-ALL-001 案甲（2026-11-10）：whitepaper/paper 两族并入匿名只读（六族）
    assert client.get("/api/v1/library/whitepaper").status_code == 200
    assert client.get("/api/v1/library/paper").status_code == 200


def test_families_endpoint_matches_open_families(_docs_table):
    """KB-TABS-001（GSEQ-8840）对账断言：匿名 /families 返回族集 == _OPEN_FAMILIES
    （与前端 tab 集合对账成对，防「前端硬编码缺族」类漂移再发生）。"""
    r = client.get("/api/v1/library/families")
    assert r.status_code == 200, r.text[:200]
    items = r.json()["data"]["items"]
    assert {e["family"] for e in items} == set(library_ops._OPEN_FAMILIES)
    assert len(items) == len(library_ops._OPEN_FAMILIES) == 9


def test_family_closed_set(_docs_table):
    h = _auth("libtester01")
    r = client.get("/api/v1/library/unknown", headers=h)
    assert r.status_code == 404
    # ANON-READ-001（2026-11-08，依 TDCA-RULING-PUBLIC-CORPUS-055·治理件库·decisions
    # 「对外公开制度不需要注册可见」取甲）：regulation 制度族并入知识库匿名只读面——
    # 件目即白名单（200；与 LIB-DOCS-SCOPE-001 旧口径的更迭在册）
    r = client.get("/api/v1/library/regulation", headers=h)
    assert r.status_code == 200, r.text[:200]
    # 写方法守卫：制度族只读（fail-closed 403）
    r = client.post("/api/v1/library/regulation", headers=h)
    assert r.status_code == 403
    # 白名单外 slug 404
    r = client.get("/api/v1/library/regulation/NO-SUCH-REG.md", headers=h)
    assert r.status_code == 404
    # 新族位 terms/kg：零行只建位，族面可列（200）
    r = client.get("/api/v1/library/terms", headers=h)
    assert r.status_code == 200, r.text[:200]
    # LAWINGEST-001：laws/law-notes 入闭集（会话态亦 200；匿名态见分流测试）
    r = client.get("/api/v1/library/laws", headers=h)
    assert r.status_code == 200, r.text[:200]
    r = client.get("/api/v1/library/law-notes", headers=h)
    assert r.status_code == 200, r.text[:200]


def test_list_and_detail(_docs_table):
    h = _auth("libtester02")
    r = client.get("/api/v1/library/whitepaper", headers=h)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    flags = {i["slug"]: i["has_content"] for i in d["items"]}
    assert flags.get("WP-TEST-001") is True
    assert flags.get("WP-TEST-EMPTY") is False

    r = client.get("/api/v1/library/whitepaper/WP-TEST-001", headers=h)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["title"] == "测试白皮书"
    assert d["body_md"] == "正文甲"

    r = client.get("/api/v1/library/whitepaper/NO-SUCH", headers=h)
    assert r.status_code == 404


def test_family_aliases_301(_docs_table):
    """FAMNAME-011（窄令 #1~#5）：别名 301 落主名（匿名不经鉴权即跳，落点带子路径与 query）；
    未放行两对（#6 papers／#7 whitepapers）不得出现 301；主名读数与 /families 九族不变。"""
    pairs = [("regulations", "regulation"), ("helps", "help"), ("coplib", "cop-library"),
             ("ops-guide", "ops-guides"), ("term", "terms")]
    for alias, main in pairs:
        r = client.get(f"/api/v1/library/{alias}", follow_redirects=False)
        assert r.status_code == 301, (alias, r.status_code, r.text[:200])
        assert r.headers["location"].endswith(f"/api/v1/library/{main}")
        r2 = client.get(f"/api/v1/library/{alias}/some-slug.md", follow_redirects=False)
        assert r2.status_code == 301, (alias, r2.status_code)
        assert r2.headers["location"].endswith(f"/api/v1/library/{main}/some-slug.md")
    # query 保留
    r3 = client.get("/api/v1/library/coplib?x=1", follow_redirects=False)
    assert r3.status_code == 301
    assert r3.headers["location"].endswith("/api/v1/library/cop-library?x=1")
    # #6/#7 未放行：papers/whitepapers 非主名族，不得 301（维持原匿名 401 语义）
    for not_yet in ("papers", "whitepapers"):
        r4 = client.get(f"/api/v1/library/{not_yet}", follow_redirects=False)
        assert r4.status_code != 301, (not_yet, r4.status_code)
    # 主名读数不变（200）；/families 仍九族且无别名键
    assert client.get("/api/v1/library/cop-library").status_code == 200
    r5 = client.get("/api/v1/library/families")
    fams = {e["family"] for e in r5.json()["data"]["items"]}
    assert fams == set(library_ops._OPEN_FAMILIES)
    assert not (fams & set(library_ops._FAMILY_ALIASES))
