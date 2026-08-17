# -*- coding: utf-8 -*-
# TDCA 制度水印: TDCA-FC-20260811-002-DUAL-PROTOCOL | NSFL-V0.2 | L2 配置权市场层
"""scene_validator 测试：场景制度校验器。"""
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "engine"))

from scene_validator import SceneValidator  # noqa: E402

FINANCE = PACKAGE / "examples" / "finance"


@pytest.fixture
def validator():
    return SceneValidator(str(PACKAGE / "tdca-public" / "constitution" / "TERMS-v3.0.md"))


def test_finance_constitution_valid(validator):
    assert validator.validate_scene_constitution(str(FINANCE / "scene-constitution.md")) is True


def test_finance_nsfl_valid(validator):
    assert validator.validate_scene_nsfl(str(FINANCE / "scene-nsfl.md")) is True


def test_finance_constraints_covers_six_elements(validator):
    assert validator.validate_scene_constraints(str(FINANCE / "scene-constraints.md")) is True


def test_finance_full_validation_no_errors(validator):
    validator.validate_scene_constitution(str(FINANCE / "scene-constitution.md"))
    validator.validate_scene_nsfl(str(FINANCE / "scene-nsfl.md"))
    validator.validate_scene_constraints(str(FINANCE / "scene-constraints.md"))
    assert validator.errors == []
    assert len(validator.errors) == 0


def test_missing_nsfl_reference_detected(tmp_path, validator):
    """缺少 TDCA-NSFL 引用的场景负空间应报错。"""
    bad_nsfl = tmp_path / "scene-nsfl.md"
    bad_nsfl.write_text("# 场景负空间\nSCENE-NSFL-001: 无公共引用\n", encoding="utf-8")
    assert validator.validate_scene_nsfl(str(bad_nsfl)) is False
    assert any("TDCA-NSFL" in e for e in validator.errors)
