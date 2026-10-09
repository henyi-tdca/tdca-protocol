"""cog_align · 评测引擎（M1 服务化核心）

复用基座（不改核心，接缝式新增）:
  - CognitiveDistanceCalculator: 单对/多主体认知距离（定义 3.36/3.37，命题 3.10）
  - FuzzyCognitiveDistance: 模糊置信度增强（FUZZY_CONFIDENCE，方向性判定）
  - CognitiveStateCalculator: 输入层五维认知状态向量（ID8）

服务化增量（本引擎新增）:
  - 协商触发建议（NIA-MACM PHASE-2 对接封装）
  - 势差分析（认知水平排序，多主体）
  - 收敛轨迹（时间序列认知距离——认知漂移监测）
  - provenance 标注（ID92：合成/评测场景 vs 真实数据）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from tdca_cognitive_distance import (
    CognitiveDistanceCalculator,
    COMPATIBILITY_THRESHOLD,
)
from tdca_fuzzy_distance import FuzzyCognitiveDistance, FuzzyDirection


@dataclass(frozen=True)
class PairMeasure:
    """单对不对称认知对齐评测结果（M1 服务输出）。"""
    subject_a: str
    subject_b: str
    d_ab: float                 # d_cognitive(a,b)
    d_ba: float                 # d_cognitive(b,a)
    asymmetric: bool
    difficulty_ab: float        # exp(−d_ab)
    difficulty_ba: float        # exp(−d_ba)
    dominant_side: Optional[str]
    negotiation_required: bool  # NIA-MACM PHASE-2: distance > threshold
    fuzzy_direction: str        # HIGH/MEDIUM/LOW/NO_DIFFERENCE（模糊置信度增强）
    fuzzy_nearness: float
    provenance: str             # ID92: SIMULATED | REAL-{source}

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
            "negotiation_required": self.negotiation_required,
            "fuzzy_direction": self.fuzzy_direction,
            "fuzzy_nearness": round(self.fuzzy_nearness, 6),
            "provenance": self.provenance,
        }


@dataclass
class MultiSubjectMeasure:
    """多主体不对称对齐评测（N×N 矩阵 + 势差分析）。"""
    event: str
    subjects: List[str]
    distance_matrix: Dict[str, Dict[str, float]]
    asymmetric_pairs: List[str]
    asymmetry_ratio: float
    mean_asymmetry: float
    alignment_difficulties: Dict[str, Dict[str, float]]
    min_difficulty_pair: Optional[tuple]
    max_difficulty_pair: Optional[tuple]
    power_ranking: List[dict]           # 势差分析：认知水平排序（ID8 加权水平）
    fuzzy_clusters: List[List[str]]     # 模糊聚类（λ 截集）
    provenance: str

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
            "power_ranking": self.power_ranking,
            "fuzzy_clusters": self.fuzzy_clusters,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class ConvergenceTrace:
    """收敛轨迹（时间序列认知距离——认知漂移监测）。"""
    subject_a: str
    subject_b: str
    trace: List[float]          # 各时点 d_ab
    converging: bool            # 末段距离递减（收敛）
    final_gap: float            # 首末距离差（>0 收敛，<0 漂移）
    drift_alert: bool           # 漂移告警（末段距离较首段放大）

    def to_dict(self) -> dict:
        return {
            "subject_a": self.subject_a,
            "subject_b": self.subject_b,
            "trace": [round(x, 6) for x in self.trace],
            "converging": self.converging,
            "final_gap": round(self.final_gap, 6),
            "drift_alert": self.drift_alert,
        }


class CogAlignService:
    """认知对齐评测服务（DCD-COG-ALIGN-001 M1）。"""

    def __init__(self, dim_weights: Optional[Dict[str, float]] = None,
                 compatibility_threshold: float = COMPATIBILITY_THRESHOLD,
                 default_provenance: str = "SIMULATED"):
        self._dist = CognitiveDistanceCalculator(
            dim_weights=dim_weights,
            compatibility_threshold=compatibility_threshold,
        )
        self._fuzzy = FuzzyCognitiveDistance(weights=dim_weights)
        self._provenance = default_provenance

    # ---- 单对评测（A-1）----

    def measure(self, subject_a: str, s_a: Dict[str, float],
                subject_b: str, s_b: Dict[str, float],
                provenance: Optional[str] = None) -> PairMeasure:
        """单对不对称对齐评测。

        输出: 不对称距离（命题 3.10）+ 优势方 + 双向对齐难度（定义 3.37）
              + 协商触发建议（NIA-MACM PHASE-2）+ 模糊置信度方向（FUZZY_CONFIDENCE）
        """
        self._validate_state(s_a, "subject_a")
        self._validate_state(s_b, "subject_b")
        pair = self._dist.measure_pair(subject_a, s_a, subject_b, s_b)
        conf = self._fuzzy.fuzzy_confidence(s_a, s_b)
        return PairMeasure(
            subject_a=subject_a, subject_b=subject_b,
            d_ab=pair.d_ab, d_ba=pair.d_ba,
            asymmetric=pair.asymmetric,
            difficulty_ab=pair.difficulty_ab,
            difficulty_ba=pair.difficulty_ba,
            dominant_side=pair.dominant_side,
            negotiation_required=self._dist.negotiation_required(s_a, s_b),
            fuzzy_direction=conf.direction,
            fuzzy_nearness=conf.nearness,
            provenance=provenance or self._provenance,
        )

    # ---- 多主体评测（A-2）----

    def evaluate_event(self, event: str,
                       cognitive_states: Dict[str, Dict[str, float]],
                       provenance: Optional[str] = None) -> MultiSubjectMeasure:
        """多主体不对称对齐评测（同一事件 e 的 n 个主体）。

        输出: N×N 距离矩阵 + 不对称对 + 势差分析（认知水平排序）+ 模糊聚类
        """
        for sid, state in cognitive_states.items():
            self._validate_state(state, sid)
        base = self._dist.evaluate_event(event, cognitive_states)
        ranking = self._power_ranking(cognitive_states)
        fuzzy_report = self._fuzzy.evaluate_fuzzy_event(event, cognitive_states)
        return MultiSubjectMeasure(
            event=event,
            subjects=base.subjects,
            distance_matrix=base.distance_matrix,
            asymmetric_pairs=base.asymmetric_pairs,
            asymmetry_ratio=base.asymmetry_ratio,
            mean_asymmetry=base.mean_asymmetry,
            alignment_difficulties=base.alignment_difficulties,
            min_difficulty_pair=base.min_difficulty_pair,
            max_difficulty_pair=base.max_difficulty_pair,
            power_ranking=ranking,
            fuzzy_clusters=fuzzy_report.clusters,
            provenance=provenance or self._provenance,
        )

    # ---- 收敛轨迹（认知漂移监测，M2 场景铺垫）----

    def convergence(self, subject_a: str, subject_b: str,
                    state_series: Sequence[tuple],
                    provenance: Optional[str] = None) -> ConvergenceTrace:
        """时间序列收敛轨迹。

        state_series: [(ts_label, s_a(t), s_b(t)), ...] 按时间有序
        输出: 各时点 d_ab + 是否收敛 + 漂移告警（末段 vs 首段）
        """
        if len(state_series) < 2:
            raise ValueError("convergence 需 ≥2 个时点")
        trace = []
        for ts, s_a, s_b in state_series:
            self._validate_state(s_a, f"{subject_a}@{ts}")
            self._validate_state(s_b, f"{subject_b}@{ts}")
            trace.append(self._dist.cognitive_distance(s_a, s_b))
        half = len(trace) // 2
        first_half_avg = sum(trace[:half]) / max(half, 1)
        last_half_avg = sum(trace[half:]) / max(len(trace) - half, 1)
        gap = first_half_avg - last_half_avg
        return ConvergenceTrace(
            subject_a=subject_a, subject_b=subject_b,
            trace=trace,
            converging=gap > 1e-9,
            final_gap=gap,
            drift_alert=gap < -1e-9,
        )

    # ---- 工具 ----

    def _power_ranking(self, states: Dict[str, Dict[str, float]]) -> List[dict]:
        """势差分析：按认知水平（ID8 加权维度均值）降序排序。"""
        rows = []
        for sid, state in states.items():
            level = self._dist._cognitive_level(state)
            rows.append({"subject": sid, "cognitive_level": round(level, 6)})
        rows.sort(key=lambda r: r["cognitive_level"], reverse=True)
        return rows

    def _validate_state(self, state: Dict[str, float], label: str) -> None:
        """五维状态校验（[0,1] 区间，缺失维按 0.5 默认——对齐 CognitiveStateCalculator）。"""
        errors = []
        for dim in ("A", "D", "L", "C", "SC"):
            v = state.get(dim)
            if v is not None and not isinstance(v, (int, float)):
                errors.append(f"{label}.{dim} 非数值: {v}")
            elif v is not None and not (0.0 <= v <= 1.0):
                errors.append(f"{label}.{dim} 超出 [0,1]: {v}")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] cog_align validate failed: {'; '.join(errors)}")
