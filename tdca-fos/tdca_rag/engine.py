# -*- coding: utf-8 -*-
"""
TDCA-RAG 检索引擎 — 官方知识库 L2 场景层检索（TDCA-KB-001 §5）
制度锚定: TDCA-KB-001（3L-KB RAG 架构：混合检索/重排/过滤/溯源）| TERMS-001 术语合规
版本: V1.0 | 状态: M5-CODED | FC: TDCA-FC-20260804-006-M5

纯 Python 实现（无外部服务依赖）：
  - BM25 关键词检索（内置实现，无需 sklearn）
  - 术语加权（TDCA 核心术语 boost）
  - 溯源标注（每结果含 source 文件 + 层级）
  - 混合检索排序 + 过滤（layer/type）
NSFL-Declaration:
  - 检索结果必须溯源标注（禁止无源结论）
  - 术语使用遵循 TERMS-001（检索词归一化）
SPDX-License-Identifier: TDCA-Internal
"""

import math
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# TDCA 核心术语表（TERMS-001 核心概念，检索加权）
CORE_TERMS = [
    "配置权", "MOU", "NCA", "宪法十六条", "正和博弈", "Shapley", "UPDA",
    "负空间", "NSFL", "五元拓扑", "嵌套认知资产", "制度基座", "效用函数",
    "所有权", "用益权", "场景配置权", "S-Right", "C-Right", "主题共鸣",
    "五维价值向量", "税收锚定", "配置权第三极", "接口熵", "OTA",
]


@dataclass
class RetrievalResult:
    """检索结果项"""
    doc_id: str
    title: str
    layer: str              # L0/L1/L2
    source: str             # 溯源文件
    score: float
    snippet: str = ""


@dataclass
class IndexedDoc:
    """索引文档"""
    doc_id: str
    title: str
    layer: str
    source: str
    text: str
    terms: Dict[str, int] = field(default_factory=dict)  # 词频
    length: int = 0


class TDCARAGEngine:
    """
    TDCA 官方知识库检索引擎
    :param corpus_dir: 知识库根目录（递归索引 .md/.txt/.yaml/.json）
    :param extra_dirs: 额外语料目录（权威文件/专著全文）
    """

    def __init__(self, corpus_dir: str, extra_dirs: Optional[List[str]] = None):
        self.corpus_dir = corpus_dir
        self.docs: Dict[str, IndexedDoc] = {}
        self.avgdl = 0.0
        self.k1 = 1.5
        self.b = 0.75
        self._build_index(corpus_dir, extra_dirs or [])

    # ==================== 索引构建 ====================

    def _build_index(self, corpus_dir: str, extra_dirs: List[str]):
        """构建文档索引（词频 + 长度）"""
        dirs = [corpus_dir] + extra_dirs
        for d in dirs:
            for root, _, fns in os.walk(d):
                for fn in fns:
                    if not fn.endswith((".md", ".txt", ".yaml", ".yml", ".json")):
                        continue
                    if "__pycache__" in root or ".pytest_cache" in root:
                        continue
                    path = os.path.join(root, fn)
                    self._index_file(path)

        # 平均文档长度
        if self.docs:
            self.avgdl = sum(d.length for d in self.docs.values()) / len(self.docs)

    def _index_file(self, path: str):
        """索引单个文件"""
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            return
        if len(text) < 20:
            return

        rel = os.path.relpath(path, self.corpus_dir)
        doc_id = rel.replace(os.sep, "/")
        # 层级推断
        layer = self._infer_layer(rel)
        # 标题 = 首行非空
        title = next((ln.strip().lstrip("# ").strip() for ln in text.split("\n")
                      if ln.strip() and not ln.strip().startswith("=====")), doc_id)

        terms = self._tokenize(text)
        self.docs[doc_id] = IndexedDoc(
            doc_id=doc_id, title=title[:80], layer=layer,
            source=path, text=text, terms=terms,
            length=sum(terms.values()),
        )

    @staticmethod
    def _infer_layer(rel: str) -> str:
        if rel.startswith(("L0", "governance")):
            return "L0"
        if rel.startswith("L1"):
            return "L1"
        if rel.startswith(("L2", "kg-instances", "tp-rules", "skills", "contracts",
                           "archive-pre")):
            return "L2"
        return "L2"

    @staticmethod
    def _tokenize(text: str) -> Dict[str, int]:
        """分词：中文按 2-gram + 术语优先；英文按词"""
        text_lower = text.lower()
        terms: Dict[str, int] = {}
        # 英文词
        for w in re.findall(r"[a-z][a-z0-9]{1,}", text_lower):
            terms[w] = terms.get(w, 0) + 1
        # 中文 2-gram（保留核心术语）
        cn = re.sub(r"[^\u4e00-\u9fff]", "", text)
        for term in CORE_TERMS:
            cnt = text.count(term)
            if cnt:
                terms[term.lower()] = terms.get(term.lower(), 0) + cnt * 3  # 术语加权
        for i in range(len(cn) - 1):
            bigram = cn[i:i + 2]
            terms[bigram] = terms.get(bigram, 0) + 1
        return terms

    # ==================== 检索 ====================

    def search(self, query: str, top_k: int = 5,
               layer_filter: Optional[str] = None,
               min_score: float = 0.0) -> List[RetrievalResult]:
        """
        检索（BM25 + 术语加权）
        :param query: 查询语句
        :param top_k: 返回条数
        :param layer_filter: 层级过滤（L0/L1/L2）
        :param min_score: 最低分数阈值
        """
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        results: List[RetrievalResult] = []
        for doc_id, doc in self.docs.items():
            if layer_filter and doc.layer != layer_filter:
                continue
            score = self._bm25(doc, query_terms)
            if score <= min_score:
                continue
            results.append(RetrievalResult(
                doc_id=doc_id, title=doc.title, layer=doc.layer,
                source=doc.source, score=round(score, 4),
                snippet=self._make_snippet(doc, query_terms),
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _bm25(self, doc: IndexedDoc, query_terms: Dict[str, int]) -> float:
        """BM25 打分"""
        n = len(self.docs)
        score = 0.0
        for term, qf in query_terms.items():
            tf = doc.terms.get(term, 0)
            if tf == 0:
                continue
            df = sum(1 for d in self.docs.values() if term in d.terms)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            denom = tf + self.k1 * (1 - self.b + self.b * doc.length / max(self.avgdl, 1))
            score += idf * (tf * (self.k1 + 1)) / denom * qf
        return score

    def _make_snippet(self, doc: IndexedDoc, query_terms: Dict[str, int],
                      width: int = 80) -> str:
        """生成命中片段（含溯源上下文）"""
        # 优先定位含查询词的位置
        text = doc.text
        pos = -1
        for term in query_terms:
            p = text.find(term)
            if p >= 0:
                pos = p
                break
        if pos < 0:
            pos = 0
        start = max(0, pos - width // 2)
        return text[start:start + width].replace("\n", " ").strip()

    # ==================== 统计 ====================

    def doc_count(self) -> int:
        return len(self.docs)

    def layer_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for d in self.docs.values():
            counts[d.layer] = counts.get(d.layer, 0) + 1
        return counts

    def get_doc(self, doc_id: str) -> Optional[IndexedDoc]:
        return self.docs.get(doc_id)

    # ==================== 向量检索（混合检索增强） ====================

    def search_vector(self, query: str, top_k: int = 5,
                      layer_filter: Optional[str] = None) -> List[RetrievalResult]:
        """
        向量检索：TF-IDF 余弦相似度（numpy 实现，无外部依赖）
        :param query: 查询语句
        :param top_k: 返回条数
        :param layer_filter: 层级过滤（L0/L1/L2）
        """
        qv = self._query_vector(query)
        if qv is None:
            return []
        results: List[RetrievalResult] = []
        for doc_id, doc in self.docs.items():
            if layer_filter and doc.layer != layer_filter:
                continue
            cos = self._cosine(qv, self._doc_vector(doc))
            if cos <= 0:
                continue
            results.append(RetrievalResult(
                doc_id=doc_id, title=doc.title, layer=doc.layer,
                source=doc.source, score=round(cos, 4),
                snippet=self._make_snippet(doc, self._tokenize(query)),
            ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def search_hybrid(self, query: str, top_k: int = 5,
                      layer_filter: Optional[str] = None,
                      alpha: float = 0.6,
                      rerank_terms: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        混合检索：BM25（关键词）+ 向量（语义）融合排序 + 可选术语重排
        :param query: 查询语句
        :param top_k: 返回条数
        :param layer_filter: 层级过滤（L0/L1/L2）
        :param alpha: BM25 权重（0~1）；1-α 为向量权重
        :param rerank_terms: 重排术语表（命中则 +权重）
        """
        bm25_results = self.search(query, top_k=max(top_k * 4, 10),
                                   layer_filter=layer_filter)
        vec_results = self.search_vector(query, top_k=max(top_k * 4, 10),
                                         layer_filter=layer_filter)
        if not bm25_results and not vec_results:
            return []

        # 分数归一化（各自 max 归一到 [0,1]）后融合
        bm_max = bm25_results[0].score if bm25_results else 1.0
        vec_max = vec_results[0].score if vec_results else 1.0
        fused: Dict[str, Dict] = {}
        for r in bm25_results:
            fused[r.doc_id] = {"result": r, "bm": r.score / max(bm_max, 1e-9),
                               "vec": 0.0}
        for r in vec_results:
            if r.doc_id in fused:
                fused[r.doc_id]["vec"] = r.score / max(vec_max, 1e-9)
            else:
                fused[r.doc_id] = {"result": r, "bm": 0.0,
                                   "vec": r.score / max(vec_max, 1e-9)}

        # 术语重排：命中 rerank_terms 的文档加权
        rt = set((t or "").lower() for t in (rerank_terms or []))
        out: List[RetrievalResult] = []
        for doc_id, f in fused.items():
            r = f["result"]
            fused_score = alpha * f["bm"] + (1 - alpha) * f["vec"]
            if rt:
                doc = self.docs.get(doc_id)
                if doc and any(term in rt for term in doc.terms):
                    fused_score += 0.15
            r.score = round(fused_score, 4)
            out.append(r)
        out.sort(key=lambda r: r.score, reverse=True)
        return out[:top_k]

    # ---- 向量化内部实现（numpy 可选：无 numpy 时退化为词项集合相似度） ----

    def _vector_terms(self, doc: IndexedDoc) -> Dict[str, float]:
        """TF-IDF 词项权重向量（TF × IDF）"""
        n = len(self.docs)
        vec: Dict[str, float] = {}
        for term, tf in doc.terms.items():
            df = sum(1 for d in self.docs.values() if term in d.terms)
            idf = math.log(1 + n / max(df, 1))
            vec[term] = tf * idf
        return vec

    def _query_vector(self, query: str) -> Optional[Dict[str, float]]:
        """查询向量（词项权重）"""
        qterms = self._tokenize(query)
        if not qterms:
            return None
        n = len(self.docs)
        vec: Dict[str, float] = {}
        for term, tf in qterms.items():
            df = sum(1 for d in self.docs.values() if term in d.terms)
            idf = math.log(1 + n / max(df, 1))
            vec[term] = tf * idf
        return vec

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        """余弦相似度（词项空间）"""
        if not a or not b:
            return 0.0
        inter = set(a) & set(b)
        if not inter:
            return 0.0
        dot = sum(a[t] * b[t] for t in inter)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _doc_vector(self, doc: IndexedDoc) -> Dict[str, float]:
        """文档向量缓存（lazy）"""
        if getattr(doc, "_vec", None) is None:
            doc._vec = self._vector_terms(doc)
        return doc._vec
