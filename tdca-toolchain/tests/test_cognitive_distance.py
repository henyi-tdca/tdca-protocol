"""
TDCA 多主体认知距离与不对称对齐评测 · 数学验证测试
====================================================
对齐权威定义:
  - 定义 3.36 认知距离函数 d_cognitive(a,b) = inf{Length(γ)}
  - 命题 3.10 不对称性: d(a,b) ≠ d(b,a)（认知势差）
  - 定义 3.37 对齐难度 Difficulty_align = exp(−d)
  - NIA-MACM PHASE-2: distance > threshold → 协商协议
"""
import math
import pytest

from tdca_cognitive_distance import (
    CognitiveDistanceCalculator,
    DIM_WEIGHTS,
    COMPATIBILITY_THRESHOLD,
)


def _s(**kw):
    """构造五维认知状态向量（缺省 0.5）。"""
    base = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    base.update(kw)
    return base


class TestCognitiveDistance:
    """定义 3.36: 认知距离函数。"""

    def test_zero_self_distance(self):
        """自身距离 d(a,a) = 0（距离公理）。"""
        calc = CognitiveDistanceCalculator()
        s = _s(A=0.8, D=0.9, L=0.7, C=0.6, SC=0.95)
        assert calc.cognitive_distance(s, s) == 0.0

    def test_symmetric_states_distance(self):
        """相同状态 → 距离 0。"""
        calc = CognitiveDistanceCalculator()
        s = _s(A=0.8, D=0.8, L=0.8, C=0.8, SC=0.8)
        assert calc.cognitive_distance(s, s) == 0.0

    def test_distance_grows_with_divergence(self):
        """认知状态差异越大 → 距离越大（单调性直觉）。"""
        calc = CognitiveDistanceCalculator()
        base = _s()
        near = _s(A=0.6, D=0.6)
        far = _s(A=0.1, D=0.1, SC=0.1)
        assert calc.cognitive_distance(base, far) > calc.cognitive_distance(base, near)

    def test_weighted_euclidean_respects_SC_weight(self):
        """加权语义距离: SC（安全合规）权重最高——SC 差异贡献更大。"""
        calc = CognitiveDistanceCalculator()
        s1 = _s()
        # 仅 SC 差异 0.5 vs 仅 A 差异 0.5
        sc_diff = _s(SC=0.0)
        a_diff = _s(A=0.0)
        d_sc = calc.cognitive_distance(s1, sc_diff)
        d_a = calc.cognitive_distance(s1, a_diff)
        # SC 权重 0.30 > A 权重 0.15 → SC 差异距离更大
        assert d_sc > d_a


class TestAsymmetry:
    """命题 3.10: 认知距离不对称性（认知势差）。"""

    def test_high_cog_understands_low_easier(self):
        """高认知主体理解低认知主体距离短（命题 3.10 认知势差）。"""
        calc = CognitiveDistanceCalculator()
        high = _s(A=0.9, D=0.9, L=0.9, C=0.9, SC=0.95)   # 高认知
        low = _s(A=0.3, D=0.3, L=0.3, C=0.3, SC=0.3)     # 低认知
        d_high_to_low = calc.cognitive_distance(high, low)   # 高→低: 容易（短）
        d_low_to_high = calc.cognitive_distance(low, high)   # 低→高: 困难（长）
        assert d_high_to_low < d_low_to_high

    def test_asymmetry_detected(self):
        """measure_pair 识别不对称性 + 优势方。"""
        calc = CognitiveDistanceCalculator()
        pair = calc.measure_pair(
            "HIGH", _s(A=0.9, D=0.9, SC=0.95),
            "LOW", _s(A=0.3, D=0.3, SC=0.3),
        )
        assert pair.asymmetric is True
        assert pair.d_ab < pair.d_ba           # HIGH→LOW 距离短
        assert pair.dominant_side == "HIGH"    # 认知势差优势方
        assert pair.difficulty_ab > pair.difficulty_ba  # 高→低对齐难度大（易对齐）

    def test_symmetric_pairs_not_asymmetric(self):
        """同认知水平主体 → 距离对称（无势差）。"""
        calc = CognitiveDistanceCalculator()
        pair = calc.measure_pair(
            "A1", _s(A=0.7, D=0.7), "A2", _s(A=0.7, D=0.7),
        )
        assert pair.asymmetric is False
        assert abs(pair.d_ab - pair.d_ba) < 1e-12


class TestAlignmentDifficulty:
    """定义 3.37: 对齐难度 exp(−d)。"""

    def test_difficulty_bounds(self):
        """对齐难度 ∈ (0,1]: d→0 难度→1；d→∞ 难度→0。"""
        calc = CognitiveDistanceCalculator()
        s1 = _s()
        s2 = _s(A=0.0, D=0.0, L=0.0, C=0.0, SC=0.0)
        d = calc.cognitive_distance(s1, s2)
        difficulty = math.exp(-d)
        assert 0.0 < difficulty <= 1.0

    def test_near_align_high_difficulty(self):
        """近认知 → 高对齐难度（接近 1 = 完全可对齐）。"""
        calc = CognitiveDistanceCalculator()
        s1 = _s()
        s2 = _s(A=0.51, D=0.49)
        d = calc.cognitive_distance(s1, s2)
        assert math.exp(-d) > 0.9


class TestMultiSubjectEvaluation:
    """多主体不对称对齐评测（用户核心需求）。"""

    def test_distance_matrix(self):
        """同一事件多主体认知状态 → 距离矩阵。"""
        calc = CognitiveDistanceCalculator()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "M1": _s(A=0.6, D=0.6, SC=0.6),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = calc.evaluate_event("cross-border-policy", states)
        assert set(report.subjects) == {"H1", "M1", "L1"}
        # 矩阵对角线 0
        for s in report.subjects:
            assert report.distance_matrix[s][s] == 0.0
        calc.validate(report)

    def test_asymmetric_pairs_identified(self):
        """认知势差存在 → 不对称对识别 + 比值。"""
        calc = CognitiveDistanceCalculator()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = calc.evaluate_event("e", states)
        assert "H1→L1" in report.asymmetric_pairs or "L1→H1" in report.asymmetric_pairs
        assert report.asymmetry_ratio > 0.0
        assert report.mean_asymmetry > 0.0

    def test_alignment_difficulty_matrix(self):
        """对齐难度矩阵（exp(−d)）。"""
        calc = CognitiveDistanceCalculator()
        states = {
            "H1": _s(A=0.9, SC=0.95),
            "L1": _s(A=0.3, SC=0.3),
        }
        report = calc.evaluate_event("e", states)
        for a in report.subjects:
            for b in report.subjects:
                diff = report.alignment_difficulties[a][b]
                assert 0.0 < diff <= 1.0

    def test_min_max_difficulty_pairs(self):
        """最易/最难对齐对识别（含不对称有向性——命题 3.10）。"""
        calc = CognitiveDistanceCalculator()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "M1": _s(A=0.6, D=0.6, SC=0.6),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = calc.evaluate_event("e", states)
        assert report.min_difficulty_pair is not None
        assert report.max_difficulty_pair is not None
        # 最易对齐 = 认知最接近对（H1↔M1 或 M1↔L1 中更近）
        assert report.min_difficulty_pair[0] != report.min_difficulty_pair[1]
        assert report.min_difficulty_pair[2] > report.max_difficulty_pair[2] * 0.5
        # 最难对齐含 L1（最低认知端——有向距离被势差放大，命题 3.10）
        assert "L1" in report.max_difficulty_pair[:2]

    def test_asymmetric_directional_pairs(self):
        """不对称性: 认知势差存在 → 全部有向对均不对称（6 有向对）。"""
        calc = CognitiveDistanceCalculator()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "M1": _s(A=0.6, D=0.6, SC=0.6),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = calc.evaluate_event("e", states)
        # 3 主体 → 6 有向对（排除自身），认知水平互异 → 全部不对称
        assert len(report.asymmetric_pairs) == 6
        assert report.asymmetry_ratio > 0.9


class TestNIAMACMPHASE2:
    """NIA-MACM PHASE-2: 认知距离 → 协商触发。"""

    def test_negotiation_triggered_when_distant(self):
        """distance > threshold → 进入协商协议。"""
        calc = CognitiveDistanceCalculator()
        s_near = _s(A=0.8, D=0.8, SC=0.8)
        s_far = _s(A=0.2, D=0.2, SC=0.2)
        assert calc.negotiation_required(s_near, s_far) is True

    def test_no_negotiation_when_close(self):
        """认知接近 → 不触发协商（直接协作）。"""
        calc = CognitiveDistanceCalculator()
        s1 = _s(A=0.8, D=0.8, SC=0.8)
        s2 = _s(A=0.79, D=0.81, SC=0.79)
        assert calc.negotiation_required(s1, s2) is False


class TestIntegration:
    """与单主体认知状态计算器集成（复用 CognitiveStateCalculator 输出）。"""

    def test_feeds_from_cognitive_state_calculator(self):
        """多主体距离计算可直接消费单主体五维向量输出。"""
        from tdca_cognitive_state import CognitiveStateCalculator
        single = CognitiveStateCalculator()
        # 三个主体对同一事件的认知状态（模拟）
        h1 = single.compute(embedding_similarity=0.9, constraint_satisfaction_rate=0.9,
                            cross_domain_success_rate=9.0, total_calls=10,
                            negative_space_detection_accuracy=0.95)
        m1 = single.compute(embedding_similarity=0.6, constraint_satisfaction_rate=0.6,
                            cross_domain_success_rate=6.0, total_calls=10,
                            negative_space_detection_accuracy=0.6)
        l1 = single.compute(embedding_similarity=0.3, constraint_satisfaction_rate=0.3,
                            cross_domain_success_rate=3.0, total_calls=10,
                            negative_space_detection_accuracy=0.3)
        calc = CognitiveDistanceCalculator()
        report = calc.evaluate_event("data-cross-border", {
            "H1": h1, "M1": m1, "L1": l1,
        })
        calc.validate(report)
        # 认知势差: H1 理解 L1 距离 < L1 理解 H1 距离
        d_hl = calc.cognitive_distance(h1, l1)
        d_lh = calc.cognitive_distance(l1, h1)
        assert d_hl < d_lh
