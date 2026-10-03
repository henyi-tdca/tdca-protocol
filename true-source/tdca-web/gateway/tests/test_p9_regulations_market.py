# -*- coding: utf-8 -*-
"""P9 规范索引区与沙盒最小链测试（/api/v1/regulations/* + /api/v1/market-sim/*——A-20/21）。

验收映射：① 会话鉴权 fail-closed
          ② 索引区：三件在册（《授权件模板》present，版本读件内 V0.1-DRAFT、
            生效读注记 V1.0-FROZEN——分源标注，⛔ 不硬编码）
          ③ 《注册登记制度》《配置权市场规范》未入册如实报 present=False；
            /spec/{key} 缺失 ⟹ 503 fail-closed（不冒充在册、不回显正文）
          ④ P7 红线第八项与索引区同源（/ops/redlines 收录状态一致）
          ⑤ 沙盒最小链：无授权件 → deny（链止于准入，留痕完整）；
            有 active 授权件 → settled（发布→准入→撮合→结算四步 NCA 全留痕）
          ⑥ 全程 SIMULATED 硬标注（⛔ 不冒充真实 e-CNY／真实税务）
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "P9-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(uname="p9tester01"):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _mk_grant(seller: str, scene: str) -> None:
    """造 active 授权件（P2 准入闸门机验之依赖；此处仅测试夹具）。"""
    with get_sessionmaker().begin() as s:
        s.add(M.AuthGrant(
            grant_id=f"AG-TEST{scene}", subject_agent=seller,
            scene_constraint=scene, asset_order=2, full_composition=1,
            legal_signer="法律主体-测试", signature="TESTSIGNATURE-OK",
            parent_grant_id=None, status="active", created_at="2026-10-03T00:00:00+00:00"))


def test_no_session_401():
    assert client.get("/api/v1/regulations/index").status_code == 401
    assert client.get("/api/v1/market-sim/chains").status_code == 401


def test_index_template_auth_present():
    h = _auth()
    r = client.get("/api/v1/regulations/index", headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True
    by_key = {x["key"]: x for x in d["regulations"]}
    tpl = by_key["template_auth"]
    assert tpl["present"] is True
    assert tpl["version"] == "V0.1-DRAFT"          # 读件内真实值（非硬编码）
    assert tpl["effective_status"] == "V1.0-FROZEN"  # 读生效注记件
    assert tpl["version_source"] != tpl["effective_source"]
    assert len(tpl["files"]) == 4                   # 三件＋生效注记
    # 索引只列名目与状态：⛔ 不回显正文
    assert "content" not in str(tpl["files"][0].keys())


def test_index_two_specs_missing_reported():
    h = _auth()
    r = client.get("/api/v1/regulations/index", headers=h)
    by_key = {x["key"]: x for x in r.json()["data"]["regulations"]}
    for key in ("registration_registry", "config_market"):
        assert by_key[key]["present"] is False
        assert "未入册" in by_key[key]["note"]


def test_spec_missing_503_fail_closed():
    h = _auth()
    r = client.get("/api/v1/regulations/spec/config_market", headers=h)
    assert r.status_code == 503 and "SPEC_UNAVAILABLE" in r.text
    r2 = client.get("/api/v1/regulations/spec/moon", headers=h)
    assert r2.status_code == 404


def test_redline_registry_same_source():
    h = _auth()
    r_idx = client.get("/api/v1/regulations/index", headers=h)
    present = {x["key"]: x["present"]
               for x in r_idx.json()["data"]["regulations"]}
    r = client.get("/api/v1/ops/redlines", headers=h)
    assert r.status_code == 200
    rl = {x["key"]: x for x in r.json()["data"]["red_lines"]}
    idx_text = rl["registry"]["index"]
    assert ("已收录" if present["registration_registry"] else "未收录") in idx_text
    assert "/api/v1/regulations/index" in idx_text
    assert rl["constitution"]["name"] == "宪法十六条"  # 前七项名目未动


def test_chain_denied_without_grant():
    h = _auth()
    r = client.post("/api/v1/market-sim/chain",
                    json={"seller_ref": "AGENT-NO-GRANT", "asset_summary": "五阶资产-配置权样例",
                          "scene": "notification", "price_points": 100}, headers=h)
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["simulated"] is True and d["result"] == "denied"
    steps = d["steps"]
    assert [s["step"] for s in steps] == ["发布", "准入审查"]
    assert steps[-1]["ok"] is False and "无有效授权件" in steps[-1]["detail"]
    assert all(s["nca_ref"].startswith("NCA-WEB-") for s in steps)
    with get_sessionmaker().begin() as s:
        row = s.get(M.MarketSimRun, d["run_id"])
        assert row is not None and row.result == "denied"
        assert s.get(M.NcaChain, row.nca_ref) is not None


def test_chain_settled_with_grant():
    h = _auth()
    _mk_grant("AGENT-WITH-GRANT", "notification")
    r = client.post("/api/v1/market-sim/chain",
                    json={"seller_ref": "AGENT-WITH-GRANT",
                          "asset_summary": "五阶资产-配置权样例",
                          "scene": "notification", "price_points": 200}, headers=h)
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["result"] == "settled"
    assert [s["step"] for s in d["steps"]] == ["发布", "准入审查", "撮合", "结算"]
    assert all(s["ok"] and s["simulated"] for s in d["steps"])
    assert "SIMULATED" in d["steps"][-1]["detail"]  # 站内积分模拟硬标注
    r2 = client.get(f"/api/v1/market-sim/chain/{d['run_id']}", headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["run"]["result"] == "settled"
    r3 = client.get("/api/v1/market-sim/chains", params={"result": "settled"},
                    headers=h)
    assert r3.status_code == 200 and r3.json()["data"]["count"] >= 1


def test_chain_input_validation():
    h = _auth()
    r = client.post("/api/v1/market-sim/chain",
                    json={"seller_ref": "", "asset_summary": "", "scene": ""},
                    headers=h)
    assert r.status_code == 400
    r2 = client.post("/api/v1/market-sim/chain",
                     json={"seller_ref": "a", "asset_summary": "b", "scene": "c",
                           "price_points": -1}, headers=h)
    assert r2.status_code == 400
