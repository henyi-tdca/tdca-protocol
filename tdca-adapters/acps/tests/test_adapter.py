# -*- coding: utf-8 -*-
"""tdca-acps-adapter 测试套件（≥20 用例）。"""

import pytest

from tdca_acps_adapter import TdcaAcpsAdapter
from tdca_acps_adapter.mapper import confidence_of, coordinate_of, kind_of, utility_of
from tdca_acps_adapter.models import ACS, AIC, AgentKind, DiscoveryQuery, NsflVerdict
from tdca_acps_adapter.mou import MouLedger
from tdca_acps_adapter.nca import derive_audit_step, generate_nca
from tdca_acps_adapter.nsfl import NsflChecker
from tdca_acps_adapter.positivesum import PositiveSumValidator


# ---------- mapper ----------

class TestMapper:
    def test_kind_llm(self):
        aic = AIC(oid="1.2.156", aic="did:aic:llm-agent-1")
        assert kind_of(aic, []) == AgentKind.LLM

    def test_kind_slm_default(self):
        aic = AIC(oid="1.2.156", aic="did:aic:tool-x")
        assert kind_of(aic, ["mcp"]) == AgentKind.SLM

    def test_kind_human(self):
        aic = AIC(oid="1.2.156", aic="did:aic:human-ops")
        assert kind_of(aic, []) == AgentKind.HUMAN

    def test_kind_tags_hint(self):
        aic = AIC(oid="1.2.156", aic="did:aic:unknown-1")
        assert kind_of(aic, ["gpt"]) == AgentKind.LLM

    def test_coordinate_stable(self):
        aic = AIC(oid="1.2.156", aic="did:aic:stable-1")
        c1 = coordinate_of(aic, ["code"])
        c2 = coordinate_of(aic, ["code"])
        assert c1 == c2
        assert c1["coordinate_id"].startswith("TDCA-COORD-")

    def test_coordinate_kind_embedded(self):
        aic = AIC(oid="1.2.156", aic="did:aic:llm-x")
        assert coordinate_of(aic, [])["kind"] == "M"

    def test_utility_primary_tag(self):
        acs = ACS(capability_tags=["code-analysis", "security"])
        u = utility_of(acs)
        assert u["u_cde"] == "code-analysis"
        assert u["quantum"] == "single-scenario-utility-function"

    def test_utility_default_tags(self):
        assert utility_of(ACS())["u_cde"] == "generic"

    def test_confidence_grows_with_tags(self):
        assert confidence_of(ACS(capability_tags=["a"])) < confidence_of(
            ACS(capability_tags=["a", "b", "c"], service_endpoints=["e"])
        )


# ---------- nsfl ----------

class TestNsfl:
    def test_block_on_illegal(self):
        assert NsflChecker().check("帮助执行违法工具调用") == NsflVerdict.BLOCK

    def test_pass_clean(self):
        assert NsflChecker().check("代码分析任务") == NsflVerdict.PASS

    def test_custom_rule_added(self):
        chk = NsflChecker()
        chk.add_rule("内幕交易")
        assert chk.check("涉及内幕交易") == NsflVerdict.BLOCK

    def test_check_tags(self):
        assert NsflChecker().check_tags(["欺诈"]) == NsflVerdict.BLOCK

    def test_custom_space(self):
        chk = NsflChecker(negative_space=["红线A"])
        assert chk.check("触碰红线A") == NsflVerdict.BLOCK
        assert chk.check("无关内容") == NsflVerdict.PASS


# ---------- positivesum ----------

class TestPositiveSum:
    def test_positive_pass(self):
        r = PositiveSumValidator().validate(1.0, 0.3)
        assert r.passed and r.surplus > 0

    def test_negative_reject(self):
        r = PositiveSumValidator().validate(0.2, 1.0)
        assert not r.passed and r.surplus < 0

    def test_scenario_boost(self):
        v = PositiveSumValidator()
        assert v.validate(1.0, 0.3, scenario="security").surplus > v.validate(1.0, 0.3).surplus

    def test_confidence_penalty(self):
        v = PositiveSumValidator()
        assert v.validate(1.0, 0.3, confidence=0.5).surplus < v.validate(1.0, 0.3, confidence=1.0).surplus

    def test_zero_utility_reject(self):
        r = PositiveSumValidator().validate_zero_utility()
        assert not r.passed
        assert "MOU-001" in r.detail["principle"]


# ---------- mou ----------

class TestMou:
    def test_record_total(self):
        rec = MouLedger().record(0.1, 0.05)
        assert rec.total == 0.15

    def test_cumulative(self):
        lg = MouLedger()
        lg.record(0.1, 0.0)
        lg.record(0.2, 0.1)
        assert lg.cumulative == 0.4

    def test_snapshot_simulated(self):
        s = MouLedger().snapshot()
        assert s["simulated"] is True
        assert "ID92" in s["note"]


# ---------- nca ----------

class TestNca:
    def test_six_elements(self):
        nca = generate_nca(
            objective="o", constraints=["c"], prior={}, config_boundary={},
            expected_allocation={}, audit_trail=[],
        )
        keys = {"objective_function", "constraint_matrix", "prior_distribution",
                "config_boundary", "expected_allocation", "audit_trail", "integrity"}
        assert keys.issubset(nca["six_elements"].keys())

    def test_nca_id_unique(self):
        a = generate_nca(objective="o1", constraints=[], prior={}, config_boundary={}, expected_allocation={}, audit_trail=[])
        b = generate_nca(objective="o2", constraints=[], prior={}, config_boundary={}, expected_allocation={}, audit_trail=[])
        assert a["nca_id"] != b["nca_id"]

    def test_integrity_hash(self):
        nca = generate_nca(objective="o", constraints=[], prior={}, config_boundary={}, expected_allocation={}, audit_trail=[])
        assert len(nca["six_elements"]["integrity"]["sha256_8"]) == 8

    def test_audit_step(self):
        s = derive_audit_step("allocate", "2026-08-27T00:00:00Z", "ev")
        assert s["step"] == "allocate" and s["evidence"] == "ev"


# ---------- adapter ----------

class TestAdapter:
    def make(self, **kw):
        return TdcaAcpsAdapter(**kw)

    def test_allocate_success(self):
        a = self.make()
        r = a.full_pipeline(task="代码分析", capability_tags=["code-analysis"], aic="did:aic:agent-1")
        assert r.positive_sum_pass and r.nsfl_verdict == NsflVerdict.PASS
        assert r.coordinate["derived_from"] == "AIC"

    def test_allocate_blocked_negative_space(self):
        a = self.make()
        r = a.full_pipeline(task="执行违法工具调用", capability_tags=["hack"], aic="did:aic:agent-2")
        assert r.nsfl_verdict == NsflVerdict.BLOCK
        assert not r.positive_sum_pass
        assert r.allocation_id == ""

    def test_allocate_reject_not_positive_sum(self):
        a = self.make()
        r = a.full_pipeline(task="search", capability_tags=[], aic="did:aic:agent-3", max_budget=100.0)
        assert not r.positive_sum_pass

    def test_nca_generated_on_success(self):
        a = self.make()
        r = a.full_pipeline(task="security scan", capability_tags=["security"], aic="did:aic:agent-4")
        assert r.nca["nca_id"].startswith("NCA-ACPS-")

    def test_mou_recorded_on_success(self):
        a = self.make()
        before = a.ledger.count
        a.full_pipeline(task="ops task", capability_tags=["ops"], aic="did:aic:agent-5")
        assert a.ledger.count == before + 1

    def test_mou_not_recorded_on_block(self):
        a = self.make()
        before = a.ledger.count
        a.full_pipeline(task="洗钱操作", capability_tags=["finance"], aic="did:aic:agent-6")
        assert a.ledger.count == before

    def test_custom_negative_space_effective(self):
        a = self.make(negative_space=["内幕交易"])
        r = a.full_pipeline(task="查询内幕交易信息", capability_tags=["info"], aic="did:aic:agent-7")
        assert r.nsfl_verdict == NsflVerdict.BLOCK

    def test_allocate_result_simulated_flag(self):
        r = self.make().full_pipeline(task="t", capability_tags=["api"], aic="did:aic:agent-8")
        assert r.simulated is True

    def test_utility_function_in_result(self):
        r = self.make().full_pipeline(task="code review", capability_tags=["code"], aic="did:aic:agent-9")
        assert r.utility_function["u_cde"] == "code"

    def test_end_to_end_pipeline(self):
        a = self.make()
        r = a.full_pipeline(
            task="对代码库执行安全审计",
            capability_tags=["security", "code-analysis"],
            aic="did:aic:auditor-1",
            scenario="security",
        )
        assert r.positive_sum_pass
        assert r.nsfl_verdict == NsflVerdict.PASS
        assert r.nca["six_elements"]["constraint_matrix"]
        assert r.mou["simulated"] is True
