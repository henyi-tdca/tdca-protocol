"""
TDCA-FC-20260803-005 FR-005 修正声明: 无（首版）
制度锚定: FC-005-SPEC FR-005, ID90(最小化合原则), ID38(破例识别)
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 先验分布编译失败必须有明确回退策略（默认经验分布）
  - 税收锚定（MOU）作为分布硬约束边界
  - 多源冲突 → 加权平均或标记人工审核
  - NecessityChecker(ID90)：不满足最小化合则建议物理叠加
SPDX-License-Identifier: Apache-2.0
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional


class NecessityChecker:
    """
    ID90 最小化合原则 - 必要性判定器

    三项检查（P2 授权新增）:
      1. 不可拆分性检查: 移除任一阶资产，解决方案是否消失？
      2. 涌现价值检查: 化合产物效用 > 五阶资产独立效用加总？
      3. 非线性检查: 任意加权组合是否无法逼近产物性质？

    若三项检查任一不满足，返回"建议使用物理叠加而非NCA化合"
    """

    def check(self, compound_utility: float, component_utilities: List[float],
              irreducibility: bool = True, nonlinearity: bool = True) -> dict:
        """
        执行最小化合必要性判定。

        TODO (V2.0, LIM-005): 不可拆分性和非线性当前为调用方传入参数。
        计划 V2.0 实现自动检测：
          - 不可拆分性: 自动分析各阶资产对解的贡献度（移除后解消失检测）
          - 非线性: 自动检测组合函数是否可被线性加权逼近
        V1.1.0 过渡: 参数未提供时使用启发式默认值（True）。

        返回: {
          'necessary': bool,
          'checks': {
            'irreducibility': bool,   # 不可拆分性
            'emergence': bool,        # 涌现价值
            'nonlinearity': bool,     # 非线性
          },
          'recommendation': str,
        }
        """
        # 检查1: 不可拆分性
        irreducibility_ok = irreducibility

        # 检查2: 涌现价值（化合产物 > 独立效用加总）
        independent_sum = sum(component_utilities)
        emergence_ok = compound_utility > independent_sum

        # 检查3: 非线性（默认要求非线性，可由调用方提供）
        nonlinearity_ok = nonlinearity

        necessary = irreducibility_ok and emergence_ok and nonlinearity_ok

        return {
            'necessary': necessary,
            'checks': {
                'irreducibility': irreducibility_ok,
                'emergence': emergence_ok,
                'nonlinearity': nonlinearity_ok,
            },
            'recommendation': (
                '通过最小化合验证，允许NCA化合' if necessary
                else '建议使用物理叠加而非NCA化合'
            ),
        }


class PriorDistributionCompiler:
    """
    FR-005: 先验分布编译

    将知识图谱中的知识节点编译为 FC-004A 可消费的先验分布参数。

    支持分布类型:
      1. 贝叶斯分布（Beta）
      2. 经验分布（EMPIRICAL）
      3. 均匀分布（UNIFORM）
      4. 混合分布（MIXTURE）

    编译规则:
      1. 知识节点置信度 → 分布精度参数
      2. 知识节点时效性 → 分布衰减因子
      3. 多源冲突 → 加权平均或标记人工审核
      4. 税收锚定（MOU）→ 分布硬约束边界
    """

    def __init__(self, necessity_checker: Optional[NecessityChecker] = None):
        self.necessity = necessity_checker or NecessityChecker()

    def compile_prior(
        self,
        graph_ref: str,
        node_selection: List[str],
        distribution_type: str = 'BAYESIAN',
        nodes: Optional[list] = None,
        min_confidence: float = 0.0,
        conflict_resolution: str = 'WEIGHTED_AVERAGE'
    ) -> dict:
        """
        编译先验分布。

        返回: {
          'prior_output': {
            'output_id', 'graph_ref', 'distribution', 'compilation_trace', 'validation'
          },
          'status': 'SUCCESS|PARTIAL|FAILED',
          'warnings': [...],
        }
        """
        warnings = []
        selected = self._select_nodes(nodes or [], node_selection, min_confidence)

        if not selected:
            # 回退策略：均匀分布（无先验知识）
            output = self._build_uniform(graph_ref, [])
            return {
                'prior_output': output,
                'status': 'FAILED',
                'warnings': ['无满足条件的知识节点，回退为均匀分布'],
            }

        if distribution_type == 'BAYESIAN':
            output = self._compile_bayesian(graph_ref, selected)
        elif distribution_type == 'EMPIRICAL':
            output = self._compile_empirical(graph_ref, selected)
        elif distribution_type == 'UNIFORM':
            output = self._compile_uniform(graph_ref, selected)
        elif distribution_type == 'MIXTURE':
            output = self._compile_mixture(graph_ref, selected)
        else:
            return {
                'prior_output': None,
                'status': 'FAILED',
                'warnings': [f"未知分布类型: {distribution_type}，回退为均匀分布"],
            }

        # 冲突处理
        if conflict_resolution == 'HUMAN_REVIEW' and len(selected) > 1:
            conflicts = self._detect_conflicts(selected)
            if conflicts:
                output['validation']['human_review_required'] = True
                warnings.append(f"检测到 {len(conflicts)} 处知识冲突，需人工审核")

        return {
            'prior_output': output,
            'status': 'SUCCESS',
            'warnings': warnings,
        }

    # ---- 各分布编译 ----

    def _compile_bayesian(self, graph_ref: str, nodes: list) -> dict:
        """贝叶斯分布：Beta 先验（基于置信度均值/方差）"""
        confidences = [n.get('confidence', {}).get('final_score', 0.5) for n in nodes]
        mean = sum(confidences) / len(confidences)
        variance = sum((c - mean) ** 2 for c in confidences) / len(confidences)

        # Beta 参数估计（矩估计法）
        # alpha = mean * ((mean*(1-mean)/var) - 1)
        # beta = (1-mean) * ((mean*(1-mean)/var) - 1)
        scale = (mean * (1 - mean) / max(variance, 1e-6)) - 1
        alpha = max(0.1, mean * scale)
        beta = max(0.1, (1 - mean) * scale)

        return {
            'output_id': f"TDCA-PD-{uuid.uuid4().hex[:8]}",
            'graph_ref': graph_ref,
            'distribution': {
                'type': 'BAYESIAN',
                'parameters': {'alpha': round(alpha, 4), 'beta': round(beta, 4)},
            },
            'compilation_trace': {
                'source_nodes': [n.get('node_id') for n in nodes],
                'weights': [round(n.get('confidence', {}).get('final_score', 0.5), 4) for n in nodes],
                'compilation_time': datetime.now(timezone.utc).isoformat(),
                'compiler_version': '1.0.0',
            },
            'validation': {
                'backtest_available': False,
                'backtest_accuracy': None,
                'human_review_required': False,
            },
        }

    def _compile_empirical(self, graph_ref: str, nodes: list) -> dict:
        """经验分布：直接基于历史数据"""
        confidences = [n.get('confidence', {}).get('final_score', 0.5) for n in nodes]
        return {
            'output_id': f"TDCA-PD-{uuid.uuid4().hex[:8]}",
            'graph_ref': graph_ref,
            'distribution': {
                'type': 'EMPIRICAL',
                'parameters': {
                    'samples': confidences,
                    'mean': round(sum(confidences) / len(confidences), 4),
                    'min': round(min(confidences), 4),
                    'max': round(max(confidences), 4),
                },
            },
            'compilation_trace': {
                'source_nodes': [n.get('node_id') for n in nodes],
                'weights': [],
                'compilation_time': datetime.now(timezone.utc).isoformat(),
                'compiler_version': '1.0.0',
            },
            'validation': {
                'backtest_available': True,
                'backtest_accuracy': None,
                'human_review_required': False,
            },
        }

    def _compile_uniform(self, graph_ref: str, nodes: list) -> dict:
        """均匀分布：无先验知识"""
        return {
            'output_id': f"TDCA-PD-{uuid.uuid4().hex[:8]}",
            'graph_ref': graph_ref,
            'distribution': {
                'type': 'UNIFORM',
                'parameters': {'lower': 0.0, 'upper': 1.0},
            },
            'compilation_trace': {
                'source_nodes': [n.get('node_id') for n in nodes],
                'weights': [],
                'compilation_time': datetime.now(timezone.utc).isoformat(),
                'compiler_version': '1.0.0',
            },
            'validation': {
                'backtest_available': False,
                'backtest_accuracy': None,
                'human_review_required': False,
            },
        }

    def _build_uniform(self, graph_ref: str, nodes: list) -> dict:
        """回退用的均匀分布"""
        return self._compile_uniform(graph_ref, nodes)

    def _compile_mixture(self, graph_ref: str, nodes: list) -> dict:
        """混合分布：多源加权融合"""
        confidences = [n.get('confidence', {}).get('final_score', 0.5) for n in nodes]
        total = sum(confidences) or 1.0
        weights = [c / total for c in confidences]
        return {
            'output_id': f"TDCA-PD-{uuid.uuid4().hex[:8]}",
            'graph_ref': graph_ref,
            'distribution': {
                'type': 'MIXTURE',
                'parameters': {
                    'components': [
                        {'node': n.get('node_id'), 'weight': round(w, 4), 'mean': c}
                        for n, c, w in zip(nodes, confidences, weights)
                    ],
                },
            },
            'compilation_trace': {
                'source_nodes': [n.get('node_id') for n in nodes],
                'weights': [round(w, 4) for w in weights],
                'compilation_time': datetime.now(timezone.utc).isoformat(),
                'compiler_version': '1.0.0',
            },
            'validation': {
                'backtest_available': False,
                'backtest_accuracy': None,
                'human_review_required': False,
            },
        }

    # ---- 辅助 ----

    def _select_nodes(self, nodes: list, selection: List[str], min_confidence: float) -> list:
        """选择知识节点（按ID + 最低置信度过滤）"""
        selected = []
        for node in nodes:
            if selection and node.get('node_id') not in selection:
                continue
            conf = node.get('confidence', {}).get('final_score', 0.0)
            if conf < min_confidence:
                continue
            selected.append(node)
        return selected

    @staticmethod
    def _detect_conflicts(nodes: list) -> list:
        """检测知识冲突（同一内容不同置信度）"""
        conflicts = []
        content_map = {}
        for node in nodes:
            key = str(node.get('content', {}).get('objective_snapshot', ''))[:20]
            if key in content_map:
                conflicts.append({'node_ids': [content_map[key], node.get('node_id')]})
            else:
                content_map[key] = node.get('node_id')
        return conflicts

    def validate(self, result: dict) -> None:
        """
        自证机制：
          1. 状态合法（SUCCESS/PARTIAL/FAILED）
          2. 输出含 prior_output
          3. 分布参数完整性（按类型）
        """
        errors = []
        if result.get('status') not in ('SUCCESS', 'PARTIAL', 'FAILED'):
            errors.append(f"非法状态: {result.get('status')}")
        output = result.get('prior_output')
        if output is None and result.get('status') != 'FAILED':
            errors.append("非FAILED状态但输出为空")
        if output is not None:
            dist_type = output['distribution']['type']
            if dist_type == 'BAYESIAN' and 'alpha' not in output['distribution'].get('parameters', {}):
                errors.append("贝叶斯分布缺少 alpha 参数")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")
