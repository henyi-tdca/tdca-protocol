"""cog_align · M2 评测场景包（评测产品化）

三场景（DCD-COG-ALIGN-001 §五 M2）:
  1. 思想病毒防御: 检测认知漂移（认知状态异常变化——思想病毒感染的信号）
  2. 认知漂移监测: 时间序列漂移/收敛分析（对齐评测 = 检测认知漂移的工具）
  3. 对齐度分档: 按对齐难度分档（高度/中度/低度/不可对齐）——对齐度产品化分级

复用: CogAlignService（M1 引擎）+ ConvergenceTrace（收敛/漂移）
制度锚定: ID60（不对称对齐）/ 定义 3.37（对齐难度 exp(−d)）/ 思想病毒防御叙事
NSFL-Declaration: 场景判定为评测输出（SIMULATED 数据），不构成真实安全结论；
                 漂移告警仅提示需人工复核（ID92 数据纪律）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .engine import CogAlignService, ConvergenceTrace

# 对齐度分档（对齐难度 difficulty = exp(−d)，d ∈ [0,1] → difficulty ∈ [exp(−1)≈0.368, 1]）
TIER_HIGH_ALIGN = 0.7       # difficulty ≥ 0.7 → 高度对齐（d ≤ 0.357）
TIER_MEDIUM_ALIGN = 0.55    # 0.55 ≤ difficulty < 0.7 → 中度对齐
TIER_LOW_ALIGN = 0.45       # 0.45 ≤ difficulty < 0.55 → 低度对齐
# < 0.45 → 不可对齐（d > 0.799，可达——全维相反 d=0.9 → difficulty≈0.407）

# 认知漂移告警阈值（末段平均距离 − 首段平均距离 > 阈值才告警——需显著漂移）
DRIFT_ALERT_THRESHOLD = 0.05


@dataclass(frozen=True)
class ScenarioResult:
    """场景评测结果（产品化输出）。"""
    scenario: str                    # 场景标识
    subject_a: str
    subject_b: str
    verdict: str                     # 判定（e.g. "NO_DRIFT" / "DRIFT_ALERT"）
    detail: dict                     # 场景明细
    recommendation: str              # 建议动作
    provenance: str

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "subject_a": self.subject_a,
            "subject_b": self.subject_b,
            "verdict": self.verdict,
            "detail": self.detail,
            "recommendation": self.recommendation,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class AlignmentTier:
    """对齐度分档结果。"""
    subject_a: str
    subject_b: str
    difficulty_ab: float
    difficulty_ba: float
    tier_ab: str                     # 高度/中度/低度/不可对齐
    tier_ba: str
    asym_tier: bool                  # 双向分档不一致（不对称性的产品化呈现）

    def to_dict(self) -> dict:
        return {
            "subject_a": self.subject_a,
            "subject_b": self.subject_b,
            "difficulty_ab": round(self.difficulty_ab, 6),
            "difficulty_ba": round(self.difficulty_ba, 6),
            "tier_ab": self.tier_ab,
            "tier_ba": self.tier_ba,
            "asym_tier": self.asym_tier,
        }


class CogAlignScenarios:
    """评测场景包（M2 产品化）。"""

    def __init__(self, service: Optional[CogAlignService] = None):
        self._svc = service or CogAlignService()

    # ---- 场景 1: 思想病毒防御（认知漂移检测）----

    def thought_virus_defense(self, subject: str,
                              state_series: Sequence[tuple],
                              baseline_state: Dict[str, float],
                              provenance: str = "SIMULATED") -> ScenarioResult:
        """思想病毒防御场景: 检测主体认知状态随时间的异常漂移。

        输入: subject 认知状态时间序列（ts, state）+ 基准认知状态
        判定: 序列末段状态与基准的认知距离显著增大 → 疑似认知漂移（思想病毒信号）
        """
        if not state_series or len(state_series) < 2:
            raise ValueError("[NSFL-TRIGGER] 思想病毒防御需 ≥2 个时点")
        self._svc._validate_state(baseline_state, "baseline")

        distances = []
        for ts, state in state_series:
            self._svc._validate_state(state, f"{subject}@{ts}")
            distances.append(self._svc._dist.cognitive_distance(baseline_state, state))

        # 首段 vs 末段平均距离
        half = len(distances) // 2
        early_avg = sum(distances[:half]) / max(half, 1)
        late_avg = sum(distances[half:]) / max(len(distances) - half, 1)
        drift = late_avg - early_avg

        if drift > DRIFT_ALERT_THRESHOLD:
            verdict = "DRIFT_ALERT"
            recommendation = ("认知漂移信号：主体认知状态偏离基准且持续增大——"
                              "疑似思想病毒传播，建议人工复核 + 负空间熔断检查")
        else:
            verdict = "NO_DRIFT"
            recommendation = "认知状态稳定，无显著漂移——维持监测"

        return ScenarioResult(
            scenario="thought_virus_defense",
            subject_a=f"{subject}-baseline",
            subject_b=subject,
            verdict=verdict,
            detail={
                "baseline": {k: round(v, 4) for k, v in baseline_state.items()},
                "series_distances": [round(x, 6) for x in distances],
                "early_avg_distance": round(early_avg, 6),
                "late_avg_distance": round(late_avg, 6),
                "drift_delta": round(drift, 6),
            },
            recommendation=recommendation,
            provenance=provenance,
        )

    # ---- 场景 2: 认知漂移监测（时间序列收敛/漂移）----

    def cognitive_drift_monitor(self, subject_a: str, subject_b: str,
                                state_series: Sequence[tuple],
                                provenance: str = "SIMULATED") -> ScenarioResult:
        """认知漂移监测场景: 两主体间认知距离的时间序列收敛/漂移分析。

        复用 M1 convergence（首末段 gap）→ 收敛（正向）/ 漂移（负向）判定。
        """
        trace = self._svc.convergence(subject_a, subject_b, state_series,
                                      provenance=provenance)
        if trace.drift_alert:
            verdict = "DRIFT_ALERT"
            recommendation = "认知距离放大——两主体对齐恶化，建议进入协商协议（NIA-MACM PHASE-2）"
        elif trace.converging:
            verdict = "CONVERGING"
            recommendation = "认知距离收敛——对齐改善，可维持协作"
        else:
            verdict = "STABLE"
            recommendation = "认知距离平稳，无显著变化"

        return ScenarioResult(
            scenario="cognitive_drift_monitor",
            subject_a=subject_a,
            subject_b=subject_b,
            verdict=verdict,
            detail={
                "trace": [round(x, 6) for x in trace.trace],
                "final_gap": round(trace.final_gap, 6),
            },
            recommendation=recommendation,
            provenance=provenance,
        )

    # ---- 场景 3: 对齐度分档（产品化分级）----

    def alignment_tiering(self, subject_a: str, s_a: Dict[str, float],
                          subject_b: str, s_b: Dict[str, float],
                          provenance: str = "SIMULATED") -> AlignmentTier:
        """对齐度分档: 按对齐难度（定义 3.37）分档（高度/中度/低度/不可对齐）。"""
        pair = self._svc.measure(subject_a, s_a, subject_b, s_b,
                                 provenance=provenance)
        tier_ab = self._tier(pair.difficulty_ab)
        tier_ba = self._tier(pair.difficulty_ba)
        return AlignmentTier(
            subject_a=subject_a, subject_b=subject_b,
            difficulty_ab=pair.difficulty_ab,
            difficulty_ba=pair.difficulty_ba,
            tier_ab=tier_ab, tier_ba=tier_ba,
            asym_tier=tier_ab != tier_ba,
        )

    def tier_matrix(self, cognitive_states: Dict[str, Dict[str, float]],
                    provenance: str = "SIMULATED") -> Dict[str, Dict[str, str]]:
        """多主体对齐度分档矩阵（产品化：一眼看清生态对齐态势）。"""
        matrix: Dict[str, Dict[str, str]] = {}
        subjects = list(cognitive_states.keys())
        for a in subjects:
            matrix[a] = {}
            for b in subjects:
                if a == b:
                    matrix[a][b] = "SELF"
                    continue
                t = self.alignment_tiering(a, cognitive_states[a], b, cognitive_states[b],
                                           provenance=provenance)
                matrix[a][b] = f"{t.tier_ab}(asym:{'Y' if t.asym_tier else 'N'})"
        return matrix

    @staticmethod
    def _tier(difficulty: float) -> str:
        if difficulty >= TIER_HIGH_ALIGN:
            return "高度对齐"
        if difficulty >= TIER_MEDIUM_ALIGN:
            return "中度对齐"
        if difficulty >= TIER_LOW_ALIGN:
            return "低度对齐"
        return "不可对齐"
