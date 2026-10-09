# -*- coding: utf-8 -*-
"""
TDCA-KB 存储测试 — 知识单元 CRUD 与场景查询
制度锚定: TDCA-KG-001 §4.2/§4.3 | ID56 | FC: TDCA-FC-20260804-006
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_kb.models.knowledge_unit import KnowledgeUnit


class TestKnowledgeUnitModel:
    """知识单元领域模型"""

    def test_seal_hash_deterministic(self, sample_unit):
        u1 = KnowledgeUnit(id=sample_unit.id, source=sample_unit.source,
                           chapter=sample_unit.chapter, section=sample_unit.section,
                           content_text=sample_unit.content_text,
                           ota_version=sample_unit.ota_version)
        u2 = KnowledgeUnit(id=sample_unit.id, source=sample_unit.source,
                           chapter=sample_unit.chapter, section=sample_unit.section,
                           content_text=sample_unit.content_text,
                           ota_version=sample_unit.ota_version)
        assert u1.compute_seal() == u2.compute_seal()

    def test_seal_changes_with_content(self):
        u1 = KnowledgeUnit(id="K1", source="制度白皮书", chapter="c", section="s",
                           content_text="文本A")
        u2 = KnowledgeUnit(id="K1", source="制度白皮书", chapter="c", section="s",
                           content_text="文本B")
        assert u1.compute_seal() != u2.compute_seal()

    def test_to_kg_node_labels(self, sample_unit):
        node = sample_unit.to_kg_node()
        assert "KnowledgeUnit" in node["labels"]
        assert "制度" in node["labels"][1]
        assert node["properties"]["seal"] == sample_unit.compute_seal()

    def test_kg_node_properties(self, sample_unit):
        node = sample_unit.to_kg_node()
        assert node["properties"]["priority"] == 5
        assert node["properties"]["mou_impact"] == "MEDIUM"


class TestKnowledgeBaseCRUD:
    """知识单元 CRUD — 任务书 M1 测试覆盖点"""

    def test_create(self, kb_store, sample_unit):
        assert kb_store.create_unit(sample_unit) == "KB-INST-001"

    def test_get(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        got = kb_store.get_unit("KB-INST-001")
        assert got is not None
        assert got.priority == 5
        assert got.source == "制度白皮书"

    def test_get_missing(self, kb_store):
        assert kb_store.get_unit("NOPE") is None

    def test_update(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        assert kb_store.update_unit("KB-INST-001", priority=4, stability="EVOLVING")
        got = kb_store.get_unit("KB-INST-001")
        assert got.priority == 4
        assert got.stability == "EVOLVING"

    def test_update_invalid_field(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        with pytest.raises(ValueError):
            kb_store.update_unit("KB-INST-001", non_existent=1)

    def test_delete(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        assert kb_store.delete_unit("KB-INST-001") is True
        assert kb_store.get_unit("KB-INST-001") is None

    def test_delete_missing(self, kb_store):
        assert kb_store.delete_unit("NOPE") is False

    def test_list_by_source(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        rows = kb_store.list_units(source="制度白皮书")
        assert len(rows) == 1

    def test_list_empty(self, kb_store):
        assert kb_store.list_units() == []


class TestKnowledgeBaseSceneQuery:
    """核心查询模式 — TDCA-KG-001 §4.3"""

    def test_query_by_scene(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        rows = kb_store.query_by_scene("沙盒准入")
        assert len(rows) == 1
        assert rows[0].id == "KB-INST-001"

    def test_query_excludes_unconfirmed(self, kb_store, sample_unit):
        sample_unit.human_confirmed = False
        kb_store.create_unit(sample_unit)
        assert kb_store.query_by_scene("沙盒准入") == []

    def test_query_excludes_deprecated(self, kb_store, sample_unit):
        sample_unit.stability = "DEPRECATED"
        kb_store.create_unit(sample_unit)
        assert kb_store.query_by_scene("沙盒准入") == []

    def test_query_excludes_other_scene(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        assert kb_store.query_by_scene("无关场景") == []

    def test_query_order_priority_desc(self, kb_store, sample_unit):
        kb_store.create_unit(sample_unit)
        low = KnowledgeUnit(
            id="KB-INST-002", source="制度白皮书", chapter="c", section="s",
            content_text="低优先级", applicable_scenes=["沙盒准入"],
            human_confirmed=True, priority=1)
        kb_store.create_unit(low)
        rows = kb_store.query_by_scene("沙盒准入")
        assert rows[0].id == "KB-INST-001"  # priority 5 在前
        assert rows[1].id == "KB-INST-002"


class TestKnowledgeBaseNSFL:
    """负空间校验 — 认知负空间"""

    def test_invalid_source_blocked(self, kb_store):
        bad = KnowledgeUnit(id="K-BAD", source="伪造来源", chapter="c",
                            section="s", content_text="x")
        with pytest.raises(ValueError):
            kb_store.create_unit(bad)

    def test_invalid_stability_blocked(self, kb_store):
        bad = KnowledgeUnit(id="K-BAD", source="制度白皮书", chapter="c",
                            section="s", content_text="x", stability="WEIRD")
        with pytest.raises(ValueError):
            kb_store.create_unit(bad)

    def test_invalid_mou_impact_blocked(self, kb_store):
        bad = KnowledgeUnit(id="K-BAD", source="制度白皮书", chapter="c",
                            section="s", content_text="x", mou_impact="HUGE")
        with pytest.raises(ValueError):
            kb_store.create_unit(bad)
