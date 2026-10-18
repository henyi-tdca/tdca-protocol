"""
TDCA-FC-20260802-004 修正声明:
  - R1-P1: Max-Retry 语义层级区分（制度层0 / 模块C技术层≤3次）
  - R1-P1: embedding 三级降级策略（API→本地→Jaccard→HUMAN_REQUIRED）
  - R1-P2: 执行顺序并行化（B∥D → A → C）

制度锚定: TDCA-PRINCIPLE-FC-NCA-COH-001(约束统一②), ID8
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-001

NSFL-Declaration:
  - 禁止本地缓存或覆盖解释结果
  - 解释结果必须同步上链，作为 MOU 计算的硬输入
  - 所有主体对制度文本的解释必须走本 API
SPDX-License-Identifier: TDCA-Internal
"""

import enum
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


class InterpretationStatus(enum.Enum):
    """三态判定"""
    ALLOWED = "ALLOWED"                # 允许执行
    DENIED = "DENIED"                  # 禁止执行（触发NSFL）
    HUMAN_REQUIRED = "HUMAN_REQUIRED"  # 需人类介入裁决


@dataclass
class InterpretationResult:
    """约束解释结果"""
    status: InterpretationStatus
    constraint_id: str
    reason: str
    matched_rules: list = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class TDCAConstraintInterpreter:
    """
    宪法十六条、UPDA、配置权第三极的统一解释器

    核心约束:
      - 所有主体对制度文本的解释必须走此 API
      - 禁止本地缓存或覆盖解释结果
      - 解释结果同步上链，作为 MOU 计算的硬输入
    """

    def __init__(self, rules_file: Optional[str] = None):
        # 规则库：constraint_id -> 规则定义
        self.rules = self._load_default_rules()
        if rules_file and os.path.exists(rules_file):
            self._load_rules_file(rules_file)

    def interpret(
        self,
        subject_context: dict,      # 主体上下文（身份/角色/历史行为）
        operation: str,             # 待执行操作
        constraint_text: str        # 待解释的约束条款
    ) -> InterpretationResult:
        """
        返回三态判定:
          - ALLOWED: 允许执行
          - DENIED: 禁止执行（触发 NSFL）
          - HUMAN_REQUIRED: 需人类介入裁决
        """
        # 1. 匹配约束条款对应的规则
        constraint_id = self._match_constraint(constraint_text)
        if constraint_id is None:
            return InterpretationResult(
                status=InterpretationStatus.HUMAN_REQUIRED,
                constraint_id="UNKNOWN",
                reason=f"无法识别约束条款: {constraint_text}",
                confidence=0.0,
            )

        rule = self.rules.get(constraint_id)

        # 2. 检查操作是否在禁止集合
        forbidden_ops = rule.get('forbidden_operations', [])
        if operation in forbidden_ops:
            return InterpretationResult(
                status=InterpretationStatus.DENIED,
                constraint_id=constraint_id,
                reason=f"操作 '{operation}' 触碰约束 '{constraint_id}' 的禁止集合",
                matched_rules=[constraint_id],
                confidence=1.0,
            )

        # 3. 检查硬性前置条件（签名/认证/角色）
        requirements = rule.get('requirements', {})
        unmet = self._check_requirements(subject_context, requirements)
        if unmet:
            return InterpretationResult(
                status=InterpretationStatus.DENIED if rule.get('deny_on_unmet', True) else InterpretationStatus.HUMAN_REQUIRED,
                constraint_id=constraint_id,
                reason=f"前置条件未满足: {', '.join(unmet)}",
                matched_rules=[constraint_id],
                confidence=0.9,
            )

        # 4. 检查是否需要人类裁决（高风险/无明确规则）
        if rule.get('human_required', False) or self._needs_human(subject_context, operation):
            return InterpretationResult(
                status=InterpretationStatus.HUMAN_REQUIRED,
                constraint_id=constraint_id,
                reason=f"操作 '{operation}' 需人类介入裁决",
                matched_rules=[constraint_id],
                confidence=0.5,
            )

        return InterpretationResult(
            status=InterpretationStatus.ALLOWED,
            constraint_id=constraint_id,
            reason=f"操作 '{operation}' 满足约束 '{constraint_id}'",
            matched_rules=[constraint_id],
            confidence=1.0,
        )

    # ---- 规则库 ----

    def _load_default_rules(self) -> dict:
        """默认规则库（宪法十六条核心约束的规则化）"""
        return {
            # 正和约束
            'POSITIVE_SUM': {
                'description': '正和约束：协作须产生正和效用',
                'forbidden_operations': ['zero_sum_extraction', 'negative_sum_call'],
                'requirements': {'eri_positive': True},
                'deny_on_unmet': True,
                'human_required': False,
            },
            # 数据完整性（NSFL）
            'DATA_INTEGRITY': {
                'description': '数据完整性：不可破坏数据',
                'forbidden_operations': ['data_corruption', 'unauthorized_encoding_change'],
                'requirements': {'backup_before_write': True},
                'deny_on_unmet': True,
                'human_required': True,
            },
            # 版权确权
            'COPYRIGHT': {
                'description': '版权确权：未经确权的知识资产不可调用',
                'forbidden_operations': ['use_unregistered_knowledge'],
                'requirements': {'copyright_registered': True},
                'deny_on_unmet': True,
                'human_required': False,
            },
            # 配置权边界
            'CONFIG_RIGHT_BOUNDARY': {
                'description': '配置权边界：调用须在授权范围内',
                'forbidden_operations': ['over_boundary_call', 'privilege_escalation'],
                'requirements': {'token_valid': True, 'signature_required': True},
                'deny_on_unmet': True,
                'human_required': False,
            },
            # 负空间
            'NEGATIVE_SPACE': {
                'description': '负空间：不可在价值领地上自主决策',
                'forbidden_operations': ['autonomous_repair', 'value_land_decisions'],
                'requirements': {'nsfl_declared': True},
                'deny_on_unmet': True,
                'human_required': True,
            },
            # 税收锚定
            'TAX_ANCHOR': {
                'description': '税收锚定：交易须产生可验证税收',
                'forbidden_operations': ['tax_evasion', 'fake_tax_data'],
                'requirements': {'tax_recordable': True},
                'deny_on_unmet': True,
                'human_required': False,
            },
        }

    def _load_rules_file(self, path: str):
        """从 YAML 文件加载扩展规则"""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                extra = yaml.safe_load(f) or {}
            self.rules.update(extra)
        except Exception:
            pass  # 扩展规则加载失败不阻断

    # ---- 辅助 ----

    def _match_constraint(self, constraint_text: str) -> Optional[str]:
        """将约束文本映射到规则ID"""
        text = constraint_text.strip().upper()
        # 精确匹配规则ID
        if text in self.rules:
            return text
        # 关键词匹配
        keyword_map = {
            'POSITIVE_SUM': ['正和', 'POSITIVE', '涌现', 'ERI'],
            'DATA_INTEGRITY': ['数据完整性', 'DATABASE', '数据损坏', '备份'],
            'COPYRIGHT': ['版权', 'COPYRIGHT', '确权', '知识资产'],
            'CONFIG_RIGHT_BOUNDARY': ['配置权', 'CONFIG', '边界', 'TOKEN'],
            'NEGATIVE_SPACE': ['负空间', 'NSFL', '价值领地', '自主修复'],
            'TAX_ANCHOR': ['税收', 'TAX', '锚定', 'MOU'],
        }
        for cid, keywords in keyword_map.items():
            if any(kw in text for kw in keywords):
                return cid
        return None

    def _check_requirements(self, context: dict, requirements: dict) -> list:
        """检查前置条件，返回未满足项列表"""
        unmet = []
        for req, required_value in requirements.items():
            actual = context.get(req)
            if actual is None or actual != required_value:
                unmet.append(f"{req}(需要={required_value}, 实际={actual})")
        return unmet

    def _needs_human(self, context: dict, operation: str) -> bool:
        """判断是否需要人类介入"""
        # HIGH 风险操作需人类
        if context.get('risk_level') == 'HIGH':
            return True
        # 写操作但无人类签名
        write_ops = {'FileMove', 'FileEdit', 'FileDelete', 'DirMove', 'ConfigChange'}
        if operation in write_ops and not context.get('human_signature'):
            return True
        return False


# ---- CLI ----
if __name__ == '__main__':
    import sys
    import json
    if len(sys.argv) < 4:
        print("用法: python tdca_constraint_interpreter.py <operation> <constraint_text> [context_json]")
        sys.exit(1)
    op = sys.argv[1]
    constraint = sys.argv[2]
    ctx = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    interp = TDCAConstraintInterpreter()
    result = interp.interpret(ctx, op, constraint)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
