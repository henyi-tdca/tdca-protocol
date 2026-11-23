# -*- coding: utf-8 -*-
"""公开登记面测试（/api/public/registrations*——GENESIS-007 公域只读面）。

验收映射：① 列表／详页匿名 200 不变（EVIDGATE-015 回报项 3 之证）；
          ② EVIDGATE-015 步 2 加门：证据包端点匿名 401 fail-closed；
          ③ 授权态 200 且 8 项复算必需字段全量可取（sha256 全值／时间戳／记录号／
            链段五字段），复算功能不废；④ 详情备注节三组字等面侧字段不受影响。
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api_v1
import registrations_public_ops

from app import app

client = TestClient(app)

_PW = "Ts-pass-2026"

_NOTE = ("登记存证 内容哈希（sha256）：" + "AB12" * 16 + " 短值 CD34EF56AB78EF90 字节 1234 "
         "链序：NCA-WEB-aabbccdd（前序 NCA-WEB-0000ffff）")


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


@pytest.fixture()
def _reg_db(tmp_path, monkeypatch):
    """ownership_records＋nca_chain 最小表（公开面实读；_DB 指向临时库）。"""
    db = tmp_path / "tdca.db"
    conn = sqlite3.connect(db)
    conn.execute("""CREATE TABLE ownership_records (
        record_id TEXT PRIMARY KEY, work_title TEXT, owner_ref TEXT,
        expression_form TEXT, jurisdiction_branch TEXT, source_lineage TEXT,
        scene TEXT, status TEXT, note TEXT, nca_ref TEXT,
        created_at TEXT, updated_at TEXT)""")
    conn.execute("""CREATE TABLE nca_chain (
        nca_id TEXT PRIMARY KEY, prev_nca TEXT, ts TEXT,
        rec_hash TEXT, prev_hash TEXT)""")
    conn.execute("INSERT INTO ownership_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("OR-G7-00AA00BB", "测试登记件", "owner-x", "md", "cn",
                  "tdca-protocol/docs/cop-library/x.md", "scene", "registered",
                  _NOTE, "NCA-WEB-aabbccdd",
                  "2026-11-23T00:00:00+08:00", "2026-11-23T00:00:00+08:00"))
    conn.execute("INSERT INTO nca_chain VALUES (?,?,?,?,?)",
                 ("NCA-WEB-aabbccdd", "NCA-WEB-0000ffff", "2026-11-08T09:10:26",
                  "REC-HASH-0001", "PREV-HASH-0000"))
    conn.commit()
    conn.close()
    monkeypatch.setattr(registrations_public_ops, "_DB", str(db))
    yield db


def _auth(uname):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _data(r):
    j = r.json()
    return j.get("data", j)


def test_list_and_detail_anonymous_untouched(_reg_db):
    """EVIDGATE-015 回报项 3：列表／详页匿名 200 未变；四字段与备注节照出。"""
    r = client.get("/api/public/registrations")
    assert r.status_code == 200, r.text[:200]
    d = _data(r)
    assert d["count"] == 1
    assert d["items"][0]["record_id"] == "OR-G7-00AA00BB"
    assert "NCA-WEB-" not in r.text          # T-1 脱敏面保持

    r = client.get("/api/public/registrations/OR-G7-00AA00BB")
    assert r.status_code == 200, r.text[:200]
    d = _data(r)
    assert d["fields"]["ownership_info"]["登记记录号"] == "OR-G7-00AA00BB"
    assert d["fields"]["ownership_info"]["链上序号"] == "已存证"
    assert "NCA-WEB-" not in r.text          # 详页脱敏面保持（含备注节）
    assert d["labels"] and d["proof_boundary"]["provable"]


def test_evidence_anonymous_401_fail_closed(_reg_db):
    """EVIDGATE-015 步 2：匿名 401（⛔ 200）；错误面不含任何链段内容。"""
    r = client.get("/api/public/registrations/OR-G7-00AA00BB/evidence")
    assert r.status_code == 401, r.status_code
    assert "NCA-WEB-" not in r.text
    assert "栏四" not in r.text


def test_evidence_authorized_200_eight_required_fields(_reg_db):
    """EVIDGATE-015 步 2：授权态 200，8 项复算必需字段全量可取（复算功能不废）。"""
    h = _auth("evidgate01")
    r = client.get("/api/public/registrations/OR-G7-00AA00BB/evidence", headers=h)
    assert r.status_code == 200, r.text[:300]
    d = _data(r)
    # 8 必需：记录号／时间戳／sha256 全值／链段五字段
    assert d["栏三_登记时间戳与记录号"]["登记记录号"] == "OR-G7-00AA00BB"
    assert d["栏三_登记时间戳与记录号"]["登记时间戳"] == "2026-11-23T00:00:00+08:00"
    assert d["栏二_内容哈希与字节"]["sha256 全值"] == "AB12" * 16
    seg = d["栏四_链段"]
    assert seg["当条链号"] == "NCA-WEB-aabbccdd"
    assert seg["前序衔接"] == "NCA-WEB-0000ffff"
    assert seg["链记录时间"] == "2026-11-08T09:10:26"
    assert seg["当条自哈希"] == "REC-HASH-0001"
    assert seg["前序哈希"] == "PREV-HASH-0000"
    # 非必需字段仍在（输出结构零改动）
    assert d["栏二_内容哈希与字节"]["sha256 短值"] == "CD34EF56AB78EF90"
    assert d["栏一_件名与路径"]["件名（净名）"] == "测试登记件"


def test_evidence_authorized_invalid_id_404(_reg_db):
    """加门后授权态的 404 语义不变（无效记录号仍 RECORD_NOT_FOUND）。"""
    h = _auth("evidgate02")
    r = client.get("/api/public/registrations/OR-G7-DEADBEEF/evidence", headers=h)
    assert r.status_code == 404
