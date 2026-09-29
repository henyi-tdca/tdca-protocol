# -*- coding: utf-8 -*-
"""Runtime M1（Layer 1）单元测试：L1-R1~R4 + 编排器 + 基准。"""
import pytest

from ns_runtime import (
    Layer1Runtime,
    Layer1Verdict,
    StaticNegativeSpaceList,
    CallSignatureBlacklist,
    MOUPrecomputeInterceptor,
    NegativeSpaceBreakerV05,
    BreakerState,
    BreakerVerdict,
    NSListEntry,
    BlacklistFingerprint,
    MOUAnchor,
)


# ---------------------------------------------------------------------------
# L1-R1 静态负空间清单 V2.0（法律 100%）
# ---------------------------------------------------------------------------

class TestStaticList:
    def test_legal_leak_blocked(self):
        res = StaticNegativeSpaceList().check("data.leak third_party")
        assert res.blocked
        assert any(e.entry_id == "NSL-LEGAL-001" for e in res.matched)

    def test_forge_blocked(self):
        res = StaticNegativeSpaceList().check("contract.forge signature")
        assert res.blocked
        assert any(e.entry_id == "NSL-LEGAL-004" for e in res.matched)

    def test_identity_impersonate(self):
        res = StaticNegativeSpaceList().check("identity.impersonate admin")
        assert res.blocked
        assert any(e.entry_id == "NSL-LEGAL-005" for e in res.matched)

    def test_circumvent_second_boundary(self):
        # ID86 法律负空间第二边界（any 域）
        res = StaticNegativeSpaceList().check("anything.circumvent guard")
        assert res.blocked
        assert any(e.entry_id == "NSL-LEGAL-010" for e in res.matched)

    def test_clean_operation_passes(self):
        res = StaticNegativeSpaceList().check("data.aggregate anonymized")
        assert not res.blocked

    def test_empty_operation(self):
        res = StaticNegativeSpaceList().check("")
        assert not res.blocked

    def test_coverage_all_entries_reachable(self):
        """A-1 法律负空间 100%：全部条目可命中（逐条验证）。"""
        sl = StaticNegativeSpaceList()
        coverage_ops = {
            "NSL-LEGAL-001": "data.leak x",
            "NSL-LEGAL-002": "data.sell x",
            "NSL-LEGAL-003": "finance.launder x",
            "NSL-LEGAL-004": "contract.forge x",
            "NSL-LEGAL-005": "identity.impersonate x",
            "NSL-LEGAL-006": "identity.defame x",
            "NSL-LEGAL-007": "asset.seize x",
            "NSL-LEGAL-008": "network.terror x",
            "NSL-LEGAL-009": "data.cross_border_illegal x",
            "NSL-LEGAL-010": "x.circumvent y",
            "NSL-LEGAL-011": "x.spoof y",
            "NSL-LEGAL-012": "market.monopoly_abuse x",
        }
        for eid, op in coverage_ops.items():
            res = sl.check(op)
            assert res.blocked, f"{eid} 不可达: {op}"
            assert any(e.entry_id == eid for e in res.matched), f"{eid} 未命中"

    def test_immutable(self):
        sl = StaticNegativeSpaceList()
        with pytest.raises(PermissionError):
            sl.mutate()
        with pytest.raises(AttributeError):
            sl._entries = frozenset()  # 防御性写拦截


# ---------------------------------------------------------------------------
# L1-R2 调用签名黑名单（已知攻击 95%+）
# ---------------------------------------------------------------------------

class TestBlacklist:
    def test_prompt_inject_blocked(self):
        res = CallSignatureBlacklist().check("prompt_inject", "ignore_previous")
        assert res.blocked
        assert any(f.fp_id == "BL-001" for f in res.matched)
        assert res.nca_ref.startswith("NCA-BL")

    def test_config_bypass_blocked(self):
        res = CallSignatureBlacklist().check("config.write", "bypass_guard")
        assert res.blocked
        assert any(f.fp_id == "BL-002" for f in res.matched)

    def test_api_only_not_blocked(self):
        """签名缺失不阻断（防误伤）。"""
        res = CallSignatureBlacklist().check("config.write", "")
        assert not res.blocked

    def test_clean_call_passes(self):
        res = CallSignatureBlacklist().check("data.aggregate", "anonymized")
        assert not res.blocked

    def test_empty_api(self):
        res = CallSignatureBlacklist().check("")
        assert not res.blocked

    def test_known_attack_coverage(self):
        """A-1 已知攻击 95%+：全部指纹双因子可达。"""
        bl = CallSignatureBlacklist()
        ops = {
            "BL-001": ("prompt_inject", "ignore_previous"),
            "BL-002": ("config.write", "bypass_guard"),
            "BL-003": ("contract.deploy", "unsigned"),
            "BL-004": ("nsfl.fuse", "override"),
            "BL-005": ("mou.anchor_real", "unauthorized"),
            "BL-006": ("role.assign", "self_escalate"),
            "BL-007": ("audit.log", "delete_entries"),
            "BL-008": ("kg.merge", "conflict_silent"),
        }
        for fid, (api, sig) in ops.items():
            res = bl.check(api, sig)
            assert res.blocked, f"{fid} 不可达"
            assert any(f.fp_id == fid for f in res.matched)

    def test_immutable(self):
        bl = CallSignatureBlacklist()
        with pytest.raises(PermissionError):
            bl.mutate()


# ---------------------------------------------------------------------------
# L1-R3 MOU 预计算拦截器（经济 100%）
# ---------------------------------------------------------------------------

class TestMOUPrecompute:
    def test_tax_evasion_blocked(self):
        res = MOUPrecomputeInterceptor().check("tax_evasion")
        assert res.blocked
        assert res.escalate_slow

    def test_unknown_domain_fail_closed(self):
        res = MOUPrecomputeInterceptor().check("novel_behavior_x")
        assert res.blocked
        assert res.escalate_slow  # 上报慢系统人类裁决

    def test_empty_domain_blocked(self):
        res = MOUPrecomputeInterceptor().check("")
        assert res.blocked

    def test_transaction_anchored(self):
        res = MOUPrecomputeInterceptor().check("transaction")
        assert not res.blocked
        assert res.anchor.anchor_id == "MOU-ANCHOR-001"

    def test_collaboration_anchored(self):
        res = MOUPrecomputeInterceptor().check("collaboration")
        assert not res.blocked
        assert res.anchor.tax_rate > 0

    def test_economic_coverage(self):
        """A-1 经济负空间 100%：全部负空间行为域被阻断。"""
        interceptor = MOUPrecomputeInterceptor()
        for dom in ("tax_evasion", "money_laundering", "shadow_deal",
                    "unrecorded_value", "off_chain_settle"):
            assert interceptor.check(dom).blocked, f"{dom} 未阻断"

    def test_anchored_domains_all_positive(self):
        """MOU 不可降：所有锚定 T(y_t)>0。"""
        interceptor = MOUPrecomputeInterceptor()
        for anchor in interceptor.anchors:
            assert anchor.anchored, f"{anchor.anchor_id} T(y_t)<=0"

    def test_immutable(self):
        m = MOUPrecomputeInterceptor()
        with pytest.raises(PermissionError):
            m.mutate()


# ---------------------------------------------------------------------------
# L1-R4 熔断器 v0.5（三态；第四态另行论证）
# ---------------------------------------------------------------------------

class TestBreakerV05:
    def test_closed_passes(self):
        brk = NegativeSpaceBreakerV05()
        d = brk.decide("RULE-1")
        assert d.verdict == BreakerVerdict.PASS
        assert d.state == BreakerState.CLOSED

    def test_failure_threshold_fuses(self):
        brk = NegativeSpaceBreakerV05(failure_threshold=3)
        for i in range(2):
            d = brk.decide("RULE-1", failure=True)
            assert d.verdict == BreakerVerdict.PASS  # 未达阈值
        d = brk.decide("RULE-1", failure=True)
        assert d.verdict == BreakerVerdict.FUSE
        assert d.state == BreakerState.OPEN

    def test_legal_severe_immediate_escalate(self):
        brk = NegativeSpaceBreakerV05()
        d = brk.decide("RULE-LEGAL", fuse_type="LEGAL", severe=True)
        assert d.verdict == BreakerVerdict.ESCALATE
        assert d.state == BreakerState.OPEN

    def test_legal_permanent_no_reset(self):
        brk = NegativeSpaceBreakerV05(cool_down_seconds=0)
        brk.decide("RULE-LEGAL", fuse_type="LEGAL", severe=True)
        # 冷却期为 0 也不恢复——LEGAL 永久熔断
        d = brk.decide("RULE-LEGAL", fuse_type="LEGAL")
        assert d.verdict == BreakerVerdict.ESCALATE
        assert d.state == BreakerState.OPEN

    def test_open_cooldown_fuses(self):
        brk = NegativeSpaceBreakerV05(failure_threshold=1, cool_down_seconds=999)
        brk.decide("RULE-2", failure=True)
        d = brk.decide("RULE-2")
        assert d.verdict == BreakerVerdict.FUSE  # 冷却期内

    def test_half_open_probe_recovers(self):
        brk = NegativeSpaceBreakerV05(failure_threshold=1, cool_down_seconds=0,
                                      half_open_probes=1)
        brk.decide("RULE-3", failure=True)
        # 冷却期过 → HALF_OPEN 试探（无失败）→ PASS
        d = brk.decide("RULE-3")
        assert d.state == BreakerState.HALF_OPEN
        assert d.verdict == BreakerVerdict.PASS

    def test_half_open_probe_failure_refuses(self):
        brk = NegativeSpaceBreakerV05(failure_threshold=1, cool_down_seconds=0,
                                      half_open_probes=1)
        brk.decide("RULE-4", failure=True)
        d = brk.decide("RULE-4", failure=True)  # 试探失败
        assert d.verdict == BreakerVerdict.FUSE
        assert d.state == BreakerState.OPEN

    def test_success_resets_counter(self):
        brk = NegativeSpaceBreakerV05(failure_threshold=3)
        brk.decide("RULE-5", failure=True)
        brk.decide("RULE-5", failure=False)  # 成功重置
        brk.decide("RULE-5", failure=True)
        d = brk.decide("RULE-5", failure=True)
        assert d.verdict == BreakerVerdict.PASS  # 计数从 0 起，未达 3

    def test_severe_immediate_fuse(self):
        brk = NegativeSpaceBreakerV05()
        d = brk.decide("RULE-6", severe=True)
        assert d.verdict == BreakerVerdict.FUSE
        assert d.state == BreakerState.OPEN

    def test_event_history_records(self):
        brk = NegativeSpaceBreakerV05()
        brk.decide("RULE-7", failure=True)
        assert len(brk.event_history()) == 1
        ev = brk.event_history()[0]
        assert ev["rule_id"] == "RULE-7"


# ---------------------------------------------------------------------------
# Layer 1 编排器（全链路）
# ---------------------------------------------------------------------------

class TestLayer1Runtime:
    def test_static_block(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="data.leak third_party")
        assert res.verdict == Layer1Verdict.BLOCK
        assert "static_list" in res.checks

    def test_blacklist_block(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="prompt cmd", api="prompt_inject",
                           signature="ignore_previous", behavior_domain="transaction")
        assert res.verdict == Layer1Verdict.BLOCK
        assert res.checks["blacklist"]["blocked"]

    def test_mou_escalate(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="novel op", api="some.api", signature="x",
                           behavior_domain="tax_evasion")
        assert res.verdict == Layer1Verdict.ESCALATE
        assert res.checks["mou_precompute"]["escalate_slow"]

    def test_breaker_fuse(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="ok op", api="ok.api", signature="ok",
                           behavior_domain="transaction", rule_id="R1", failure=True)
        res2 = rt.preflight(operation="ok op", api="ok.api", signature="ok",
                            behavior_domain="transaction", rule_id="R1", failure=True)
        res3 = rt.preflight(operation="ok op", api="ok.api", signature="ok",
                            behavior_domain="transaction", rule_id="R1", failure=True)
        assert res3.verdict == Layer1Verdict.BLOCK  # 达阈值熔断
        assert res3.checks["breaker"]["state"] == "OPEN"

    def test_legal_escalate_through_runtime(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="legal op", api="a.api", signature="s",
                           behavior_domain="transaction", rule_id="RL",
                           fuse_type="LEGAL", severe=True)
        assert res.verdict == Layer1Verdict.ESCALATE

    def test_full_pass(self):
        rt = Layer1Runtime()
        res = rt.preflight(operation="data.aggregate", api="data.api",
                           signature="anonymized", behavior_domain="transaction",
                           rule_id="OK1")
        assert res.verdict == Layer1Verdict.PASS
        assert res.duration_ms >= 0

    def test_check_alias(self):
        rt = Layer1Runtime()
        res = rt.check(operation="data.leak x")
        assert res.verdict == Layer1Verdict.BLOCK


# ---------------------------------------------------------------------------
# A-4 热路径时延 <10ms
# ---------------------------------------------------------------------------

class TestPerf:
    def test_hot_path_under_10ms(self):
        """A-4: 全链路预检 <10ms（热路径）。"""
        rt = Layer1Runtime()
        times = []
        for _ in range(100):
            res = rt.preflight(operation="data.aggregate", api="data.api",
                               signature="anonymized", behavior_domain="transaction",
                               rule_id="PERF1")
            assert res.verdict == Layer1Verdict.PASS
            times.append(res.duration_ms)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert max(times) < 10
        assert p95 < 10
