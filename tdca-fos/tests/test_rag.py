# -*- coding: utf-8 -*-
"""
TDCA-RAG 检索引擎测试
制度锚定: TDCA-KB-001 §5（RAG 架构）| TERMS-001 | FC: TDCA-FC-20260804-006-M5
SPDX-License-Identifier: TDCA-Internal
"""

import os
import pytest

from tdca_rag.engine import TDCARAGEngine, CORE_TERMS

# 可移植路径解析（修复跨机器硬编码——workspace 相对上溯，替代旧机器绝对路径）
_WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KB = os.path.join(_WS, "tdca-official-kb")
AUTH = os.path.join(_WS, "_authority_text")
PDF = os.path.join(_WS, "_pdf_text")


@pytest.fixture(scope="module")
def engine():
    return TDCARAGEngine(KB, extra_dirs=[AUTH, PDF])


class TestIndex:
    """索引构建"""

    def test_doc_count(self, engine):
        assert engine.doc_count() >= 35  # 知识库 36 + 权威 2 + 专著 2 减去部分

    def test_layers_present(self, engine):
        counts = engine.layer_counts()
        assert counts.get("L0", 0) >= 5
        assert counts.get("L1", 0) >= 5
        assert counts.get("L2", 0) >= 5

    def test_core_terms_defined(self):
        assert len(CORE_TERMS) >= 20


class TestSearch:
    """检索质量"""

    def test_constitution_search(self, engine):
        rs = engine.search("宪法十六条", top_k=5)
        assert len(rs) > 0
        # 应命中宪法相关文档
        assert any("宪法" in r.title or "宪法" in r.snippet for r in rs)

    def test_mou_search(self, engine):
        rs = engine.search("MOU 税收锚定", top_k=3)
        assert len(rs) > 0
        # KB-ECON-001 含 MOU 权威内容
        assert any("ECON" in r.doc_id or "MOU" in r.snippet for r in rs)

    def test_value_vector_search(self, engine):
        rs = engine.search("五维价值向量", top_k=3)
        assert len(rs) > 0
        assert any("V=(U" in r.snippet or "U,S,F,C,R" in r.snippet or "价值向量" in r.snippet for r in rs)

    def test_top_k_limit(self, engine):
        rs = engine.search("配置权", top_k=3)
        assert len(rs) <= 3

    def test_layer_filter(self, engine):
        rs = engine.search("宪法", top_k=10, layer_filter="L0")
        assert len(rs) > 0
        assert all(r.layer == "L0" for r in rs)

    def test_min_score_filter(self, engine):
        rs = engine.search("宪法十六条", top_k=10, min_score=1.0)
        assert all(r.score >= 1.0 for r in rs)

    def test_empty_query(self, engine):
        rs = engine.search("")
        assert rs == []


class TestTraceability:
    """溯源标注（NSFL：检索必须可溯源）"""

    def test_result_has_source(self, engine):
        rs = engine.search("正和博弈", top_k=3)
        assert len(rs) > 0
        for r in rs:
            assert r.source and os.path.exists(r.source)
            assert r.layer in {"L0", "L1", "L2"}
            assert r.title

    def test_snippet_nonempty(self, engine):
        rs = engine.search("配置权第三极", top_k=3)
        for r in rs:
            assert r.snippet  # 片段非空

    def test_score_positive(self, engine):
        rs = engine.search("MOU", top_k=3)
        for r in rs:
            assert r.score > 0
