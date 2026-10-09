# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     multisig 三方多签门控测试（SV-4/SV-6）
# 约束矩阵:     FC-SBX-OPS-001 SV-4/SV-6
# 先验分布:     任务书 §五 SV-4/SV-6
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""multisig 三方多签门控测试（SV-4 / SV-6）。"""

from __future__ import annotations

import pytest

from app import multisig


class TestCollectSignature:
    def test_valid_roles(self):
        for role in multisig.TRINITY_ROLES:
            sig = multisig.collect_signature(role, f"did:tdca:{role.upper()}-001", f"sig-{role}")
            assert sig["role"] == role
            assert sig["signature"]

    def test_invalid_role_rejected(self):
        with pytest.raises(ValueError):
            multisig.collect_signature("platform", "did:tdca:X", "s")  # 平台非三位一体

    def test_empty_signature_rejected(self):
        with pytest.raises(ValueError):
            multisig.collect_signature("innovator", "did:tdca:X", "")


class TestVerifyTrinitySignatures:
    def _all(self):
        return [
            {"role": "innovator", "did": "d1", "signature": "s1"},
            {"role": "investor", "did": "d2", "signature": "s2"},
            {"role": "government", "did": "d3", "signature": "s3"},
        ]

    def test_all_three_complete(self):
        r = multisig.verify_trinity_signatures(self._all())
        assert r["complete"] is True
        assert r["count"] == 3
        assert r["missing"] == []

    def test_missing_one_incomplete(self):
        r = multisig.verify_trinity_signatures(self._all()[:2])
        assert r["complete"] is False
        assert "government" in r["missing"]

    def test_duplicate_role_not_double_counted(self):
        sigs = self._all() + [{"role": "innovator", "did": "d9", "signature": "s9"}]
        r = multisig.verify_trinity_signatures(sigs)
        assert r["count"] == 3  # 同角色重复不重复计票（SV-6 异构三角）
        assert r["complete"] is True

    def test_invalid_structure_rejected(self):
        with pytest.raises(ValueError):
            multisig.verify_trinity_signatures([{"role": "hacker"}])
        with pytest.raises(ValueError):
            multisig.verify_trinity_signatures("not-a-list")


class TestTermination:
    def test_trinity_roles_can_terminate(self):
        for role in multisig.TRINITY_ROLES:
            assert multisig.can_trigger_termination(role) is True  # SV-4 三方皆可

    def test_non_trinity_cannot(self):
        assert multisig.can_trigger_termination("platform") is False
