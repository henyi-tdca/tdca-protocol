# -*- coding: utf-8 -*-
"""P6 模拟锚与版权事件测试（/api/v1/anchor/*——A-17）。

验收映射：① 会话鉴权 fail-closed
          ② 三锚状态全 SIMULATED 硬标注＋组件在位核查如实报（不冒充接入）
          ③ 事件闭集机验：register/amend/cancel 受理；transfer/license → 400（归 8b）
          ④ 登记须载生成来源谱系（8a 口径）；缺 → 400
          ⑤ 事件落库＋NCA 链存证（DB 实读）；列表过滤
          ⑥ 响应硬标注 simulated: True，⛔ 不冒充真实锚
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "P6-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth():
    uname = "p6tester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def test_no_session_401():
    r = client.get("/api/v1/anchor/status")
    assert r.status_code == 401


def test_anchor_status_simulated():
    r = client.get("/api/v1/anchor/status", headers=_auth())
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True
    assert "SIMULATED" in d["anchors"]["copyright_chain"]
    assert "SIMULATED" in d["anchors"]["settlement"]
    assert "SIMULATED" in d["anchors"]["tax"]
    # 组件在位核查：如实报在位（不 MISSING、不冒充接入）
    assert d["components"]["event_template"].endswith("copyright-event-templates-v1.0.yaml")
    assert d["components"]["nca_generator"].endswith("nca_generator.py")
    assert d["components"]["axiom6_audit"].endswith("axiom6.go")
    assert d["components"]["notary"].endswith("notary.py")
    assert d["components"]["nca_template_set"].endswith("contract-templates-v1.0.yaml")


def test_transfer_license_out_of_scope_400():
    for et in ("transfer", "license"):
        r = client.post("/api/v1/anchor/copyright-event",
                        json={"event_type": et, "work_title": "某作品",
                              "owner_ref": "主体-甲"}, headers=_auth())
        assert r.status_code == 400 and "8b" in r.text


def test_register_requires_source_lineage_400():
    r = client.post("/api/v1/anchor/copyright-event",
                    json={"event_type": "register", "work_title": "元函数-样例",
                          "owner_ref": "主体-甲"}, headers=_auth())
    assert r.status_code == 400 and "source_lineage" in r.text


def test_register_amend_cancel_persisted_201():
    h = _auth()
    r = client.post("/api/v1/anchor/copyright-event",
                    json={"event_type": "register", "work_title": "元函数-样例",
                          "owner_ref": "主体-甲",
                          "source_lineage": "谱系：TDCA 原生智能体生成"}, headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert d["simulated"] is True and d["template_ref"] == "CRIGHT-EVENT-001"
    eid = d["event_id"]
    with get_sessionmaker().begin() as s:
        row = s.get(M.CopyrightEvent, eid)
        assert row is not None and row.nca_ref is not None
        assert s.get(M.NcaChain, row.nca_ref) is not None  # 落 NCA 链（版权链模拟锚）
    r2 = client.post("/api/v1/anchor/copyright-event",
                     json={"event_type": "amend", "work_title": "元函数-样例",
                           "owner_ref": "主体-甲", "note": "谱系补充"}, headers=h)
    assert r2.status_code == 201 and r2.json()["data"]["template_ref"] == "CRIGHT-EVENT-002"
    r3 = client.post("/api/v1/anchor/copyright-event",
                     json={"event_type": "cancel", "work_title": "元函数-样例",
                           "owner_ref": "主体-甲", "note": "协作终结留痕"}, headers=h)
    assert r3.status_code == 201 and r3.json()["data"]["template_ref"] == "CRIGHT-EVENT-003"
    r4 = client.get("/api/v1/anchor/copyright-events",
                    params={"event_type": "cancel"}, headers=h)
    assert r4.status_code == 200
    types = [e["event_type"] for e in r4.json()["data"]["events"]]
    assert "cancel" in types
