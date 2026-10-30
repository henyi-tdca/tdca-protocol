# -*- coding: utf-8 -*-
"""P8b 授权登记管理测试（/api/v1/authorization/*——A-24）。

验收映射：① 会话鉴权 fail-closed（内部端点 401；公开查免会话）
          ② 口径面：登记二分（授权侧＝谁能怎么用）／四要件／五操作／
            公开四字段／签名须本人、智能体不代持代填／授权件仅内部存证
          ③ 四要件缺一 → 400 fail-closed（⛔ 不代填代证）
          ④ 登记→变更→注销全流程：落库＋NCA 存证＋状态机（注销后操作 409）
          ⑤ 五操作面板：op 非法 400；pre_accept→pre-accepted、
            activate→active、amend_terms→amended、append／sub_grant 保持 active；
            授权状态随操作实时同步；逐笔 NCA 存证
          ⑥ 四条不公开负空间：写入命中 → 400 fail-closed（内容不回显）；
            读取兜底脱敏（手工写入含敏感内容行 → 查询输出被替换）
          ⑦ 公开查：免会话仅回四字段（权属信息／授权信息／授权状态／获取方式），
            ⛔ 不含内部编号／凭据值／NCA 引用
          ⑧ 输出 SIMULATED 硬标注
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "P8b-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(uname="p8btester01"):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _full_req(**over):
    body = {"asset_ref": "资产族样例", "grantee_ref": "被授权方-甲",
            "scene": "生产交付（内循环部署与运行）",
            "req_scene": True, "req_five_forms": True,
            "req_full_grant": True, "req_legal_signature": True,
            "template_fields": {"权属信息": "权利人：创始人（脱敏标识）",
                                "授权信息": "范围：复制·部署·运行",
                                "授权状态": "有效",
                                "获取方式": "经权利人授权路径"}}
    body.update(over)
    return body


def test_no_session_401_and_public_no_session():
    r = client.get("/api/v1/authorization/rules")
    assert r.status_code == 401
    r2 = client.post("/api/v1/authorization/register", json=_full_req())
    assert r2.status_code == 401
    # 公开查免会话（不存在的键 → 404；此处仅验证免会话可达性）
    r3 = client.get("/api/v1/authorization/public/AR-none00000")
    assert r3.status_code == 404


def test_rules_surface():
    r = client.get("/api/v1/authorization/rules", headers=_auth())
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True
    assert "合约备案" in d["registry_split"]["authorization"] and "非确权" in d["registry_split"]["authorization"]
    assert "归谁" in d["registry_split"]["ownership"]
    assert len(d["four_requirements"]) == 4
    labels = [x["label"] for x in d["four_requirements"]]
    assert any("场景约束" in x for x in labels)
    assert any("法律主体签名" in x for x in labels)
    ops = {x["op"] for x in d["operations"]}
    assert ops == {"pre_accept", "activate", "append", "amend_terms", "sub_grant"}
    assert list(d["public_four_fields"]) == ["权属信息", "授权信息", "授权状态", "获取方式"]
    assert len(d["non_public_four"]) == 4
    assert "不入主仓" in d["storage"]


def test_register_requires_four_requirements_400():
    h = _auth()
    for missing in ("req_scene", "req_five_forms", "req_full_grant",
                    "req_legal_signature"):
        body = _full_req()
        body[missing] = False
        r = client.post("/api/v1/authorization/register", json=body, headers=h)
        assert r.status_code == 400 and "四要件" in r.text, missing
    # 必填缺项
    r2 = client.post("/api/v1/authorization/register",
                     json={k: v for k, v in _full_req().items()
                           if k not in ("scene", "template_fields")},
                     headers=h)
    assert r2.status_code == 400 and "scene" in r2.text


def test_register_201_full_requirements():
    h = _auth()
    r = client.post("/api/v1/authorization/register", json=_full_req(), headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert d["simulated"] is True and d["status"] == "active"
    assert d["record_id"].startswith("AR-")
    assert d["nca_ref"].startswith("NCA-WEB-")
    with get_sessionmaker().begin() as s:
        row = s.get(M.AuthorizationRecord, d["record_id"])
        assert row is not None and row.nca_ref is not None
        assert s.get(M.NcaChain, row.nca_ref) is not None
        assert all([row.req_scene, row.req_five_forms,
                    row.req_full_grant, row.req_legal_signature])


def test_register_amend_cancel_flow():
    h = _auth()
    r = client.post("/api/v1/authorization/register", json=_full_req(), headers=h)
    rid = r.json()["data"]["record_id"]
    r2 = client.post("/api/v1/authorization/amend",
                     json={"record_id": rid, "scope_note": "范围补充说明（人填）"},
                     headers=h)
    assert r2.status_code == 200 and r2.json()["data"]["status"] == "amended"
    r3 = client.post("/api/v1/authorization/cancel",
                     json={"record_id": rid, "note": "授权终结留痕"}, headers=h)
    assert r3.status_code == 200 and r3.json()["data"]["status"] == "cancelled"
    r4 = client.post("/api/v1/authorization/operate",
                     json={"record_id": rid, "op": "activate"}, headers=h)
    assert r4.status_code == 409
    r5 = client.post("/api/v1/authorization/amend",
                     json={"record_id": rid, "note": "试图变更已注销"}, headers=h)
    assert r5.status_code == 409


def test_operate_panel_status_sync():
    h = _auth("p8btester02")
    rid = client.post("/api/v1/authorization/register",
                      json=_full_req(), headers=h).json()["data"]["record_id"]
    seq = [("pre_accept", "pre-accepted"), ("activate", "active"),
           ("append", "active"), ("amend_terms", "amended"),
           ("sub_grant", "active")]
    for op, expect in seq:
        r = client.post("/api/v1/authorization/operate",
                        json={"record_id": rid, "op": op, "note": f"操作留痕-{op}"},
                        headers=h)
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["status"] == expect and d["simulated"] is True
        assert d["nca_ref"].startswith("NCA-WEB-")
    # 操作后状态实时同步（查询复核）
    r2 = client.get(f"/api/v1/authorization/query/{rid}", headers=h)
    assert r2.json()["data"]["record"]["status"] == "active"
    # 操作历史逐笔落 NCA（note 留痕）
    with get_sessionmaker().begin() as s:
        row = s.get(M.AuthorizationRecord, rid)
        for op, _ in seq:
            assert f"操作留痕-{op}" in row.note
    # op 非法 400
    r3 = client.post("/api/v1/authorization/operate",
                     json={"record_id": rid, "op": "fly"}, headers=h)
    assert r3.status_code == 400 and "op" in r3.text


def test_public_space_write_blocked_400():
    h = _auth()
    r = client.post("/api/v1/authorization/register",
                    json=_full_req(note="api_key: abcdefgh123456789"), headers=h)
    assert r.status_code == 400 and "PUBLIC_SPACE_VIOLATION" in r.text
    assert "abcdefgh123456789" not in r.text  # ⛔ 命中内容不回显
    r2 = client.post("/api/v1/authorization/register",
                     json=_full_req(template_fields={"权属信息": "涉及 负空间 表述"}),
                     headers=h)
    assert r2.status_code == 400 and "PUBLIC_SPACE_VIOLATION" in r2.text
    r3 = client.post("/api/v1/authorization/register",
                     json=_full_req(scene="联系人 13812345678"), headers=h)
    assert r3.status_code == 400 and "自然人敏感信息" in r3.text


def test_public_space_read_redacted():
    """读取兜底脱敏：绕过写入层的手工行在查询输出与公开查投影中被替换。"""
    h = _auth()
    rid = client.post("/api/v1/authorization/register",
                      json=_full_req(), headers=h).json()["data"]["record_id"]
    with get_sessionmaker().begin() as s:
        s.get(M.AuthorizationRecord, rid).note = "token: abcdefgh123456789"
    r2 = client.get(f"/api/v1/authorization/query/{rid}", headers=h)
    note = r2.json()["data"]["record"]["note"]
    assert "abcdefgh123456789" not in note and "脱敏" in note


def test_public_query_four_fields_only():
    h = _auth("p8btester03")
    tpl = {"权属信息": "权利人：创始人（脱敏标识）",
           "授权信息": "范围：复制·部署·运行",
           "授权状态": "有效",
           "获取方式": "经权利人授权路径",
           "内部备注": "此字段不应出现在公开面"}
    rid = client.post("/api/v1/authorization/register",
                      json=_full_req(template_fields=tpl), headers=h
                      ).json()["data"]["record_id"]
    r = client.get(f"/api/v1/authorization/public/{rid}")  # ⛔ 免会话
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["simulated"] is True
    assert d["权属信息"] == tpl["权属信息"]
    assert d["授权信息"] == tpl["授权信息"]
    assert d["授权状态"] == tpl["授权状态"]
    assert d["获取方式"] == tpl["获取方式"]
    assert "内部备注" not in d and tpl["内部备注"] not in str(d)
    assert "nca_ref" not in d and "NCA-WEB" not in str(d)
    assert "授权码" not in str(d.get("授权信息", ""))


def test_query_filters_and_status_invalid_400():
    h = _auth("p8btester04")
    client.post("/api/v1/authorization/register", json=_full_req(), headers=h)
    r = client.get("/api/v1/authorization/query",
                   params={"status": "active"}, headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["simulated"] is True and d["count"] >= 1
    assert all(x["status"] == "active" for x in d["records"])
    assert all(x["four_requirements"]["legal_signature_ok"] for x in d["records"])
    r3 = client.get("/api/v1/authorization/query",
                    params={"status": "moon"}, headers=h)
    assert r3.status_code == 400
