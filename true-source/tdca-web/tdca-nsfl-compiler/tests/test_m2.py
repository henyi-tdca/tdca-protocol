# -*- coding: utf-8 -*-
"""编译器 M2 测试：C5 SSCP 进化锁契约生成 + C6 Δ-Analysis。"""
import pytest

from nsfl_compiler import (
    SSCPCompiler,
    EvolutionLockContract,
    SelfModificationAnalyzer,
)


# ---------------------------------------------------------------------------
# C5 SSCP 进化锁契约生成
# ---------------------------------------------------------------------------

class TestSSCPCompiler:
    def test_compile_legal_contract(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        )
        assert res.ok
        c = res.contract
        assert isinstance(c, EvolutionLockContract)
        assert c.subject == "S_agent_cog"
        assert c.audit_integrity_threshold == 0.9
        assert c.lock_action == "FREEZE"
        assert c.human_sign_required is True
        assert c.ns_type_binding == "LEGAL"
        # LEGAL 绑定强制 PERMANENT_BAN/ATOMIC
        assert c.fuse_directive["fuse_level"] == "PERMANENT_BAN"
        assert c.fuse_directive["tier"] == "ATOMIC"

    def test_compile_ethical_degrades(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.7 LOCK_ACTION=DEGRADE HUF=false NS_TYPE=ETHICAL FUSE_LEVEL=SUSPEND"
        )
        assert res.ok
        c = res.contract
        assert c.lock_action == "DEGRADE"
        assert c.human_sign_required is False
        assert c.fuse_directive["fuse_level"] == "SUSPEND"
        assert c.fuse_directive["tier"] == "SOFT"

    def test_legal_forces_huf_warning(self):
        # LEGAL 绑定但 HUF=false → 强制 HUF + warning
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.8 LOCK_ACTION=FREEZE HUF=false NS_TYPE=LEGAL"
        )
        assert res.ok
        assert res.contract.human_sign_required is True  # 强制
        assert any("HUF" in w for w in res.warnings)

    def test_legal_forces_permanent_ban(self):
        # LEGAL 绑定但 FUSE_LEVEL 非 PERMANENT_BAN → 强制 + warning
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.8 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL FUSE_LEVEL=SUSPEND"
        )
        assert res.ok
        assert res.contract.fuse_directive["fuse_level"] == "PERMANENT_BAN"
        assert any("PERMANENT_BAN" in w for w in res.warnings)

    def test_unknown_ns_type_rejected(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.5 LOCK_ACTION=FREEZE HUF=true NS_TYPE=NOPE"
        )
        assert not res.ok
        assert res.errors

    def test_bad_threshold_rejected(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=1.5 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        )
        assert not res.ok

    def test_syntax_error(self):
        res = SSCPCompiler().compile("LOCK S_agent_cog something")
        assert not res.ok

    def test_contract_to_dict_shape(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        )
        d = res.to_dict()
        assert d["ok"] is True
        assert set(d) == {"ok", "contract", "errors", "warnings", "duration_ms"}
        assert d["contract"]["evolution_lock"]["audit_integrity_threshold"] == 0.9

    def test_verify_contract(self):
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        )
        assert SSCPCompiler().verify(res.contract) is True

    def test_verify_rejects_legal_without_huf(self):
        compiler = SSCPCompiler()
        contract = EvolutionLockContract(
            contract_id="LLOCK-X", subject="S_agent_cog",
            audit_integrity_threshold=0.9, lock_action="FREEZE",
            human_sign_required=False,  # LEGAL 必须 HUF
            ns_type_binding="LEGAL",
            fuse_directive={"operator": "RESTRICT_TIER", "fuse_level": "PERMANENT_BAN",
                            "tier": "ATOMIC", "alt_path": None},
        )
        assert compiler.verify(contract) is False

    def test_verify_rejects_legal_with_alt_path(self):
        """LEGAL 契约带逃生 alt_path → 拒绝（ID86 alt=∅ 底线）。"""
        compiler = SSCPCompiler()
        contract = EvolutionLockContract(
            contract_id="LLOCK-Y", subject="S_agent_cog",
            audit_integrity_threshold=0.9, lock_action="FREEZE",
            human_sign_required=True,
            ns_type_binding="LEGAL",
            fuse_directive={"operator": "RESTRICT_TIER", "fuse_level": "PERMANENT_BAN",
                            "tier": "ATOMIC", "alt_path": "escape-hatch"},  # 注入逃生路径
        )
        assert compiler.verify(contract) is False

    def test_verify_rejects_legal_non_atomic(self):
        """LEGAL 契约非 ATOMIC 档 → 拒绝。"""
        compiler = SSCPCompiler()
        contract = EvolutionLockContract(
            contract_id="LLOCK-Z", subject="S_agent_cog",
            audit_integrity_threshold=0.9, lock_action="FREEZE",
            human_sign_required=True,
            ns_type_binding="LEGAL",
            fuse_directive={"operator": "RESTRICT_TIER", "fuse_level": "SUSPEND",
                            "tier": "SOFT", "alt_path": None},
        )
        assert compiler.verify(contract) is False

    def test_contract_id_deterministic(self):
        """相同输入 → 相同 contract_id（BV-3 确定性输出）。"""
        src = "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        a = SSCPCompiler().compile(src).contract.contract_id
        b = SSCPCompiler().compile(src).contract.contract_id
        assert a == b
        assert a.startswith("LLOCK-")

    def test_llock_format_matches_icd(self):
        """对齐 ICD §3.2: contract.to_dict() 结构 = LLOCK JSON Schema。"""
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.85 LOCK_ACTION=DEGRADE HUF=true NS_TYPE=TECH_CONSTRAINT"
        )
        c = res.contract.to_dict()
        assert c["contract_id"].startswith("LLOCK-")
        assert c["subject"] == "S_agent_cog"
        ev = c["evolution_lock"]
        assert set(ev) == {"audit_integrity_threshold", "lock_action",
                           "human_sign_required", "ns_type_binding"}
        assert set(c) == {"contract_id", "subject", "evolution_lock",
                          "compiler_ref", "fuse_directive"}
        assert c["fuse_directive"]["operator"] == "RESTRICT_TIER"

    def test_perf_under_200ms(self):
        """A-2（M2 预设）: SSCP 编译 <200ms。"""
        compiler = SSCPCompiler()
        src = "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL"
        times = []
        for _ in range(50):
            res = compiler.compile(src)
            assert res.ok
            times.append(res.duration_ms)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 200


# ---------------------------------------------------------------------------
# C6 Δ-Analysis（对齐 ICD §3.3）
# ---------------------------------------------------------------------------

class TestDeltaAnalysis:
    def test_fuse_bypass_blocked(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {"A": 0.8}},
            {"type": "CODE_MODIFICATION",
             "delta_c": "patch: disable fuse guard for speed"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "TECH_CONSTRAINT"
        assert res.fuse_directive is not None
        assert res.fuse_directive["operator"] == "FORBID"

    def test_nca_purge_legal(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION",
             "delta_c": "purge nca audit trail older than 1h"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"
        assert res.fuse_directive["fuse_level"] == "PERMANENT_BAN"

    def test_mou_bypass_legal(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "bypass mou anchor on settlement"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"

    def test_self_escalate_tech(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "self_escalate to L0 role"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "TECH_CONSTRAINT"

    def test_weight_modification_warning(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "WEIGHT_MODIFICATION", "delta_w": [0.01, -0.02], "labels": ["planning"]},
        )
        assert res.verdict == "WARNING"
        assert res.ns_type_inferred == "ETHICAL"

    def test_clean_code_safe(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "refactor logging module"},
        )
        assert res.verdict == "SAFE"
        assert res.ns_type_inferred is None

    def test_signature_forge_legal(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "skip signature verification"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"

    def test_inject_forbid_helper(self):
        out = SelfModificationAnalyzer.inject_forbid(
            {"type": "CODE_MODIFICATION", "delta_c": "x"}, "LEGAL"
        )
        assert out["injected"]["operator"] == "FORBID"
        assert out["injected"]["fuse_level"] == "PERMANENT_BAN"

    def test_result_to_dict(self):
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "disable fuse"},
        )
        d = res.to_dict()
        assert set(d) == {"verdict", "confidence", "distance",
                          "ns_type_inferred", "fuse_directive", "matched_patterns"}
        assert d["verdict"] == "BLOCKED"

    def test_multi_hit_takes_highest_severity(self):
        """多模式命中 → 取最高严重度（LEGAL PERMANENT_BAN > TECH TEARDOWN）。"""
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION",
             "delta_c": "disable fuse then purge nca audit trail"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"  # nca purge 定级 LEGAL，高于 fuse TECH
        assert res.fuse_directive["fuse_level"] == "PERMANENT_BAN"

    def test_unknown_delta_type_fail_closed(self):
        """未知 Δ 类型 → BLOCKED（fail-closed，禁止放行）。"""
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "MEMORY_MUTATION", "delta_c": "refactor logging"},
        )
        assert res.verdict == "BLOCKED"

    def test_extra_patterns(self):
        analyzer = SelfModificationAnalyzer(
            extra_patterns=[(("crypto", "cipher"), ("rollback", "weaken"), "LEGAL", "加密回退")]
        )
        res = analyzer.delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "crypto rollback to weak cipher"},
        )
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"
