# -*- coding: utf-8 -*-
"""P3 形式化与实验线结论入站测试（/api/v1/formal/*——A-14）。

验收映射：① 会话鉴权 fail-closed（无登录 401）
          ② 结论面三禁逐条机验（公式符号 / 数值引用 / 内部编号 → 400 fail-closed）
          ③ 数据性质闭集（formal-proved/simulated/assessed；越界 400）
          ④ 条件形态须载明适用边界（scope_note 缺失 400）
          ⑤ 入站落库 + NCA（DB 实读）；list 过滤
          ⑥ 口径守卫：返回注明 入站 ≠ 入主仓 ≠ 对外
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

_PW = "Fm-pass-2026"


def _auth():
    uname = "fmtester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _payload(**over):
    p = {"claim_text": "协调天花板在有限层级内成立",
         "data_nature": "formal-proved", "scope_note": ""}
    p.update(over)
    return p


def test_no_session_401():
    r = client.post("/api/v1/formal/conclusion", json=_payload())
    assert r.status_code == 401


def test_formula_detected_400():
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(claim_text="对于所有 n 有 ∀n, P(n) 成立"),
                    headers=_auth())
    assert r.status_code == 400 and "公式" in r.text


def test_numeric_ref_detected_400():
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(claim_text="机验结果为 935 个任务全部通过"),
                    headers=_auth())
    assert r.status_code == 400 and "数值" in r.text


def test_internal_id_detected_400():
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(claim_text="见 #42 与 C-14 所载结论"),
                    headers=_auth())
    assert r.status_code == 400 and "内部编号" in r.text


def test_data_nature_closed_set_400():
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(data_nature="proved"), headers=_auth())
    assert r.status_code == 400 and "DATA_NATURE" in r.text


def test_conditional_scope_required_400():
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(claim_text="错觉循环不动点限于离散情形"),
                    headers=_auth())
    assert r.status_code == 400 and "SCOPE_REQUIRED" in r.text


def test_register_persisted_and_list_201():
    h = _auth()
    r = client.post("/api/v1/formal/conclusion",
                    json=_payload(claim_text="错觉循环不动点在离散有界模型内成立",
                                  data_nature="formal-proved",
                                  scope_note="限于离散有界模型；不涉实数情形"),
                    headers=h)
    assert r.status_code == 201, r.text
    cid = r.json()["data"]["conclusion_id"]
    assert "入站 ≠ 入主仓 ≠ 对外" in r.json()["data"]["note"]
    with get_sessionmaker().begin() as s:
        row = s.get(M.FormalConclusion, cid)
        assert row is not None and row.data_nature == "formal-proved"
        assert row.scope_note is not None and row.nca_ref is not None
    r2 = client.get("/api/v1/formal/conclusion/list",
                    params={"data_nature": "formal-proved"}, headers=h)
    assert r2.status_code == 200
    ids = [c["conclusion_id"] for c in r2.json()["data"]["conclusions"]]
    assert cid in ids
