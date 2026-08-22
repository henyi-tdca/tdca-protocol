"""
TDCA 多主体认知距离 · 模糊数学运算层
=======================================
运用模糊数学（Fuzzy Mathematics）对多主体认知状态做距离/贴近度/包含度/置信度运算，
对齐权威设计:

  - AUTHORITY-ECONOMICS:2636（FUZZY_CONFIDENCE 模糊置信度）: 输出方向性判断
    （高/中/低/无显著差异）+ 置信区间，而非精确数值
  - ID85 三可原则「可模糊计算」: 负空间可场景化比较、可共情观察、可模糊计算
  - 定义 3.36（认知距离函数）/ 命题 3.10（不对称性，认知势差）
    / 定义 3.37（对齐难度 exp(−d)）——模糊化后语义不变

模糊数学工具（Zadeh 模糊集理论）:
  1. 模糊贴近度（Fuzzy Nearness）: 格贴近度 / 海明贴近度 / 欧氏贴近度 / 最大最小贴近度
  2. 模糊包含度（Fuzzy Subsethood）: |A∩B|/|A|——天然不对称（认知势差的模糊体现）
  3. 模糊置信度（Fuzzy Confidence）: 方向性判定 + 置信区间（FUZZY_CONFIDENCE）
  4. 三角模糊数（Triangular Fuzzy Number）: 认知状态带不确定性区间 (l, m, u)

不对称性（命题 3.10 的模糊对应）:
  认知势差 → 模糊包含度不对称——低认知主体的认知状态被高认知主体包含程度高
  （subsethood(L→H) 大），反之小（subsethood(H→L) 小）——距离天然不对称。

制度锚定: ID8（NIA-MACM 3.0 五维认知状态向量）+ ID60（不对称对齐原理）
         + ID85（三可原则: 可模糊计算）+ FUZZY_CONFIDENCE（AUTHORITY-ECONOMICS:2636）
NSFL-Declaration:
  - 模糊计算只用于认知距离度量，不改变负空间绝对性（法律禁止仍精确熔断，无模糊计算，ID86）
  - 模糊置信度必须标注方向 + 置信区间，禁止输出伪精确数值
  - 禁止伪造认知状态数据
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from tdca_cognitive_distance import DIMS, DIM_WEIGHTS  # 复用维度定义（顶层平铺导入，同既有惯例）

# 模糊置信度档位（FUZZY_CONFIDENCE 方向性判定）
class FuzzyDirection(str):
    HIGH = "HIGH"            # 显著接近（贴近度高）
    MEDIUM = "MEDIUM"        # 中等接近
    LOW = "LOW"              # 显著远离
    NO_DIFFERENCE = "NO_DIFFERENCE"  # 无显著差异


# 贴近度 → 方向档位阈值
_NEARNESS_HIGH = 0.75
_NEARNESS_MEDIUM = 0.55


@dataclass(frozen=True)
class TriangularFuzzyNumber:
    """三角模糊数 (l, m, u)：认知状态维度带不确定性区间。"""
    l: float
    m: float
    u: float

    def __post_init__(self):
        if not (self.l <= self.m <= self.u):
            raise ValueError(f"三角模糊数须满足 l≤m≤u: ({self.l},{self.m},{self.u})")

    @property
    def crisp(self) -> float:
        """去模糊化（重心）: (l + m + u) / 3。"""
        return (self.l + self.m + self.u) / 3.0

    def distance_to(self, other: "TriangularFuzzyNumber") -> float:
        """三角模糊数距离（Chen 法: 顶点距离加权）。"""
        return math.sqrt(
            ((self.l - other.l) ** 2 + 2 * (self.m - other.m) ** 2 + (self.u - other.u) ** 2) / 4.0
        )


@dataclass(frozen=True)
class FuzzyNearness:
    """模糊贴近度结果（多算子）。"""
    lattice: float            # 格贴近度
    hamming: float            # 海明贴近度
    euclidean: float          # 欧氏贴近度
    maxmin: float             # 最大最小贴近度
    integrated: float         # 综合贴近度（多算子加权）

    def to_dict(self) -> dict:
        return {
            "lattice": round(self.lattice, 6),
            "hamming": round(self.hamming, 6),
            "euclidean": round(self.euclidean, 6),
            "maxmin": round(self.maxmin, 6),
            "integrated": round(self.integrated, 6),
        }


@dataclass
class FuzzyConfidence:
    """模糊置信度（FUZZY_CONFIDENCE 对齐）——方向性判断 + 置信区间。"""
    direction: str            # HIGH / MEDIUM / LOW / NO_DIFFERENCE
    nearness: float           # 贴近度（综合）
    confidence_interval: Tuple[float, float]   # 贴近度置信区间
    support: int              # 支撑维度数（有多少维支持该判断）
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "nearness": round(self.nearness, 6),
            "confidence_interval": [round(self.confidence_interval[0], 6),
                                    round(self.confidence_interval[1], 6)],
            "support": self.support,
            "note": self.note,
        }


@dataclass
class FuzzyMultiSubjectReport:
    """模糊多主体不对称对齐评测报告。"""
    event: str
    subjects: List[str]
    nearness_matrix: Dict[str, Dict[str, float]]          # 贴近度矩阵（对称）
    subsethood_matrix: Dict[str, Dict[str, float]]        # 包含度矩阵（不对称）
    confidence_matrix: Dict[str, Dict[str, dict]]         # 置信度矩阵
    asymmetric_pairs: List[str]
    clusters: List[List[str]] = field(default_factory=list)  # 模糊聚类（阈值 λ）

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "subjects": self.subjects,
            "nearness_matrix": self.nearness_matrix,
            "subsethood_matrix": self.subsethood_matrix,
            "confidence_matrix": self.confidence_matrix,
            "asymmetric_pairs": self.asymmetric_pairs,
            "clusters": self.clusters,
        }


class FuzzyCognitiveDistance:
    """模糊认知距离计算器（模糊数学运算层）。

    输入: 多主体认知状态（精确值或三角模糊数）
    输出: 贴近度矩阵 / 包含度矩阵（不对称）/ 模糊置信度 / 模糊聚类
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = dict(DIM_WEIGHTS if weights is None else weights)

    # ---- 模糊贴近度（Zadeh 模糊集理论）----

    def fuzzy_nearness(self, s_a: Dict[str, float], s_b: Dict[str, float]) -> FuzzyNearness:
        """模糊贴近度（4 算子）: 度量两主体认知状态接近程度（对称）。

        综合贴近度 = 海明/欧氏/最大最小三算子均值（均自反恒 1）；
        lattice 为参考算子（格贴近度自反可能 <1，模糊数学已知特性）。
        """
        lattice = self._lattice_nearness(s_a, s_b)
        hamming = self._hamming_nearness(s_a, s_b)
        euclidean = self._euclidean_nearness(s_a, s_b)
        maxmin = self._maxmin_nearness(s_a, s_b)
        integrated = (hamming + euclidean + maxmin) / 3.0
        return FuzzyNearness(lattice=lattice, hamming=hamming,
                             euclidean=euclidean, maxmin=maxmin,
                             integrated=integrated)

    def _lattice_nearness(self, a: dict, b: dict) -> float:
        """格贴近度（参考算子）: (A∘B) ∧ (1 − A⊙B)——内积与补外积的交。

        注: 格贴近度自反时 = min(max(a), 1−min(a))，对非极值向量可能 <1
        （模糊数学已知特性）——故仅作参考算子，综合贴近度用自反恒 1 的
        海明/欧氏/最大最小三算子。
        """
        inner = max(min(a.get(d, 0.5), b.get(d, 0.5)) for d in DIMS)   # A∘B 内积
        outer = min(max(a.get(d, 0.5), b.get(d, 0.5)) for d in DIMS)   # A⊙B 外积
        return min(inner, 1.0 - outer)

    def _hamming_nearness(self, a: dict, b: dict) -> float:
        """海明贴近度（加权）: 1 − Σw·|a−b|（自反恒 1）。"""
        return 1.0 - sum(
            self._weights.get(d, 1.0 / len(DIMS)) * abs(a.get(d, 0.5) - b.get(d, 0.5))
            for d in DIMS
        )

    def _euclidean_nearness(self, a: dict, b: dict) -> float:
        """欧氏贴近度: 1 − √(Σw·(a−b)²)（自反恒 1）。"""
        sq = sum(
            self._weights.get(d, 1.0 / len(DIMS)) * (a.get(d, 0.5) - b.get(d, 0.5)) ** 2
            for d in DIMS
        )
        return 1.0 - math.sqrt(sq)

    def _maxmin_nearness(self, a: dict, b: dict) -> float:
        """最大最小贴近度: Σmin(a,b) / Σmax(a,b)（自反恒 1）。"""
        num = sum(min(a.get(d, 0.5), b.get(d, 0.5)) for d in DIMS)
        den = sum(max(a.get(d, 0.5), b.get(d, 0.5)) for d in DIMS)
        return num / den if den > 0 else 0.0

    # ---- 模糊包含度（不对称性——命题 3.10 的模糊对应）----

    def fuzzy_subsethood(self, s_a: Dict[str, float], s_b: Dict[str, float]) -> float:
        """模糊包含度 subsethood(A,B) = |A∩B| / |A|——A 多大程度被 B 包含。

        不对称性: subsethood(L→H) 大（低认知被高认知包含），subsethood(H→L) 小
        ——认知势差的模糊体现（命题 3.10）。
        """
        a_mag = sum(self._weights.get(d, 1.0 / len(DIMS)) * s_a.get(d, 0.5) for d in DIMS)
        if a_mag <= 0:
            return 0.0
        inter = sum(
            self._weights.get(d, 1.0 / len(DIMS)) * min(s_a.get(d, 0.5), s_b.get(d, 0.5))
            for d in DIMS
        )
        return inter / a_mag

    # ---- 模糊置信度（FUZZY_CONFIDENCE 对齐）----

    def fuzzy_confidence(self, s_a: Dict[str, float], s_b: Dict[str, float]) -> FuzzyConfidence:
        """模糊置信度: 方向性判断（高/中/低/无显著差异）+ 置信区间。

        置信区间: 各算子贴近度的 min-max（反映多算子一致性）；
        support: 贴近度≥0.5 的维度数（判断支撑度）。
        """
        near = self.fuzzy_nearness(s_a, s_b)
        integrated = near.integrated

        if integrated >= _NEARNESS_HIGH:
            direction = FuzzyDirection.HIGH
        elif integrated >= _NEARNESS_MEDIUM:
            direction = FuzzyDirection.MEDIUM
        elif integrated <= 0.5 - (_NEARNESS_MEDIUM - 0.5):
            direction = FuzzyDirection.LOW
        else:
            direction = FuzzyDirection.NO_DIFFERENCE

        operator_values = [near.hamming, near.euclidean, near.maxmin]  # 综合算子（lattice 参考）
        ci = (min(operator_values), max(operator_values))
        support = sum(1 for d in DIMS
                      if abs(s_a.get(d, 0.5) - s_b.get(d, 0.5)) <= 0.5)
        return FuzzyConfidence(
            direction=direction, nearness=integrated,
            confidence_interval=ci, support=support,
        )

    # ---- 模糊多主体评测 ----

    def evaluate_fuzzy_event(
        self, event: str, cognitive_states: Dict[str, Dict[str, float]]
    ) -> FuzzyMultiSubjectReport:
        """模糊多主体不对称对齐评测。

        输入: {subject: 五维认知状态}（同一事件）
        输出: 贴近度矩阵（对称）+ 包含度矩阵（不对称）+ 置信度矩阵 + 聚类
        """
        subjects = list(cognitive_states.keys())
        near_matrix: Dict[str, Dict[str, float]] = {s: {} for s in subjects}
        sub_matrix: Dict[str, Dict[str, float]] = {s: {} for s in subjects}
        conf_matrix: Dict[str, Dict[str, dict]] = {s: {} for s in subjects}
        asymmetric_pairs: List[str] = []

        for a in subjects:
            for b in subjects:
                if a == b:
                    near_matrix[a][b] = 1.0
                    sub_matrix[a][b] = 1.0
                    conf_matrix[a][b] = {"direction": FuzzyDirection.HIGH,
                                         "nearness": 1.0,
                                         "confidence_interval": [1.0, 1.0],
                                         "support": 5,
                                         "note": "自身完全接近"}
                    continue
                near = self.fuzzy_nearness(cognitive_states[a], cognitive_states[b])
                sub_ab = self.fuzzy_subsethood(cognitive_states[a], cognitive_states[b])
                sub_ba = self.fuzzy_subsethood(cognitive_states[b], cognitive_states[a])
                conf = self.fuzzy_confidence(cognitive_states[a], cognitive_states[b])
                near_matrix[a][b] = round(near.integrated, 6)
                sub_matrix[a][b] = round(sub_ab, 6)
                conf_matrix[a][b] = conf.to_dict()
                if abs(sub_ab - sub_ba) > 1e-12:
                    asymmetric_pairs.append(f"{a}→{b}")

        clusters = self._fuzzy_cluster(near_matrix, subjects)
        return FuzzyMultiSubjectReport(
            event=event, subjects=subjects,
            nearness_matrix=near_matrix, subsethood_matrix=sub_matrix,
            confidence_matrix=conf_matrix, asymmetric_pairs=asymmetric_pairs,
            clusters=clusters,
        )

    # ---- 模糊聚类（阈值 λ 截集）----

    @staticmethod
    def _fuzzy_cluster(near_matrix: Dict[str, Dict[str, float]],
                       subjects: List[str], lambda_threshold: float = 0.6) -> List[List[str]]:
        """模糊聚类: 贴近度 ≥ λ 的主体归同一类（简单连通分量）。"""
        n = len(subjects)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for i in range(n):
            for j in range(i + 1, n):
                if near_matrix[subjects[i]][subjects[j]] >= lambda_threshold:
                    union(i, j)

        groups: Dict[int, List[str]] = {}
        for i, s in enumerate(subjects):
            groups.setdefault(find(i), []).append(s)
        return [sorted(v) for v in groups.values()]

    # ---- 自证 ----

    def validate(self, report: FuzzyMultiSubjectReport) -> None:
        """自证: 贴近度矩阵对称 + 自身贴近 1 + 贴近度 ∈ [0,1] + 包含度 ∈ [0,1]。"""
        errors = []
        for a in report.subjects:
            if abs(report.nearness_matrix[a][a] - 1.0) > 1e-9:
                errors.append(f"自身贴近度 ≠ 1: {a}")
            for b in report.subjects:
                na = report.nearness_matrix[a][b]
                if not (0.0 <= na <= 1.0):
                    errors.append(f"贴近度越界: {a}→{b}={na}")
                if abs(report.nearness_matrix[a][b] - report.nearness_matrix[b][a]) > 1e-9:
                    errors.append(f"贴近度不对称（应对称）: {a}↔{b}")
                sub = report.subsethood_matrix[a][b]
                if not (0.0 <= sub <= 1.0):
                    errors.append(f"包含度越界: {a}→{b}={sub}")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] fuzzy validate failed: {'; '.join(errors)}")
