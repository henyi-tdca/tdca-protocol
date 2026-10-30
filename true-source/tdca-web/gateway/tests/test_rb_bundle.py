# -*- coding: utf-8 -*-
"""BUNDLE-001 权利束＋保留束过渡承载测试（#RB 前缀＋单行 JSON；十三项校验）。"""
import json

import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import models as M
from rights_bundle import RB_BASIS, RB_STAGE, RB_THIRTEEN

client = TestClient(app)

_PW = "RB-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth(uname="rbtester01"):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _rb_note(granted, retained, tail=""):
    core = "#RB" + json.dumps(
        {"granted": granted, "retained": retained,
         "basis": RB_BASIS, "stage": RB_STAGE}, ensure_ascii=False)
    return core + ((" " + tail) if tail else "")


def _or_body(**over):
    body = {"work_title": "权利束样例作品", "owner_ref": "rbtester01",
            "source_lineage": "测试谱系"}
    body.update(over)
    return body


GRANT_TWO = ["复制权", "信息网络传播权"]
RETAIN_REST = [x for x in RB_THIRTEEN if x not in GRANT_TWO]
RETAIN_NO_OTHER = [x for x in RETAIN_REST if x != "其他权利"]


def test_rb_valid_note_stored_transition():
    h = _auth()
    note = _rb_note(GRANT_TWO, RETAIN_REST, "人话备注保留")
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note=note), headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert "rb_anomaly" not in d
    rid = d["record_id"]
    q = client.get(f"/api/v1/ownership/query/{rid}", headers=h).json()["data"]
    stored = q["record"]["note"]
    assert stored.startswith("#RB{")
    assert '"stage": "transition"' in stored or '"stage":"transition"' in stored
    assert "人话备注保留" in stored  # ⛔ 删用户输入


def test_rb_invalid_name_rejected_human_message():
    h = _auth("rbtester02")
    note = _rb_note(["使用权"], RETAIN_REST)
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note=note), headers=h)
    assert r.status_code == 400
    assert "'使用权'不是法定项名" in r.text
    assert "复制权" in r.text  # 人话：附十三项清单


def test_rb_other_rights_requires_explanation():
    h = _auth("rbtester03")
    retained = [x for x in RB_THIRTEEN if x != "复制权"]
    note = _rb_note(["复制权", "其他权利"], retained)
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note=note), headers=h)
    assert r.status_code == 400
    assert "其他权利" in r.text and "说明" in r.text
    # 附说明 → 照收
    note2 = _rb_note(["复制权", "其他权利"], retained, "兜底项说明一句")
    r2 = client.post("/api/v1/ownership/register",
                     json=_or_body(note=note2), headers=h)
    assert r2.status_code == 201, r2.text


def test_rb_fixed_basis_stage_and_missing_key():
    h = _auth("rbtester04")
    bad = json.dumps({"granted": ["复制权"], "retained": RETAIN_REST,
                      "basis": "随便", "stage": "transition"}, ensure_ascii=False)
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note="#RB" + bad), headers=h)
    assert r.status_code == 400 and "basis" in r.text
    bad2 = json.dumps({"granted": ["复制权"], "retained": RETAIN_REST,
                       "basis": RB_BASIS, "stage": "final"}, ensure_ascii=False)
    r2 = client.post("/api/v1/ownership/register",
                     json=_or_body(note="#RB" + bad2), headers=h)
    assert r2.status_code == 400 and "stage" in r2.text
    bad3 = json.dumps({"granted": ["复制权"], "retained": RETAIN_REST,
                       "basis": RB_BASIS}, ensure_ascii=False)
    r3 = client.post("/api/v1/ownership/register",
                     json=_or_body(note="#RB" + bad3), headers=h)
    assert r3.status_code == 400 and "stage" in r3.text


def test_rb_compatible_with_negative_space_scan():
    h = _auth("rbtester05")
    note = _rb_note(GRANT_TWO, RETAIN_REST, "说明文字")
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note=note), headers=h)
    assert r.status_code == 201, r.text  # #RB 与项名不误伤
    # 自由文本里塞凭据 → 仍被负空间拦截（RB 校验在前、负空间在后，两层俱在）
    evil = _rb_note(GRANT_TWO, RETAIN_REST, "api_key: sk-abcdef1234567890")
    r2 = client.post("/api/v1/ownership/register",
                     json=_or_body(note=evil), headers=h)
    assert r2.status_code == 400
    assert "PUBLIC_SPACE_VIOLATION" in r2.text


def test_rb_duplicate_prefix_last_wins_and_anomaly():
    h = _auth("rbtester06")
    first = _rb_note(["表演权"], [x for x in RB_THIRTEEN if x != "表演权"])
    second = _rb_note(GRANT_TWO, RETAIN_REST, "最终以这条为准")
    note = first + "\n" + second
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note=note), headers=h)
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert "rb_anomaly" in d and "最后一条" in d["rb_anomaly"]


def test_rb_p8b_register_and_amend_paths():
    h = _auth("rbtester07")
    body = {"asset_ref": "资产族样例", "grantee_ref": "被授权方-乙",
            "scene": "生产交付（内循环部署与运行）",
            "req_scene": True, "req_five_forms": True,
            "req_full_grant": True, "req_legal_signature": True,
            "note": _rb_note(GRANT_TWO, RETAIN_NO_OTHER)}
    r = client.post("/api/v1/authorization/register", json=body, headers=h)
    assert r.status_code == 201, r.text
    rid = r.json()["data"]["record_id"]
    stored = client.get(f"/api/v1/authorization/query/{rid}",
                        headers=h).json()["data"]["record"]["note"]
    assert stored.startswith("#RB{")
    # amend 带非法项名 → 400 人话
    bad = client.post("/api/v1/authorization/amend",
                      json={"record_id": rid,
                            "note": _rb_note(["转播权"], RETAIN_REST)}, headers=h)
    assert bad.status_code == 400
    assert "转播权" in bad.text


def test_rb_plain_note_untouched():
    h = _auth("rbtester08")
    r = client.post("/api/v1/ownership/register",
                    json=_or_body(note="普通备注，无权利束"), headers=h)
    assert r.status_code == 201, r.text
    q = client.get(f"/api/v1/ownership/query/"
                   f"{r.json()['data']['record_id']}", headers=h)
    assert q.json()["data"]["record"]["note"] == "普通备注，无权利束"
