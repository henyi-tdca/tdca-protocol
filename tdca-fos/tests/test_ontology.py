# -*- coding: utf-8 -*-
"""
TDCA-Graph Core 本体论与 Schema 测试
制度锚定: TDCA-KG-001 §2.2/§3.2 | ID56 | FC: TDCA-FC-20260804-006
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_graph.core.ontology import (
    NodeType, EdgeType, PrincipleNode, PrincipleCategory,
    FunctionSpecNode, NCANode,
)
from tdca_graph.schema.init_schema import (
    TDCAGraphSchemaInstaller, EDGE_CONSTRAINTS,
)


class TestNodeTypeEnum:
    """节点类型枚举完整性 — TDCA-KG-001 §2.2"""

    def test_all_labels_count(self):
        assert len(NodeType.all_labels()) == 12

    def test_institutional_layer_present(self):
        labels = NodeType.all_labels()
        assert "Principle" in labels
        assert "Constitution" in labels
        assert "NSFLRule" in labels

    def test_all_dimension_labels_present(self):
        labels = set(NodeType.all_labels())
        assert labels >= {
            "FunctionSpec", "AgentRole", "CodeModule",          # 技术层
            "AssetClass", "MOUAnchor",                          # 经济层
            "TopologyNode", "RelationEdge",                     # 拓扑层
            "NCA", "CognitiveState",                            # 认知层
        }

    def test_edge_types_count(self):
        assert len(EdgeType.all_names()) == 9

    def test_edge_derives_from(self):
        assert EdgeType.DERIVES_FROM.value == "DERIVES_FROM"

    def test_nest_refine_pair(self):
        assert EdgeType.NESTS.value == "NESTS"
        assert EdgeType.REFINES.value == "REFINES"


class TestPrincipleNode:
    """制度原理节点 — ID56 封印"""

    def test_seal_hash_deterministic(self):
        p1 = PrincipleNode(id="ID29", name="制度基座具有不可还原的第一性",
                           category=PrincipleCategory.INSTITUTIONAL, priority=5)
        p2 = PrincipleNode(id="ID29", name="制度基座具有不可还原的第一性",
                           category=PrincipleCategory.INSTITUTIONAL, priority=5)
        assert p1.seal_hash() == p2.seal_hash()

    def test_seal_hash_is_sha256(self):
        p = PrincipleNode(id="ID29", name="x",
                          category=PrincipleCategory.COGNITIVE, priority=3)
        assert len(p.seal_hash()) == 64

    def test_seal_differs_on_priority(self):
        p_low = PrincipleNode(id="ID29", name="x",
                              category=PrincipleCategory.INSTITUTIONAL, priority=3)
        p_high = PrincipleNode(id="ID29", name="x",
                               category=PrincipleCategory.INSTITUTIONAL, priority=5)
        assert p_low.seal_hash() != p_high.seal_hash()


class TestFunctionSpecCompleteness:
    """函数语料六要素完整性 — ID68"""

    def test_incomplete_spec(self):
        fs = FunctionSpecNode(objective="目标")
        assert not fs.is_complete()

    def test_complete_spec(self):
        fs = FunctionSpecNode(
            objective="目标",
            constraints=[{"type": "约束"}],
            prior={"dist": "BAYESIAN"},
            config_right={"who": "DID"},
            allocation={"share": 0.5},
            audit_trail="TDCA-REV-001",
        )
        assert fs.is_complete()
        assert all(fs.completeness().values())


class TestSchemaInstaller:
    """Neo4j Schema 安装器 — M1 关键交付"""

    def test_constraint_count(self):
        installer = TDCAGraphSchemaInstaller(driver=None, dry_run=True)
        assert len(installer.node_constraint_statements()) == 12

    def test_index_count(self):
        installer = TDCAGraphSchemaInstaller(driver=None, dry_run=True)
        assert len(installer.index_statements()) == 10

    def test_dry_run_report(self):
        installer = TDCAGraphSchemaInstaller(driver=None, dry_run=True)
        report = installer.install()
        assert report["dry_run"] is True
        assert report["total_statements"] >= 31

    def test_constraint_syntax(self):
        installer = TDCAGraphSchemaInstaller(driver=None, dry_run=True)
        stmts = installer.node_constraint_statements()
        for s in stmts:
            assert "CREATE CONSTRAINT" in s
            assert "IF NOT EXISTS" in s

    def test_relation_edge_composite_key(self):
        installer = TDCAGraphSchemaInstaller(driver=None, dry_run=True)
        stmts = installer.node_constraint_statements()
        rel = [s for s in stmts if "relation_edge_unique" in s]
        assert len(rel) == 1
        assert "n.source, n.target, n.edge_type" in rel[0]

    def test_edge_constraints_contract(self):
        """边契约覆盖 9 种边 — TDCA-KG-001 §2.2"""
        assert set(EDGE_CONSTRAINTS.keys()) == set(EdgeType.all_names())

    def test_compiles_to_contract(self):
        assert EDGE_CONSTRAINTS["COMPILES_TO"] == (["AgentRole"], ["CodeModule"])

    def test_nest_self_loop_allowed(self):
        assert EDGE_CONSTRAINTS["NESTS"] == (["NCA"], ["NCA"])
