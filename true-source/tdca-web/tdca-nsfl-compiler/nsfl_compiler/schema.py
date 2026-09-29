# -*- coding: utf-8 -*-
"""
C3 · NSFL schema 校验（Schema Validator）
========================================
将语义分析后的声明编译为 NS_Rule 结构，并执行 VALIDATE_RULES
（对齐 D-2 schema V0.1-REV2-FINAL §四 全部制度校验）:

  - rule_id 安全（长度 ≤64，仅字母数字/_-，防 NCA/审计注入）
  - ALLOW/FORBID 的 parameter 仅 str 域标签
  - fuse_type==LEGAL: operator 仅 FORBID / severity 恒 HIGH / alt_path 恒 None
    / enabled 恒 True（防 OTA 软重置）
  - layer 与 ns_type 推导一致 → 拒绝
  - severity > severity_max → 拒绝（L1≤LOW、L2≤MEDIUM 越级拒绝）
  - LIMIT_* parameter 有限正 Decimal（NaN/Inf/负数拒绝）
  - RESTRICT_TIER parameter ∈ FuseLevel

锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL（§四）+ DCD-NSFL-COMPILER-001（C3）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .operators import FuseLevel, NS_Operator
from .parser import NSFLDeclaration
from .semantic import SemanticAnalyzer

# ---- NS_Type 三元归属（对齐 D-2 schema §三）----

NS_TYPE_FUSE_TYPE: Dict[str, str] = {
    "LEGAL": "LEGAL",
    "DATA_CROSS_BORDER": "ETHICAL",   # 场景化声明（非 LEGAL）
    "TRANSACTION_LIMIT": "TECHNICAL",
    "SENSITIVE_CONTENT": "ETHICAL",
    "TECH_CONSTRAINT": "TECHNICAL",
    "ETHICAL": "ETHICAL",
    "EMOTIONAL": "EMOTIONAL",
    "BELIEF": "BELIEF",
}

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

NS_TYPE_SEVERITY_MAX: Dict[str, str] = {
    "LEGAL": "HIGH",
    "DATA_CROSS_BORDER": "MEDIUM",
    "TRANSACTION_LIMIT": "MEDIUM",
    "SENSITIVE_CONTENT": "MEDIUM",
    "TECH_CONSTRAINT": "MEDIUM",
    "ETHICAL": "LOW",
    "EMOTIONAL": "LOW",
    "BELIEF": "LOW",
}

_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
_RULE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_FUSE_LEVELS = {f.value for f in FuseLevel}


@dataclass(frozen=True)
class NSFLRule:
    """负空间规则（对齐 D-2 schema §四 NS_Rule 数据类）。"""
    rule_id: str
    ns_type: str
    operator: NS_Operator
    parameter: Optional[Any] = None     # Decimal（LIMIT_*）/ str（RESTRICT_TIER 档位/域标签）/ None
    unit: Optional[str] = None          # LIMIT_* 必填
    severity: str = "LOW"               # 默认=ns_type.severity_max
    layer: str = "L1"                   # 默认=ns_type.layer
    alt_path: Optional[str] = None
    source_ref: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "ns_type": self.ns_type,
            "fuse_type": NS_TYPE_FUSE_TYPE[self.ns_type],
            "operator": self.operator.value,
            "parameter": str(self.parameter) if self.parameter is not None else None,
            "unit": self.unit,
            "severity": self.severity,
            "layer": self.layer,
            "alt_path": self.alt_path,
            "source_ref": self.source_ref,
            "enabled": self.enabled,
        }


class SchemaValidationError(ValueError):
    """schema 校验失败（携带 code）。"""

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class SchemaValidator:
    """NSFLDeclaration → NSFLRule（含 VALIDATE_RULES 全量校验）。"""

    def __init__(self, semantic: Optional[SemanticAnalyzer] = None):
        self.semantic = semantic or SemanticAnalyzer()

    def validate(self, decl: NSFLDeclaration, rule_id: Optional[str] = None,
                 source_ref: str = "") -> NSFLRule:
        # 1. 语义前置（NS_Type 合法 + 运算符匹配 + layer 一致）
        sem = self.semantic.analyze(decl)
        if not sem.ok:
            first = sem.issues[0]
            raise SchemaValidationError(first.code, first.message)

        # 2. 运算符执行语义 → 熔断级指令
        from .operators import NSFLOperatorSemantics
        try:
            directive = NSFLOperatorSemantics.resolve(decl.ns_type, decl.operator, decl.parameter)
        except ValueError as exc:
            # ⊘/⊙ 参数语义非法 → 归一为 schema 校验错误（档位/前缀/缺参）
            code = "NS-007" if "parameter" in str(exc) else "NS-008"
            raise SchemaValidationError(code, str(exc))

        # 3. 组装 NS_Rule 基础字段
        safe_action = re.sub(r"[^A-Za-z0-9_-]", "-", decl.action)[:40]
        rid = rule_id or f"NSFL-{decl.ns_type}-{safe_action}"
        if not _RULE_ID_RE.match(rid):
            raise SchemaValidationError("NS-006", f"rule_id 非法: {rid!r}（长度 ≤64 且仅字母数字/_-）")

        ns_type = decl.ns_type
        operator = directive.operator
        severity = NS_TYPE_SEVERITY_MAX[ns_type]
        layer = NS_TYPE_LAYER[ns_type]
        fuse_type = NS_TYPE_FUSE_TYPE[ns_type]

        rule = NSFLRule(
            rule_id=rid,
            ns_type=ns_type,
            operator=operator,
            parameter=self._coerce_parameter(operator, directive, ns_type),
            severity=severity,
            layer=layer,
            alt_path=directive.alt_path,
            source_ref=source_ref,
            enabled=True,
        )

        # 4. VALIDATE_RULES（制度底线，fail-closed）
        self._validate_institutional(rule, fuse_type, ns_type)
        return rule

    # ---- 参数化 ----

    def _coerce_parameter(self, operator: NS_Operator, directive, ns_type: str):
        param = directive.parameter
        if operator in (NS_Operator.ALLOW, NS_Operator.FORBID):
            return None
        if operator in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN, NS_Operator.LIMIT_EQ):
            return self._coerce_decimal(param, ns_type)
        if operator == NS_Operator.RESTRICT_TIER:
            if param is None:
                raise SchemaValidationError("NS-007", "RESTRICT_TIER 缺 parameter")
            # 支持 "domain@tier" / "domain:tier" / 纯档位值
            for sep in ("@", ":"):
                if sep in param:
                    param = param.rsplit(sep, 1)[1]
            if param.upper() not in _FUSE_LEVELS:
                raise SchemaValidationError("NS-008", f"RESTRICT_TIER 档位不在 FuseLevel 集: {param!r}")
            return param.upper()
        return param

    def _coerce_decimal(self, value, ns_type: str) -> Decimal:
        try:
            d = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise SchemaValidationError("NS-009", f"LIMIT parameter 非法数值: {value!r}")
        if not d.is_finite():
            raise SchemaValidationError("NS-009", f"LIMIT parameter 必须有限（NaN/Inf 拒绝）: {value!r}")
        if d < 0:
            raise SchemaValidationError("NS-009", f"LIMIT parameter 必须非负: {value!r}")
        return d

    # ---- 制度底线 ----

    def _validate_institutional(self, rule: NSFLRule, fuse_type: str, ns_type: str) -> None:
        # fuse_type==LEGAL → operator 仅 FORBID
        if fuse_type == "LEGAL" and rule.operator != NS_Operator.FORBID:
            raise SchemaValidationError("NS-010", "fuse_type==LEGAL → operator 仅限 FORBID")
        # fuse_type==LEGAL → severity 恒 HIGH（显式降级拒绝）
        if fuse_type == "LEGAL" and rule.severity != "HIGH":
            raise SchemaValidationError("NS-011", "fuse_type==LEGAL → severity 恒 HIGH（完整 IIE 不可降级）")
        # fuse_type==LEGAL → alt_path 恒 None
        if fuse_type == "LEGAL" and rule.alt_path is not None:
            raise SchemaValidationError("NS-012", "fuse_type==LEGAL → alt_path 恒 None（ID86 绝对熔断）")
        # fuse_type==LEGAL → enabled 恒 True
        if fuse_type == "LEGAL" and not rule.enabled:
            raise SchemaValidationError("NS-013", "fuse_type==LEGAL → enabled 恒 True（防 OTA 软重置）")
        # severity 越级拒绝
        if _SEVERITY_RANK[rule.severity] > _SEVERITY_RANK[NS_TYPE_SEVERITY_MAX[ns_type]]:
            raise SchemaValidationError("NS-014", f"severity {rule.severity} 超过 {ns_type} 上限 {NS_TYPE_SEVERITY_MAX[ns_type]}")
        # layer 与 ns_type 推导一致（语义已查，此处双保险）
        if rule.layer != NS_TYPE_LAYER[ns_type]:
            raise SchemaValidationError("NS-003", f"layer {rule.layer!r} 与 ns_type={ns_type} 不一致")
