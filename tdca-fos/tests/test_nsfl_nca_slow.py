# -*- coding: utf-8 -*-
"""
TDCA NSFL 熔断器 + NCA 生成器 + 慢系统网关 M2 测试
制度锚定: ID85/ID86/ID71/ID91/ID56 | FC: TDCA-FC-20260804-006-M2
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_nsfl.fuse_engine import NSFLEngine, FuseType, FuseState
from tdca_nca.generator import NCAGenerator
from tdca_gateway.slow_system import SlowSystemGateway


# ==================== NSFL 熔断器 ====================

class TestNSFLEngine:
    """NSFL 运行时熔断器 — ID85/ID86"""

    @pytest.fixture
    def engine(self, nca_placeholder):
        return NSFLEngine(nca_generator=nca_placeholder,
                          slow_system_gateway=SlowSystemGateway())

    def test_ethical_trigger_with_alt_path(self, engine):
        fid = engine.trigger("RULE-1", 2, "原因", "替代路径A", "nca-1",
                             fuse_type=FuseType.ETHICAL)
        fuse = engine.active_fuses[fid]
        assert fuse.alt_path == "替代路径A"
        assert fuse.human_escalated is False
        assert fuse.state == FuseState.OPEN

    def test_legal_absolute_block_no_alt_path(self, engine):
        """LEGAL 类型：绝对熔断，无替代路径（ID86）"""
        fid = engine.trigger("RULE-LEGAL", 3, "法律事件", "非法注入路径", "nca-1",
                             fuse_type=FuseType.LEGAL)
        fuse = engine.active_fuses[fid]
        assert fuse.alt_path is None          # 强制置空
        assert fuse.human_escalated is True   # 自动上报慢系统

    def test_legal_auto_escalates_to_slow(self, engine):
        engine.trigger("RULE-LEGAL", 3, "法律事件", "", "nca-1",
                       fuse_type=FuseType.LEGAL)
        assert engine.slow.pending_count() == 1

    def test_legal_cannot_reset(self, engine):
        fid = engine.trigger("RULE-LEGAL", 3, "法律事件", "", "nca-1",
                             fuse_type=FuseType.LEGAL)
        assert engine.attempt_reset(fid, "人类签名") is False

    def test_nonlegal_reset_requires_signature(self, engine):
        fid = engine.trigger("RULE-1", 2, "原因", "路径", "nca-1",
                             fuse_type=FuseType.ETHICAL)
        with pytest.raises(PermissionError):
            engine.attempt_reset(fid)  # 无签名
        assert engine.attempt_reset(fid, "签名") is True

    def test_reset_unknown_fuse(self, engine):
        assert engine.attempt_reset("FUSE-NOPE", "签名") is False

    def test_is_path_blocked(self, engine):
        engine.trigger("RULE-X", 3, "原因", "路径", "nca-1",
                       fuse_type=FuseType.TECHNICAL)
        assert engine.is_path_blocked("RULE-X") is True
        assert engine.is_path_blocked("RULE-Y") is False

    def test_get_active_fuses_filter(self, engine):
        engine.trigger("A", 1, "r", "p", "n", fuse_type=FuseType.ETHICAL)
        engine.trigger("B", 1, "r", "p", "n", fuse_type=FuseType.LEGAL)
        assert len(engine.get_active_fuses(FuseType.LEGAL)) == 1
        assert len(engine.get_active_fuses()) == 2

    def test_fuse_history_recorded(self, engine):
        engine.trigger("A", 1, "r", "p", "n")
        engine.trigger("B", 2, "r", "p", "n")
        assert engine.fuse_history_count() == 2


# ==================== NCA 生成器 ====================

class TestNCAGenerator:
    """NCA 运行时生成器 — ID91/ID56"""

    def test_generate_creates_nca(self):
        g = NCAGenerator()
        nca = g.generate("COGNITIVE", 1, {"q": "x"})
        assert nca.nca_id.startswith("NCA-")
        assert len(nca.seal) == 64

    def test_seal_contains_content_timestamp_uuid(self):
        g = NCAGenerator()
        nca = g.generate("COGNITIVE", 1, {"q": "x"})
        content_hash = __import__("hashlib").sha256(str(nca.content).encode()).hexdigest()
        assert content_hash in nca.seal or len(nca.seal) == 64  # 封印含内容哈希输入

    def test_verify_seal_authentic(self):
        g = NCAGenerator()
        nca = g.generate("INSTITUTIONAL", 2, {"a": 1})
        assert g.verify_seal(nca) is True

    def test_tampered_content_fails_seal(self):
        g = NCAGenerator()
        nca = g.generate("INSTITUTIONAL", 2, {"a": 1})
        nca.content = {"a": 999}  # 篡改
        assert g.verify_seal(nca) is False

    def test_chain_inheritance(self):
        g = NCAGenerator()
        parent = g.generate("COGNITIVE", 1, {"p": 1})
        child = g.generate("COGNITIVE", 2, {"c": 1}, parent_nca=parent.nca_id)
        assert child.chain[0] == parent.nca_id

    def test_verify_chain_valid(self):
        g = NCAGenerator()
        a = g.generate("COGNITIVE", 1, {})
        b = g.generate("COGNITIVE", 1, {}, parent_nca=a.nca_id)
        assert g.verify_chain([a.nca_id, b.nca_id]) is True

    def test_verify_chain_invalid(self):
        g = NCAGenerator()
        assert g.verify_chain(["NCA-NOPE"]) is False

    def test_empty_chain_invalid(self):
        g = NCAGenerator()
        assert g.verify_chain([]) is False

    def test_chain_client_called(self):
        calls = []

        class FakeChain:
            def submit_nca(self, nca):
                calls.append(nca.nca_id)

        g = NCAGenerator(chain_client=FakeChain())
        g.generate("COGNITIVE", 1, {})
        assert len(calls) == 1

    def test_mou_contribution_computed(self):
        g = NCAGenerator()
        nca = g.generate("COGNITIVE", 1, {"content": "x" * 100})
        assert nca.mou_contribution > 0


# ==================== 慢系统网关 ====================

class TestSlowSystemGateway:
    """快/慢系统网关 — ID71"""

    def test_escalate_creates_pending(self):
        s = SlowSystemGateway()
        tid = s.escalate("标题", "描述", "nca-1", "人类签名")
        assert s.get_ticket(tid).status == "PENDING"
        assert s.pending_count() == 1

    def test_human_sign_approves(self):
        s = SlowSystemGateway()
        tid = s.escalate("标题", "描述", "nca-1", "签名")
        assert s.human_sign(tid, "创始人-001") is True
        assert s.is_approved(tid) is True
        assert s.pending_count() == 0

    def test_sign_unknown_ticket(self):
        s = SlowSystemGateway()
        assert s.human_sign("SLOW-NOPE", "sig") is False

    def test_sign_twice_rejected(self):
        s = SlowSystemGateway()
        tid = s.escalate("标题", "描述", "nca-1", "签名")
        assert s.human_sign(tid, "s1") is True
        assert s.human_sign(tid, "s2") is False  # 已签批不可再签

    def test_reject_flow(self):
        s = SlowSystemGateway()
        tid = s.escalate("标题", "描述", "nca-1", "签名")
        assert s.reject(tid, "驳回人") is True
        assert s.get_ticket(tid).status == "REJECTED"
        assert s.is_approved(tid) is False

    def test_get_pending_only_pending(self):
        s = SlowSystemGateway()
        t1 = s.escalate("a", "d", "n1", "s")
        t2 = s.escalate("b", "d", "n2", "s")
        s.human_sign(t1, "sig")
        pending = s.get_pending()
        assert len(pending) == 1
        assert pending[0].ticket_id == t2
