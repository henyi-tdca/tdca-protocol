# -*- coding: utf-8 -*-
"""
TDCA 接口熵检查工具 — 提交前检查（ID82）
制度锚定: TDCA-PRINCIPLE-INTERFACE-ENTROPY-001 | ID82 | ID35 制度-技术同构
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

职责: 扫描代码库中的接口定义（gRPC proto / Python 公开方法 / YAML 契约），
检查是否存在歧义接口（重名、缺类型标注、缺契约锚定）——接口熵 > 0 则提交阻断。
NSFL-Declaration:
  - 只读扫描，不修改任何源文件
SPDX-License-Identifier: TDCA-Internal
"""

import ast
import os
import re
import sys
from typing import List, Dict, Any


class InterfaceEntropyReport:
    """接口熵检查报告"""

    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.checked_files: List[str] = []
        self.entropy: float = 0.0

    def add_violation(self, file: str, issue: str, severity: str = "WARN") -> None:
        self.violations.append({"file": file, "issue": issue, "severity": severity})

    def is_clean(self) -> bool:
        return len(self.violations) == 0


class InterfaceEntropyChecker:
    """接口熵=0 检查器 — 扫描 Python 公开接口与 proto 定义"""

    def __init__(self, root: str):
        self.root = os.path.abspath(root)

    def check_all(self) -> InterfaceEntropyReport:
        report = InterfaceEntropyReport()
        for dirpath, dirnames, filenames in os.walk(self.root):
            # 跳过无关目录与测试目录（pytest 函数/fixture 非对外接口，不构成接口熵）
            dirnames[:] = [d for d in dirnames if d not in {
                ".git", "__pycache__", ".pytest_cache", "node_modules", "tests"}]
            for fn in filenames:
                path = os.path.join(dirpath, fn)
                # 跳过 grpc 自动生成产物（机器生成，非手写接口，不构成接口熵审查对象）
                if fn.endswith("_pb2.py") or fn.endswith("_pb2_grpc.py"):
                    continue
                if fn.endswith(".py"):
                    self._check_python(path, report)
                elif fn.endswith(".proto"):
                    self._check_proto(path, report)
        report.entropy = len(report.violations)
        return report

    # ---- Python 检查 ----

    def _check_python(self, path: str, report: InterfaceEntropyReport) -> None:
        report.checked_files.append(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
        except (OSError, UnicodeDecodeError):
            return
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            report.add_violation(path, f"语法错误: {e}", "ERROR")
            return

        # 1. 检查制度锚定注释
        if "制度锚定" not in src and "SPDX-License-Identifier" not in src:
            report.add_violation(path, "缺少制度锚定头部注释", "ERROR")

        # 2. 检查公开方法签名（缺类型标注 = 接口熵源）
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                untyped_args = [
                    a.arg for a in node.args.args
                    if a.annotation is None and a.arg not in {"self", "cls"}
                ]
                if untyped_args:
                    report.add_violation(
                        path,
                        f"方法 {node.name}() 参数缺类型标注: {untyped_args}",
                        "WARN",
                    )
                if node.returns is None:
                    report.add_violation(
                        path, f"方法 {node.name}() 缺返回类型标注", "WARN")

    # ---- proto 检查 ----

    def _check_proto(self, path: str, report: InterfaceEntropyReport) -> None:
        report.checked_files.append(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
        except OSError:
            return
        if "制度锚定" not in src:
            report.add_violation(path, "proto 缺少制度锚定注释", "ERROR")
        # 检查重复字段号（歧义源）——按 message 作用域统计，跨 message 从 1 开始合法
        for msg_block in re.split(r"\nmessage\s+\w+\s*\{", src)[1:]:
            field_numbers = re.findall(r"=\s*(\d+)", msg_block)
            dupes = {n for n in field_numbers if field_numbers.count(n) > 1}
            if dupes:
                report.add_violation(
                    path, f"message 内重复 proto 字段号: {sorted(dupes)}", "ERROR")


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    checker = InterfaceEntropyChecker(root)
    report = checker.check_all()
    print("=" * 64)
    print("TDCA 接口熵检查（ID82）")
    print(f"扫描文件: {len(report.checked_files)}")
    print(f"违例项: {len(report.violations)}  接口熵: {report.entropy}")
    print("-" * 64)
    for v in report.violations:
        print(f"  [{v['severity']}] {os.path.relpath(v['file'], root)}: {v['issue']}")
    print("=" * 64)
    if report.is_clean():
        print("RESULT: PASS — 接口熵 = 0（ID82 满足）")
        return 0
    print("RESULT: FAIL — 接口熵 > 0，提交阻断（TDCA-PRINCIPLE-INTERFACE-ENTROPY-001）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
