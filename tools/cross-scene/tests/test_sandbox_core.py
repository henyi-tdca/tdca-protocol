# SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-
"""W3 T-P3-001 跨场景沙盒核心测试（发布树版：沙盒引擎直测，无 D-2/HTTP 依赖）。"""
import pytest
from cross_scene.sandbox import CrossSceneSandbox


def test_activation_decreases_with_interactions():
    """交互冲突增多 → 衰减增大 → 激活系数下降（externality_decay 建模）。"""
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    a0 = sb.activation_coefficient()["activation_coefficient"]
    sb.interactions.append({"conflicts": 10, "mapping_cost": 5})
    a1 = sb.activation_coefficient()["activation_coefficient"]
    assert a1 < a0


def test_data_isolation_sanitized_view():
    """数据隔离：脱敏共享视图 + 原始数据禁止直取。"""
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    r = sb.inject_data("A", {"id": "USER-1", "did": "DID-X", "revenue": 100}, nsfl_verdict="PASS")
    assert r["injection_status"] == "SUCCESS"
    view = sb.get_shared_view("A", caller="B")
    assert "revenue" in view and "id" not in view and "did" not in view   # 脱敏
    with pytest.raises(PermissionError):
        sb.get_shared_view("A", caller="A")   # 原始数据隔离


def test_algorithm_hash_verifies():
    """算法哈希上链 + 篡改检测。"""
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    assert sb.verify_algorithm_hash() is True
    sb.algorithm_hash = "tampered"
    assert sb.verify_algorithm_hash() is False


def test_evaluate_explainable_fields():
    """评估明细可解释（激活系数/MOU/PCR/衰减/网络效应）。"""
    sb = CrossSceneSandbox.create(["A", "B", "C"], 9000.0, "DID-1")
    detail = sb.activation_coefficient()
    assert set(detail) >= {"activation_coefficient", "total_mou", "total_pcr",
                           "externality_decay", "externality_benefit"}
    assert detail["total_pcr"] == 9000.0
    assert detail["externality_benefit"] > 0   # 3 场景网络效应
