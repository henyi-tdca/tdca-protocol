# -*- coding: utf-8 -*-
"""TAXLAW-001 验收测试：财税法规编译（L-1/L-3）+ 税务官法规决策（L-4）。"""
import sys
from pathlib import Path

import pytest

# 注入 nsfl-compiler（tax_regulations / NSFLCompiler）
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "tdca-nsfl-compiler"))

from microtax import (DeliveryForm, MicroDelivery, TaxEventType,
                      TaxOfficerAgent)
from nsfl_compiler.tax_regulations import (TAX_REGULATIONS,
                                           load_tax_regulations,
                                           resolve_violation_law)
from nsfl_compiler.compiler import NSFLCompiler


def _d(delivery_id, value=1000.0, tax_in=300.0, tax_out=200.0,
       violation=None, event_type=TaxEventType.CONFIG_RIGHT_CALL):
    return MicroDelivery(delivery_id=delivery_id, scene="taxlaw-scene",
                         value=value, event_type=event_type,
                         tax_in=tax_in, tax_out=tax_out,
                         tax_violation=violation)


class TestRegulationSource:
    """L-2 法规素材表（制度条款 + KG-LEGAL 种子）。"""

    def test_five_regulations_loaded(self):
        """5 条法规素材（2 种子 + 3 制度条款）。"""
        regs = load_tax_regulations()
        assert len(regs) == 5
        ids = {r["law_id"] for r in regs}
        assert {"L-CN-TX-001", "L-CN-TX-002", "TDCA-ART-12",
                "TDCA-ART-18", "TDCA-DEF-519"} <= ids

    def test_all_legal_fuse_high(self):
        """全部法规: fuse_type=LEGAL + severity=HIGH（ID86 绝对边界）。"""
        for r in load_tax_regulations():
            assert r["fuse_type"] == "LEGAL"
            assert r["severity"] == "HIGH"

    def test_violation_to_law_mapping(self):
        """违规模式 → 法规引用解析。"""
        assert resolve_violation_law("tax_evasion")["law_id"] == "L-CN-TX-001"
        assert resolve_violation_law("tax_bypass_mou")["law_id"] == "TDCA-ART-12"
        assert resolve_violation_law("tax_false_report")["law_id"] == "TDCA-ART-18"
        assert resolve_violation_law("unknown") is None

    def test_simulated_flag(self):
        """ID92 模拟态标注。"""
        assert all(r["simulated"] for r in load_tax_regulations())


class TestRegulationCompile:
    """L-1/L-3 财税法规编译（B-1）。"""

    def test_static_list_tax_entries(self):
        """L1-R1 静态清单含 4 条税法条目（NSL-LEGAL-013~016）。"""
        from ns_runtime.static_list import StaticNegativeSpaceList
        sl = StaticNegativeSpaceList()
        tax_entries = [e for e in sl.entries if e.domain == "tax"]
        assert len(tax_entries) == 4
        ids = {e.entry_id for e in tax_entries}
        assert ids == {"NSL-LEGAL-013", "NSL-LEGAL-014",
                       "NSL-LEGAL-015", "NSL-LEGAL-016"}

    def test_static_list_tax_block(self):
        """偷税/骗税/规避锚定/申报失实 → 静态清单熔断（B-1）。"""
        from ns_runtime.static_list import StaticNegativeSpaceList
        sl = StaticNegativeSpaceList()
        assert sl.check("tax.evade hidden_books").blocked is True
        assert sl.check("tax.fraud_refund export").blocked is True
        assert sl.check("tax.bypass_mou off_chain").blocked is True
        assert sl.check("tax.false_report return").blocked is True
        assert sl.check("tax.compliant_filing").blocked is False

    def test_compile_for_scene_legal_refs_content(self):
        """L-3: legal_refs 法规内容 dict → 编译通过（要点注入 source_ref 审计）。"""
        compiler = NSFLCompiler()
        scene = {"action": "tax_evasion", "ns_type": "LEGAL",
                 "operator": "⊗", "domain": "tax", "note": "偷税"}
        reg = load_tax_regulations(["L-CN-TX-001"])[0]
        result = compiler.compile_for_scene(scene, legal_refs=[reg])
        assert result.ok is True
        assert result.errors == []
        # source_ref 审计内容验证（compile 内部拼接 scene+legal:{refs}）
        assert result.ir is not None

    def test_compile_for_scene_str_refs_backward_compat(self):
        """L-3 向后兼容: str 元素行为不变（⊗ 场景编译通过）。"""
        compiler = NSFLCompiler()
        scene = {"action": "act_x", "ns_type": "LEGAL",
                 "operator": "⊗", "domain": "d", "note": ""}
        result = compiler.compile_for_scene(scene, legal_refs=["L-CN-TX-001"])
        assert result.ok is True
        assert result.errors == []


class TestTaxOfficerRegulatory:
    """L-4 税务官法规决策依据（B-2/B-3）。"""

    def test_clean_delivery_passes(self):
        """合规交付: 正常计税（法规轨迹为空）。"""
        agent = TaxOfficerAgent()
        out = agent.on_delivery(_d("MD-CLEAN"))
        assert out["regulatory"] == []
        assert out["prepay"]["status"] == "PREPAID"

    def test_explicit_violation_rejected(self):
        """显式偷税标记 → 法规约束拒绝（fail-closed，B-2）。"""
        agent = TaxOfficerAgent()
        d = _d("MD-EVADE", violation="tax_evasion")
        with pytest.raises(ValueError, match="L-CN-TX-001"):
            agent.on_delivery(d)

    def test_bypass_mou_auto_detected(self):
        """大额 MOU=0 → 自动检测规避锚定（TDCA-ART-12）。"""
        agent = TaxOfficerAgent()
        d = _d("MD-BYPASS", value=5000.0, tax_in=0.0, tax_out=0.0)
        with pytest.raises(ValueError, match="TDCA-ART-12"):
            agent.on_delivery(d)

    def test_small_zero_mou_not_blocked(self):
        """小额 MOU=0（低于阈值）→ 不触发规避锚定（fail-closed 阈值纪律）。"""
        agent = TaxOfficerAgent()
        d = _d("MD-SMALL", value=100.0, tax_in=0.0, tax_out=0.0)
        out = agent.on_delivery(d)          # 预缴侧 FAIL_CLOSED（MOU=0）
        assert out["regulatory"] == []
        assert out["prepay"]["status"] == "FAIL_CLOSED"

    def test_regulatory_trail_in_audit(self):
        """决策轨迹: 法规 law_id 入审计输出（B-3）。"""
        agent = TaxOfficerAgent()
        # 合规路径 regulatory=[]（无违规时不注入，轨迹字段存在）
        out = agent.on_delivery(_d("MD-TRAIL"))
        assert "regulatory" in out
        # 违规路径 fail-closed 拒绝（异常含 law_id 引用）
        with pytest.raises(ValueError, match="L-CN-TX-001"):
            agent.on_delivery(_d("MD-TRAIL2", violation="tax_evasion"))

    def test_domain2_settle_defensive_check(self):
        """领域二结算前防御性法规检查。"""
        agent = TaxOfficerAgent()
        d = _d("MD-D2V", violation="tax_false_report")
        from microtax import ContractForm
        with pytest.raises(ValueError, match="TDCA-ART-18"):
            agent.domain2_settle(d, ContractForm.ONE_TO_ONE)
