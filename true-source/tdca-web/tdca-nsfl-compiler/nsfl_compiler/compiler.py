# -*- coding: utf-8 -*-
"""
TDCA-NSFL-COMPILER-001 · NSFL 编译器主入口（M1 编译器核心）
=========================================================
流水线: 自然语言/action_code 声明 → 词法（C1）→ 语法（C1）→ 语义（C1）
      → 运算符执行语义（C2）→ schema 校验（C3）→ 字节码/IR（C4）。

使用:
    from nsfl_compiler import NSFLCompiler
    result = NSFLCompiler().compile("NSFL: ⊗ data.leak(third_party) — 绝对禁止泄露第三方数据")
    result.ir.to_dict()  /  result.ok  /  result.status

纪律:
  - BV-3: 编译器只读（不写任何文件/状态，无 AI 写权限）
  - F-4: 编译产物可验证（IR 确定性），升级权保留人类
  - A-2: 单条声明编译 <100ms（P95<200ms）——发布期一次性，非运行热路径

锚定: DCD-NSFL-COMPILER-001 + TDCA-NSFL-COMPILER-001 立项方案（C1-C4）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from .ir import CompileStatus, NSFLIR, emit_bytecode
from .operators import NSFLOperatorSemantics
from .parser import NSFLDeclaration, NSFLParser
from .schema import NSFLRule, SchemaValidator, SchemaValidationError
from .semantic import SemanticAnalyzer
from .dev_watermark import DEV_NSFL_TAG


@dataclass
class NSFLCompileResult:
    """编译结果（含 IR / 状态 / 诊断）。"""
    ok: bool
    status: CompileStatus
    ir: Optional[NSFLIR] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "status": self.status.value,
            "ir": self.ir.to_dict() if self.ir is not None else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "duration_ms": round(self.duration_ms, 3),
        }


class NSFLCompiler:
    """NSFL 编译器主入口（M1 C1-C4 全流水线，线程安全无状态）。"""

    def __init__(self) -> None:
        self.parser = NSFLParser  # 每次 compile 实例化（无状态保持）
        self.semantic = SemanticAnalyzer()
        self.schema_validator = SchemaValidator(self.semantic)

    # ---- 主入口 ----

    def compile(self, source: str, rule_id: Optional[str] = None,
                source_ref: str = "", dev_mode: bool = False) -> NSFLCompileResult:
        """单条 NSFL 声明编译（A-2 时延目标 <100ms）。

        dev_mode=True → 注入 DEV_NSFL 不可移除水印（开发调试产物标记，
        防误入生产，DCD-NSFL-STATUS-001 维护任务 1）。
        """
        t0 = time.perf_counter()
        try:
            decl = NSFLParser(source).parse()
            rule = self.schema_validator.validate(decl, rule_id=rule_id, source_ref=source_ref)
        except (SchemaValidationError, ValueError) as exc:
            return NSFLCompileResult(
                ok=False,
                status=CompileStatus.FAILED,
                errors=[str(exc)],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        # C2 熔断级指令（规则已通过语义校验，resolve 必成功）
        directive = NSFLOperatorSemantics.resolve(decl.ns_type, decl.operator, decl.parameter)
        bytecode = emit_bytecode(rule, source_ref=source_ref)

        warnings: List[str] = []
        status = CompileStatus.OK
        # 语义注释缺失 → PARTIAL（对齐 toolchain PARTIAL 语义：部分字段无法硬化）
        if not decl.note.strip():
            warnings.append("声明缺少自然语言语义注释（C1 语义硬化不完整）")
            status = CompileStatus.PARTIAL
        # 开发模式水印（不可移除）
        if dev_mode:
            warnings.append(f"开发模式产物（{DEV_NSFL_TAG} 水印已注入，不可入生产）")

        ir = NSFLIR(
            declaration=decl.to_dict(),
            rule=rule.to_dict(),
            bytecode=bytecode,
            directive=directive.to_dict(),
            status=status,
            warnings=warnings,
        )
        if dev_mode:
            from .dev_watermark import inject_dev_watermark
            return NSFLCompileResult(
                ok=True,
                status=status,
                ir=self._with_dev_watermark(ir),
                warnings=warnings,
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
        return NSFLCompileResult(
            ok=True,
            status=status,
            ir=ir,
            warnings=warnings,
            duration_ms=(time.perf_counter() - t0) * 1000,
        )

    # ---- 开发模式水印（DCD-NSFL-STATUS-001 维护任务 1）----

    @staticmethod
    def _with_dev_watermark(ir: NSFLIR) -> NSFLIR:
        """注入 DEV_NSFL 水印（declaration.provenance 字段，不可移除）。"""
        from .dev_watermark import inject_dev_watermark
        d = ir.to_dict()
        watermarked = inject_dev_watermark(d)
        # 重建 IR（仅 declaration 内 provenance 变化）
        return NSFLIR(
            declaration=watermarked["declaration"],
            rule=watermarked["rule"],
            bytecode=ir.bytecode,
            directive=watermarked["directive"],
            compiler_version=ir.compiler_version,
            status=ir.status,
            warnings=ir.warnings,
        )

    # ---- 场景驱动入口（裁决方案 B 主导——沙盒编译反应釜）----

    def compile_for_scene(self, scene: dict, legal_refs: Optional[list] = None,
                          rule_id: Optional[str] = None) -> NSFLCompileResult:
        """场景 + 素材 → NSFL 编译（对齐 SEA 沙盒出盒流程 2.4）。

        场景驱动（方案 B）: 业务场景声明 + KG-LEGAL 素材检索法条引用 →
        NSFL 声明 → 编译。素材（KG-LEGAL）是输入原料，非合规替代路径（ID90）。

        scene: {
          "action": "unlicensed_reproduce",     # 行为标识
          "ns_type": "LEGAL",                   # 声明负空间类型（素材推导）
          "operator": "⊗",                      # ⊗ 禁止 / ⊙ 场景化
          "parameter": None | "domain:tier",    # ⊙ 场景参数
          "note": "未经许可复制作品（著作权法第 10 条）",  # 语义注释
          "domain": "copyright",                # 行为域（素材归组）
        }
        legal_refs: 素材引用列表（如 ["L-CN-CR-001"]）——记入 source_ref 审计。
        L-3 扩展（TDCA-TASK-TAXLAW-001）: 元素支持法规内容 dict
        {law_id, point, ...}——要点注入审计；str 行为完全兼容（不破坏既有）。
        """
        action = self._action_token(str(scene.get("action", "act_unknown")))
        ns_type = str(scene.get("ns_type", "ETHICAL"))
        op = str(scene.get("operator", "⊗"))
        parameter = scene.get("parameter")
        note = str(scene.get("note", ""))
        domain = str(scene.get("domain", "scene"))

        # L-3: legal_refs 内容化（dict 法规内容 → 要点注入；str 保持原样）
        ref_parts: List[str] = []
        for r in (legal_refs or []):
            if isinstance(r, dict):
                ref_parts.append(f"{r.get('law_id')}:{r.get('point', '')}")
            else:
                ref_parts.append(str(r))
        refs = "|".join(ref_parts) if ref_parts else "no-legal-ref"

        param_clause = f" | {parameter}" if parameter else ""
        source = f"NSFL: {op} {ns_type}.{domain}.{action}{param_clause} — {note}"
        return self.compile(source, rule_id=rule_id, source_ref=f"scene+legal:{refs}")

    # ---- 兼容入口 ----

    def compile_action_code(self, layer: str, action: str, certainty: str) -> dict:
        """存量兼容（对齐 tdca-ns-ops NSFLApi.compile_action_code 契约，A-7）。

        layer: subject/scene/institutional 或 NS_Type（小写）
        action: 行为自然语言描述
        certainty: high/medium/low
        """
        ns_type_map = {
            "subject": "ETHICAL",
            "scene": "SENSITIVE_CONTENT",
            "institutional": "LEGAL",
        }
        ns_type = ns_type_map.get(layer.lower(), "ETHICAL")
        src = f"NSFL: ⊗ {action[:24]} (certainty={certainty})"
        note = action
        # 用 NSFL 语法包裹（⊗ 绝对禁止 + 语义注释）
        safe_action = self._action_token(action)
        source = f"NSFL: ⊗ {ns_type}.{safe_action} — {note}"
        result = self.compile(source, source_ref=layer)
        return {
            "action_code": f"NSFL: ⊗ {layer}.{action[:24]} (certainty={certainty})",
            "compile_status": result.status.value,
            "warnings": result.warnings,
            "sat_expression": None,
            "formal_form": result.ir.declaration["note"] if result.ir else None,
            "source": action,
            "blocked_for_ambiguity": result.status == CompileStatus.PARTIAL,
            "message": ("模糊声明不可直接编译" if result.status == CompileStatus.PARTIAL else ""),
        }

    @staticmethod
    def _action_token(action: str) -> str:
        """自然语言行为 → 安全标识符 token（仅 ASCII 字母数字，非 ASCII → _，限长）。"""
        out = []
        for ch in action:
            out.append(ch if (ch.isascii() and (ch.isalnum() or ch in "._-")) else "_")
        tok = "".join(out)[:48]
        if not tok or tok[0].isdigit():
            tok = "act_" + tok
        return tok or "act_unknown"
