# -*- coding: utf-8 -*-
"""L1SI175-B1 批1可信面匿名端点测试。

验收映射（交办令 S1-1~S1-4 机验判据）：
  S1-3  GET /api/v1/ci/badge          匿名 200（一行绿/红；⛔ 日志详情）
        POST /api/v1/ci/run           匿名 401（触发仍须登录）
        GET  /api/v1/ci/runs          匿名 401（历史仍须登录）
  S1-1  GET /api/v1/formal/conclusion/catalog 匿名 200，字段只含
        claim_text/data_nature（⛔ conclusion_id/nca_ref/scope_note）；
        含内部编号存量行整行不列（fail-closed）
  S1-2  GET /api/v1/toolshelf/catalog 匿名 200，字段只含 name/category/purpose；
        命中脱敏正则整件不列；POST /register 匿名 401
  S1-4  GET /api/v1/library/paper/catalog 匿名 200（slug/title/摘要）；
        摘要命中脱敏正则 → summary=null 标「待核定」；
        GET /api/v1/library/paper/{slug} 正文匿名 401（paper 未入 _OPEN_FAMILIES）
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_database_url, get_sessionmaker
from db import models as M

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


@pytest.fixture()
def _seed():
    sm = get_sessionmaker()
    with sm.begin() as s:
        s.add(M.CiRun(run_id="CI-B1TEST-01", suite="gateway-regression", status="PASS",
                      exit_code=0, detail="机密日志尾部", operator="founder",
                      started_at="2026-10-26T00:00:00+00:00",
                      finished_at="2026-10-26T00:05:00+00:00"))
        s.add(M.FormalConclusion(
            conclusion_id="FC-B1TEST-01", claim_text="协调天花板在有限层级内成立",
            data_nature="formal-proved", scope_note="限于离散层级",
            nca_ref=None, created_at="2026-10-26T00:00:00+00:00"))
        s.add(M.FormalConclusion(
            conclusion_id="FC-B1TEST-02", claim_text="本结论引用内部件号 TL-ABC123 须被挡",
            data_nature="assessed", scope_note=None,
            nca_ref=None, created_at="2026-10-26T00:01:00+00:00"))
        s.add(M.ToolItem(tool_id="TL-B1TEST-01", name="NSFL 编译器", category="compiler",
                         description="将 NSFL 源编译为可执行目标。第二句不返。",
                         version="1.0", requires_grant=1, status="available",
                         nca_ref=None, created_at="2026-10-26T00:00:00+00:00"))
        s.add(M.ToolItem(tool_id="TL-B1TEST-02", name="内部适配器", category="adapter",
                         description="适配凭据为 token 的内部接口",
                         version="0.1", requires_grant=0, status="available",
                         nca_ref=None, created_at="2026-10-26T00:01:00+00:00"))
    yield
    with sm.begin() as s:
        for m, col, vals in [
                (M.CiRun, M.CiRun.run_id, ["CI-B1TEST-01"]),
                (M.FormalConclusion, M.FormalConclusion.conclusion_id,
                 ["FC-B1TEST-01", "FC-B1TEST-02"]),
                (M.ToolItem, M.ToolItem.tool_id, ["TL-B1TEST-01", "TL-B1TEST-02"])]:
            for v in vals:
                s.query(m).filter(col == v).delete()


@pytest.fixture()
def _docs_table():
    conn = sqlite3.connect(get_database_url().split("sqlite:///", 1)[1])
    conn.execute("""CREATE TABLE IF NOT EXISTS docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        family TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL, body_md TEXT NOT NULL,
        source_path TEXT NOT NULL,
        data_nature TEXT NOT NULL DEFAULT 'simulated',
        synced_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    conn.execute("INSERT OR REPLACE INTO docs (family, slug, title, body_md, source_path)"
                 " VALUES ('paper', 'paper-clean', '公开论文甲',"
                 " '# 标题\n\n本文提出协作架构的基础方法。\n\n第二段不返。',"
                 " 'docs/papers/clean.md')")
    conn.execute("INSERT OR REPLACE INTO docs (family, slug, title, body_md, source_path)"
                 " VALUES ('paper', 'paper-dirty', '公开论文乙',"
                 " '本文结论存证于 NCA-AAAA 链上须被挡。',"
                 " 'docs/papers/dirty.md')")
    conn.execute("INSERT OR REPLACE INTO docs (family, slug, title, body_md, source_path)"
                 " VALUES ('paper', 'paper-quote-dirty', '公开论文丙',"
                 " '> 引用块首行载内部决定号 NC-20261026-001 须被挡。',"
                 " 'docs/papers/qdirty.md')")
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect(get_database_url().split("sqlite:///", 1)[1])
    conn.execute("DROP TABLE IF EXISTS docs")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- S1-3

def test_s13_badge_anonymous(_seed):
    r = client.get("/api/v1/ci/badge")
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["status"] == "PASS" and d["suite"] == "gateway-regression"
    assert "detail" not in d and "operator" not in d  # ⛔ 日志详情不出匿名面


def test_s13_run_and_runs_still_authed(_seed):
    assert client.post("/api/v1/ci/run", json={"suites": []}).status_code == 401
    assert client.get("/api/v1/ci/runs").status_code == 401


# ---------------------------------------------------------------- S1-1

def test_s11_conclusion_catalog_anonymous(_seed):
    r = client.get("/api/v1/formal/conclusion/catalog")
    assert r.status_code == 200, r.text[:200]
    items = r.json()["data"]["conclusions"]
    assert len(items) == 1            # FC-B1TEST-02 含内部编号 → 整行不列
    row = items[0]
    assert set(row.keys()) == {"claim_text", "data_nature"}
    assert row["data_nature"] == "formal-proved"


def test_s11_conclusion_list_still_authed(_seed):
    assert client.get("/api/v1/formal/conclusion/list").status_code == 401


# ---------------------------------------------------------------- S1-2

def test_s12_toolshelf_catalog_anonymous(_seed):
    r = client.get("/api/v1/toolshelf/catalog")
    assert r.status_code == 200, r.text[:200]
    tools = r.json()["data"]["tools"]
    assert len(tools) == 1            # TL-B1TEST-02 描述含凭据措辞 → 整件不列
    row = tools[0]
    assert set(row.keys()) == {"name", "category", "purpose"}
    assert row["name"] == "NSFL 编译器"
    assert row["purpose"] == "将 NSFL 源编译为可执行目标"   # 首句截断，第二句不返
    assert "tool_id" not in row and "nca_ref" not in row and "version" not in row


def test_s12_register_still_authed(_seed):
    r = client.post("/api/v1/toolshelf/register",
                    json={"name": "x", "category": "other"})
    assert r.status_code == 401


# ---------------------------------------------------------------- S1-4

def test_s14_paper_catalog_anonymous(_docs_table):
    r = client.get("/api/v1/library/paper/catalog")
    assert r.status_code == 200, r.text[:200]
    items = {i["slug"]: i for i in r.json()["data"]["items"]}
    assert items["paper-clean"]["summary"].startswith("本文提出协作架构")
    assert "第二段" not in items["paper-clean"]["summary"]      # 首段截 200 字
    assert items["paper-dirty"]["summary"] is None               # 命中脱敏 → 待核定
    assert items["paper-dirty"]["summary_note"] == "摘要待核定"
    # 引用块首行载 NC- 内部决定号 → 去记号后仍命中脱敏 → 待核定
    assert items["paper-quote-dirty"]["summary"] is None
    assert items["paper-quote-dirty"]["summary_note"] == "摘要待核定"


def test_s14_paper_body_still_401(_docs_table):
    """正文端点不变：paper 未入 _OPEN_FAMILIES，匿名 401。"""
    assert client.get("/api/v1/library/paper/paper-clean").status_code == 401
