"""
TDCA 多主体认知距离 · 模糊数学运算层测试
==========================================
验证模糊贴近度公理 / 包含度不对称（命题 3.10 模糊对应）/
模糊置信度档位（FUZZY_CONFIDENCE）/ 三角模糊数 / 模糊聚类。
"""
import math
import pytest

from tdca_fuzzy_distance import (
    FuzzyCognitiveDistance,
    FuzzyDirection,
    TriangularFuzzyNumber,
)
from tdca_cognitive_distance import CognitiveDistanceCalculator  # 经典版对照


def _s(**kw):
    base = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    base.update(kw)
    return base


class TestFuzzyNearnessAxioms:
    """模糊贴近度公理（Zadeh 模糊集理论）。"""

    def test_self_nearness_is_one(self):
        """N(A,A) = 1（自反性——综合算子；lattice 为参考可 <1）。"""
        fz = FuzzyCognitiveDistance()
        s = _s(A=0.8, D=0.9, SC=0.95)
        near = fz.fuzzy_nearness(s, s)
        assert near.hamming == 1.0
        assert near.euclidean == 1.0
        assert near.maxmin == 1.0
        assert near.integrated == 1.0
        # lattice 为参考算子（格贴近度自反可能 <1，模糊数学特性）
        assert 0.0 <= near.lattice <= 1.0

    def test_symmetry(self):
        """N(A,B) = N(B,A)（贴近度对称——对比距离的不对称）。"""
        fz = FuzzyCognitiveDistance()
        a = _s(A=0.9, SC=0.95)
        b = _s(A=0.3, SC=0.3)
        assert fz.fuzzy_nearness(a, b).integrated == pytest.approx(
            fz.fuzzy_nearness(b, a).integrated)

    def test_bounds(self):
        """贴近度 ∈ [0,1]。"""
        fz = FuzzyCognitiveDistance()
        a = _s()
        b = _s(A=0.0, D=0.0, L=0.0, C=0.0, SC=0.0)
        near = fz.fuzzy_nearness(a, b)
        for v in (near.lattice, near.hamming, near.euclidean, near.maxmin, near.integrated):
            assert 0.0 <= v <= 1.0

    def test_monotonic(self):
        """认知越接近 → 贴近度越高。"""
        fz = FuzzyCognitiveDistance()
        base = _s()
        near_state = _s(A=0.6, D=0.6)
        far_state = _s(A=0.1, D=0.1, SC=0.1)
        assert fz.fuzzy_nearness(base, near_state).integrated > \
            fz.fuzzy_nearness(base, far_state).integrated


class TestFuzzySubsethoodAsymmetry:
    """模糊包含度——命题 3.10 的模糊对应（认知势差不对称）。"""

    def test_low_contained_in_high(self):
        """低认知主体被高认知主体包含程度高: subsethood(L→H) 大。"""
        fz = FuzzyCognitiveDistance()
        high = _s(A=0.9, D=0.9, L=0.9, C=0.9, SC=0.95)
        low = _s(A=0.3, D=0.3, L=0.3, C=0.3, SC=0.3)
        sub_lh = fz.fuzzy_subsethood(low, high)    # L 被 H 包含
        sub_hl = fz.fuzzy_subsethood(high, low)    # H 被 L 包含
        assert sub_lh > sub_hl                      # 不对称（命题 3.10）

    def test_symmetric_when_equal_level(self):
        """同认知水平 → 包含度对称。"""
        fz = FuzzyCognitiveDistance()
        a = _s(A=0.7, D=0.7)
        b = _s(A=0.7, D=0.7)
        assert fz.fuzzy_subsethood(a, b) == pytest.approx(fz.fuzzy_subsethood(b, a))

    def test_full_containment(self):
        """A ⊆ B → subsethood(A,B) = 1。"""
        fz = FuzzyCognitiveDistance()
        small = _s(A=0.2, D=0.2, L=0.2, C=0.2, SC=0.2)
        big = _s(A=0.8, D=0.8, L=0.8, C=0.8, SC=0.8)
        assert fz.fuzzy_subsethood(small, big) == pytest.approx(1.0)


class TestFuzzyConfidence:
    """模糊置信度（FUZZY_CONFIDENCE 对齐: 方向性判断 + 置信区间）。"""

    def test_high_direction_for_near(self):
        """认知接近 → 方向 HIGH。"""
        fz = FuzzyCognitiveDistance()
        conf = fz.fuzzy_confidence(_s(A=0.8, SC=0.8), _s(A=0.79, SC=0.79))
        assert conf.direction == FuzzyDirection.HIGH
        assert conf.nearness > 0.75

    def test_low_direction_for_far(self):
        """认知远离 → 方向 LOW。"""
        fz = FuzzyCognitiveDistance()
        conf = fz.fuzzy_confidence(_s(A=0.9, SC=0.95), _s(A=0.1, SC=0.1))
        assert conf.direction in (FuzzyDirection.LOW, FuzzyDirection.NO_DIFFERENCE)

    def test_confidence_interval(self):
        """置信区间 = 多算子 min-max（反映一致性）。"""
        fz = FuzzyCognitiveDistance()
        conf = fz.fuzzy_confidence(_s(A=0.8, SC=0.8), _s(A=0.3, SC=0.3))
        lo, hi = conf.confidence_interval
        assert lo <= conf.nearness <= hi
        assert 0.0 <= lo <= hi <= 1.0

    def test_support_dimensions(self):
        """support = 支撑维度数（≤5）。"""
        fz = FuzzyCognitiveDistance()
        conf = fz.fuzzy_confidence(_s(A=0.9), _s(A=0.1))
        assert 1 <= conf.support <= 5


class TestTriangularFuzzyNumber:
    """三角模糊数（认知状态不确定性表达）。"""

    def test_crisp_centroid(self):
        """去模糊化（重心）: (l+m+u)/3。"""
        t = TriangularFuzzyNumber(0.2, 0.5, 0.8)
        assert t.crisp == pytest.approx(0.5)

    def test_distance(self):
        """三角模糊数距离（Chen 法）。"""
        t1 = TriangularFuzzyNumber(0.2, 0.5, 0.8)
        t2 = TriangularFuzzyNumber(0.2, 0.5, 0.8)
        assert t1.distance_to(t2) == pytest.approx(0.0)
        t3 = TriangularFuzzyNumber(0.8, 0.9, 1.0)
        assert t1.distance_to(t3) > 0.0

    def test_invalid_order_rejected(self):
        """l > u → 拒绝（fail-closed）。"""
        with pytest.raises(ValueError):
            TriangularFuzzyNumber(0.8, 0.5, 0.2)


class TestFuzzyMultiSubject:
    """模糊多主体不对称对齐评测。"""

    def test_report_structure(self):
        """贴近度矩阵（对称）+ 包含度矩阵（不对称）+ 置信度矩阵。"""
        fz = FuzzyCognitiveDistance()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "M1": _s(A=0.6, D=0.6, SC=0.6),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = fz.evaluate_fuzzy_event("policy", states)
        assert set(report.subjects) == {"H1", "M1", "L1"}
        fz.validate(report)

    def test_asymmetry_via_subsethood(self):
        """认知势差 → 包含度不对称对识别。"""
        fz = FuzzyCognitiveDistance()
        states = {
            "H1": _s(A=0.9, D=0.9, SC=0.95),
            "L1": _s(A=0.3, D=0.3, SC=0.3),
        }
        report = fz.evaluate_fuzzy_event("e", states)
        assert "H1→L1" in report.asymmetric_pairs
        assert "L1→H1" in report.asymmetric_pairs
        assert report.subsethood_matrix["L1"]["H1"] > report.subsethood_matrix["H1"]["L1"]

    def test_clustering(self):
        """模糊聚类: 认知接近主体归同类（H1/H2 同簇）。"""
        fz = FuzzyCognitiveDistance()
        states = {
            "H1": _s(A=0.9, SC=0.95),
            "H2": _s(A=0.88, SC=0.93),
            "L1": _s(A=0.1, D=0.1, L=0.1, C=0.1, SC=0.1),  # 显著远离
        }
        report = fz.evaluate_fuzzy_event("e", states)
        # H1/H2 贴近度 > λ → 同簇
        assert report.nearness_matrix["H1"]["H2"] > 0.6
        # H1 与 L1 贴近度低（显著认知差距）→ 不强制同簇
        assert report.nearness_matrix["H1"]["L1"] < 0.6
        # 验证 H1/H2 同簇
        for cluster in report.clusters:
            if "H1" in cluster:
                assert "H2" in cluster


class TestFuzzyVsClassical:
    """模糊运算 vs 经典加权欧氏——互补一致性。"""

    def test_direction_agreement(self):
        """模糊贴近度与经典距离方向一致（近→近，远→远）。"""
        fz = FuzzyCognitiveDistance()
        cl = CognitiveDistanceCalculator()
        near_a, near_b = _s(A=0.8, SC=0.8), _s(A=0.79, SC=0.79)
        far_a, far_b = _s(A=0.9, SC=0.95), _s(A=0.1, SC=0.1)
        # 模糊: 近对贴近度 > 远对贴近度
        assert fz.fuzzy_nearness(near_a, near_b).integrated > \
            fz.fuzzy_nearness(far_a, far_b).integrated
        # 经典: 近对距离 < 远对距离
        assert cl.cognitive_distance(near_a, near_b) < \
            cl.cognitive_distance(far_a, far_b)

    def test_asymmetry_both_layers(self):
        """经典势差与模糊包含度均体现不对称（互补验证命题 3.10）。"""
        fz = FuzzyCognitiveDistance()
        cl = CognitiveDistanceCalculator()
        high = _s(A=0.9, D=0.9, SC=0.95)
        low = _s(A=0.3, D=0.3, SC=0.3)
        # 经典: 低→高距离 > 高→低距离
        assert cl.cognitive_distance(low, high) > cl.cognitive_distance(high, low)
        # 模糊: 低被高包含 > 高被低包含
        assert fz.fuzzy_subsethood(low, high) > fz.fuzzy_subsethood(high, low)
