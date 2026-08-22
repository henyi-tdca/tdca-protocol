# FC-ID: TDCA-TASK-CTS-L1-001 | 用例执行基座
"""被测目标接口约定（duck-typing）与用例结果结构。

target 须提供以下能力（缺能力 = 对应用例 FAIL，G-1 fail-closed）：
  agent_id: str                      智能体标识
  registry_version: str              对齐的术语注册表版本（如 "V2.1"）
  submit_ns_declaration(decl) -> str         C-1：提交 NSFL 负空间声明，返回声明哈希；语法错误必须 raise
  report_violation(event) -> dict            C-1：输出三档分级熔断事件
  deliver(task) -> dict                      C-2：产出 NCA 存证（11 字段或 NCA-Lite 8 字段）
  evidence_chain() -> list[dict]             C-2：返回存证链（含 payload_ref 链式引用）
  meter(call_type, amount) -> dict           C-3：计税（CALL-RULES 三档 + microtax M-1 契约）
  generate_offer(template_id, parties) -> dict  C-4：CCP 模板生成邀约
  parse_contract(instance) -> dict           C-4：解析他方契约实例
  interface_doc() -> str                     C-5：对外接口文档文本（注册表概念须带 T-编号）
  adjudicate(request) -> dict                C-6：正和判定治理请求处理
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

# NCA 工程型 11 字段（pack/templates/nca-template.yaml 权威）
NCA_11_FIELDS = ("NCA-ID", "Function-Call-ID", "Operation-Type", "Operator",
                 "Timestamp", "Scope", "Pre-State", "Post-State",
                 "Config-Right-Token", "Audit-Trail", "Human-Signature")
NCA_LITE_8_FIELDS = ("nca_lite", "id", "action", "operator", "timestamp",
                     "scope", "payload_ref", "provenance")

# CALL-RULES V1.2 三档税率（D-011 模拟态口径，实例参数非轮廓常量）
TAX_RATES = {"日抛": 0.02, "化合": 0.075, "服务": 0.0075}

THETA_ANCHOR_DEV = 0.20  # θ_ANCHOR_DEV 占位参数（T-068 定标项，模拟态）


@dataclass
class CaseResult:
    case_id: str
    requirement: str
    passed: bool
    detail: str = ""
    elapsed_ms: float = 0.0
    provenance: str = "simulated"   # ID92：套件全部合成数据


def run_case(case_id: str, requirement: str, fn) -> CaseResult:
    """单用例执行：fn 返回 (passed, detail)；异常 = FAIL（fail-closed，不静默）。"""
    t0 = time.perf_counter()
    try:
        ok, detail = fn()
    except Exception as e:  # 目标崩溃 = 用例失败（判别力的一部分）
        ok, detail = False, f"目标异常: {type(e).__name__}: {e}"
    ms = (time.perf_counter() - t0) * 1000
    return CaseResult(case_id=case_id, requirement=requirement,
                      passed=bool(ok), detail=str(detail), elapsed_ms=round(ms, 2))
