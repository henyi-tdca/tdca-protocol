# -*- coding: utf-8 -*-
"""公开只读制度件取得面自核（丙案 · L1SI151-PUBLIC-ROUTE-001）。

验收映射（施工令 §四步2 四项）：
  ① 匿名取列表（含甲类 8 件、不含未入站/乙类）
  ② 匿名取件（sha256 与内容逐位一致）
  ③ 未入站件取不到（统一 404，fail-closed）
  ④ 乙类件取不到（且不在列表）
  附：未知族 404／限流 429／旧别名 /api/site/docs 同一实现／写方法 405
"""
import hashlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import public_docs_ops

from app import app

client = TestClient(app)

_DOCS = list(public_docs_ops._PUBLIC_DOCS["regulation"])  # 本面既有用例锁定 regulation 族

_EXTRA = "README.md"
_YILEI = "TDCA-SIGNOFF-SCENE-ENCOUNTER-001-场景线·相遇专章·签批记录（条例·创始人签批·V1.0生效）.md"


@pytest.fixture(autouse=True)
def _docs_dir(tmp_path, monkeypatch):
    d = tmp_path / "docs" / "regulations"
    d.mkdir(parents=True)
    for name in _DOCS:
        body = (f"件号测试占位\n版本: **V9.9-TEST**\n正文占位 {name}\n").encode("utf-8")
        (d / name).write_bytes(body)
    (d / _EXTRA).write_text("未入站件不得出现", encoding="utf-8")
    (d / _YILEI).write_text("乙类存证件不得出现 GSEQ-3965", encoding="utf-8")
    monkeypatch.setenv("TDCA_PUBLIC_DOCS_DIR", str(d))
    public_docs_ops._hits.clear()
    yield
    public_docs_ops._hits.clear()


def test_anonymous_list_only_public_eight():
    r = client.get("/api/public/docs")
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    assert data["count"] == len(_DOCS)  # 动态取 regulation 族在册数（多族承载后 _PUBLIC_DOCS 为分族映射）
    names = {e["filename"] for e in data["documents"]}
    assert names == set(_DOCS)
    assert _EXTRA not in names and _YILEI not in names
    for e in data["documents"]:
        assert e["family"] == "regulation"
        assert e["sha256_16"] == e["sha256"].upper()[:16]
        assert e["version"]  # 件内真实版本可读


def test_anonymous_get_doc_sha256_matches():
    name = _DOCS[0]
    r = client.get(f"/api/public/docs/regulation/{name}")
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    raw = data["content"].encode("utf-8")
    assert data["sha256"] == hashlib.sha256(raw).hexdigest()
    assert data["filename"] == name and data["family"] == "regulation"
    assert "正文占位" in data["content"]


def test_unlisted_doc_not_found():
    r = client.get(f"/api/public/docs/regulation/{_EXTRA}")
    assert r.status_code == 404


def test_evidence_doc_never_appears():
    r_list = client.get("/api/public/docs")
    assert _YILEI not in {e["filename"] for e in r_list.json()["documents"]}
    r_get = client.get(f"/api/public/docs/regulation/{_YILEI}")
    assert r_get.status_code == 404


def test_unknown_family_404():
    assert client.get("/api/public/docs/whitepaper").status_code == 404
    assert client.get("/api/public/docs/whitepaper/x.md").status_code == 404


def test_alias_same_implementation():
    r1 = client.get("/api/public/docs")
    r2 = client.get("/api/site/docs")
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    name = _DOCS[1]
    ra = client.get(f"/api/site/docs/regulation/{name}")
    rb = client.get(f"/api/public/docs/regulation/{name}")
    assert ra.status_code == rb.status_code == 200
    assert ra.json() == rb.json()


def test_rate_limit_429():
    ok = 0
    last = None
    for _ in range(65):
        last = client.get("/api/public/docs")
        if last.status_code == 200:
            ok += 1
    assert ok == 60, f"放行 {ok} 次（应恰 60）"
    assert last.status_code == 429


def test_write_methods_not_open():
    assert client.post("/api/public/docs").status_code == 405
    assert client.put("/api/public/docs/regulation/x").status_code == 405
    assert client.delete("/api/public/docs/regulation/x").status_code == 405


def test_missing_public_doc_fail_closed_503(tmp_path, monkeypatch):
    d = tmp_path / "empty" / "docs" / "regulations"
    d.mkdir(parents=True)
    (d / _DOCS[0]).write_text("独一件", encoding="utf-8")  # 其余 7 件缺失
    monkeypatch.setenv("TDCA_PUBLIC_DOCS_DIR", str(d))
    r = client.get("/api/public/docs")
    body = r.json()
    assert r.status_code == 503
    assert body["code"] == "TDCA-E-EXT-EXT-001" and "文档源异常" in body["detail"]
    assert body["error"] == "DOC_SOURCE_UNAVAILABLE"  # 段三②：过渡期两存（deprecated，下版删）
