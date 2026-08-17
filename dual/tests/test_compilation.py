# -*- coding: utf-8 -*-
# TDCA 制度水印: TDCA-FC-20260811-002-DUAL-PROTOCOL | NSFL-V0.2 | L2 配置权市场层
"""dual_protocol_compiler 测试：化合编译器。"""
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "engine"))

from dual_protocol_compiler import DualProtocolCompiler  # noqa: E402

TDCA = str(PACKAGE / "tdca-public")
FINANCE = str(PACKAGE / "examples" / "finance")


@pytest.fixture
def compiler():
    return DualProtocolCompiler(
        tdca_path=TDCA, scene_path=FINANCE, scene_name="finance", mode="strict"
    )


def test_load_tdca(compiler):
    tdca = compiler.load_tdca()
    assert "TDCA-CONST-v3.1.2" in tdca
    assert "NSFL-v0.2" in tdca


def test_load_scene(compiler):
    scene = compiler.load_scene()
    assert "scene-constitution" in scene
    assert "scene-constraints" in scene
    assert "scene-nsfl" in scene


def test_isomorphism_passes(compiler):
    assert compiler.validate_isomorphism() is True
    assert compiler.validation_errors == []


def test_minimal_compound_passes(compiler):
    passed, message = compiler.check_minimal_compound()
    assert passed is True, message
    assert "通过" in message


def test_compile_and_export(tmp_path, compiler):
    assert compiler.validate_isomorphism() is True
    passed, _ = compiler.check_minimal_compound()
    assert passed is True
    out = compiler.export(str(tmp_path))
    out_dir = Path(out)
    assert (out_dir / "dual-constitution.md").exists()
    assert (out_dir / "dual-constraints.md").exists()
    assert (out_dir / "dual-nsfl.md").exists()
    assert (out_dir / "dual-six-elements.md").exists()
    assert (out_dir / "dual-review.md").exists()
    assert (out_dir / "dual-nca.json").exists()


def test_strict_mode_conflict_detection(tmp_path, compiler):
    """strict 模式应检测场景宪法中的冲突条款。"""
    bad_scene = tmp_path / "bad-scene"
    bad_scene.mkdir()
    (bad_scene / "scene-constitution.md").write_text(
        "# 冲突场景宪法\n本场景宪法不遵守 TDCA 宪法第 4 条（C01 可观测性原则）。\n", encoding="utf-8"
    )
    (bad_scene / "scene-constraints.md").write_text("# 约束\n", encoding="utf-8")
    (bad_scene / "scene-nsfl.md").write_text("# 负空间\nTDCA-NSFL 引用\nSCENE-NSFL-001 CRITICAL BLOCK\n", encoding="utf-8")
    c = DualProtocolCompiler(
        tdca_path=TDCA, scene_path=str(bad_scene), scene_name="bad", mode="strict"
    )
    assert c.validate_isomorphism() is False
    assert any("冲突" in e for e in c.validation_errors)
