# -*- coding: utf-8 -*-
"""
TDCA OTA 版本控制 + 版本差异 + 联动版本化 M4 测试
制度锚定: TDCA-KG-001 §3.1/§6.2 B5 | TypeSystem-Confirmation-001 §9.3
       | ID71 | ID91 | FC: TDCA-FC-20260804-006-M4
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_graph.version.ota_control import (
    OTAController, GraphVersion, NSFLTrigger, SlowSystemRequired,
)
from tdca_graph.query.engine import TDCAGraphQueryEngine
from tdca_pipeline.sync_engine import SevenRepoSyncEngine
from tdca_nca.generator import NCAGenerator
from tdca_kb.models.knowledge_unit import KnowledgeUnit


# ==================== OTA 版本控制 ====================

class TestOTAProposeUpdate:
    """M4 OTA 更新提案"""

    def test_normal_update_advances(self):
        ota = OTAController()
        vid = ota.propose_update("node-A", {"priority": 3}, "DeepSeek-V4")
        assert vid.startswith("v1.0.1")
        assert ota.current_version == vid
        assert ota.version_count() == 2

    def test_immutable_anchor_blocked(self):
        ota = OTAController()
        with pytest.raises(NSFLTrigger):
            ota.propose_update("REPO-003-type-tag", {}, "x")

    def test_all_four_anchors_hardcoded(self):
        ota = OTAController()
        for anchor in ota._IMMUTABLE_ANCHORS:
            with pytest.raises(NSFLTrigger):
                ota.propose_update(anchor, {}, "x")

    def test_constitution_requires_signature(self):
        ota = OTAController()
        with pytest.raises(SlowSystemRequired):
            ota.propose_update("node-C", {}, "x", is_constitution=True)

    def test_priority5_requires_signature(self):
        ota = OTAController()
        with pytest.raises(SlowSystemRequired):
            ota.propose_update("node-D", {}, "x", priority=5)

    def test_priority5_with_signature_ok(self):
        ota = OTAController()
        vid = ota.propose_update("node-D", {}, "x", priority=5, human_signed=True)
        v = ota.get_version(vid)
        assert v.human_signature is not None  # 签名固化

    def test_conflict_detection(self):
        """M4: 同一节点当前版本已变更 → 连续修改需确认"""
        ota = OTAController()
        ota.propose_update("node-X", {"a": 1}, "m")
        with pytest.raises(ValueError):
            ota.propose_update("node-X", {"a": 2}, "m")  # 同节点连续变更


class TestOTAMerkleChain:
    """M4 Merkle 链式验证"""

    def test_merkle_includes_parent(self):
        ota = OTAController()
        v1 = ota.propose_update("a", {"x": 1}, "m")
        v2 = ota.propose_update("b", {"y": 2}, "m")
        m1 = ota.get_version(v1)
        m2 = ota.get_version(v2)
        # 不同节点 + 不同父版本 → 哈希不同
        assert m1.merkle_root != m2.merkle_root

    def test_merkle_reproducible(self):
        ota1 = OTAController()
        ota2 = OTAController()
        v1 = ota1.propose_update("a", {"x": 1}, "m")
        v2 = ota2.propose_update("a", {"x": 1}, "m")
        assert ota1.get_version(v1).merkle_root == ota2.get_version(v2).merkle_root

    def test_verify_lineage_with_provider(self):
        ota = OTAController()
        vid = ota.propose_update("a", {"x": 1}, "m")
        v = ota.get_version(vid)
        # merkle_provider 返回正确哈希 → lineage 通过
        assert v.verify_lineage("v1.0.0",
                                lambda _id: v.merkle_root if _id == vid else None) is True
        # 返回错误哈希 → lineage 失败
        assert v.verify_lineage("v1.0.0", lambda _id: "tampered") is False


class TestOTAChain:
    """OTA 谱系完整性"""

    def test_verify_chain_valid(self):
        ota = OTAController()
        ota.propose_update("a", {}, "m")
        v2 = ota.propose_update("b", {}, "m")
        assert ota.verify_chain(v2) is True

    def test_verify_chain_broken(self):
        ota = OTAController()
        assert ota.verify_chain("v99.0.0") is False

    def test_lineage_depth(self):
        ota = OTAController()
        ota.propose_update("a", {}, "m")
        v2 = ota.propose_update("b", {}, "m")
        v3 = ota.propose_update("c", {}, "m")
        assert ota.lineage_depth(v3) == 3
        assert ota.lineage_depth("v1.0.0") == 0

    def test_human_sign_backfill(self):
        """M4: 慢系统补签"""
        ota = OTAController()
        # 宪法级必须带签名创建（否则 SlowSystemRequired）
        vid = ota.propose_update("node-P5", {}, "m", priority=5, human_signed=True)
        assert ota.get_version(vid).human_signature is not None
        # 已签名版本不可重复补签
        assert ota.human_sign(vid, "again") is False

    def test_human_sign_unknown_version(self):
        ota = OTAController()
        assert ota.human_sign("v99.0.0", "sig") is False


class TestOTADiff:
    """M4 版本差异"""

    def test_diff_between_versions(self):
        ota = OTAController()
        ota.propose_update("node-1", {}, "m")
        ota.propose_update("node-2", {}, "m")
        ota.propose_update("node-3", {}, "m")
        d = ota.diff("v1.0.0", ota.current_version)
        assert set(d["changed_nodes"]) == {"node-1", "node-2", "node-3"}
        assert d["merkle_root"] == ota.get_version(ota.current_version).merkle_root

    def test_diff_single_step(self):
        ota = OTAController()
        v1 = ota.propose_update("node-1", {}, "m")
        d = ota.diff("v1.0.0", v1)
        assert d["changed_nodes"] == ["node-1"]

    def test_diff_unknown_version(self):
        ota = OTAController()
        with pytest.raises(ValueError):
            ota.diff("v1.0.0", "v9.9.9")


# ==================== 版本差异 API（engine）====================

class TestEngineVersionDiff:
    """M4-2 查询引擎版本差异"""

    def test_engine_diff_with_ota(self, memory_driver, nca_placeholder):
        ota = OTAController()
        ota.propose_update("node-1", {}, "m")
        ota.propose_update("node-2", {}, "m")
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder,
                                      ota=ota)
        diff = engine.get_version_diff("v1.0.0", ota.current_version)
        assert set(diff) == {"node-1", "node-2"}
        assert nca_placeholder.count() == 1  # 查询生成 NCA

    def test_engine_diff_without_ota(self, memory_driver, nca_placeholder):
        engine = TDCAGraphQueryEngine(memory_driver, nca_generator=nca_placeholder)
        assert engine.get_version_diff("v1.0.0", "v1.0.1") == []


# ==================== 联动管道版本化 ====================

class FakeKG2:
    """图引擎假实现（带 upsert/get）"""

    def __init__(self):
        self.nodes = {}

    def upsert_node(self, node):
        self.nodes[node["properties"]["unit_id"]] = node

    def get_node(self, nid):
        return self.nodes.get(nid, {})


class FakeKB2:
    def __init__(self, unit=None):
        self.unit = unit

    def get_unit(self, unit_id):
        return self.unit


@pytest.fixture
def ku_unit():
    return KnowledgeUnit(
        id="KB-INST-001", source="制度白皮书", chapter="宪法十六条", section="第一条",
        content_text="制度基座具有不可还原的第一性",
        applicable_scenes=["沙盒准入"], priority=3, human_confirmed=True,
    )


class TestPipelineVersioned:
    """M4-3 联动管道版本化"""

    def test_kb_to_kg_triggers_ota(self, ku_unit, nca_placeholder):
        ota = OTAController()
        engine = SevenRepoSyncEngine(
            kb_store=FakeKB2(ku_unit),
            kg_engine=FakeKG2(),
            nca_generator=nca_placeholder,
            ota_controller=ota,
        )
        engine.run_pipeline("kb_update", ku_unit.id)
        assert ota.version_count() == 2  # 根 + 新版本
        assert ota.current_version.startswith("v1.0.1")

    def test_version_changed_nodes(self, ku_unit, nca_placeholder):
        ota = OTAController()
        engine = SevenRepoSyncEngine(
            kb_store=FakeKB2(ku_unit), kg_engine=FakeKG2(),
            nca_generator=nca_placeholder, ota_controller=ota,
        )
        engine.run_pipeline("kb_update", ku_unit.id)
        d = ota.diff("v1.0.0", ota.current_version)
        assert d["changed_nodes"] == [ku_unit.id]

    def test_priority5_auto_signed(self, nca_placeholder):
        """宪法级知识单元（priority=5）联动时自动带签名（ID71）"""
        ota = OTAController()
        unit = KnowledgeUnit(
            id="KB-CONST-001", source="制度白皮书", chapter="宪法十六条",
            section="第一条", content_text="宪法级", priority=5, human_confirmed=True,
        )
        engine = SevenRepoSyncEngine(
            kb_store=FakeKB2(unit), kg_engine=FakeKG2(),
            nca_generator=nca_placeholder, ota_controller=ota,
        )
        engine.run_pipeline("kb_update", unit.id)
        v = ota.get_version(ota.current_version)
        assert v.human_signature is not None  # 自动签名已固化

    def test_no_ota_no_crash(self, ku_unit, nca_placeholder):
        engine = SevenRepoSyncEngine(
            kb_store=FakeKB2(ku_unit), kg_engine=FakeKG2(),
            nca_generator=nca_placeholder, ota_controller=None,
        )
        engine.run_pipeline("kb_update", ku_unit.id)  # 不应抛异常

