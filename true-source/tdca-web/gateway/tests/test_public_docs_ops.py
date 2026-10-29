# -*- coding: utf-8 -*-
"""公开只读制度件取得面自核（丙案 · L1SI151-PUBLIC-ROUTE-001）。

验收映射（施工令 §四步2 四项）：
  ① 匿名取列表（含甲类 8 件、不含未入站件）
  ② 匿名取件（sha256 与内容逐位一致）
  ③ 未入站件取不到（统一 404，fail-closed）
  ④ ~~乙类件取不到~~（L1SI180-TERMS-004/005 甲案解除：签批记录已改写零命中并入册上站，
     原「乙类不得出现」之负向用例改为「新三件正向在架」用例，见 test_yilei_batch2_now_listed）
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
    # L1SI180-TERMS-004/005：_YILEI（签批记录）已改写零命中并入册上站，乙类负向前提解除，不再作暗桩
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
    assert _EXTRA not in names  # L1SI180-TERMS-004/005：_YILEI 已依规入册，不再负向断言
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


def test_yilei_batch2_now_listed():
    """L1SI180-TERMS-004/005 甲案：入站批 2 三件（含原乙类签批记录）已合规入册上站——
    列表可见且逐件可取（原 test_evidence_doc_never_appears 之负向前提解除，正向替代）。"""
    r_list = client.get("/api/public/docs")
    listed = {e["filename"] for e in r_list.json()["documents"]}
    for name in (
        "TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-追认附记.md",
        _YILEI,
        "TDCA-TEMPLATE-AUTH-001-生效注记.md",
    ):
        assert name in listed
        r_get = client.get(f"/api/public/docs/regulation/{name}")
        assert r_get.status_code == 200, r_get.text[:200]


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


def test_display_name_mapping_no_draft():
    """L1SI154-011 段C：显示名去 DRAFT 且路径/slug 一字不改（防断链）。"""
    r = client.get("/api/public/docs")
    assert r.status_code == 200, r.text[:200]
    docs = {e["filename"]: e for e in r.json()["documents"]}
    mapped = public_docs_ops._DISPLAY_NAME
    assert mapped, "显示名映射不得为空"
    for fname, disp in mapped.items():
        assert fname in docs, f"映射键不在在册清单: {fname}"
        assert "DRAFT" not in disp and "未生效" not in disp, disp
    for fname, e in docs.items():
        assert e["slug"] == fname and e["filename"] == fname  # 路径/slug 不改
        assert e["display_name"] == mapped.get(fname, fname)  # 未映射件=文件名
        assert e["sha256_16"] == e["sha256"].upper()[:16]  # 哈希口径不变
    # 旧路径取件仍 200，取件包壳同样带显示名，sha 口径不变
    name = next(iter(mapped))
    r2 = client.get(f"/api/public/docs/regulation/{name}")
    assert r2.status_code == 200, r2.text[:200]
    body2 = r2.json()
    assert body2["display_name"] == mapped[name]
    import hashlib as _hl
    assert body2["sha256"] == _hl.sha256(body2["content"].encode("utf-8")).hexdigest()


def test_ingest002_list_42_no_droop():
    """L1SI155-INGEST-002 防掉条用例：regulation 族 47 条（L1SI180-TERMS-004/005 三件上站后 44→47）；
    L1SI154-028 九件与新入册 16 件一件不缺（防"掉条回落"）。"""
    r = client.get("/api/public/docs/regulation")
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    assert data["count"] == 47, f"清单条数漂移: {data['count']}"
    返回集 = {e["filename"] for e in data["documents"]}
    在册集 = set(public_docs_ops._PUBLIC_DOCS["regulation"])  # 以测试现行 import 风格取用
    assert 返回集 == 在册集, f"与在册清单不等：缺 {sorted(在册集 - 返回集)} 多 {sorted(返回集 - 在册集)}"
    names = {e["filename"] for e in data["documents"]}
    must = {
        # L1SI154-028 九件（部署面已入册，⛔ 不得掉回不可见）
        "TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md",
        "TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md",
        "TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md",
        "TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md",
        "TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md",
        "TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md",
        "TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md",
        "TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md",
        "TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md",
        # L1SI155-INGEST-002 新 16 件
        "TDCA-PUB-CORPUS-069-惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md",
        "TDCA-PUB-CORPUS-070-租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md",
        "TDCA-PUB-CORPUS-071-IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md",
        "TDCA-PUB-CORPUS-074-制度治理规范对外纯版（六判据链·英文待补）.md",
        "TDCA-PUB-CORPUS-058-流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md",
        "TDCA-PUB-CORPUS-101-流程环节卡授权配置（五问·七类失败·第1张卡补五问版）.md",
        "TDCA-PUB-CORPUS-102-流程环节卡结算计税（五问·七类失败·第2张卡补五问版）.md",
        "TDCA-PUB-CORPUS-097-流程环节卡谈判（五问·七类失败·第10张卡）.md",
        "TDCA-PUB-CORPUS-098-流程环节卡试错（五问·七类失败·第11张卡）.md",
        "TDCA-PUB-CORPUS-099-流程环节卡验证（五问·七类失败·第12张卡）.md",
        "TDCA-PUB-CORPUS-100-流程环节卡履约准备（五问·七类失败·第13张卡）.md",
        "TDCA-PUB-CORPUS-093-流程环节卡履约（五问·七类失败·第14张卡）.md",
        "TDCA-PUB-CORPUS-094-流程环节卡结算分配（五问·七类失败·第15张卡）.md",
        "TDCA-PUB-CORPUS-095-流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md",
        "TDCA-PUB-CORPUS-096-流程环节卡争议裁决（五问·七类失败·第17张卡）.md",
        "TDCA-PUB-CORPUS-103-授权件模板对外版（中文人读·V1.0-FROZEN按签批更正版本面貌·八字段与四要件）.md",
    }
    missing = must - names
    assert not missing, f"掉条: {missing}"
