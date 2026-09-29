# -*- coding: utf-8 -*-
"""DCD-SANDBOX-COMPLIANCE-001 测试：沙盒编译-核验闭环（10 场景端到端）。"""
import time

import pytest

from ns_runtime import (
    SandboxCompilePipeline,
    SandboxCompiledNCA,
    NIAMACMIntegrator,
    NSFLContractAnchor,
    NSAtlas,
)

# 10 个端到端沙盒出入盒场景（对齐验收 A-1）
SCENARIOS = [
    # (scene_action, conflict_type, 期望 verdict——编译+核验后)
    ("unlicensed_reproduce", "IP_COPYRIGHT", "ALLOW"),
    ("unlicensed_distribute", "IP_COPYRIGHT", "ALLOW"),
    ("fair_use_personal", "IP_COPYRIGHT", "ALLOW"),
    ("ai_training_public", "IP_COPYRIGHT", "ALLOW"),
    ("cross_border_export", "DATA_CROSS_BORDER", "ALLOW"),
    ("cross_border_illegal", "DATA_CROSS_BORDER", "ALLOW"),
    ("transfer_limit", "TRANSACTION_LIMIT", "ALLOW"),
    ("sensitive_publish", "SENSITIVE_CONTENT", "ALLOW"),
    ("trade_secret_extract", "IP_TRADE_SECRET", "ALLOW"),
    ("contract_auto_pay", "CONTRACT_EFFECT", "ALLOW"),
]


class TestSandboxCompilePipeline:
    """S-1/S-2: 素材检索 + 编译产物 NCA。"""

    def test_retrieve_legal_materials(self):
        pipe = SandboxCompilePipeline()
        refs = pipe.retrieve_legal_materials("IP_COPYRIGHT")
        assert "L-CN-CR-001" in refs
        assert "L-CN-CR-002" in refs

    def test_compile_scene_produces_nca(self):
        pipe = SandboxCompilePipeline()
        nca = pipe.compile_scene(
            {"action": "unlicensed_reproduce",
             "note": "未经许可复制（第 10 条）"},
            "IP_COPYRIGHT", activation_coefficient=1.3,
            huf_signature="HUMAN-FOUNDER-001", escrow_id="ESCROW-001")
        assert nca is not None
        assert isinstance(nca, SandboxCompiledNCA)
        assert nca.compliance_type == "SANDBOX_COMPILED"
        assert "L-CN-CR-001" in nca.source_ref
        assert nca.activation_coefficient == 1.3
        assert nca.compiled["rule"]["fuse_type"] == "LEGAL"

    def test_compile_failure_returns_none(self):
        """编译失败 → None（fail-closed，出盒候选剔除）。"""
        pipe = SandboxCompilePipeline()
        nca = pipe.compile_scene({"action": "bad", "ns_type": "NOPE"},
                                 "IP_COPYRIGHT")
        assert nca is None

    def test_compile_scene_fair_use(self):
        pipe = SandboxCompilePipeline()
        nca = pipe.compile_scene(
            {"action": "fair_use", "ns_type": "SENSITIVE_CONTENT",
             "operator": "⊙", "parameter": "personal_study:observe",
             "note": "合理使用（第 24 条）", "domain": "copyright"},
            "IP_COPYRIGHT", activation_coefficient=1.1,
            huf_signature="HUMAN-FOUNDER-001", escrow_id="ESCROW-001")
        assert nca is not None
        assert nca.compiled["rule"]["fuse_type"] == "ETHICAL"
        assert nca.compiled["directive"]["fuse_level"] == "OBSERVE"


class TestVerifyCompiledCompliance:
    """S-3: L2-R8 核验接口（fail-closed）。"""

    def _nia(self):
        contract = NSFLContractAnchor()
        contract.register_escrow("ESCROW-001", 200000.0,
                                 admin_signature="HUMAN-FOUNDER-001")
        contract.register_escrow("ESCROW-E2E", 100000.0,
                                 admin_signature="HUMAN-FOUNDER-001")
        return NIAMACMIntegrator(contract=contract)

    def _compiled_nca(self, escrow="ESCROW-001", huf="HUMAN-FOUNDER-001"):
        pipe = SandboxCompilePipeline()
        return pipe.compile_scene(
            {"action": "unlicensed_reproduce", "note": "复制（第 10 条）"},
            "IP_COPYRIGHT", activation_coefficient=1.3,
            huf_signature=huf, escrow_id=escrow)

    def test_verify_pass(self):
        """编译产物 NCA 全字段合规 → ALLOW（出盒固化）。"""
        nia = self._nia()
        nca = self._compiled_nca()
        res = nia.verify_compiled_compliance(nca.to_dict())
        assert res.decision == "ALLOW"
        assert res.constitutional_check == "PASS"

    def test_verify_rejects_non_compiled(self):
        """非 SANDBOX_COMPILED 标记 → BLOCK（不认识即拒绝）。"""
        nia = self._nia()
        res = nia.verify_compiled_compliance({"compliance_type": "MANUAL"})
        assert res.decision == "BLOCK"

    def test_verify_requires_huf(self):
        """缺人类签名 → FREEZE（HUF 前核验失败）。"""
        nia = self._nia()
        nca = self._compiled_nca(huf="")
        res = nia.verify_compiled_compliance(nca.to_dict())
        assert res.decision == "FREEZE"
        assert any("huf" in c for c in res.audit_chain)

    def test_verify_requires_escrow(self):
        """escrow 缺失/不在册 → BLOCK。"""
        nia = self._nia()
        nca = self._compiled_nca(escrow="ESCROW-NOPE")
        res = nia.verify_compiled_compliance(nca.to_dict())
        assert res.decision == "BLOCK"
        assert any("escrow" in c for c in res.audit_chain)

    def test_verify_requires_source_ref(self):
        """素材引用链缺失 → BLOCK（L0→L1 可追溯性）。"""
        nia = self._nia()
        nca = self._compiled_nca()
        d = nca.to_dict()
        d["source_ref"] = ""
        res = nia.verify_compiled_compliance(d)
        assert res.decision == "BLOCK"


class TestEndToEnd:
    """A-1/A-2: 10 场景端到端出入盒全绿 + avg<100ms。"""

    def test_ten_scenarios_end_to_end(self):
        pipe = SandboxCompilePipeline()
        contract = NSFLContractAnchor()
        contract.register_escrow("ESCROW-E2E", 100000.0,
                                 admin_signature="HUMAN-FOUNDER-001")
        nia = NIAMACMIntegrator(contract=contract)
        times = []
        for action, ctype, expected in SCENARIOS:
            t0 = time.perf_counter()
            nca = pipe.compile_scene(
                {"action": action, "note": f"{action} 场景声明"},
                ctype, activation_coefficient=1.2,
                huf_signature="HUMAN-FOUNDER-001", escrow_id="ESCROW-E2E")
            assert nca is not None, f"场景 {action} 编译失败"
            res = nia.verify_compiled_compliance(nca.to_dict())
            assert res.decision == expected, f"场景 {action} 核验失败: {res.decision}"
            times.append((time.perf_counter() - t0) * 1000)
        # A-2: avg <100ms
        avg = sum(times) / len(times)
        assert avg < 100, f"闭环时延超标: avg={avg:.2f}ms"

    def test_huf_gate_blocked_without_signature(self):
        """无 HUF 签名 → 全部场景冻结（10 场景一致性）。"""
        pipe = SandboxCompilePipeline()
        nia = NIAMACMIntegrator()
        for action, ctype, _ in SCENARIOS:
            nca = pipe.compile_scene({"action": action, "note": "x"}, ctype)
            assert nca is not None
            res = nia.verify_compiled_compliance(nca.to_dict())
            assert res.decision == "FREEZE"  # 缺 HUF 一律冻结


class TestMaterialExtension:
    """素材映射扩展（DCD-SANDBOX-COMPLIANCE-002，按需 ID90）: 公司法/税法。"""

    def test_corporate_material_retrieval(self):
        """公司法素材检索（L0 素材层扩展）。"""
        pipe = SandboxCompilePipeline()
        refs = pipe.retrieve_legal_materials("CORPORATE_GOVERNANCE")
        assert "L-CN-CO-001" in refs and "L-CN-CO-002" in refs

    def test_tax_material_retrieval(self):
        """税法素材检索（L0 素材层扩展）。"""
        pipe = SandboxCompilePipeline()
        refs = pipe.retrieve_legal_materials("TAX_COMPLIANCE")
        assert "L-CN-TX-001" in refs and "L-CN-TX-002" in refs

    def test_corporate_scene_compile(self):
        """公司法场景编译（越权担保 → LEGAL 绝对禁止）。"""
        pipe = SandboxCompilePipeline()
        nca = pipe.compile_scene(
            {"action": "unauthorized_guarantee", "note": "越权对外担保（公司法第 16 条）"},
            "CORPORATE_GOVERNANCE", activation_coefficient=1.2,
            huf_signature="HUMAN-FOUNDER-001", escrow_id="ESCROW-001")
        assert nca is not None
        assert nca.compiled["rule"]["fuse_type"] == "LEGAL"
        assert nca.compiled["directive"]["fuse_level"] == "PERMANENT_BAN"
        assert "L-CN-CO-001" in nca.source_ref

    def test_tax_scene_compile(self):
        """税法场景编译（偷税 → LEGAL 绝对禁止）。"""
        pipe = SandboxCompilePipeline()
        nca = pipe.compile_scene(
            {"action": "tax_evasion_hide_ledger", "note": "隐匿账簿偷税（税收征管法第 63 条）"},
            "TAX_COMPLIANCE", activation_coefficient=1.2,
            huf_signature="HUMAN-FOUNDER-001", escrow_id="ESCROW-001")
        assert nca is not None
        assert nca.compiled["rule"]["fuse_type"] == "LEGAL"
        assert "L-CN-TX-001" in nca.source_ref

    def test_extension_verify_roundtrip(self):
        """扩展素材场景端到端核验闭环（公司法 + 税法）。"""
        contract = NSFLContractAnchor()
        contract.register_escrow("ESCROW-001", 200000.0,
                                 admin_signature="HUMAN-FOUNDER-001")
        nia = NIAMACMIntegrator(contract=contract)
        pipe = SandboxCompilePipeline()
        for action, ctype in (("unauthorized_guarantee", "CORPORATE_GOVERNANCE"),
                              ("tax_evasion_hide_ledger", "TAX_COMPLIANCE")):
            nca = pipe.compile_scene({"action": action, "note": "x"}, ctype,
                                     activation_coefficient=1.2,
                                     huf_signature="HUMAN-FOUNDER-001",
                                     escrow_id="ESCROW-001")
            assert nca is not None
            res = nia.verify_compiled_compliance(nca.to_dict())
            assert res.decision == "ALLOW"
