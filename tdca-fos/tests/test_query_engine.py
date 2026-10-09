# -*- coding: utf-8 -*-
"""
TDCA-Graph 查询引擎测试 — 边查询与 NCA 生成
制度锚定: TDCA-KG-001 §3.3/§5.3 | ID82/ID91 | FC: TDCA-FC-20260804-006
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_graph.query.engine import (
    TDCAGraphQueryEngine, InterfaceEntropyViolation,
)


class TestGetDevelopmentConstraints:
    """查询 3.3：开发约束查询"""

    def test_returns_constraint_set(self, memory_driver, nca_placeholder):
        memory_driver.route("total_interface_entropy", {
            "target_role": "Constitution-Trainer",
            "required_principles": ["ID29", "ID35"],
            "required_constitutions": [1, 2],
            "required_nsfl_rules": ["NSFL-LEGAL-001"],
            "required_function_specs": [],
            "total_interface_entropy": 0,
        })
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        result = engine.get_development_constraints(
            "Constitution-Trainer", "GOVERNANCE", "DeepSeek-V4", "scene-1")
        assert result["interface_entropy"] == 0.0
        assert result["constraint_set"]["required_principles"] == ["ID29", "ID35"]

    def test_raises_on_entropy_positive(self, memory_driver, nca_placeholder):
        memory_driver.route("total_interface_entropy", {
            "target_role": "x",
            "total_interface_entropy": 3,
        })
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        with pytest.raises(InterfaceEntropyViolation):
            engine.get_development_constraints(
                "x", "GOVERNANCE", "DeepSeek-V4", "scene-1")

    def test_generates_nca(self, memory_driver, nca_placeholder):
        memory_driver.route("total_interface_entropy", {
            "target_role": "t", "total_interface_entropy": 0,
        })
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        result = engine.get_development_constraints(
            "t", "GOVERNANCE", "DeepSeek-V4", "scene-2")
        assert result["nca_reference"] is not None
        assert nca_placeholder.count() == 1

    def test_version_carried(self, memory_driver, nca_placeholder):
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder,
                                      current_version="v1.2.0")
        result = engine.get_development_constraints(
            "t", "GOVERNANCE", "DeepSeek-V4", "s")
        assert result["version"] == "v1.2.0"

    def test_fail_closed_without_nca(self, memory_driver):
        """AGENT-DEPLOY-001-FOLLOWUP TASK-006: 无 NCA 生成器 → fail-closed 拒绝（ID91）"""
        from tdca_graph.query.engine import NCAGenerationFailure
        engine = TDCAGraphQueryEngine(memory_driver)  # nca=None
        with pytest.raises(NCAGenerationFailure):
            engine.get_development_constraints(
                "t", "GOVERNANCE", "DeepSeek-V4", "s")


class TestSection53Queries:
    """TDCA-KG-001 §5.3 五个核心查询"""

    def test_get_required_principles(self, memory_driver, nca_placeholder):
        memory_driver.route("REQUIRES", [{"id": "ID29", "name": "n", "priority": 5}])
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        rows = engine.get_required_principles("Constitution-Trainer")
        assert rows[0]["id"] == "ID29"
        assert nca_placeholder.count() == 1

    def test_detect_contradictions(self, memory_driver, nca_placeholder):
        memory_driver.route("CONTRADICTS", [{"p1_id": "ID1", "p2_id": "ID2",
                                             "alert": "CONTRADICTION_DETECTED"}])
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        rows = engine.detect_principle_contradictions(["ID1", "ID2"])
        assert rows[0]["alert"] == "CONTRADICTION_DETECTED"

    def test_get_nsfl_rules(self, memory_driver, nca_placeholder):
        memory_driver.route("MUST_OBEY", [{"id": "NSFL-LEGAL-001", "type": "LEGAL",
                                           "pattern": "⊗", "level": "HARD"}])
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        rows = engine.get_nsfl_rules_for_role("Constitution-Trainer")
        assert rows[0]["id"] == "NSFL-LEGAL-001"

    def test_verify_spec_completeness(self, memory_driver, nca_placeholder):
        memory_driver.route("DEFINED_BY", {
            "has_objective": True, "has_constraints": True, "has_prior": True,
            "has_config_right": True, "has_allocation": True, "has_audit_trail": True,
        })
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        result = engine.verify_function_spec_completeness("role-x")
        assert all(result.values())

    def test_verify_nsfl_on_path(self, memory_driver, nca_placeholder):
        memory_driver.route("nsfl_triggered", [{
            "rule_id": "NSFL-INST-001", "timestamp": 1,
            "alert": "NEGATIVE_SPACE_ON_PATH",
        }])
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        rows = engine.verify_nsfl_on_path("Compile-Agent", "Constitution-Trainer")
        assert rows[0]["alert"] == "NEGATIVE_SPACE_ON_PATH"

    def test_mrcr_isolation(self, memory_driver, nca_placeholder):
        memory_driver.route("HOLDS_ROLE", {"isolated": True})
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        assert engine.check_mrcr_isolation("agent-1", ["s1", "s2"]) is True
