# -*- coding: utf-8 -*-
"""L1SI175-A1 术语匿名脱敏与检索测试（/api/v1/knowledge/terms）。

验收映射（A1-001 回报第三/四/五项）：
  A1-1  匿名返回只出 term＋脱敏 def：T-/TDCA-件号/NC-/ID/FC- 五类编号 → 占位
        （前置核查实测 237+9+17+15+1 处来源即此表）；⛔ 匿名不含 id 字段
  A1-1  登录面保持全量：含 id、def 原文不改（脱敏不溯源）
  A1-2  检索走现有 ?q=：空词全量 / 常见词过滤 / 无匹配空表
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "A1-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


@pytest.fixture()
def _seed():
    sm = get_sessionmaker()
    rows = [
        ("T-001", "甲词", "见 TDCA-SYMBOL-RENAME-ORDER-V1.0 与 NC-2 及 ID21 的 FC-ABC1 说明", "real"),
        ("T-002", "乙词", "普通释义不含编号", "real"),
        ("T-003", "函数词", "涉及 L-6 演进与 ID29 定义", "real"),
    ]
    with sm.begin() as s:
        for tid, term, dfn, prov in rows:
            s.add(M.TermsRegistry(term_id=tid, term=term, definition=dfn,
                                  data_provenance=prov))
    yield
    with sm.begin() as s:
        for tid, *_ in rows:
            s.query(M.TermsRegistry).filter(M.TermsRegistry.term_id == tid).delete()


def _auth():
    uname = "a1tester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


_SENSITIVE = ["T-001", "TDCA-SYMBOL-RENAME-ORDER-V1.0", "NC-2", "ID21", "FC-ABC1", "ID29"]


def test_anonymous_desensitized_no_id(_seed):
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200, r.text[:200]
    items = r.json()["data"]["terms"]
    by_term = {i["term"]: i for i in items}
    assert set(by_term["甲词"].keys()) == {"term", "def"}   # ⛔ 匿名不含 id
    for bad in _SENSITIVE:
        assert bad not in by_term["甲词"]["def"], f"脱敏漏网 {bad}"
        assert bad not in by_term["函数词"]["def"], f"脱敏漏网 {bad}"
    # 五类逐类：占位在册
    assert "〔内部编号〕" in by_term["甲词"]["def"]
    # 全表扫：任何匿名行都不含五类编号（含 conftest 预种行）
    import re as _re
    pat = _re.compile(r"\bT-\d{3}\b|TDCA-[A-Z0-9-]+|\bNC-\d+\b|\bID\d+\b|\bFC-[A-Z0-9]+\b")
    for it in items:
        assert not pat.search(it["def"]), f"漏网: {it['term']}"


def test_authed_full_with_id(_seed):
    r = client.get("/api/v1/knowledge/terms", headers=_auth())
    assert r.status_code == 200, r.text[:200]
    items = {i["term"]: i for i in r.json()["data"]["terms"]}
    row = items["甲词"]
    assert "id" in row and row["id"] == "T-001"            # 登录面含 id
    assert "TDCA-SYMBOL-RENAME-ORDER-V1.0" in row["def"]   # 原文不改（脱敏不溯源）
    assert "NC-2" in row["def"] and "ID21" in row["def"]


def test_search_existing_q_param(_seed):
    # 空词 → 全量（conftest 预种 8 ＋ 本件种 3 ＝ 11）
    assert client.get("/api/v1/knowledge/terms").json()["data"]["total"] == 11
    # 常见词 → 过滤（命中词或释义，本件独有词）
    r = client.get("/api/v1/knowledge/terms?q=甲词")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1
    # 释义关键词（本件独有）
    r = client.get("/api/v1/knowledge/terms?q=普通释义")
    assert r.json()["data"]["total"] == 1
    # 无匹配 → 空表
    r = client.get("/api/v1/knowledge/terms?q=绝不存在词xyz")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0


def test_search_anonymous_also_desensitized(_seed):
    """检索（匿名）命中含编号释义时，返回仍脱敏（过滤在原文上做，展示才脱敏）。"""
    r = client.get("/api/v1/knowledge/terms?q=函数词")
    assert r.status_code == 200
    items = r.json()["data"]["terms"]
    assert len(items) == 1
    assert "ID29" not in items[0]["def"] and "〔内部编号〕" in items[0]["def"]
