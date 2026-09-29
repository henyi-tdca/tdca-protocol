# -*- coding: utf-8 -*-
"""
C4 · NSFL 字节码 / IR 输出（Bytecode & Intermediate Representation）
=================================================================
将 NS_Rule 编译为 NS-Bytecode（指令序列），并组装 NSFLIR——
对齐 tdca-toolchain CompileStatus（OK/PARTIAL/FAILED）与
IntermediateRepresentation.to_dict 惯例。

NS-Bytecode 指令集（V0.1）:
  NSFL_DECL  rule_id, ns_type
  NS_OP      operator          # FORBID / LIMIT_MAX / LIMIT_MIN / LIMIT_EQ / RESTRICT_TIER
  NS_TIER    fuse_level, tier  # CCP T6 档位 + Soft/Hard/Atomic 分级
  NS_ACT     action            # 行为标识
  NS_PARAM   parameter         # 操作数（可选）
  NS_ALT     alt_path          # 替代路径（LEGAL 恒 NONE）
  NS_SRC     source_ref        # 源引用

锚定: DCD-NSFL-COMPILER-001（C4 字节码/IR）+ tdca-toolchain CompileStatus
     + TDCA-NSFL-COMPILER-001 A-2（IR 结构稳定，编译时延可测）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .schema import NSFLRule


class CompileStatus(Enum):
    """对齐 tdca-toolchain CompileStatus。"""
    OK = "OK"
    PARTIAL = "PARTIAL"   # 部分字段无法硬化（如语义注释歧义）
    FAILED = "FAILED"


@dataclass(frozen=True)
class NSFLBytecode:
    """单条字节码指令。"""
    opcode: str
    operand: Optional[str] = None

    def to_dict(self) -> dict:
        return {"opcode": self.opcode, "operand": self.operand}


def emit_bytecode(rule: NSFLRule, source_ref: str = "") -> List[NSFLBytecode]:
    """NS_Rule → 字节码指令序列（确定性输出，BV-3 可验证）。"""
    instrs = [
        NSFLBytecode("NSFL_DECL", f"{rule.rule_id}|{rule.ns_type}"),
        NSFLBytecode("NS_OP", rule.operator.value),
        NSFLBytecode("NS_TIER", f"{rule.severity}|{rule.layer}"),
        NSFLBytecode("NS_ACT", rule.source_ref or ""),
    ]
    if rule.parameter is not None:
        instrs.append(NSFLBytecode("NS_PARAM", str(rule.parameter)))
    if rule.alt_path is not None:
        instrs.append(NSFLBytecode("NS_ALT", rule.alt_path))
    if source_ref:
        instrs.append(NSFLBytecode("NS_SRC", source_ref))
    return instrs


@dataclass
class NSFLIR:
    """NSFL 中间表示（模型无关，对齐 toolchain IR 惯例）。"""
    declaration: dict                     # AST 声明
    rule: dict                            # NS_Rule 结构
    bytecode: List[NSFLBytecode]          # NS-Bytecode
    directive: dict                       # C2 熔断级指令
    compiler_version: str = "0.1.0"
    status: CompileStatus = CompileStatus.OK
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "declaration": self.declaration,
            "rule": self.rule,
            "bytecode": [b.to_dict() for b in self.bytecode],
            "directive": self.directive,
            "compiler_version": self.compiler_version,
            "status": self.status.value,
            "warnings": list(self.warnings),
        }
