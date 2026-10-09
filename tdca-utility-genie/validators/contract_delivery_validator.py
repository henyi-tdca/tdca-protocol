"""
TDCA-FC-20260802-004 修正声明: 无（首版）
制度锚定: ID79（MOU原理）, ID43（MCT原理/制度即货币）
Granted-By: TDCA-PRINCIPLE-MOU-001

NSFL-Declaration:
  - 税收锚定（MOU）是唯一硬验证标准，不可被模型预测替代
  - 禁止用效用最大化替代制度约束
  - 效用未达标时触发反函数重求解或负空间熔断
SPDX-License-Identifier: TDCA-Internal
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class DeliveryValidationReport:
    """交付效用确认报告"""
    contract_id: str
    utility_achievement: float          # 目标达成率 %
    tax_anchor_verification: bool
    variance_analysis: dict             # 偏差分析
    root_cause: str                     # config / execution / target / none
    recommendation: str
    nca_record: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class ContractDeliveryValidator:
    """
    智能合约交付效用确认器（ID79 + ID43）

    核心约束:
      - 合约执行后，对比预设目标效用与实际效用
      - 通过 MOU 税收锚定验证效用的真实性
      - 生成效用确认报告，作为后续审计依据
      - 效用未达标时，触发反函数重求解或负空间熔断
    """

    def validate(
        self,
        contract_id: str,
        target_utility: dict,          # 预设目标效用 {dimension: value}
        actual_mou: Optional[dict],    # 实际 MOU 记录（税收锚定）
        execution_trace: Optional[dict],  # 执行过程 NCA
        token_ref: str
    ) -> DeliveryValidationReport:
        """
        返回效用确认报告:
          - utility_achievement: 目标达成率（%）
          - tax_anchor_verification: 税收锚定验证结果
          - variance_analysis: 偏差分析
          - root_cause: 若未达标，根因分类（配置/执行/目标）
          - recommendation: 后续建议
          - nca_record: 确认过程 NCA
        """
        # Token-Ref 校验
        if not token_ref or not token_ref.startswith('TDCA-CRT-'):
            raise ValueError(f"[NSFL-TRIGGER] 无效 Token-Ref: {token_ref}")

        # 计算目标达成率（多维度平均）
        achievement_list = []
        variance = {}
        for dim, target_val in target_utility.items():
            actual_val = self._extract_actual(dim, actual_mou, execution_trace)
            if target_val and target_val > 0:
                rate = (actual_val / target_val) * 100.0
                achievement_list.append(rate)
                variance[dim] = {
                    'target': target_val,
                    'actual': actual_val,
                    'achievement_rate': round(rate, 2),
                }
            else:
                variance[dim] = {'target': target_val, 'actual': actual_val, 'achievement_rate': None}

        utility_achievement = sum(achievement_list) / len(achievement_list) if achievement_list else 0.0

        # 税收锚定验证（MOU 是唯一硬验证标准）
        tax_anchor_verification = False
        if actual_mou is not None:
            actual_total = actual_mou.get('Actual-Total') or actual_mou.get('actual_total')
            tax_anchor_verification = (actual_total is not None and actual_total > 0)

        # 根因分析与建议
        if utility_achievement >= 100.0:
            root_cause = 'none'
            recommendation = '确认通过，归档 NCA'
        elif utility_achievement >= 80.0:
            root_cause = 'none'
            recommendation = '确认通过，标记警告，生成改进建议'
        else:
            # 根因分类
            root_cause = self._classify_root_cause(
                tax_anchor_verification, execution_trace)
            if root_cause == 'config':
                recommendation = '触发反函数重求解'
            elif root_cause == 'execution':
                recommendation = '触发能力塑造'
            elif root_cause == 'target':
                recommendation = '触发负空间熔断（目标不可行）'
            else:
                recommendation = '需人工进一步分析'

        nca_record = {
            'operation_type': 'DeliveryValidation',
            'contract_id': contract_id,
            'token_ref': token_ref,
            'achievement': round(utility_achievement, 2),
            'tax_anchor_verified': tax_anchor_verification,
            'root_cause': root_cause,
        }

        return DeliveryValidationReport(
            contract_id=contract_id,
            utility_achievement=round(utility_achievement, 2),
            tax_anchor_verification=tax_anchor_verification,
            variance_analysis=variance,
            root_cause=root_cause,
            recommendation=recommendation,
            nca_record=nca_record,
        )

    def validate_report(self, report: DeliveryValidationReport) -> None:
        """
        自证机制：
          1. 达成率在 [0, 100] 区间
          2. 达成率 ≥ 100 时根因应为 none
          3. 根因分类合法
        """
        errors = []
        if report.utility_achievement < 0:
            errors.append(f"达成率为负: {report.utility_achievement}")
        if report.utility_achievement >= 100 and report.root_cause != 'none':
            errors.append(f"达成率100%但根因={report.root_cause}")
        if report.root_cause not in ('none', 'config', 'execution', 'target', 'unknown'):
            errors.append(f"非法根因分类: {report.root_cause}")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")

    @staticmethod
    def _extract_actual(dim: str, actual_mou: Optional[dict], execution_trace: Optional[dict]) -> float:
        """从 MOU 或执行轨迹提取实际效用值"""
        if actual_mou is not None and isinstance(actual_mou, dict):
            # MOU 中的税收锚定优先
            if dim == 'tax':
                return float(actual_mou.get('Actual-Total') or actual_mou.get('actual_total') or 0)
            if dim in actual_mou:
                val = actual_mou[dim]
                return float(val) if val is not None else 0.0
        if execution_trace is not None and isinstance(execution_trace, dict):
            if dim in execution_trace:
                val = execution_trace[dim]
                return float(val) if val is not None else 0.0
        return 0.0

    @staticmethod
    def _classify_root_cause(tax_anchor_verified: bool, execution_trace: Optional[dict]) -> str:
        """根因分类：配置/执行/目标"""
        if not tax_anchor_verified:
            return 'config'  # 税收锚定未通过 → 配置问题
        if execution_trace is not None:
            errors = execution_trace.get('errors', [])
            if errors:
                return 'execution'
        return 'target'  # 其他情况 → 目标设定问题
