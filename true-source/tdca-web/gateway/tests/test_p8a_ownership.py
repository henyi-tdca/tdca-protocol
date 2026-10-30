# -*- coding: utf-8 -*-
"""P8a 权属登记管理测试（/api/v1/ownership/*——A-19）。

验收映射：① 会话鉴权 fail-closed
          ② 口径面：登记二分／入口（凡具表达形式者皆可登记）／法域四支
            （⛔ 不代作法律判定）／场景非必须／转让许可归 8b
          ③ 登记须载生成来源谱系——缺 → 400
          ④ 场景非必须守检：无场景登记成功
          ⑤ 登记→变更→注销全流程：落库＋NCA 存证＋状态机（注销后变更 409）
          ⑥ 四条不公开负空间：写入命中 → 400 fail-closed（内容不回显）；
            读取兜底脱敏（手工写入含敏感内容行 → 查询输出被替换）
          ⑦ 法域分支过滤查询；输出 SIMULATED 硬标注
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "P8a-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(uname="p8atester01"):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def test_no_session_401():
    r = client.get("/api/v1/ownership/rules")
    assert r.status_code == 401


def test_rules_surface():
    r = client.get("/api/v1/ownership/rules", headers=_auth())
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True
    assert d["entry"] == "凡具表达形式者皆可登记"
    assert "归谁" in d["registry_split"]["ownership"]
    # L1SI182-RIGHT-CENTER-001 处4：authorization 说明改「合约备案＝…（⛔ 非确权）」（照抄令面定稿）
    assert "合约备案" in d["registry_split"]["authorization"] and "非确权" in d["registry_split"]["authorization"]
    branches = {b["key"]: b for b in d["jurisdiction_branches"]}
    assert branches["copyright"]["branch"] == "著作权"
    assert branches["patent"]["branch"] == "专利法"
    assert branches["data"]["branch"] == "数据法"
    assert branches["trademark"]["branch"] == "商标法"
    assert d["scene_optional"] and "8b" in d["out_of_scope"] and "可备案存档" in d["out_of_scope"]
    assert len(d["non_public_four"]) == 4


def test_register_requires_source_lineage_400():
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "元函数样例", "owner_ref": "主体-甲"},
                    headers=_auth())
    assert r.status_code == 400 and "source_lineage" in r.text


def test_register_scene_optional_201():
    """场景非必须守检：无场景登记成功（⛔ 不得因无场景拒登记）。"""
    h = _auth()
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "数据集合样例", "owner_ref": "主体-甲",
                          "source_lineage": "谱系：TDCA 原生智能体生成",
                          "jurisdiction_branch": "data"},
                    headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert d["simulated"] is True and d["status"] == "registered"
    assert d["scene_recorded"] is False and d["nca_ref"].startswith("NCA-WEB-")


def test_register_amend_cancel_flow():
    h = _auth()
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "文字作品样例", "owner_ref": "主体-乙",
                          "source_lineage": "谱系：人类用户原创",
                          "jurisdiction_branch": "copyright",
                          "scene": "notification"},
                    headers=h)
    assert r.status_code == 201
    rid = r.json()["data"]["record_id"]
    with get_sessionmaker().begin() as s:
        row = s.get(M.OwnershipRecord, rid)
        assert row is not None and row.nca_ref is not None
        assert s.get(M.NcaChain, row.nca_ref) is not None
    r2 = client.post("/api/v1/ownership/amend",
                     json={"record_id": rid, "note": "表达形式补充：文字＋配图"},
                     headers=h)
    assert r2.status_code == 200 and r2.json()["data"]["status"] == "amended"
    r3 = client.post("/api/v1/ownership/cancel",
                     json={"record_id": rid, "note": "协作终结留痕"}, headers=h)
    assert r3.status_code == 200 and r3.json()["data"]["status"] == "cancelled"
    r4 = client.post("/api/v1/ownership/amend",
                     json={"record_id": rid, "note": "试图变更已注销"}, headers=h)
    assert r4.status_code == 409


def test_amend_empty_400_and_branch_invalid_400():
    h = _auth()
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "标识样例", "owner_ref": "主体-丙",
                          "source_lineage": "谱系：原生智能体生成"},
                    headers=h)
    rid = r.json()["data"]["record_id"]
    r2 = client.post("/api/v1/ownership/amend",
                     json={"record_id": rid}, headers=h)
    assert r2.status_code == 400
    r3 = client.post("/api/v1/ownership/register",
                     json={"work_title": "x", "owner_ref": "y",
                           "source_lineage": "z", "jurisdiction_branch": "moon"},
                     headers=h)
    assert r3.status_code == 400 and "jurisdiction_branch" in r3.text


def test_public_space_write_blocked_400():
    h = _auth()
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "样例", "owner_ref": "主体-丁",
                          "source_lineage": "谱系：生成",
                          "note": "api_key: abcdefgh123456789"},
                    headers=h)
    assert r.status_code == 400 and "PUBLIC_SPACE_VIOLATION" in r.text
    assert "abcdefgh123456789" not in r.text  # ⛔ 命中内容不回显
    r2 = client.post("/api/v1/ownership/register",
                     json={"work_title": "样例", "owner_ref": "主体-丁",
                           "source_lineage": "谱系：生成",
                           "note": "涉及 NSFL 与负空间表述"},
                     headers=h)
    assert r2.status_code == 400 and "PUBLIC_SPACE_VIOLATION" in r2.text
    r3 = client.post("/api/v1/ownership/register",
                     json={"work_title": "样例", "owner_ref": "主体-丁",
                           "source_lineage": "谱系：生成",
                           "scene": "联系人 13812345678"},
                     headers=h)
    assert r3.status_code == 400 and "自然人敏感信息" in r3.text


def test_public_space_read_redacted():
    """读取兜底脱敏：绕过写入层的手工行（存量/异常路径）在查询输出中被替换。"""
    h = _auth()
    r = client.post("/api/v1/ownership/register",
                    json={"work_title": "兜底样例", "owner_ref": "主体-戊",
                          "source_lineage": "谱系：生成"}, headers=h)
    rid = r.json()["data"]["record_id"]
    with get_sessionmaker().begin() as s:
        s.get(M.OwnershipRecord, rid).note = "token: abcdefgh123456789"
    r2 = client.get(f"/api/v1/ownership/query/{rid}", headers=h)
    assert r2.status_code == 200
    note = r2.json()["data"]["record"]["note"]
    assert "abcdefgh123456789" not in note and "脱敏" in note


def test_query_filters():
    h = _auth("p8atester02")
    for title, branch in [("文本A", "copyright"), ("数据集B", "data")]:
        client.post("/api/v1/ownership/register",
                    json={"work_title": title, "owner_ref": "主体-己",
                          "source_lineage": "谱系：生成",
                          "jurisdiction_branch": branch}, headers=h)
    r = client.get("/api/v1/ownership/query",
                   params={"jurisdiction_branch": "data"}, headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True
    assert all(x["jurisdiction_branch"] == "data" for x in d["records"])
    assert any(x["jurisdiction_index"]["branch"] == "数据法" for x in d["records"])
    r3 = client.get("/api/v1/ownership/query", params={"status": "moon"}, headers=h)
    assert r3.status_code == 400
