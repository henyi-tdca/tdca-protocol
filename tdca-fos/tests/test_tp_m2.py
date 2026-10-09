# -*- coding: utf-8 -*-
"""
TDCA-TP 推理引擎 M2 完整测试 — 五规则 × 正例/反例 + 快慢路径
制度锚定: TDCA-KG-001 §2.3 | ID38/ID82/ID54/ID79/SPEC-002 | FC: TDCA-FC-20260804-006-M2
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_tp.engine.inference_engine import (
    TDCATPReasoner, AlertSeverity, InferenceResult,
)
from tdca_nca.generator import NCAGenerator
from tdca_nsfl.fuse_engine import NSFLEngine, FuseType


@pytest.fixture
def nca_gen():
    return NCAGenerator()


@pytest.fixture
def nsfl(nca_gen):
    return NSFLEngine(nca_generator=nca_gen)


@pytest.fixture
def reasoner(nca_gen, nsfl):
    return TDCATPReasoner(nca_generator=nca_gen, nsfl_engine=nsfl)


class TestRuleRegistration:
    """五规则注册完整性"""

    def test_five_rules_registered(self):
        r = TDCATPReasoner()
        assert set(r.list_rules()) == {
            "ExceptionDetection", "InterfaceEntropyZero", "MRCRSceneIsolation",
            "MOUContinuousVerification", "NCANestingDepth",
        }

    def test_severity_map(self, reasoner):
        assert reasoner.get_rule("ExceptionDetection")["severity"] == AlertSeverity.CRITICAL
        assert reasoner.get_rule("InterfaceEntropyZero")["severity"] == AlertSeverity.CRITICAL
        assert reasoner.get_rule("MRCRSceneIsolation")["severity"] == AlertSeverity.WARNING
        assert reasoner.get_rule("MOUContinuousVerification")["severity"] == AlertSeverity.WARNING
        assert reasoner.get_rule("NCANestingDepth")["severity"] == AlertSeverity.INFO

    def test_unknown_rule_raises(self, reasoner):
        with pytest.raises(ValueError):
            reasoner.execute("NoSuchRule", {})

    def test_inference_result_type(self, reasoner):
        out = reasoner.execute("ExceptionDetection", {"principle_id": "ID1"})
        assert isinstance(out, InferenceResult)


class TestExceptionDetectionID38:
    """规则 1：破例识别 — ID38（正例/反例）"""

    def test_positive_bypass_detected(self, reasoner):
        out = reasoner.execute("ExceptionDetection", {
            "principle_id": "ID29", "principle_priority": 5,
            "draft_text": "申请绕过 ID29 建立例外通道",
        })
        assert out.triggered is True
        assert out.severity == AlertSeverity.CRITICAL
        assert out.alert["type"] == "PSEUDO_INNOVATION"
        assert "绕过" in out.alert["evidence"]["detected_patterns"]

    def test_negative_no_bypass(self, reasoner):
        out = reasoner.execute("ExceptionDetection", {
            "principle_id": "ID29", "principle_priority": 5,
            "draft_text": "常规开发请求，遵循既有制度",
        })
        assert out.triggered is False
        assert out.action_taken == "NO_ACTION"

    def test_low_priority_principle_not_triggered(self, reasoner):
        out = reasoner.execute("ExceptionDetection", {
            "principle_id": "ID35", "principle_priority": 3,
            "draft_text": "申请绕过 ID35",
        })
        assert out.triggered is False

    def test_critical_triggers_nsfl_fuse(self, reasoner, nsfl):
        out = reasoner.execute("ExceptionDetection", {
            "principle_id": "ID29", "principle_priority": 5,
            "draft_text": "绕过 ID29",
        })
        assert out.action_taken.startswith("NSFL_FUSE_TRIGGERED")
        assert nsfl.fuse_history_count() == 1

    def test_generates_nca(self, reasoner, nca_gen):
        out = reasoner.execute("ExceptionDetection", {
            "principle_id": "ID29", "principle_priority": 5,
            "draft_text": "绕过 ID29",
        })
        assert out.nca_reference.startswith("NCA-")
        assert nca_gen.count() >= 1


class TestInterfaceEntropyID82:
    """规则 2：接口熵=0 — ID82（正例/反例）"""

    def test_positive_entropy_positive(self, reasoner):
        out = reasoner.execute("InterfaceEntropyZero", {
            "code_module_id": "mod-1", "compiler": "DeepSeek-V4",
            "calculated_entropy": 0.1,
        })
        assert out.triggered is True
        assert out.alert["action"] == "BLOCK_DEPLOYMENT"

    def test_negative_zero_entropy(self, reasoner):
        out = reasoner.execute("InterfaceEntropyZero", {
            "code_module_id": "mod-1", "compiler": "DeepSeek-V4",
            "calculated_entropy": 0.0,
        })
        assert out.triggered is False

    def test_wrong_compiler_skipped(self, reasoner):
        out = reasoner.execute("InterfaceEntropyZero", {
            "code_module_id": "mod-1", "compiler": "OtherModel",
            "calculated_entropy": 0.5,
        })
        assert out.triggered is False

    def test_entropy_critical_fuse(self, reasoner, nsfl):
        out = reasoner.execute("InterfaceEntropyZero", {
            "code_module_id": "mod-1", "compiler": "DeepSeek-V4",
            "calculated_entropy": 0.3,
        })
        assert out.action_taken.startswith("NSFL_FUSE_TRIGGERED")


class TestMRCRIsolationID54:
    """规则 3：MRCR 场景隔离 — ID54（正例/反例）"""

    def test_positive_isolated_false(self, reasoner):
        out = reasoner.execute("MRCRSceneIsolation", {
            "agent_id": "a1", "scenes": ["s1", "s2"],
            "isolation_verified": False,
        })
        assert out.triggered is True
        assert out.severity == AlertSeverity.WARNING
        assert out.alert["action"] == "WARN_AND_AUDIT"

    def test_negative_isolated_true(self, reasoner):
        out = reasoner.execute("MRCRSceneIsolation", {
            "agent_id": "a1", "scenes": ["s1", "s2"],
            "isolation_verified": True,
        })
        assert out.triggered is False

    def test_single_scene_no_trigger(self, reasoner):
        out = reasoner.execute("MRCRSceneIsolation", {
            "agent_id": "a1", "scenes": ["s1"],
        })
        assert out.triggered is False

    def test_warning_no_fuse(self, reasoner, nsfl):
        out = reasoner.execute("MRCRSceneIsolation", {
            "agent_id": "a1", "scenes": ["s1", "s2"],
            "isolation_verified": False,
        })
        assert out.action_taken == "WARN_AND_AUDIT"
        assert nsfl.fuse_history_count() == 0


class TestMOUContinuousID79:
    """规则 4：MOU 连续验证 — ID79（正例/反例）"""

    def test_positive_insufficient_mou(self, reasoner):
        out = reasoner.execute("MOUContinuousVerification", {
            "window_days": 30, "mou_count": 20,  # 缺失 10 天 > 7%
        })
        assert out.triggered is True
        assert out.alert["action"] == "WARN_AND_REQUEST_MOU"

    def test_negative_sufficient_mou(self, reasoner):
        out = reasoner.execute("MOUContinuousVerification", {
            "window_days": 30, "mou_count": 29,  # 缺失 1 天 < 7%
        })
        assert out.triggered is False

    def test_missing_rate_calculation(self, reasoner):
        out = reasoner.execute("MOUContinuousVerification", {
            "window_days": 30, "mou_count": 20,
        })
        assert abs(out.alert["evidence"]["missing_rate"] - 10 / 30) < 1e-6

    def test_warning_no_fuse(self, reasoner, nsfl):
        out = reasoner.execute("MOUContinuousVerification", {
            "window_days": 30, "mou_count": 20,
        })
        assert out.action_taken == "WARN_AND_REQUEST_MOU"
        assert nsfl.fuse_history_count() == 0


class TestNCANestingDepth:
    """规则 5：NCA 嵌套深度 — SPEC-002（正例/反例）"""

    def test_positive_too_deep(self, reasoner):
        out = reasoner.execute("NCANestingDepth", {
            "nca_id": "nca-x", "nesting_depth": 11, "max_depth": 10,
        })
        assert out.triggered is True
        assert out.severity == AlertSeverity.INFO

    def test_negative_within_depth(self, reasoner):
        out = reasoner.execute("NCANestingDepth", {
            "nca_id": "nca-x", "nesting_depth": 5, "max_depth": 10,
        })
        assert out.triggered is False

    def test_info_action_logged(self, reasoner):
        out = reasoner.execute("NCANestingDepth", {
            "nca_id": "nca-x", "nesting_depth": 11, "max_depth": 10,
        })
        assert out.alert["action"] == "LOG_AND_MONITOR"
