# -*- coding: utf-8 -*-
"""
C1 · NSFL 语义分析器（Semantic Analyzer）
=========================================
对 AST（NSFLDeclaration）做语义检查:
  1. NS_Type 合法性（锚定 D-2 schema §三 枚举，未知值 fail-closed）
  2. 运算符-类型匹配（LEGAL 仅 ⊗ FORBID；场景/主体类型的运算符约束）
  3. layer 显式标注与 ns_type 推导一致（否则拒绝，schema §四）
  4. parameter 语义预检（数值域/档位域标签——终检在 schema 校验）

锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL（§三/§四）
     + DCD-NSFL-COMPILER-001（C1 语义分析）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .parser import NSFLDeclaration

# ---------------------------------------------------------------------------
# NS_Type 注册表（对齐 D-2 schema §三——fuse_type/layer/severity_max 三元归属）
# ---------------------------------------------------------------------------

NS_TYPE_LAYER: Dict[str, str] = {
    "LEGAL": "L0",
    "DATA_CROSS_BORDER": "L2",
    "TRANSACTION_LIMIT": "L2",
    "SENSITIVE_CONTENT": "L2",
    "TECH_CONSTRAINT": "L2",
    "ETHICAL": "L1",
    "EMOTIONAL": "L1",
    "BELIEF": "L1",
}

# 各 NS_Type 允许的运算符（语义白名单）：
#   ⊗ FORBID: 所有类型（LEGAL 强制 ⊗）
#   ⊘ LIMIT:  数值/档位约束——场景型 L2（TRANSACTION_LIMIT/TECH_CONSTRAINT）与主体型（自律边界）
#   ⊙ SCENE:  场景化约束——场景型 L2
_OPERATOR_ALLOW: Dict[str, Set[str]] = {
    "LEGAL": {"⊗"},
    "DATA_CROSS_BORDER": {"⊗", "⊙"},
    "TRANSACTION_LIMIT": {"⊗", "⊘", "⊙"},
    "SENSITIVE_CONTENT": {"⊗", "⊙"},
    "TECH_CONSTRAINT": {"⊗", "⊘"},
    "ETHICAL": {"⊗", "⊘"},
    "EMOTIONAL": {"⊗"},
    "BELIEF": {"⊗"},
}


@dataclass
class SemanticIssue:
    code: str        # 如 NS-001 / NS-002
    message: str
    line: int = 0
    col: int = 0

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "line": self.line, "col": self.col}


@dataclass
class SemanticResult:
    ok: bool
    issues: List[SemanticIssue] = field(default_factory=list)
    inferred_layer: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "inferred_layer": self.inferred_layer,
            "issues": [i.to_dict() for i in self.issues],
        }


class SemanticAnalyzer:
    """AST → 语义检查结果（不修改 AST）。"""

    def __init__(self) -> None:
        self._known_types: Set[str] = set(NS_TYPE_LAYER.keys())

    def analyze(self, decl: NSFLDeclaration) -> SemanticResult:
        issues: List[SemanticIssue] = []

        # 1. NS_Type 合法性（fail-closed：未知枚举值拒绝）
        if decl.ns_type not in self._known_types:
            issues.append(SemanticIssue(
                "NS-001",
                f"未知 NS_Type: {decl.ns_type!r}（注册表 V1.1 仅含 {sorted(self._known_types)}）",
                decl.line, decl.col,
            ))
            return SemanticResult(ok=False, issues=issues)

        # 2. 运算符-类型匹配
        allowed = _OPERATOR_ALLOW[decl.ns_type]
        if decl.operator not in allowed:
            issues.append(SemanticIssue(
                "NS-002",
                f"NS_Type={decl.ns_type} 不允许运算符 {decl.operator}（允许: {sorted(allowed)}）",
                decl.line, decl.col,
            ))

        # 3. layer 显式标注一致性
        inferred = NS_TYPE_LAYER[decl.ns_type]
        if decl.layer is not None and decl.layer != inferred:
            issues.append(SemanticIssue(
                "NS-003",
                f"layer 标注 {decl.layer!r} 与 NS_Type={decl.ns_type} 推导层 {inferred!r} 不一致",
                decl.line, decl.col,
            ))

        # 4. parameter 语义预检
        if decl.operator == "⊗" and decl.parameter is not None:
            issues.append(SemanticIssue(
                "NS-004",
                "⊗ FORBID 语义不接受 '| parameter' 操作数（绝对禁止无参数域）",
                decl.line, decl.col,
            ))
        if decl.operator in ("⊘", "⊙") and decl.parameter is None:
            issues.append(SemanticIssue(
                "NS-005",
                f"{decl.operator} 语义须提供 '| parameter' 操作数（LIMIT 数值/档位、SCENE 域标签）",
                decl.line, decl.col,
            ))

        return SemanticResult(ok=not issues, issues=issues, inferred_layer=inferred)
