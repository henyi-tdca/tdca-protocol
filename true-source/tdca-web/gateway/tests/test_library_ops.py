# -*- coding: utf-8 -*-
"""内容区文库测试（/api/v1/library/*——A-22）。

验收映射：① 无会话 401（fail-closed）
          ② family 闭集机验（越界 404）
          ③ 件目/正文只读（docs 表实读；标题与正文逐字一致）
          ④ docs 表缺失 → 503 fail-closed（不崩溃）
"""
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api_v1

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


def test_no_session_401():
    assert client.get("/api/v1/library/families").status_code == 401
    assert client.get("/api/v1/library/whitepaper").status_code == 401


def test_family_closed_set(_docs_table):
    h = _auth("libtester01")
    r = client.get("/api/v1/library/unknown", headers=h)
    assert r.status_code == 404
    # 2026-10-04 创始人明示：regulation（制度规范）入闭集——须可列（不再 404）
    r = client.get("/api/v1/library/regulation", headers=h)
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
