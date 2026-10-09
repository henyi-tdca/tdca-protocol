# -*- coding: utf-8 -*-
"""效用精灵 × 模糊数学层化合测试（TDCA-PRINCIPLE-FUZZY-DISTANCE-001 §五）。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tdca-toolchain"))

import pytest

from fuzzy_integration import (
    FuzzyUtilityGenieIntegration,
    FuzzyWatermark,
    ID90Check,
)
from tdca_fuzzy_distance import FuzzyCognitiveDistance


def _s(**kw):
    b = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    b.update(kw)
    return b


def _fuzzy_report():
    """生成多主体模糊评测（供化合输入）。"""
    fz = FuzzyCognitiveDistance()
    states = {
        "H1": _s(A=0.9, D=0.9, SC=0.95),
        "M1": _s(A=0.6, D=0.6, SC=0.6),
        "L1": _s(A=0.3, D=0.3, SC=0.3),
    }
    return fz.evaluate_fuzzy_event("compound-test", states)


class TestFuzzyInput:
    """utility_genie.fuzzy_input 接口。"""

    def test_input_contract(self):
        """接口接收三输入 → 封装为 fuzzy_context。"""
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        ctx = genie.fuzzy_input(
            report.confidence_matrix, report.subsethood_matrix, report.clusters)
        assert set(ctx) == {"confidence_matrix", "subsethood_matrix",
                            "lambda_clusters", "lambda_threshold",
                            "operator_selection"}
        assert ctx["lambda_threshold"] == 0.6
        assert ctx["operator_selection"] == "hamming+euclidean+maxmin"

    def test_end_to_end_fuzzy_to_input(self):
        """模糊层 evaluate_fuzzy_event 输出直接可作化合输入（接口闭合）。"""
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        ctx = genie.fuzzy_input(report.confidence_matrix,
                                report.subsethood_matrix, report.clusters)
        # 置信度矩阵含方向性判断
        h1_l1 = ctx["confidence_matrix"]["H1"]["L1"]
        assert h1_l1["direction"] in ("HIGH", "MEDIUM", "LOW", "NO_DIFFERENCE")


class TestID90:
    """ID90 三条件化合必要性检查。"""

    def test_pricing_passes(self):
        genie = FuzzyUtilityGenieIntegration()
        check = genie.check_id90("pricing", {})
        assert check.passed is True
        assert check.irreducible and check.emergent_value and check.nonlinear

    def test_early_warning_passes(self):
        genie = FuzzyUtilityGenieIntegration()
        check = genie.check_id90("early_warning", {})
        assert check.passed is True

    def test_nca_quality_passes(self):
        genie = FuzzyUtilityGenieIntegration()
        check = genie.check_id90("nca_quality", {})
        assert check.passed is True

    def test_unknown_scene_rejected(self):
        """未知场景 → 不通过（ID90 最小化合——不盲目化合）。"""
        genie = FuzzyUtilityGenieIntegration()
        check = genie.check_id90("random_thing", {})
        assert check.passed is False


class TestWatermark:
    """模糊度水印审计。"""

    def test_watermark_fields(self):
        wm = FuzzyWatermark(lambda_threshold=0.6,
                            operator_selection="hamming+euclidean+maxmin",
                            fail_closed_triggered=False, timestamp=1.0)
        d = wm.to_dict()
        assert set(d) == {"lambda_threshold", "operator_selection",
                          "fail_closed_triggered", "trigger_reason", "timestamp"}

    def test_compound_carries_watermark(self):
        """化合结果含水印（λ/算子/fail-closed 记录）。"""
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_early_warning(report.clusters, report.confidence_matrix)
        assert result.watermark.lambda_threshold == 0.6
        assert result.watermark.operator_selection == "hamming+euclidean+maxmin"
        assert result.watermark.fail_closed_triggered is False
        assert result.nca_ref.startswith("NCA-FUZZY-")

    def test_fail_closed_watermark(self):
        """fail-closed 触发 → 水印记录原因。"""
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_early_warning([], {})
        assert result.watermark.fail_closed_triggered is True
        assert "无主体" in result.watermark.trigger_reason


class TestCompoundPricing:
    """化合场景 1: 配置权定价（Shapley 认知权重修正）。"""

    def test_low_cog_boosted(self):
        """低认知主体 Shapley 上浮（哑元风险补偿，UPDA 倾斜）。"""
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        shapley = {"H1": 40.0, "M1": 35.0, "L1": 25.0}   # 原始 Shapley
        result = genie.compound_pricing(shapley, report.confidence_matrix,
                                        report.subsethood_matrix)
        out = result.output
        # 认知权重: L1（低认知）权重 > 1（上浮）
        assert out["cognitive_weights"]["L1"] > 1.0
        assert out["cognitive_weights"]["H1"] < 1.0
        # 修正后 Shapley: L1 占比上升，H1 占比下降
        assert out["shapley_adjusted"]["L1"] > shapley["L1"]
        # 效率性保持: 总额不变
        assert abs(sum(out["shapley_adjusted"].values()) - sum(shapley.values())) < 1e-6

    def test_id90_gate(self):
        """ID90 检查通过才化合（水印 + nca_ref）。"""
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_pricing({"A": 50.0, "B": 50.0},
                                        report.confidence_matrix,
                                        report.subsethood_matrix)
        assert result.id90.passed is True
        assert result.nca_ref.startswith("NCA-FUZZY-PRICE")


class TestCompoundEarlyWarning:
    """化合场景 2: 负空间预警（群体理性约束）。"""

    def test_high_fragmentation_warns(self):
        """群体高度分裂 → HIGH 预警。"""
        genie = FuzzyUtilityGenieIntegration()
        # 3 主体 3 簇（完全分裂）
        result = genie.compound_early_warning([["H1"], ["M1"], ["L1"]], {})
        assert result.output["level"] == "HIGH"
        assert "人工介入" in result.output["advice"]

    def test_low_fragmentation_ok(self):
        """认知凝聚 → LOW。"""
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_early_warning([["H1", "M1", "L1"]], {})
        assert result.output["level"] == "LOW"

    def test_empty_fail_closed(self):
        """无主体 → fail-closed（UNKNOWN + 水印标记）。"""
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_early_warning([], {})
        assert result.output["level"] == "UNKNOWN"
        assert result.watermark.fail_closed_triggered is True


class TestCompoundNCAQuality:
    """化合场景 3: NCA 质量评估（认知资产折旧率）。"""

    def test_high_subsethood_depreciates(self):
        """高包含度链（低原创性）→ 折旧率上升 → MOU 降权。"""
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_nca_quality([0.9, 0.85, 0.88], mou_impact=0.5)
        out = result.output
        assert out["depreciation_rate"] > 0.5
        assert out["mou_impact_adjusted"] < out["mou_impact_original"]

    def test_low_subsethood_keeps(self):
        """低包含度（高原创性）→ 折旧率低 → MOU 保持。"""
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_nca_quality([0.1, 0.2, 0.15], mou_impact=0.5)
        out = result.output
        assert out["depreciation_rate"] < 0.1
        assert out["mou_impact_adjusted"] > 0.4

    def test_id90_gate(self):
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_nca_quality([0.5], mou_impact=0.5)
        assert result.id90.passed is True
        assert result.nca_ref.startswith("NCA-FUZZY-NQ")


class TestCompoundResultShape:
    """化合结果结构统一（含审计）。"""

    def test_result_shape(self):
        report = _fuzzy_report()
        genie = FuzzyUtilityGenieIntegration()
        result = genie.compound_pricing({"A": 50.0, "B": 50.0},
                                        report.confidence_matrix,
                                        report.subsethood_matrix)
        d = result.to_dict()
        assert set(d) == {"scene", "fuzzy_input", "output", "id90", "watermark", "nca_ref"}
        assert d["id90"]["passed"] is True

class TestLegacyECE:
    """遗留 1: 化合与 ECE 引擎。"""

    class _FakeGenie:
        def __init__(self):
            self.calls = []
        def calibrate_algorithm(self, nca):
            self.calls.append(nca)

    class _FakeECE:
        def __init__(self, genie):
            self.genie = genie

    def test_ece_calibrates(self):
        """化合产物经 ECE nca_to_genie 管道 → 效用精灵校准。"""
        genie = self._FakeGenie()
        ece = self._FakeECE(genie)
        report = _fuzzy_report()
        g = FuzzyUtilityGenieIntegration()
        result = g.compound_pricing({"A": 50.0, "B": 50.0},
                                    report.confidence_matrix, report.subsethood_matrix)
        out = g.compound_with_ece("pricing", result, ece)
        assert out.output["ece_calibrated"] is True
        assert len(genie.calls) == 1
        assert genie.calls[0]["nca_ref"].startswith("NCA-FUZZY-")
        assert "watermark" in genie.calls[0]

    def test_ece_missing_non_blocking(self):
        """无 ECE 引擎 → 记录待校准（不阻断）。"""
        report = _fuzzy_report()
        g = FuzzyUtilityGenieIntegration()
        result = g.compound_early_warning(report.clusters, report.confidence_matrix)
        out = g.compound_with_ece("early_warning", result, None)
        assert out.output["ece_calibrated"] is False


class TestLegacyID90Dynamic:
    """遗留 2: ID90 三条件动态实判。"""

    def test_pricing_dynamic(self):
        """配置权定价动态判: 有认知势差 → 通过；无势差 → 拒绝。"""
        report = _fuzzy_report()
        g = FuzzyUtilityGenieIntegration()
        ctx = g.fuzzy_input(report.confidence_matrix, report.subsethood_matrix, [])
        # 有不对称包含度 → irreducible=True
        check = g.check_id90_dynamic("pricing", ctx, {"weights_effect": True})
        assert check.passed is True
        # 无势差（对称包含度）→ 拒绝
        sym_sub = {"A": {"B": 0.5}, "B": {"A": 0.5}}
        ctx_sym = g.fuzzy_input(report.confidence_matrix, sym_sub, [])
        check2 = g.check_id90_dynamic("pricing", ctx_sym, {"weights_effect": True})
        assert check2.passed is False

    def test_early_warning_dynamic(self):
        """负空间预警动态判: 分裂度非线性跃迁。"""
        g = FuzzyUtilityGenieIntegration()
        ctx = {"lambda_clusters": [["H1"], ["M1"], ["L1"]]}  # 完全分裂
        check = g.check_id90_dynamic("early_warning", ctx)
        assert check.nonlinear is True
        assert check.passed is True

    def test_nca_quality_dynamic(self):
        """NCA 质量动态判: 高包含度链 → 通过；低包含度 → 拒绝。"""
        g = FuzzyUtilityGenieIntegration()
        check = g.check_id90_dynamic("nca_quality", {},
                                     {"subsethood_chain": [0.9, 0.8]})
        assert check.passed is True
        check2 = g.check_id90_dynamic("nca_quality", {},
                                      {"subsethood_chain": [0.1, 0.2]})
        assert check2.passed is False

    def test_unknown_scene_rejected(self):
        g = FuzzyUtilityGenieIntegration()
        assert g.check_id90_dynamic("random", {}).passed is False


class TestLegacyFullPipeline:
    """遗留 3: fuzzy_input → compute 全流程串联。"""

    def test_full_pipeline_pricing_with_compute(self):
        """fuzzy_input → compound_pricing → compute_fn 消费。"""
        report = _fuzzy_report()
        g = FuzzyUtilityGenieIntegration()
        ctx = g.fuzzy_input(report.confidence_matrix, report.subsethood_matrix,
                            report.clusters)
        result = g.full_pipeline(
            "pricing", ctx,
            compute_fn=lambda output, **kw: {"adjusted_total": sum(output["shapley_adjusted"].values())},
            compute_kwargs={"shapley_values": {"H1": 40.0, "M1": 35.0, "L1": 25.0}},
        )
        assert "compute_result" in result.output
        assert abs(result.output["compute_result"]["adjusted_total"] - 100.0) < 1e-3  # 效率性保持（浮点容差）

    def test_full_pipeline_early_warning(self):
        report = _fuzzy_report()
        g = FuzzyUtilityGenieIntegration()
        ctx = g.fuzzy_input(report.confidence_matrix, report.subsethood_matrix,
                            report.clusters)
        result = g.full_pipeline("early_warning", ctx)
        assert result.output["level"] in ("LOW", "MEDIUM", "HIGH")

    def test_full_pipeline_unknown_rejected(self):
        g = FuzzyUtilityGenieIntegration()
        with pytest.raises(ValueError):
            g.full_pipeline("random", {})
