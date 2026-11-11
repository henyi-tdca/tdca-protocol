# -*- coding: utf-8 -*-
"""kg_ops 只读面测试（夹具＝对外包同构微型包；L1SI211-KG-SITE-001）。"""
import os

import pytest
from fastapi.testclient import TestClient

NODES = """nodes:
- id: n0001
  layer: L0
  layer_name: 宪法层
  type: Constitution
  type_name: 宪法条款
  label: 场景边界
- id: n0002
  layer: L0
  layer_name: 宪法层
  type: Principle
  type_name: 原则
  label: 所有权层
- id: n0003
  layer: L1
  layer_name: 协议规范层
  type: FunctionSpec
  type_name: 功能规约
  label: 配置权市场规范
"""

EDGES = """edges:
- id: e00001
  type: DERIVES_FROM
  source: n0001
  target: n0002
- id: e00002
  type: IMPLEMENTS
  source: n0003
  target: n0001
"""

MANIFEST = "package: TDCA Knowledge Graph V1 · Public\ncounts:\n  nodes: 3\n"
README = "# TDCA 知识图谱 · 对外结构包\n"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    d = tmp_path / "kg" / "v1"
    d.mkdir(parents=True)
    (d / "nodes.yaml").write_text(NODES, encoding="utf-8")
    (d / "edges.yaml").write_text(EDGES, encoding="utf-8")
    (d / "manifest.yaml").write_text(MANIFEST, encoding="utf-8")
    (d / "README.md").write_text(README, encoding="utf-8")
    monkeypatch.setenv("TDCA_KG_DIR", str(d))
    import kg_ops
    kg_ops._CACHE = None
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(kg_ops.router)
    return TestClient(app)


def test_static_files_ok(client):
    for name in ("manifest.yaml", "nodes.yaml", "edges.yaml", "README.md"):
        r = client.get("/kg/v1/" + name)
        assert r.status_code == 200, name
        assert len(r.headers["X-Content-SHA256-16"]) == 16


def test_static_unknown_404(client):
    assert client.get("/kg/v1/secret.yaml").status_code == 404
    assert client.get("/kg/v1/../nodes.yaml").status_code == 404


def _d(r):
    """解 ID91 信封并核验水印三字段（前端统一客户端缺印拒绝渲染的回归判据）。"""
    body = r.json()
    assert body["nca_watermark"].startswith("sha256:")
    assert body["data_nature"] == "real"
    assert body["ts"]
    return body["data"]


def test_manifest_sha(client):
    r = client.get("/api/v1/kg/manifest")
    assert r.status_code == 200
    assert _d(r)["sha256_16"]


def test_nodes_filter(client):
    r = client.get("/api/v1/kg/nodes", params={"layer": "L0"})
    assert _d(r)["count"] == 2
    r = client.get("/api/v1/kg/nodes", params={"q": "配置权"})
    assert _d(r)["count"] == 1
    r = client.get("/api/v1/kg/nodes", params={"type": "Principle"})
    assert _d(r)["count"] == 1


def test_node_detail_with_relations(client):
    r = client.get("/api/v1/kg/node/n0001")
    body = _d(r)
    assert body["node"]["label"] == "场景边界"
    assert [e["type"] for e in body["out_edges"]] == ["DERIVES_FROM"]
    assert [e["type"] for e in body["in_edges"]] == ["IMPLEMENTS"]


def test_node_unknown_404(client):
    assert client.get("/api/v1/kg/node/n9999").status_code == 404
    assert client.get("/api/v1/kg/node/..%2Fetc").status_code == 404


def test_subgraph_depth(client):
    r = client.get("/api/v1/kg/subgraph", params={"root": "n0001", "depth": 1})
    body = _d(r)
    assert {n["id"] for n in body["nodes"]} == {"n0001", "n0002", "n0003"}
    r = client.get("/api/v1/kg/subgraph", params={"root": "n0001", "depth": 2})
    assert r.status_code == 200


def test_edges_filter(client):
    r = client.get("/api/v1/kg/edges", params={"type": "IMPLEMENTS"})
    assert _d(r)["count"] == 1


def test_write_methods_405(client):
    assert client.post("/api/v1/kg/nodes").status_code == 405
    assert client.post("/kg/v1/nodes.yaml").status_code == 405
