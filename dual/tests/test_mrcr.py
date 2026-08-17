# -*- coding: utf-8 -*-
# TDCA 制度水印: TDCA-FC-20260811-002-DUAL-PROTOCOL | NSFL-V0.2 | L2 配置权市场层
"""mrcr_manager 测试：多角色兼容性管理器。"""
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "engine"))

from mrcr_manager import MRCRManager  # noqa: E402


@pytest.fixture
def mrcr():
    m = MRCRManager()
    m.register_role("user-A", "Developer", "general")
    m.register_role("user-A", "Financial-Engineer", "finance")
    m.set_scene_prohibitions("finance", {"financial_prohibitions": ["bypass_risk_control"]})
    return m


def test_register_role_and_role_query(mrcr):
    assert mrcr.get_role("user-A", "general") == "Developer"
    assert mrcr.get_role("user-A", "finance") == "Financial-Engineer"
    assert mrcr.get_role("user-B", "finance") is None


def test_scene_isolation(mrcr):
    assert "user-A" in mrcr.scene_users("general")
    assert "user-A" in mrcr.scene_users("finance")


def test_permission_granted(mrcr):
    assert mrcr.check_permission("user-A", "general", "code_generation") is True
    assert mrcr.check_permission("user-A", "finance", "risk_validation") is True


def test_permission_denied_no_role(mrcr):
    assert mrcr.check_permission("user-X", "finance", "code_generation") is False


def test_prohibition_blocks_action(mrcr):
    # finance 场景禁止 bypass_risk_control
    assert mrcr.check_permission("user-A", "finance", "bypass_risk_control") is False


def test_audit_trail_records(mrcr):
    mrcr.audit_action("user-A", "finance", "code_generation", True)
    mrcr.audit_action("user-A", "finance", "bypass_risk_control", False)
    trail = mrcr.get_audit_trail("user-A", "finance")
    assert len(trail) == 2
    assert trail[0]["action"] == "code_generation"
    assert trail[0]["result"] is True
    assert trail[1]["action"] == "bypass_risk_control"
    assert trail[1]["role"] == "Financial-Engineer"


def test_independent_audit_between_scenes(mrcr):
    mrcr.audit_action("user-A", "general", "testing", True)
    assert len(mrcr.get_audit_trail("user-A", "general")) == 1
    assert len(mrcr.get_audit_trail("user-A", "finance")) == 0
