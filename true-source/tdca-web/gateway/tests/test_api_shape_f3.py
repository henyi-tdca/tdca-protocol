# -*- coding: utf-8 -*-
"""API-SHAPE 步 2（F-3 六端点兼容期）：新旧形态并存实测。

判据（SHAPE-STEP1-001 §三）：旧键全保留 ≥1 版；新键 data.items/data.total
与信封四键并存；既有前端读旧键不坏。"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _data(path):
    r = client.get(path)
    assert r.status_code == 200, (path, r.status_code)
    j = r.json()
    assert set(("data", "nca_watermark", "ts", "data_nature")) <= set(j), path
    return j["data"]


def test_f3_announcements_dual_shape():
    d = _data("/api/v1/announcements/list")
    assert isinstance(d.get("announcements"), list)      # 旧键保留
    assert d.get("items") == d.get("announcements")      # 新键同值
    assert d.get("total") == d.get("count")


def test_f3_five_orders_dual_shape():
    d = _data("/api/v1/assets/five-orders")
    assert isinstance(d.get("assets"), list) and len(d["assets"]) == 5
    assert d.get("items") == d.get("assets")
    assert d.get("total") == 5


def test_f3_terms_dual_shape():
    d = _data("/api/v1/knowledge/terms")
    assert isinstance(d.get("terms"), list)
    assert d.get("items") == d.get("terms")
    assert d.get("total") == len(d["terms"])


def test_f3_ledger_public_dual_shape():
    d = _data("/api/v1/audit/ledger-public")
    assert isinstance(d.get("events"), list)
    assert d.get("items") == d.get("events")
    assert "total" in d and "next_cursor" in d           # 游标键不受影响


def test_f3_library_families_dual_shape():
    r = client.get("/api/v1/library/families")             # 匿名面
    if r.status_code == 503:
        import pytest
        pytest.skip("测试沙箱缺文库内容目录，端点如实 503（环境限，非形态问题）")
    d = r.json()["data"]
    assert isinstance(d.get("items"), list)
    assert d.get("total") == len(d["items"])


def test_f3_conclusion_catalog_dual_shape():
    d = _data("/api/v1/formal/conclusion/catalog")
    assert isinstance(d.get("conclusions"), list)
    assert d.get("items") == d.get("conclusions")
    assert d.get("total") == d.get("count")
