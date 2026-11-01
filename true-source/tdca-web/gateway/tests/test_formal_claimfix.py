# -*- coding: utf-8 -*-
"""SITE-CLAIMFIX-001 块 A 测试（PATCH 更新端点＋目录 scope_summary＋分级 fail-closed）。

验收映射（AMEND-001 四条＋原件 §六）：
  ① 权限限死：匿名 401／viewer 403／operator 可调；
  ② 机验同入站：claim_text 公式→400；scope_summary 公式/数值/内部编号/假设标号→400；
  ③ 存证追加不覆盖：NCA 恰加一条（操作类型＝结论更新，指向同 conclusion_id），
    原 nca_ref 行不动，conclusion_id 不变；
  ④ 幂等：同值重复 PATCH 不新增存证、返回 updated=False；
  ⑤ 目录：formal-proved 无 scope_summary 不列（fail-closed）、有则列且带字段；
    simulated 无 scope_summary 照常列（存量豁免）；count 相应变化；
  ⑥ PATCH_EMPTY（两项均缺）→ 400；未知 id → 404。
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_session, get_sessionmaker
from db import models as M


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


client = TestClient(app)

_PW = "Fm-pass-2026"


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


def _mk(token, claim, nature="formal-proved", scope=""):
    r = client.post("/api/v1/formal/conclusion",
                    json={"claim_text": claim, "data_nature": nature,
                          "scope_note": scope}, headers=token)
    assert r.status_code == 201, r.text[:200]
    return r.json()["data"]["conclusion_id"]


def _nca_count(artifact: str) -> int:
    with get_session() as s:
        return s.query(M.NcaChain).filter_by(artifact_path=artifact).count()


def test_patch_no_session_401():
    r = client.patch("/api/v1/formal/conclusion/FC-none",
                     json={"scope_summary": "对外版适用范围"})
    assert r.status_code == 401


def test_patch_viewer_403():
    h = _auth("cfviewer01")
    r = client.patch("/api/v1/formal/conclusion/FC-none",
                     json={"scope_summary": "对外版适用范围"}, headers=h)
    assert r.status_code == 403


def test_patch_machine_check_400():
    h = _auth("cfoperator01", role="operator")
    cid = _mk(h, "协调天花板在有限层级内成立")
    # claim_text 公式记法
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"claim_text": "A ∧ B"}, headers=h)
    assert r.status_code == 400
    # scope_summary 公式记法
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"scope_summary": "A → B"}, headers=h)
    assert r.status_code == 400
    # scope_summary 数值引用
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"scope_summary": "上限 500 条"}, headers=h)
    assert r.status_code == 400
    # scope_summary 内部编号
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"scope_summary": "见 TDCA-X1 件"}, headers=h)
    assert r.status_code == 400
    # scope_summary 内部假设标号独立出现
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"scope_summary": "A1 信任链为分支有限集合"}, headers=h)
    assert r.status_code == 400
    # 两项均缺
    r = client.patch(f"/api/v1/formal/conclusion/{cid}", json={}, headers=h)
    assert r.status_code == 400
    # 未知 id
    r = client.patch("/api/v1/formal/conclusion/FC-notexist",
                     json={"scope_summary": "对外版"}, headers=h)
    assert r.status_code == 404


def test_patch_append_nca_and_keep_id():
    h = _auth("cfoperator02", role="operator")
    cid = _mk(h, "去前缀目标句：既有记录不失效")
    art = f"conclusion:{cid}"
    before = _nca_count(art)
    with get_session() as s:
        orig_nca = s.get(M.FormalConclusion, cid).nca_ref
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"claim_text": "既有记录不失效"}, headers=h)
    assert r.status_code == 200, r.text[:200]
    d = r.json()["data"]
    assert d["updated"] is True and d["conclusion_id"] == cid
    assert _nca_count(art) == before + 1        # 恰追加一条
    with get_session() as s:
        row = s.get(M.FormalConclusion, cid)
        assert row.claim_text == "既有记录不失效"
        assert row.nca_ref == orig_nca          # 行指针不动（原存证未覆盖）
        new_nca = s.query(M.NcaChain).filter_by(artifact_path=art) \
            .order_by(M.NcaChain.ts).all()[-1]
        assert new_nca.action == "结论更新"


def test_patch_idempotent_no_extra_nca():
    h = _auth("cfoperator03", role="operator")
    cid = _mk(h, "幂等目标句：底线只增不减")
    art = f"conclusion:{cid}"
    client.patch(f"/api/v1/formal/conclusion/{cid}",
                 json={"scope_summary": "对外版适用范围一"}, headers=h)
    n = _nca_count(art)
    r = client.patch(f"/api/v1/formal/conclusion/{cid}",
                     json={"scope_summary": "对外版适用范围一"}, headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["updated"] is False
    assert _nca_count(art) == n                 # 幂等：不新增存证


def test_catalog_fail_closed_and_summary():
    h = _auth("cfoperator04", role="operator")
    cid_a = _mk(h, "目录目标句甲：可连不可分")
    cid_b = _mk(h, "目录目标句乙：放行集向下封闭")
    _mk(h, "目录豁免句丙：实验线三问", nature="simulated")
    # 未补对外版：formal-proved 两条不列，simulated 照列
    r = client.get("/api/v1/formal/conclusion/catalog")
    d = r.json()["data"]
    claims = [c["claim_text"] for c in d["conclusions"]]
    assert "目录目标句甲：可连不可分" not in claims
    assert "目录豁免句丙：实验线三问" in claims
    # 补一条对外版：该条复列且带 scope_summary 字段
    client.patch(f"/api/v1/formal/conclusion/{cid_a}",
                 json={"scope_summary": "对外版适用范围甲"}, headers=h)
    r = client.get("/api/v1/formal/conclusion/catalog")
    d = r.json()["data"]
    row = [c for c in d["conclusions"] if c["claim_text"] == "目录目标句甲：可连不可分"]
    assert len(row) == 1 and row[0]["scope_summary"] == "对外版适用范围甲"
    assert "scope_note" not in row[0] and "conclusion_id" not in row[0]
    # 匿名面不含内部编号（fail-closed 既有口径不破）
    for c in d["conclusions"]:
        assert "FC-" not in c["claim_text"]
