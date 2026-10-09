"""
TDCA 多主体认知距离与不对称对齐评测模块
=========================================
对齐权威定义（AUTHORITY-CONSTITUTION + KB-THEORY-002 + NIA-MACM PHASE-2）:

  定义 3.36（认知距离函数）: d_cognitive(a,b) = inf{Length(γ) | γ 为连接 a,b 的认知路径}
  命题 3.10（不对称性）: d_cognitive(a,b) ≠ d_cognitive(b,a)——认知势差致不对称
    高认知主体理解低认知主体容易（距离短），反之困难（距离长）
  定义 3.37（对齐难度）: Difficulty_align(a,b) = exp(-d_cognitive(a,b))
    距离 → ∞ 对齐难度 → 0（完全不可对齐）；距离 → 0 难度 → 1（完全可对齐）
  NIA-MACM PHASE-2: 双方交换 cognitive_state_vectors → 计算 cognitive_distance(S₁,S₂)
    → 若 distance > compatibility_threshold 进入协商协议
  KB-THEORY-002: δ_cog = ‖S_cur − S_target‖₅（五维欧氏基准）

多主体不对称对齐评测（用户要求）:
  对同一件事（事件/主题 e），相关多主体各自的认知状态 S_i(e) 计算:
    - 距离矩阵 D[i][j] = d_cognitive(S_i(e), S_j(e))
    - 不对称度: 矩阵非对称性（|D[i][j] − D[j][i]| > 0 的占比/平均偏差）
    - 对齐评测: 各主体对权威认知的距离 + 主体间对齐难度

实现要点:
  - 认知势差: 认知水平（加权维度值）高的主体 → 理解低者距离短（不对称来源）
  - 加权语义距离: D 维非简单欧氏（AUTHORITY-ECONOMICS:1096）——含制度约束/场景权重/能力差异
  - 五维输入 S=(A,D,L,C,SC) ∈ [0,1]^5（复用 CognitiveStateCalculator 输出）

制度锚定: ID8（NIA-MACM 3.0 五维认知状态向量）+ ID60（不对称对齐原理）+ ID14
NSFL-Declaration:
  - 不试图消除认知差异（对称对齐不可能且功能有害，ID60）——只定位差异与对齐难度
  - 计算需真实数据，缺失维度按 CognitiveStateCalculator 默认并标记
  - 禁止伪造认知状态数据
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# 五维认知状态向量维度（ID8 NIA-MACM 3.0）
DIMS = ("A", "D", "L", "C", "SC")

# 维度权重（AUTHORITY-ECONOMICS:1096——加权语义距离，含制度/场景/能力差异）
# 制度对齐核心维（SC 安全合规/D 决策）权重更高；L/C 能力维次之
DIM_WEIGHTS: Dict[str, float] = {"A": 0.15, "D": 0.25, "L": 0.15, "C": 0.15, "SC": 0.30}

# NIA-MACM PHASE-2 兼容性阈值（distance > 阈值 → 进入协商协议）
COMPATIBILITY_THRESHOLD = 0.35


@dataclass(frozen=True)
class CognitiveDistance:
    """单对主体认知距离（含不对称信息）。"""
    subject_a: str
    subject_b: str
    d_ab: float                 # d_cognitive(a, b): a 理解 b 的距离
    d_ba: float                 # d_cognitive(b, a): b 理解 a 的距离
    asymmetric: bool            # 是否不对称（|d_ab − d_ba| > 0）
    difficulty_ab: float        # Difficulty_align(a,b) = exp(−d_ab)
    difficulty_ba: float        # Difficulty_align(b,a) = exp(−d_ba)
    dominant_side: Optional[str] = None   # 认知势差优势方（距离短侧）

    def to_dict(self) -> dict:
        return {
            "subject_a": self.subject_a,
            "subject_b": self.subject_b,
            "d_cognitive_ab": round(self.d_ab, 6),
            "d_cognitive_ba": round(self.d_ba, 6),
            "asymmetric": self.asymmetric,
            "difficulty_align_ab": round(self.difficulty_ab, 6),
            "difficulty_align_ba": round(self.difficulty_ba, 6),
            "dominant_side": self.dominant_side,
        }


@dataclass
class MultiSubjectAlignmentReport:
    """多主体不对称对齐评测报告。"""
    event: str                          # 同一件事（事件/主题标识）
    subjects: List[str]
    distance_matrix: Dict[str, Dict[str, float]]   # D[i][j] = d(i,j)
    asymmetric_pairs: List[str]         # 不对称主体对（"a→b"）
    asymmetry_ratio: float              # 不对称对占比
    mean_asymmetry: float               # 平均不对称偏差 |d_ab−d_ba|
    alignment_difficulties: Dict[str, Dict[str, float]]  # 对齐难度矩阵
    min_difficulty_pair: Optional[tuple] = None    # 最易对齐对 (a,b,diff)
    max_difficulty_pair: Optional[tuple] = None    # 最难对齐对

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "subjects": self.subjects,
            "distance_matrix": self.distance_matrix,
            "asymmetric_pairs": self.asymmetric_pairs,
            "asymmetry_ratio": round(self.asymmetry_ratio, 4),
            "mean_asymmetry": round(self.mean_asymmetry, 6),
            "alignment_difficulties": self.alignment_difficulties,
            "min_difficulty_pair": self.min_difficulty_pair,
            "max_difficulty_pair": self.max_difficulty_pair,
        }


class CognitiveDistanceCalculator:
    """多主体认知距离计算器（对齐定义 3.36/3.37 + 命题 3.10 + NIA-MACM PHASE-2）。"""

    def __init__(self, dim_weights: Optional[Dict[str, float]] = None,
                 compatibility_threshold: float = COMPATIBILITY_THRESHOLD):
        self._weights = dict(DIM_WEIGHTS if dim_weights is None else dim_weights)
        self._threshold = compatibility_threshold

    # ---- 核心距离函数（定义 3.36）----

    def cognitive_distance(self, s_a: Dict[str, float], s_b: Dict[str, float]) -> float:
        """d_cognitive(a,b): 主体 a 理解主体 b 的认知距离。

        加权语义距离（AUTHORITY-ECONOMICS:1096——非简单欧氏）:
          base = ‖S_a − S_b‖_w（五维加权欧氏）
          asymmetric_bias = 认知势差项（a 认知水平 < b 时距离放大——低认知理解高认知难）

        认知势差: level(x) = Σ w_k·x_k（加权认知水平）
          a 水平 ≥ b → a 理解 b 距离 = base（容易）
          a 水平 < b → a 理解 b 距离 = base × (1 + 势差惩罚)（困难，命题 3.10）
        """
        base = self._weighted_euclidean(s_a, s_b)
        level_a = self._cognitive_level(s_a)
        level_b = self._cognitive_level(s_b)
        if level_a < level_b and level_b > 0:
            # 认知势差惩罚: 低认知理解高认知 → 距离放大（与势差成比例，上限 2×）
            gap = (level_b - level_a) / max(level_b, 1e-9)
            return base * (1.0 + min(gap, 1.0))
        return base

    def cognitive_distance_ba(self, s_a: Dict[str, float], s_b: Dict[str, float]) -> float:
        """d_cognitive(b,a): 对称计算（b 理解 a）。"""
        return self.cognitive_distance(s_b, s_a)

    # ---- 单对评测 ----

    def measure_pair(self, subject_a: str, s_a: dict,
                     subject_b: str, s_b: dict) -> CognitiveDistance:
        """评测一对主体的认知距离（含不对称性 + 对齐难度）。"""
        d_ab = self.cognitive_distance(s_a, s_b)
        d_ba = self.cognitive_distance_ba(s_a, s_b)
        asymmetric = abs(d_ab - d_ba) > 1e-12
        dominant = subject_a if d_ab < d_ba else (subject_b if d_ba < d_ab else None)
        return CognitiveDistance(
            subject_a=subject_a, subject_b=subject_b,
            d_ab=d_ab, d_ba=d_ba,
            asymmetric=asymmetric,
            difficulty_ab=math.exp(-d_ab),
            difficulty_ba=math.exp(-d_ba),
            dominant_side=dominant,
        )

    # ---- 多主体评测（同一事件 e 的 n 个主体认知状态）----

    def evaluate_event(self, event: str,
                       cognitive_states: Dict[str, Dict[str, float]]) -> MultiSubjectAlignmentReport:
        """对同一事件 e，n 个主体的认知状态 S_i(e) 做多主体不对称对齐评测。

        输入: {subject_id: {A,D,L,C,SC}}（各主体对同一事件的认知状态向量）
        输出: 距离矩阵 + 不对称对 + 对齐难度矩阵 + 最易/最难对齐对
        """
        subjects = list(cognitive_states.keys())
        matrix: Dict[str, Dict[str, float]] = {s: {} for s in subjects}
        difficulties: Dict[str, Dict[str, float]] = {s: {} for s in subjects}
        asymmetric_pairs: List[str] = []
        asym_deltas: List[float] = []
        pairs = []

        for a in subjects:
            for b in subjects:
                if a == b:
                    matrix[a][b] = 0.0
                    difficulties[a][b] = 1.0  # 自身对齐难度 1（完全可对齐）
                    continue
                pair = self.measure_pair(a, cognitive_states[a], b, cognitive_states[b])
                matrix[a][b] = pair.d_ab
                difficulties[a][b] = pair.difficulty_ab
                if pair.asymmetric:
                    asymmetric_pairs.append(f"{a}→{b}")
                    asym_deltas.append(abs(pair.d_ab - pair.d_ba))
                pairs.append((a, b, pair.difficulty_ab))

        # 最易/最难对齐对（排除自身）
        if pairs:
            min_pair = min(pairs, key=lambda p: p[2])
            max_pair = max(pairs, key=lambda p: p[2])
            min_d = (min_pair[0], min_pair[1], round(min_pair[2], 6))
            max_d = (max_pair[0], max_pair[1], round(max_pair[2], 6))
        else:
            min_d = max_d = None

        n_pairs = len(pairs) or 1
        # 不对称比率: 不对称无序对（a≠b 且 |d_ab−d_ba|>0）/ 总无序对
        subjects_n = len(subjects)
        unordered_total = subjects_n * (subjects_n - 1) // 2 or 1
        asymmetric_unordered = sum(
            1 for i in range(subjects_n) for j in range(i + 1, subjects_n)
            if abs(matrix[subjects[i]][subjects[j]] - matrix[subjects[j]][subjects[i]]) > 1e-12
        )
        return MultiSubjectAlignmentReport(
            event=event,
            subjects=subjects,
            distance_matrix=matrix,
            asymmetric_pairs=asymmetric_pairs,
            asymmetry_ratio=asymmetric_unordered / unordered_total,
            mean_asymmetry=sum(asym_deltas) / len(asym_deltas) if asym_deltas else 0.0,
            alignment_difficulties=difficulties,
            min_difficulty_pair=min_d,
            max_difficulty_pair=max_d,
        )

    # ---- NIA-MACM PHASE-2 对接 ----

    def negotiation_required(self, s_a: dict, s_b: dict) -> bool:
        """NIA-MACM PHASE-2: distance > compatibility_threshold → 进入协商协议。"""
        return self.cognitive_distance(s_a, s_b) > self._threshold

    # ---- 工具 ----

    def _weighted_euclidean(self, s_a: dict, s_b: dict) -> float:
        """五维加权欧氏距离（缺失维按 0.5 默认——对齐 CognitiveStateCalculator）。"""
        sq = 0.0
        for dim in DIMS:
            va = s_a.get(dim, 0.5)
            vb = s_b.get(dim, 0.5)
            sq += self._weights.get(dim, 1.0 / len(DIMS)) * (va - vb) ** 2
        return math.sqrt(sq)

    def _cognitive_level(self, s: dict) -> float:
        """认知水平（加权维度均值 ∈ [0,1]）。"""
        total_w = 0.0
        acc = 0.0
        for dim in DIMS:
            w = self._weights.get(dim, 1.0 / len(DIMS))
            total_w += w
            acc += w * s.get(dim, 0.5)
        return acc / total_w if total_w > 0 else 0.0

    def validate(self, report: MultiSubjectAlignmentReport) -> None:
        """自证机制: 自身距离 0 + 自身对齐难度 1 + 对齐难度 ∈ (0,1]。"""
        errors = []
        for a in report.subjects:
            if abs(report.distance_matrix[a][a] - 0.0) > 1e-9:
                errors.append(f"自身距离 d({a},{a}) ≠ 0")
            if abs(report.alignment_difficulties[a][a] - 1.0) > 1e-9:
                errors.append(f"自身对齐难度 ≠ 1")
        for a in report.subjects:
            for b in report.subjects:
                diff = report.alignment_difficulties[a][b]
                if not (0.0 < diff <= 1.0):
                    errors.append(f"对齐难度越界: {a}→{b}={diff}")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")
