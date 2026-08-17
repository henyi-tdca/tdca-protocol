# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-20260811-002-DUAL-PROTOCOL
# 目标函数:     场景制度实时校验器（同构/负空间覆盖/六要素完整）
# 约束矩阵:     ID35 同构 + NSFL-V0.2 + 六要素完整性 + 术语映射
# 先验分布:     TDCA-DUAL-PROTOCOL-001-V1.0 设计稿
# 配置权边界:    L2 配置权市场层；只读校验不修改场景制度
# 预期分配:     校验报告（errors/warnings）
# 审计轨迹:      TDCA-NCA-20260811-006-DUAL-PROTOCOL
# 开发者:       [人类签批人]
# 模拟态标注（ID92）: 本引擎为工具实现，不构成真实配置权执行路径
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
"""TDCA 场景制度校验器 V1.0.0

功能: 在用户编写场景制度时，实时校验合规性（同构声明 / 负空间覆盖 / 六要素完整）。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class SceneValidator:
    """场景制度实时校验器。"""

    def __init__(self, tdca_terms_path: str):
        self.tdca_terms = self._load_terms(tdca_terms_path)
        self.errors = []
        self.warnings = []

    @staticmethod
    def _load_terms(tdca_terms_path: str) -> str:
        try:
            with open(tdca_terms_path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def validate_scene_constitution(self, scene_const_path: str) -> bool:
        """校验场景宪法：必须包含服从声明。"""
        with open(scene_const_path, "r", encoding="utf-8") as f:
            content = f.read()
        required_statements = ["服从 TDCA 宪法", "TDCA-CONST", "不得与任何条款冲突"]
        for stmt in required_statements:
            if stmt not in content:
                self.errors.append(f"场景宪法缺少必要声明: {stmt}")
        return len(self.errors) == 0

    def validate_scene_nsfl(self, scene_nsfl_path: str) -> bool:
        """校验场景负空间：必须引用 TDCA-NSFL。"""
        with open(scene_nsfl_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "TDCA-NSFL" not in content:
            self.errors.append("场景负空间未引用 TDCA-NSFL（必须完整包含公共负空间）")
        if "SCENE-NSFL" not in content:
            self.warnings.append("场景负空间缺少场景特定规则（若确无场景规则，最小化合判定将不通过）")
        return len(self.errors) == 0

    def validate_scene_constraints(self, scene_constraints_path: str) -> bool:
        """校验场景约束矩阵：必须覆盖 TDCA 六要素。"""
        with open(scene_constraints_path, "r", encoding="utf-8") as f:
            content = f.read()
        required_elements = [
            "objective_function", "constraint_matrix", "prior_distribution",
            "config_boundary", "expected_allocation", "audit_trail",
        ]
        # 优先尝试 YAML 解析（纯 YAML 文件），失败则文本扫描（markdown 模板）
        text = content
        if yaml is not None:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    text = str(data.get("scene_constraints", data))
            except Exception:
                text = content
        for elem in required_elements:
            if elem not in text:
                self.errors.append(f"场景约束矩阵缺失六要素: {elem}")
        return len(self.errors) == 0

    def print_report(self) -> None:
        """打印校验报告。"""
        print("=" * 60)
        print("场景制度校验报告")
        print("=" * 60)
        if self.errors:
            print("❌ 错误:")
            for error in self.errors:
                print(f"  - {error}")
        if self.warnings:
            print("⚠️ 警告:")
            for warning in self.warnings:
                print(f"  - {warning}")
        if not self.errors and not self.warnings:
            print("✅ 场景制度校验通过")
        print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python scene_validator.py <tdca_terms_path> <scene_dir>")
        sys.exit(1)
    validator = SceneValidator(sys.argv[1])
    scene_dir = Path(sys.argv[2])
    validator.validate_scene_constitution(scene_dir / "scene-constitution.md")
    validator.validate_scene_nsfl(scene_dir / "scene-nsfl.md")
    validator.validate_scene_constraints(scene_dir / "scene-constraints.md")
    validator.print_report()
    sys.exit(1 if validator.errors else 0)
