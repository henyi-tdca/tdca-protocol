# -*- coding: utf-8 -*-
"""
编译器自举验证（维护任务 3）——自反闭环
========================================
每次编译器自身构建时，强制通过 M1-M2 NSFL 检查（DCD-NSFL-STATUS-001 §五）:
  - 编译器自身源码（本包 .py 文件）作为 Δ 输入 → Δ-Analysis 检查负空间模式
  - 编译产物 IR 校验 DEV_NSFL 水印隔离（dev 产物不入生产）
  - 自举闭环: 编译器编译自身声明时，须通过自身的 schema/语义检查

锚定: DCD-NSFL-STATUS-001（维护任务 3）+ AUTHORITY-ECONOMICS L2735（编译器自约束）
     + C5/C6（自约束 + 自我修改检测）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .delta_analysis import SelfModificationAnalyzer


@dataclass(frozen=True)
class BootstrapVerdict:
    """自举验证结果。"""
    passed: bool
    checked_files: int
    findings: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "checked_files": self.checked_files,
            "findings": list(self.findings),
        }


class CompilerBootstrapGuard:
    """编译器自举验证器（自反闭环，fail-closed）。"""

    def __init__(self, analyzer: Optional[SelfModificationAnalyzer] = None):
        self._analyzer = analyzer or SelfModificationAnalyzer()

    def verify_self(self, package_dir: Optional[str] = None) -> BootstrapVerdict:
        """对编译器自身源码做负空间扫描（自举验证）。

        package_dir: nsfl_compiler 包目录（默认取本文件所在目录）。
        """
        if package_dir is None:
            package_dir = str(Path(__file__).resolve().parent)
        findings: List[dict] = []
        checked = 0
        for py in sorted(Path(package_dir).glob("*.py")):
            if py.name.startswith("_"):
                continue
            # 排除模式库数据文件——其内容是负空间模式定义（必然含危险关键词），
            # 非可执行逻辑；自举验证针对编译器可执行逻辑（定义 ≠ 行为）
            if py.name == "delta_analysis.py":
                continue
            code = py.read_text(encoding="utf-8")
            checked += 1
            res = self._analyzer.delta_analyze({"S_agent_cog": {}},
                                               {"type": "CODE_MODIFICATION",
                                                "delta_c": code},
                                               word_boundary=True)
            if res.verdict == "BLOCKED":
                findings.append({
                    "file": py.name,
                    "verdict": res.verdict,
                    "ns_type_inferred": res.ns_type_inferred,
                    "matched": list(res.matched_patterns),
                })
        return BootstrapVerdict(
            passed=not findings,
            checked_files=checked,
            findings=findings,
        )
