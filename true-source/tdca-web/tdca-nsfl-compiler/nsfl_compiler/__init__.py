# -*- coding: utf-8 -*-
"""
TDCA-NSFL-COMPILER-001 · NSFL 编译器 M1（C1-C4）
=================================================
编译器核心（词法/语法/语义 + ⊗⊘⊙ 运算符执行语义 + schema 校验 + 字节码/IR）。

锚定:
  - DCD-NSFL-COMPILER-001（已签批立项，M1 移交新会话框）
  - TDCA-NSFL-COMPILER-001 立项方案（C1-C4 规格 + A-1~7 验收）
  - D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL（NS_Type/NS_Rule 结构对齐）
  - tdca-toolchain/tdca_function_compiler.py（CompileStatus OK/PARTIAL/FAILED 对齐）
  - tdca-toolchain/tdca_constraint_interpreter.py（三态语义）
  - tdca-fos/tdca_nsfl/fuse_engine.py（FuseType 5 类，LEGAL alt=∅）
  - TDCA-TERMINOLOGY-REGISTRY V1.1（G-1 基线，无「V2.1」声称）

纪律（M1 红线）:
  - BV-3: 编译器只读规则 + 输出验证（无 AI 写权限）
  - F-4: AI 无权自动修改 NSFL / 升级权保留人类
  - ID 纪律: 按 TDCA-ID-VERIFY-001（ID93 不引用 / 四符号 / ID89 标注自创）
  - 术语: 仅注册表 V1.1

SPDX-License-Identifier: TDCA-Internal
"""
from .compiler import NSFLCompiler, NSFLCompileResult
from .lexer import NSFLToken, NSFLTokenType, NSFLLexer, NSFLSyntaxError
from .parser import NSFLDeclaration, NSFLParser
from .semantic import SemanticAnalyzer
from .operators import NSFLOperatorSemantics
from .schema import NSFLRule, SchemaValidator, SchemaValidationError
from .ir import CompileStatus, NSFLBytecode, NSFLIR
from .sscp import SSCPCompiler, EvolutionLockContract, SSCPCompileResult
from .delta_analysis import SelfModificationAnalyzer, DeltaAnalysisResult
from .dev_watermark import DevModeWatermark, inject_dev_watermark, check_dev_watermark, assert_production_clean
from .dev_advisor import DevRiskAdvisor, DevRiskHint
from .bootstrap_guard import CompilerBootstrapGuard, BootstrapVerdict

__all__ = [
    "NSFLCompiler",
    "NSFLCompileResult",
    "NSFLToken",
    "NSFLTokenType",
    "NSFLLexer",
    "NSFLSyntaxError",
    "NSFLDeclaration",
    "NSFLParser",
    "SemanticAnalyzer",
    "NSFLOperatorSemantics",
    "NSFLRule",
    "SchemaValidator",
    "SchemaValidationError",
    "CompileStatus",
    "NSFLBytecode",
    "NSFLIR",
    "SSCPCompiler",
    "EvolutionLockContract",
    "SSCPCompileResult",
    "SelfModificationAnalyzer",
    "DeltaAnalysisResult",
    "DevModeWatermark",
    "inject_dev_watermark",
    "check_dev_watermark",
    "assert_production_clean",
    "DevRiskAdvisor",
    "DevRiskHint",
    "CompilerBootstrapGuard",
    "BootstrapVerdict",
]

__version__ = "0.1.0"
