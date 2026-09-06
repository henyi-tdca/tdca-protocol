"""
TDCA-FC-20260803-005 主类 修正声明: 无（首版）
制度锚定: FC-005-SPEC, ID68, ID21, ID91
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 知识图谱编译器不替代人类价值判断
  - 先验分布编译失败必须有回退策略
  - 敏感领域知识需额外审批
SPDX-License-Identifier: Apache-2.0
"""

import os
import sys
from typing import List, Optional


class TDCAKnowledgeGraphCompiler:
    """
    FC-005 知识图谱编译器主类

    将历史 NCA、外部数据源、领域知识转化为
    可被 FC-004A 消费的规范化先验分布输入。
    """

    VERSION = '1.1.0'

    def __init__(self, modules_dir: Optional[str] = None,
                 nca_generator: Optional[callable] = None,
                 constraint_interpreter: Optional[object] = None):
        if modules_dir and modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        self._lazy = {}
        # LIM-002/003: 注入 FC-001 NCA 生成器 + FC-004B 约束解释器
        self._nca_generator = nca_generator
        self._constraint_interpreter = constraint_interpreter

    def _get(self, module_path: str, class_name: str):
        if module_path not in self._lazy:
            import importlib
            mod = importlib.import_module(module_path)
            self._lazy[module_path] = getattr(mod, class_name)
        return self._lazy[module_path]

    # ---- FR-001: 历史NCA知识抽取 ----

    def build_from_nca(self, query: dict, options: Optional[dict] = None) -> dict:
        """从历史 NCA 构建知识节点"""
        cls = self._get('extractors.nca_extractor', 'NCAExtractor')
        extractor = cls()
        result = extractor.build_from_nca(query, options)
        extractor.validate(result)
        return result

    # ---- FR-002: 外部数据源接入 ----

    def import_external_file(self, filepath: str, source_name: str,
                             trust_level: float = 0.7, mapping: Optional[dict] = None,
                             requires_approval: bool = False) -> dict:
        """从外部文件导入知识节点

        LIM-002: 集成 FC-004B 约束解释器的负空间检查。
        """
        cls = self._get('extractors.external_extractor', 'ExternalDataExtractor')

        # LIM-002: 若注入了 FC-004B，使用其负空间检查
        nsfl_checker = None
        if self._constraint_interpreter is not None:
            nsfl_checker = self._constraint_interpreter.check_negative_space

        extractor = cls(nsfl_checker=nsfl_checker)
        result = extractor.import_file(
            filepath, source_name, trust_level, mapping, requires_approval
        )
        extractor.validate(result)
        return result

    # ---- FR-003: 领域知识库管理 ----

    def create_domain_entry(self, title: str, content: dict, category: str,
                            tags: Optional[List[str]] = None, sensitive: bool = False) -> dict:
        """创建领域知识条目

        LIM-003: 注入 FC-001 NCA 生成器，确保条目创建强制生成 NCA 存证。
        """
        cls = self._get('graph.domain_manager', 'DomainKnowledgeManager')

        # LIM-003: 主类注入 nca_generator 到 DomainKnowledgeManager
        mgr = cls(nca_generator=self._nca_generator)
        entry = mgr.create_entry(title, content, category, tags, sensitive=sensitive)
        mgr.validate(entry)
        return entry

    # ---- FR-005: 先验分布编译 ----

    def compile_prior(self, graph_ref: str, node_selection: List[str],
                      distribution_type: str = 'BAYESIAN', nodes: Optional[list] = None,
                      min_confidence: float = 0.0,
                      conflict_resolution: str = 'WEIGHTED_AVERAGE') -> dict:
        """编译先验分布"""
        cls = self._get('prior_compilers.prior_compiler', 'PriorDistributionCompiler')
        compiler = cls()
        result = compiler.compile_prior(
            graph_ref, node_selection, distribution_type,
            nodes, min_confidence, conflict_resolution
        )
        compiler.validate(result)
        return result

    # ---- FR-006: 回测验证 ----

    def backtest_prior(self, prior_output: dict, test_dataset: List[dict],
                       metrics: Optional[List[str]] = None) -> dict:
        """先验分布回测验证"""
        cls = self._get('validators.backtest_validator', 'BacktestValidator')
        validator = cls()
        result = validator.backtest(prior_output, test_dataset, metrics)
        validator.validate(result)
        return result

    # ---- ID90: 最小化合检查 ----

    def necessity_check(self, compound_utility: float, component_utilities: List[float],
                        irreducibility: bool = True, nonlinearity: bool = True) -> dict:
        """最小化合必要性检查"""
        cls = self._get('prior_compilers.prior_compiler', 'NecessityChecker')
        checker = cls()
        return checker.check(compound_utility, component_utilities, irreducibility, nonlinearity)
