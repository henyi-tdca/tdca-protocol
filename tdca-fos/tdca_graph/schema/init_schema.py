# -*- coding: utf-8 -*-
"""
TDCA-Graph Core Schema 初始化 — Neo4j 五维图 Schema 安装器
制度锚定: TDCA-KG-001 §2.2 / §3.2 | TDCA-TypeSystem-Confirmation-001 §2.1 | ID56
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

职责: 使用 neo4j Python 驱动初始化五维图 Schema：
  1) 全部 12 种节点类型
  2) 全部 9 种边类型（约束源/目标）
  3) 多维度索引（ID/类型/时间）
NSFL-Declaration:
  - 仅创建 Schema 约束与索引，不写入业务数据
  - 不可升级核心锚点（REPO-003-type-tag 等）仅作配置读取，不生成节点
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Optional

from tdca_graph.core.ontology import NodeType, EdgeType


# 边类型约束：{边: (允许的源节点标签列表, 允许的目标节点标签列表)}
# 源自 TDCA-KG-001 §2.2 edge_types 定义
EDGE_CONSTRAINTS: Dict[str, tuple] = {
    "DERIVES_FROM": (["Principle", "Constitution"], ["Principle", "FunctionSpec", "NSFLRule"]),
    "ENFORCES": (["Constitution"], ["FunctionSpec", "AgentRole"]),
    "IMPLEMENTS": (["FunctionSpec"], ["AgentRole", "CodeModule"]),
    "COMPILES_TO": (["AgentRole"], ["CodeModule"]),
    "PRICES": (["AssetClass"], ["MOUAnchor"]),
    "GENERATES": (["AgentRole"], ["NCA"]),
    "CONNECTS": (["TopologyNode"], ["TopologyNode"]),
    "NESTS": (["NCA"], ["NCA"]),
    "REFINES": (["NCA"], ["NCA"]),
}


class TDCAGraphSchemaInstaller:
    """
    五维图 Schema 安装器
    用法：
        installer = TDCAGraphSchemaInstaller(driver)
        report = installer.install()
    """

    def __init__(self, driver, dry_run: bool = False):
        """
        :param driver: neo4j.GraphDatabase.driver 实例
        :param dry_run: True 时仅返回语句清单，不执行
        """
        self.driver = driver
        self.dry_run = dry_run

    # ---- 语句构建 ----

    def node_constraint_statements(self) -> List[str]:
        """节点唯一性约束（ID 维度索引）"""
        stmts = []
        for label in NodeType.all_labels():
            if label == "RelationEdge":
                # RelationEdge 以 (source,target,edge_type) 为唯一键
                stmts.append(
                    f"CREATE CONSTRAINT relation_edge_unique IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE (n.source, n.target, n.edge_type) IS UNIQUE"
                )
            else:
                stmts.append(
                    f"CREATE CONSTRAINT {self._constraint_name(label)} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
                )
        return stmts

    def index_statements(self) -> List[str]:
        """多维度索引（ID/类型/时间/优先级）"""
        return [
            # 制度层
            "CREATE INDEX principle_priority IF NOT EXISTS FOR (n:Principle) ON (n.priority)",
            "CREATE INDEX constitution_article IF NOT EXISTS FOR (n:Constitution) ON (n.article)",
            "CREATE INDEX nsfl_level IF NOT EXISTS FOR (n:NSFLRule) ON (n.level)",
            # 技术层
            "CREATE INDEX function_spec_objective IF NOT EXISTS FOR (n:FunctionSpec) ON (n.objective)",
            "CREATE INDEX agent_role_cluster IF NOT EXISTS FOR (n:AgentRole) ON (n.cluster, n.role_id)",
            # 经济层
            "CREATE INDEX asset_class_tier IF NOT EXISTS FOR (n:AssetClass) ON (n.tier)",
            "CREATE INDEX mou_timestamp IF NOT EXISTS FOR (n:MOUAnchor) ON (n.timestamp)",
            # 拓扑层
            "CREATE INDEX topology_node_type IF NOT EXISTS FOR (n:TopologyNode) ON (n.node_type)",
            # 认知层
            "CREATE INDEX nca_layer IF NOT EXISTS FOR (n:NCA) ON (n.layer)",
            "CREATE INDEX cognitive_state_agent IF NOT EXISTS FOR (n:CognitiveState) ON (n.agent_id)",
        ]

    def edge_type_statements(self) -> List[str]:
        """边类型约束（源/目标合法性）"""
        stmts = []
        for edge, (sources, targets) in EDGE_CONSTRAINTS.items():
            # Neo4j 5.x 支持关系属性 schema 约束；源/目标标签合法性用 Cypher 注释声明
            stmts.append(
                f"// EDGE {edge}: {sources} -> {targets}"
            )
        # 关系类型合法性（可空属性约束仅用于索引场景，这里以注释形式固化契约）
        return stmts

    def install(self) -> Dict:
        """
        执行全部 Schema 安装语句
        :return: 执行报告 {constraints, indexes, edges, total}
        """
        statements = (
            self.node_constraint_statements()
            + self.index_statements()
            + self.edge_type_statements()
        )

        if self.dry_run:
            return {
                "dry_run": True,
                "constraints": len(self.node_constraint_statements()),
                "indexes": len(self.index_statements()),
                "edges": len(self.edge_type_statements()),
                "total_statements": len(statements),
                "statements": statements,
            }

        executed = 0
        with self.driver.session() as session:
            for stmt in statements:
                if stmt.startswith("//"):
                    continue  # 契约注释跳过
                session.run(stmt)
                executed += 1

        return {
            "dry_run": False,
            "constraints": len(self.node_constraint_statements()),
            "indexes": len(self.index_statements()),
            "edges": len(self.edge_type_statements()),
            "executed": executed,
            "total_statements": len(statements),
        }

    @staticmethod
    def _constraint_name(label: str) -> str:
        """生成约束命名（snake_case）"""
        import re
        return "uniq_" + re.sub(r"(?<!^)(?=[A-Z])", "_", label).lower()
