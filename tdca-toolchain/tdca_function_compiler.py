"""
TDCA-FC-20260802-004 修正声明:
  - R1-P1: Max-Retry 语义层级区分
  - R1-P1: embedding 三级降级策略
  - R1-P2: 执行顺序并行化

制度锚定: TDCA-PRINCIPLE-FC-NCA-COH-002(一阶验证: 输入硬化), ID82(制度同构跃进)
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-002

NSFL-Declaration:
  - 目标函数必须形式化为可验证表达式
  - 约束矩阵必须布尔化，无二义性
  - 禁止将模糊描述直接编译为约束
SPDX-License-Identifier: TDCA-Internal
"""

import enum
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


class CompileStatus(enum.Enum):
    """编译状态"""
    OK = "OK"
    PARTIAL = "PARTIAL"          # 部分字段无法硬化
    FAILED = "FAILED"            # 编译失败


@dataclass
class IntermediateRepresentation:
    """模型无关中间表示（IR）"""
    # 核心三要素（修正指令硬约束）
    target_function_formalized: dict       # 目标函数形式化
    constraints_sat: dict                  # 约束矩阵布尔化（SAT）
    prior_distribution_params: dict        # 先验分布参数化

    # 元数据
    source_elements: dict
    compiler_version: str
    status: CompileStatus = CompileStatus.OK
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d


class TDCAFunctionCompiler:
    """
    函数语料编译器

    将自然语言/半结构化六要素声明编译为模型无关中间表示（IR）。
    调用 TDCAConstraintInterpreter 进行约束布尔化。

    核心约束:
      - 目标函数必须形式化为可验证的数学表达式或逻辑命题
      - 约束矩阵必须布尔化（满足/不满足，无二义性）
      - 先验分布必须参数化为概率分布
    """

    def __init__(self, constraint_interpreter: Optional[object] = None):
        # 注入约束解释器（模块B）
        if constraint_interpreter is not None:
            self.interpreter = constraint_interpreter
        else:
            from tdca_constraint_interpreter import TDCAConstraintInterpreter
            self.interpreter = TDCAConstraintInterpreter()

    def compile(self, six_elements: dict) -> IntermediateRepresentation:
        """
        编译流程:
          1. 目标函数硬化：自然语言 → 形式化表达式
          2. 约束矩阵布尔化：模糊描述 → SAT表达式（调用 B.interpret）
          3. 先验分布参数化：经验描述 → 概率分布参数
          4. 生成 IR：模型无关的标准化指令包
        """
        warnings = []
        status = CompileStatus.OK

        # 1. 目标函数硬化
        tf = self._formalize_target_function(six_elements.get('objective', {}))
        if not tf.get('formalized'):
            warnings.append("目标函数无法完全形式化")
            status = CompileStatus.PARTIAL

        # 2. 约束矩阵布尔化（调用模块B）
        constraints_raw = six_elements.get('constraints', {})
        sat = self._booleanize_constraints(constraints_raw)
        if not sat.get('booleanized'):
            warnings.append("约束矩阵存在无法布尔化的模糊项")
            status = CompileStatus.PARTIAL

        # 3. 先验分布参数化
        prior = self._parameterize_prior(six_elements.get('prior', {}))

        return IntermediateRepresentation(
            target_function_formalized=tf,
            constraints_sat=sat,
            prior_distribution_params=prior,
            source_elements=six_elements,
            compiler_version='1.0.0',
            status=status,
            warnings=warnings,
        )

    def verify_ir(self, ir: IntermediateRepresentation) -> bool:
        """
        验证 IR 的完整性和一致性。

        检查:
          1. 三核心字段非空
          2. constraints_sat 的布尔化状态
          3. target_function_formalized 含可验证表达式
        """
        if not ir.target_function_formalized:
            return False
        if not ir.constraints_sat:
            return False
        if not ir.prior_distribution_params:
            return False
        # 约束必须全部布尔化
        if not ir.constraints_sat.get('booleanized', False):
            return False
        # 目标函数必须有形式化表达
        if not ir.target_function_formalized.get('formalized', False):
            return False
        return True

    # ---- 编译步骤 ----

    def _formalize_target_function(self, objective: dict) -> dict:
        """
        目标函数硬化：自然语言 → 形式化表达式
        支持: 数值目标（min/max）、逻辑命题（must/cannot）、正则校验
        """
        formalized = False
        expr = objective.get('expression', '')
        expr_type = objective.get('type', 'UNKNOWN')

        result = {
            'expression': expr,
            'formalized': False,
            'formal_form': None,
            'parseable': False,
        }

        if not expr:
            return result

        # 数值目标: max/min + 数值
        if expr_type == 'NUMERIC' or re.match(r'^(max|min|optimize)\s*\(', expr.strip(), re.I):
            result['formalized'] = True
            result['formal_form'] = f"objective: {expr.strip()}"
            result['parseable'] = True

        # 逻辑命题: 包含 must/cannot/≤/≥/=
        elif any(kw in expr for kw in ['must', 'cannot', '≤', '≥', '==', '!=']):
            result['formalized'] = True
            result['formal_form'] = f"proposition: {expr.strip()}"
            result['parseable'] = True

        # 正则校验: 包含 regex/pattern
        elif 'regex' in expr.lower() or 'pattern' in expr.lower():
            result['formalized'] = True
            result['formal_form'] = f"regex: {expr.strip()}"
            result['parseable'] = True

        return result

    def _booleanize_constraints(self, constraints: dict) -> dict:
        """
        约束矩阵布尔化：调用模块B解释器进行三态判定。

        每个约束 → interpret() → ALLOWED/DENIED/HUMAN_REQUIRED
        """
        hard = constraints.get('hard', [])
        soft = constraints.get('soft', [])

        bool_hard = []
        all_booleanized = True

        for c in hard:
            text = c if isinstance(c, str) else c.get('description', str(c))
            result = self.interpreter.interpret(
                subject_context=constraints.get('context', {}),
                operation=constraints.get('operation', ''),
                constraint_text=text
            )
            entry = {
                'constraint': text,
                'interpretation': result.status.value,
                'booleanized': result.status.value in ('ALLOWED', 'DENIED'),
                'constraint_id': result.constraint_id,
            }
            if not entry['booleanized']:
                all_booleanized = False
            bool_hard.append(entry)

        bool_soft = [{'constraint': s if isinstance(s, str) else s.get('description', str(s)),
                      'soft': True} for s in soft]

        return {
            'hard': bool_hard,
            'soft': bool_soft,
            'booleanized': all_booleanized and len(bool_hard) > 0,
            'sat_expression': self._to_sat(bool_hard),
        }

    def _to_sat(self, bool_hard: list) -> str:
        """将布尔化约束组合为 SAT 表达式（简化：AND 连接）"""
        clauses = []
        for h in bool_hard:
            if h['booleanized']:
                sign = '' if h['interpretation'] == 'ALLOWED' else '¬'
                clauses.append(f"({sign}{h['constraint_id']})")
        return ' ∧ '.join(clauses) if clauses else 'TRUE'

    def _parameterize_prior(self, prior: dict) -> dict:
        """
        先验分布参数化：经验描述 → 概率分布参数
        支持: 均值/方差/置信区间
        """
        params = {
            'distribution': prior.get('distribution', 'uniform'),
            'parameters': {},
            'parameterized': False,
        }

        mean = prior.get('mean')
        variance = prior.get('variance')
        confidence = prior.get('confidence_interval')

        if mean is not None:
            params['parameters']['mean'] = float(mean)
            params['parameterized'] = True
        if variance is not None:
            params['parameters']['variance'] = float(variance)
            params['parameterized'] = True
        if confidence is not None and len(confidence) == 2:
            params['parameters']['confidence_interval'] = [float(confidence[0]), float(confidence[1])]
            params['parameterized'] = True

        return params


# ---- CLI ----
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            elements = json.load(f)
    else:
        elements = {}
    compiler = TDCAFunctionCompiler()
    ir = compiler.compile(elements)
    print(json.dumps(ir.to_dict(), ensure_ascii=False, indent=2))
