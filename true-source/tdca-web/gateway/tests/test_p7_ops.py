# -*- coding: utf-8 -*-
"""P7 站点运维端测试（/api/v1/ops/*——A-18）。

验收映射：① 红线八项目录写死（名目不改增删；第八项索引入口如实标注制度件不在本仓）
          ② 反馈入口 → INTAKE 落库（DB 实读）
          ③ 分类器：命中红线（如「宪法」/「登记制度」）→ ESCALATED_DCD＋无权处置
             （提案 403）；未命中 → CLASSIFIED，可全流程走到 RELEASED（NCA 存证）
          ④ 状态机守卫：跳步 409；分类/提案/上线权限（viewer 403）
          ⑤ 上线登记 NCA 存证（DB 实读）
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "P7-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


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


def _feedback(h, title, desc=""):
    r = client.post("/api/v1/ops/feedback",
                    json={"title": title, "description": desc}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["data"]["ticket_id"]


def test_redlines_eight_items():
    r = client.get("/api/v1/ops/redlines", headers=_auth("p7viewer01"))
    assert r.status_code == 200
    lines = r.json()["data"]["red_lines"]
    assert len(lines) == 8
    names = [l["name"] for l in lines]
    assert names == ["宪法十六条", "缔约三件套", "NCA 六要素语义", "NSFL 根本负空间",
                     "配置权三层结构", "MOU 税收锚定下限", "协作须正和效用", "登记制度"]
    reg = [l for l in lines if l["name"] == "登记制度"][0]
    assert "唯一权威源" in reg["index"] and "不重写" in reg["index"]


def test_feedback_intake_persisted():
    h = _auth("p7user01")
    tid = _feedback(h, "页面按钮错位", "复现步骤……")
    with get_sessionmaker().begin() as s:
        row = s.get(M.OpsTicket, tid)
        assert row is not None and row.status == "INTAKE" and row.nca_ref


def test_classifier_redline_escalates_dcd():
    h = _auth("p7ops01", role="operator")
    tid = _feedback(h, "宪法十六条页面展示优化", "涉及宪法展示")
    r = client.post("/api/v1/ops/classify", json={"ticket_id": tid}, headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ESCALATED_DCD"
    assert "宪法十六条" in r.json()["data"]["redline_hit"]
    # 升 DCD 后无权处置：提案 403
    r2 = client.post("/api/v1/ops/propose",
                     json={"ticket_id": tid, "proposal": "改一下"}, headers=h)
    assert r2.status_code == 403 and "DCD" in r2.text


def test_registry_redline_also_escalates():
    h = _auth("p7ops02", role="operator")
    tid = _feedback(h, "登记制度查询入口调整", "")
    r = client.post("/api/v1/ops/classify", json={"ticket_id": tid}, headers=h)
    assert r.json()["data"]["status"] == "ESCALATED_DCD"
    assert "登记制度" in r.json()["data"]["redline_hit"]


def test_full_flow_to_release():
    h = _auth("p7ops03", role="operator")
    tid = _feedback(h, "工具货架列表排序优化", "纯展示层调整")
    assert client.post("/api/v1/ops/classify", json={"ticket_id": tid}, headers=h)\
               .json()["data"]["status"] == "CLASSIFIED"
    r = client.post("/api/v1/ops/propose",
                    json={"ticket_id": tid, "proposal": "按类目排序"}, headers=h)
    assert r.json()["data"]["status"] == "PROPOSED"
    r2 = client.post("/api/v1/ops/sandbox", json={"ticket_id": tid}, headers=h)
    assert r2.json()["data"]["status"] == "SANDBOXED"
    assert r2.json()["data"]["simulated"] is True
    r3 = client.post("/api/v1/ops/release", json={"ticket_id": tid}, headers=h)
    assert r3.json()["data"]["status"] == "RELEASED"
    with get_sessionmaker().begin() as s:
        row = s.get(M.OpsTicket, tid)
        assert row.status == "RELEASED" and row.nca_ref
        assert s.get(M.NcaChain, row.nca_ref) is not None


def test_state_machine_guards():
    h = _auth("p7ops04", role="operator")
    tid = _feedback(h, "文案微调", "")
    r = client.post("/api/v1/ops/release", json={"ticket_id": tid}, headers=h)
    assert r.status_code == 409  # INTAKE 不可直接上线
    r2 = client.post("/api/v1/ops/sandbox", json={"ticket_id": tid}, headers=h)
    assert r2.status_code == 409  # INTAKE 不可直接沙盒


def test_viewer_cannot_operate():
    hv = _auth("p7viewer02")
    ho = _auth("p7ops05", role="operator")
    tid = _feedback(ho, "权限边界测试单", "")
    r = client.post("/api/v1/ops/classify", json={"ticket_id": tid}, headers=hv)
    assert r.status_code == 403
    r2 = client.post("/api/v1/ops/release", json={"ticket_id": tid}, headers=hv)
    assert r2.status_code == 403
