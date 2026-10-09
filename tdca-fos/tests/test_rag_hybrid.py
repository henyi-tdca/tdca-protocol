# -*- coding: utf-8 -*-
"""
TDCA-RAG 混合检索测试（向量增强）
制度锚定: TDCA-KB-001 §5（RAG 架构：hybrid vector + keyword + rerank）
版本: V1.0 | FC: TDCA-FC-20260804-006-M5
SPDX-License-Identifier: TDCA-Internal
"""

import os
import pytest

from tdca_rag.engine import TDCARAGEngine

# 可移植路径解析（修复跨机器硬编码——workspace 相对上溯）
_WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KB = os.path.join(_WS, "tdca-official-kb")
AUTH = os.path.join(_WS, "_authority_text")
PDF = os.path.join(_WS, "_pdf_text")


@pytest.fixture(scope="module")
def engine():
    return TDCARAGEngine(KB, extra_dirs=[AUTH, PDF])


class TestVectorSearch:
    """纯向量检索"""

    def test_vector_returns_results(self, engine):
        rs = engine.search_vector("配置权第三极", top_k=3)
        assert len(rs) > 0
        for r in rs:
            assert 0 < r.score <= 1.0  # 余弦相似度范围

    def test_vector_ranked(self, engine):
        rs = engine.search_vector("MOU 税收锚定", top_k=5)
        scores = [r.score for r in rs]
        assert scores == sorted(scores, reverse=True)

    def test_vector_layer_filter(self, engine):
        rs = engine.search_vector("宪法", top_k=10, layer_filter="L0")
        assert len(rs) > 0
        assert all(r.layer == "L0" for r in rs)

    def test_vector_empty_query(self, engine):
        assert engine.search_vector("") == []


class TestHybridSearch:
    """混合检索（BM25 + 向量融合）"""

    def test_hybrid_returns_results(self, engine):
        rs = engine.search_hybrid("配置权第三极", top_k=5)
        assert len(rs) > 0

    def test_hybrid_recall_ge_bm25(self, engine):
        """语义查询（近义词，BM25 可能漏召回）：混合检索召回 >= 纯 BM25"""
        q = "智能体协作 可信机制"
        bm = engine.search(q, top_k=10)
        hy = engine.search_hybrid(q, top_k=10)
        assert len(hy) >= len(bm)

    def test_hybrid_fusion_score_range(self, engine):
        rs = engine.search_hybrid("五维价值向量", top_k=5)
        for r in rs:
            assert 0 <= r.score <= 1.2  # 融合分（归一化 + 重排加成上限）

    def test_hybrid_layer_filter(self, engine):
        rs = engine.search_hybrid("宪法十六条", top_k=10, layer_filter="L0")
        assert len(rs) > 0
        assert all(r.layer == "L0" for r in rs)

    def test_hybrid_alpha_bm25_dominant(self, engine):
        """alpha=1 时退化为纯 BM25 分数（归一化）"""
        rs_a = engine.search_hybrid("MOU", top_k=5, alpha=1.0)
        assert len(rs_a) > 0

    def test_hybrid_alpha_vector_dominant(self, engine):
        """alpha=0 时以向量为主"""
        rs = engine.search_hybrid("MOU 税收", top_k=5, alpha=0.0)
        assert len(rs) > 0

    def test_hybrid_rerank_terms(self, engine):
        """术语重排：命中重排词加权"""
        rs = engine.search_hybrid("资产定价", top_k=5,
                                  rerank_terms=["配置权", "Shapley"])
        assert len(rs) > 0

    def test_hybrid_traceability(self, engine):
        """混合检索结果仍带溯源"""
        rs = engine.search_hybrid("正和博弈", top_k=3)
        for r in rs:
            assert r.source and r.title and r.layer in {"L0", "L1", "L2"}


class TestBackwardCompat:
    """旧接口兼容（不破坏既有调用）"""

    def test_search_unchanged(self, engine):
        rs = engine.search("配置权", top_k=3)
        assert len(rs) <= 3
        assert all(r.score > 0 for r in rs)

    def test_search_min_score_unchanged(self, engine):
        rs = engine.search("宪法十六条", top_k=10, min_score=1.0)
        assert all(r.score >= 1.0 for r in rs)

    def test_hybrid_snippet_nonempty(self, engine):
        rs = engine.search_hybrid("UPDA 协议", top_k=3)
        for r in rs:
            assert r.snippet
