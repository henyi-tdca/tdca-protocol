# -*- coding: utf-8 -*-
"""A-23 公告栏测试（/api/v1/announcements/*）。

验收映射：① 公开读取（无登录 200、初始空栏 count=0、⛔ 无预置内容）
          ② 发布权限（viewer 403；operator 201）
          ③ 空标题/正文 400
          ④ 发布后公开列表可见 + NCA 存证落链（data_provenance=real）
"""
import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "Ts-pass-2026"


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


def test_public_list_empty_200():
    """公开读取：无登录可访问；初始空栏如实报 count=0（⛔ 不预置内容）。"""
    r = client.get("/api/v1/announcements/list")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["count"] == 0
    assert d["announcements"] == []


def test_viewer_publish_403():
    r = client.post("/api/v1/announcements/publish",
                    json={"title": "某公告", "body": "正文"},
                    headers=_auth("anntester01"))
    assert r.status_code == 403


def test_empty_title_400():
    h = _auth("anntester02", role="operator")
    r = client.post("/api/v1/announcements/publish",
                    json={"title": "  ", "body": "正文"}, headers=h)
    assert r.status_code == 400
    r2 = client.post("/api/v1/announcements/publish",
                     json={"title": "标题", "body": ""}, headers=h)
    assert r2.status_code == 400


def test_publish_and_public_readback_201():
    """operator 发布 → 公开列表回读可见 → 落库 real + NCA 存证链。"""
    h = _auth("anntester03", role="operator")
    r = client.post("/api/v1/announcements/publish",
                    json={"title": "站点一期上线说明", "body": "公告栏功能上线，本公告为机验用测试内容。"},
                    headers=h)
    assert r.status_code == 201, r.text
    aid = r.json()["data"]["announcement_id"]
    assert aid.startswith("AN-")
    # 公开回读（无登录）
    r2 = client.get("/api/v1/announcements/list")
    assert r2.status_code == 200
    d = r2.json()["data"]
    assert d["count"] >= 1
    hit = next(a for a in d["announcements"] if a["announcement_id"] == aid)
    assert hit["title"] == "站点一期上线说明"
    assert hit["body"]
    # 落库与存证链
    with get_sessionmaker().begin() as s:
        row = s.get(M.Announcement, aid)
        assert row is not None and row.data_provenance == "real"
        assert row.nca_ref is not None
        nca = s.get(M.NcaChain, row.nca_ref)
        assert nca is not None and nca.action == "SiteAnnounce"
