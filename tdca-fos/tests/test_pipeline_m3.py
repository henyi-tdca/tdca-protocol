# -*- coding: utf-8 -*-
"""
TDCA 七库联动管道 M3 测试
制度锚定: TDCA-KG-001 §4.4 | ID91 | TypeSystem-Confirmation-001 §4.1 | FC: TDCA-FC-20260804-006-M3
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_pipeline.sync_engine import SevenRepoSyncEngine
from tdca_nca.generator import NCAGenerator
from tdca_kb.models.knowledge_unit import KnowledgeUnit


class FakeKG:
    """图引擎假实现"""

    def __init__(self):
        self.nodes = {}
        self.upserts = []

    def upsert_node(self, node):
        self.upserts.append(node)
        self.nodes[node["properties"]["unit_id"]] = node

    def get_node(self, nid):
        return self.nodes.get(nid, {})


class FakeContract:
    def __init__(self):
        self.evals = []

    def evaluate_upgrade(self, nca):
        self.evals.append(nca.nca_id)


class FakeSkill:
    def __init__(self):
        self.revisions = []

    def revise_boundary(self, nca):
        self.revisions.append(nca.nca_id)


class FakeGenie:
    def __init__(self):
        self.calibrations = []

    def calibrate_algorithm(self, nca):
        self.calibrations.append(nca.nca_id)


class FakeKB:
    """KB 假实现（可注入 unit）"""

    def __init__(self, unit=None):
        self.unit = unit
        self.flagged = []

    def get_unit(self, unit_id):
        return self.unit

    def flag_for_review(self, node_id):
        self.flagged.append(node_id)


@pytest.fixture
def unit():
    return KnowledgeUnit(
        id="KB-INST-001", source="制度白皮书", chapter="宪法十六条", section="第一条",
        content_text="制度基座具有不可还原的第一性",
        applicable_scenes=["沙盒准入"], priority=5, human_confirmed=True,
    )


@pytest.fixture
def engine(nca_placeholder, unit):
    return SevenRepoSyncEngine(
        kb_store=FakeKB(unit),
        kg_engine=FakeKG(),
        nca_generator=nca_placeholder,
        contract_repo=FakeContract(),
        skill_repo=FakeSkill(),
        genie_repo=FakeGenie(),
    )


class TestKbToKg:
    """检查项 5：KB→KG 联动"""

    def test_kb_update_syncs_to_kg(self, engine, unit):
        engine.run_pipeline("kb_update", unit.id)
        assert engine.kg.upserts  # 图节点已写入
        node = engine.kg.nodes.get(unit.id)
        assert node is not None
        assert "KnowledgeUnit" in node["labels"]

    def test_kb_update_generates_nca(self, engine, unit):
        from tdca_nca.generator import NCAGenerator
        engine.nca = NCAGenerator()
        before = engine.nca.count()
        engine.run_pipeline("kb_update", unit.id)
        assert engine.nca.count() > before

    def test_missing_unit_no_sync(self, engine):
        engine.kb = FakeKB(unit=None)
        engine.run_pipeline("kb_update", "KB-NOPE")
        assert engine.kg.upserts == []


class TestNcaToContract:
    """检查项 6：NCA→合约反哺"""

    def test_institutional_nca_drives_contract(self, nca_placeholder):
        nca = NCAGenerator()
        nca_ref = nca.generate("INSTITUTIONAL", 2, {"rule": "x"}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, contract_repo=FakeContract())
        engine._sync_nca_to_contract(nca_ref)
        assert engine.contract.evals == [nca_ref]

    def test_non_institutional_no_contract(self, nca_placeholder):
        nca = NCAGenerator()
        nca_ref = nca.generate("COGNITIVE", 1, {}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, contract_repo=FakeContract())
        engine._sync_nca_to_contract(nca_ref)
        assert engine.contract.evals == []


class TestNcaToSkill:
    """检查项 7：NCA→Skill 反哺"""

    def test_config_right_nca_drives_skill(self):
        nca = NCAGenerator()
        nca_ref = nca.generate("INSTITUTIONAL", 2,
                               {"config_right": {"who": "x"}}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, skill_repo=FakeSkill())
        engine._sync_nca_to_skill(nca_ref)
        assert engine.skill.revisions == [nca_ref]

    def test_no_config_right_no_skill(self):
        nca = NCAGenerator()
        nca_ref = nca.generate("INSTITUTIONAL", 2, {"rule": "x"}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, skill_repo=FakeSkill())
        engine._sync_nca_to_skill(nca_ref)
        assert engine.skill.revisions == []


class TestNcaToGenie:
    """NCA→效用精灵算法校准"""

    def test_utility_nca_drives_genie(self):
        nca = NCAGenerator()
        nca_ref = nca.generate("ECONOMIC", 3, {"mou": 100}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, genie_repo=FakeGenie())
        engine._sync_nca_to_genie(nca_ref)
        assert engine.genie.calibrations == [nca_ref]

    def test_plain_nca_no_genie(self):
        nca = NCAGenerator()
        nca_ref = nca.generate("INSTITUTIONAL", 2, {"rule": "x"}).nca_id
        engine = SevenRepoSyncEngine(
            nca_generator=nca, genie_repo=FakeGenie())
        engine._sync_nca_to_genie(nca_ref)
        assert engine.genie.calibrations == []


class TestKgToKb:
    """KG→KB 反哺"""

    def test_needs_review_flags_kb(self, unit):
        kg = FakeKG()
        kg.nodes["node-1"] = {"needs_review": True}
        kb = FakeKB(unit)
        engine = SevenRepoSyncEngine(kb_store=kb, kg_engine=kg)
        engine.run_pipeline("kg_inference", "node-1")
        assert kb.flagged == ["node-1"]

    def test_no_review_no_flag(self):
        kg = FakeKG()
        kg.nodes["node-2"] = {}
        engine = SevenRepoSyncEngine(kb_store=FakeKB(), kg_engine=kg)
        engine.run_pipeline("kg_inference", "node-2")
        assert engine.kb.flagged == []


class TestPipelineRouting:
    """管道执行路由 + NCA 存证"""

    def test_pipeline_generates_nca(self, engine, unit):
        from tdca_nca.generator import NCAGenerator
        engine.nca = NCAGenerator()
        before = engine.nca.count()
        engine.run_pipeline("kb_update", unit.id)
        assert engine.nca.count() > before

    def test_unknown_event_no_crash(self, engine):
        engine.run_pipeline("unknown_event", "x")  # 不应抛异常

    def test_pipelines_registry_complete(self, engine):
        assert set(engine.pipelines.keys()) == {
            "kb_to_kg", "nca_to_contract", "nca_to_skill",
            "nca_to_genie", "kg_to_kb",
        }
