# -*- coding: utf-8 -*-
"""
TDCA D1-D4 裁决落地测试（DCD-20260805-003）
制度锚定: TDCA-GOV-THEORY-001 | DCD-20260805-003 | FC: TDCA-FC-20260804-006-M5
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_graph.core.ontology import (
    CognitiveStateVector, AssetCognitiveVector, AssetValueVector,
)


class TestCognitiveStateVector:
    """D1：智能体状态认知向量（汇编 V2.0 语义）"""

    def test_default_zeros(self):
        v = CognitiveStateVector()
        assert v.A == 0.0 and v.SC == 0.0

    def test_agent_semantics(self):
        v = CognitiveStateVector(A=0.9, D=0.2, L=0.5, C=0.8, SC=0.95)
        # 智能体语义：A=认知活跃度, C=协作连通度, SC=自我置信度
        assert v.A == 0.9
        assert v.C == 0.8
        assert v.SC == 0.95


class TestAssetCognitiveVector:
    """D1：资产认知向量（TERMS-001 语义）"""

    def test_asset_semantics_distinct(self):
        v = AssetCognitiveVector(A=0.7, D=0.9, L=0.6, C=1.0, SC=0.8)
        # 资产语义：A=可用性, C=合规性, SC=场景一致性
        assert v.A == 0.7
        assert v.C == 1.0  # 合规性
        assert v.SC == 0.8


class TestAssetValueVector:
    """D2：五维价值向量 V=(U,S,F,C,R)"""

    def test_value_positive_r(self):
        v = AssetValueVector(U=100, S=0.5, F=0.8, C=1.0, R=0.9)
        assert v.asset_value() == pytest.approx(100 * 0.5 * 0.8 * 1.0)

    def test_r_zero_veto(self):
        """R≤0 一票否决 → 资产价值强制归零"""
        v = AssetValueVector(U=100, S=0.5, F=0.8, C=1.0, R=0.0)
        assert v.asset_value() == 0.0

    def test_r_negative_veto(self):
        """R<0（主题相悖）→ 即使其他维度高也归零"""
        v = AssetValueVector(U=100, S=0.9, F=0.9, C=1.0, R=-0.5)
        assert v.asset_value() == 0.0

    def test_dimension_semantics(self):
        v = AssetValueVector(U=1, S=2, F=3, C=4, R=5)
        assert (v.U, v.S, v.F, v.C, v.R) == (1, 2, 3, 4, 5)
