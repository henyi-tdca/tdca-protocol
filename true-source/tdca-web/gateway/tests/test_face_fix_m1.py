# -*- coding: utf-8 -*-
"""FACE-FIX-001 机面三键与自陈测试（M-1／M-4）。

验收映射（令面判据 J-3）：
  ① 四匿名端点（announcements/list、toolshelf/catalog、kg/manifest、selfcheck/spec）
    信封顶层含 permission／data_source／schema_version 三键，值齐（M-1）
  ② /health 未达 M-1 → 自陈 conformance: pending-migration（M-4）
  ③ 三键取值与 api_v1._CONSUMER_FACE_M1 集中定义一致（⛔ 端点自改数值）
夹具：kg 为包内实读（real）面，须微型包在场（同 test_kg_ops 口径），
     fail-closed 503 路径不在本件断言范围（该路径信封由 _unavailable 直出）。
"""
import pytest
from fastapi.testclient import TestClient

import api_v1
import kg_ops

from app import app

client = TestClient(app)

M1_KEYS = ("permission", "data_source", "schema_version")

_KG_MANIFEST = "package: TDCA Knowledge Graph V1 · Public\ncounts:\n  nodes: 3\n"
_KG_README = "# TDCA 知识图谱 · 对外结构包\n"
_KG_NODES = "nodes:\n- id: n0001\n  layer: L0\n  type: Constitution\n  label: 场景边界\n"
_KG_EDGES = "edges:\n- id: e00001\n  type: DERIVES_FROM\n  source: n0001\n  target: n0001\n"


@pytest.fixture(autouse=True)
def _kg_pack(tmp_path, monkeypatch):
    """kg 微型包夹具（含 teardown 清缓存；四端点其余三端点不受此夹具影响）。"""
    d = tmp_path / "kg" / "v1"
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(_KG_MANIFEST, encoding="utf-8")
    (d / "README.md").write_text(_KG_README, encoding="utf-8")
    (d / "nodes.yaml").write_text(_KG_NODES, encoding="utf-8")
    (d / "edges.yaml").write_text(_KG_EDGES, encoding="utf-8")
    monkeypatch.setenv("TDCA_KG_DIR", str(d))
    kg_ops._CACHE = None
    yield
    kg_ops._CACHE = None


@pytest.mark.parametrize("path", [
    "/api/v1/announcements/list",
    "/api/v1/toolshelf/catalog",
    "/api/v1/kg/manifest",
    "/api/v1/selfcheck/spec",
])
def test_m1_three_keys_present(path):
    """M-1：四匿名端点信封顶层三键在位。"""
    r = client.get(path)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    for k in M1_KEYS:
        assert k in body, f"{path} 缺信封键 {k}（现顶层键：{sorted(body)}）"
    assert body["permission"] == "公开（匿名可用）"
    assert body["data_source"] == "TDCA-STD-L1SI212-CONSUMER-FACE-001"
    assert body["schema_version"] == "TDCA-API-SHAPE-STANDARD-001/V1.0"


def test_m1_keys_match_central_definition():
    """三键取值集中 _CONSUMER_FACE_M1，端点不得自改。"""
    central = api_v1._consumer_face_m1()
    r = client.get("/api/v1/selfcheck/spec")
    body = r.json()
    for k in M1_KEYS:
        assert body[k] == central[k]


def test_health_self_declares_pending_migration():
    """M-4：/health 无标准信封，须自陈过渡态（⛔ 静默缺键）。"""
    r = client.get("/health")
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("conformance") == "pending-migration"
    assert body.get("status") == "OK"
