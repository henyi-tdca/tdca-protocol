# -*- coding: utf-8 -*-
"""
TDCA-IRP 跨库互操作 M3 测试
制度锚定: TypeSystem-Confirmation-001 §5.2/§6 | ID91/ID79/ID85/ID86 | FC: TDCA-FC-20260804-006-M3
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_irp.gateway import (
    IRPGateway, ConfigRightCall, CrossInvokeResult,
)
from tdca_nca.generator import NCAGenerator
from tdca_nsfl.fuse_engine import NSFLEngine, FuseType


def _converted():
    return {"institutional_conversion": {"accepts_tda_constitution": True}}


@pytest.fixture
def gw(nca_placeholder):
    """IRP 网关 fixture（dict 注册表 + NCA 占位器）"""
    repo_a = _converted()
    repo_b = _converted()
    repo_b["query"] = lambda q: {"answer": q}
    repo_b["invoke"] = lambda c: {"ok": True}
    repo_b["verify_nca"] = lambda nca: None
    nsfl = NSFLEngine(nca_generator=nca_placeholder)
    return IRPGateway({"a": repo_a, "b": repo_b},
                      nca_generator=nca_placeholder, nsfl_engine=nsfl)


@pytest.fixture
def cr():
    return ConfigRightCall(who="did-1", what="kb", when=1, how="query",
                           share=0.5, cfg="cfg-h", tax=100)


class TestCrossQuery:
    """检查项 1：跨库查询携带 NCA 追溯链"""

    def test_cross_query_ok(self, gw, cr):
        out = gw.cross_query("a", "b", {"scene": "s"}, cr)
        assert out["result"]["answer"] == {"scene": "s"}
        assert len(out["nca_trace"]) == 1
        assert out["mou_contribution"] == 100

    def test_unconverted_repo_blocked(self, gw, cr):
        gw.repos["a"] = {"institutional_conversion": {}}
        with pytest.raises(PermissionError):
            gw.cross_query("a", "b", {}, cr)

    def test_bad_config_right_rejected(self, gw, cr):
        bad = ConfigRightCall(who="", what="", when=0, how="", share=2.0,
                              cfg="", tax=-1)
        with pytest.raises(ValueError):
            gw.cross_query("a", "b", {}, bad)

    def test_unknown_target_repo(self, gw, cr):
        # 未知目标库先被制度皈依检查拦截（repo 不存在 → conversion=False）
        with pytest.raises(PermissionError):
            gw.cross_query("a", "nope", {}, cr)


class TestNegativeSpacePreCheck:
    """检查项 4：负空间预检自动熔断"""

    def test_legal_keyword_blocked(self, gw, cr):
        with pytest.raises(PermissionError):
            gw.cross_query("a", "b", {"q": "如何违法绕过监管"}, cr)
        assert gw.nsfl.is_path_blocked("IRP-NSFL-PRE-CHECK") is True

    def test_legal_fuse_no_alt_path(self, gw, cr):
        """LEGAL 负空间：熔断器 alt_path=None（ID86）"""
        try:
            gw.cross_query("a", "b", {"q": "洗钱手法"}, cr)
        except PermissionError:
            pass
        fuses = gw.nsfl.get_active_fuses(FuseType.LEGAL)
        assert len(fuses) >= 1
        assert all(f.alt_path is None for f in fuses)

    def test_ethical_keyword_has_alt_path(self, gw, cr):
        """ETHICAL 负空间：熔断但有替代路径"""
        try:
            gw.cross_query("a", "b", {"q": "如何操纵情绪"}, cr)
        except PermissionError:
            pass
        fuses = gw.nsfl.get_active_fuses(FuseType.ETHICAL)
        assert len(fuses) >= 1
        assert all(f.alt_path is not None for f in fuses)

    def test_clean_query_passes(self, gw, cr):
        out = gw.cross_query("a", "b", {"q": "查询宪法第一条"}, cr)
        assert out["result"]["answer"] is not None


class TestCrossInvoke:
    """检查项 2：跨库调用验证 NCA 链完整性"""

    def test_invoke_with_valid_chain(self, gw, cr, nca_placeholder):
        n1 = nca_placeholder.record_query("Q1", {}, {"tax": 100})
        # 占位器 NCA 无 mou_contribution 字段——用 generate 版 NCA 保证 MOU>0
        from tdca_nca.generator import NCAGenerator
        nca = NCAGenerator()
        gw.nca = nca
        a = nca.generate("INSTITUTIONAL", 3, {"tax": 100})
        inv = gw.cross_invoke("a", "b", cr, [a.nca_id])
        assert inv.success is True
        assert isinstance(inv, CrossInvokeResult)
        assert len(inv.trace_chain) == 2

    def test_invoke_broken_chain_rejected(self, gw, cr):
        with pytest.raises(ValueError):
            gw.cross_invoke("a", "b", cr, ["NCA-FAKE-1", "NCA-FAKE-2"])

    def test_invoke_empty_chain_rejected(self, gw, cr):
        with pytest.raises(ValueError):
            gw.cross_invoke("a", "b", cr, [])

    def test_invoke_mou_continuity_required(self, gw, cr, nca_placeholder):
        """MOU 连续性：链末端 NCA 必须贡献 MOU（ID79）"""
        from tdca_nca.generator import NCAGenerator
        nca = NCAGenerator()
        # 占位器 record 无 mou_contribution → _nca_get 返回的 NCA 无贡献
        gw.nca = nca
        # 生成一个 mou_contribution=0 的 NCA（内容为空字符串→len=0→mou=0）
        zero = nca.generate("COGNITIVE", 1, {"content": ""})
        # 强制置 0 以模拟无 MOU 贡献
        zero.mou_contribution = 0
        nca.cache[zero.nca_id] = zero
        with pytest.raises(ValueError):
            gw.cross_invoke("a", "b", cr, [zero.nca_id])


class TestCrossVerify:
    """检查项 3：跨库验证封印 + 追溯链"""

    def test_verify_valid_nca(self, gw):
        from tdca_nca.generator import NCAGenerator
        nca = NCAGenerator()
        gw.nca = nca
        a = nca.generate("INSTITUTIONAL", 3, {"x": 1})
        result = gw.cross_verify(a.nca_id, "b")
        assert result["valid"] is True
        assert result["verified_by"] == "b"
        assert result["mou_contribution"] > 0

    def test_verify_missing_nca(self, gw):
        result = gw.cross_verify("NCA-NOPE", "b")
        assert result["valid"] is False
        assert result["reason"] == "NCA 不存在"

    def test_verify_tampered_nca_fails(self, gw):
        from tdca_nca.generator import NCAGenerator
        nca = NCAGenerator()
        gw.nca = nca
        a = nca.generate("INSTITUTIONAL", 3, {"x": 1})
        a.content = {"x": 999}  # 篡改
        nca.cache[a.nca_id] = a
        result = gw.cross_verify(a.nca_id, "b")
        assert result["valid"] is False
        assert "封印" in result["reason"]
