# -*- coding: utf-8 -*-
"""C1 验收测试：A-7 RiskPremium 动态 / A-8 Alt-Path 推荐 / A-9 接口稳定性 + 零漂移 + H-C2-005 格式对齐。"""
import time
from decimal import Decimal

from cscp_gateway.adapters import MockNSFLUnionAdapter
from cscp_gateway.cscp_nsfl_adapter import CSCPNSFLAdapter
from cscp_gateway.state_machine import PreflightStatus

# ---- A-7 RiskPremium 动态计算（B1 weights.py 验收）----


def _req(a_rules, b_rules):
    return {"caller_scene": {"scene_id": "A", "rules": a_rules},
            "callee_scene": {"scene_id": "B", "rules": b_rules},
            "caller_tier": "L2", "cross_scene_flag": True}


def _limit(ns_type, op, val):
    return {"rule_id": f"R-{ns_type}-{op}", "ns_type": ns_type, "operator": op,
            "parameter": str(val), "unit": "CNY"}


def test_a7_risk_premium_mapping():
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())

    # HIGH（LEGAL）→ TRIGGERED + premium 1.0
    r = adapter.preflight_check(_req(
        [{"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}],
        [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
    assert r["status"] == PreflightStatus.TRIGGERED and r["risk_premium"] == 1.0

    # MEDIUM（限额取严）→ FAIL + premium 公式值（0.30~0.60 区间）
    r = adapter.preflight_check(_req(
        [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 1000000)],
        [_limit("TRANSACTION_LIMIT", "LIMIT_MAX", 500000)]))
    assert r["status"] == PreflightStatus.FAIL
    assert 0.30 <= r["risk_premium"] < 0.60

    # 无冲突 → PASS + premium = M（默认 OBSERVE 0.2）
    r = adapter.preflight_check(_req(
        [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
        [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
    assert r["status"] == PreflightStatus.PASS and r["risk_premium"] == 0.2


# ---- A-8 Alt-Path 推荐（B1 alt_path.py 验收）----

def test_a8_alt_path_recommendation():
    from nsfl_union import NSFLUnionEngine, NS_Rule, NS_Type, NS_Operator, SceneNSFL
    eng = NSFLUnionEngine()
    adapter = CSCPNSFLAdapter(eng)
    a = SceneNSFL(scene_id="A", rules=[NS_Rule("A1", NS_Type.TRANSACTION_LIMIT,
                                               NS_Operator.LIMIT_MAX, Decimal("100"), unit="CNY")])
    b = SceneNSFL(scene_id="B", rules=[NS_Rule("B1", NS_Type.TRANSACTION_LIMIT,
                                               NS_Operator.LIMIT_MAX, Decimal("50"), unit="CNY")])
    c1 = SceneNSFL(scene_id="C1", rules=[NS_Rule("C1-1", NS_Type.TRANSACTION_LIMIT,
                                                 NS_Operator.LIMIT_MAX, Decimal("100"), unit="CNY")])
    c2 = SceneNSFL(scene_id="C2", rules=[NS_Rule("C2-1", NS_Type.TRANSACTION_LIMIT,
                                                 NS_Operator.LIMIT_MAX, Decimal("50"), unit="CNY")])
    req = {"caller_scene": {"scene_id": "A", "rules": []}, "callee_scene": {"scene_id": "B", "rules": []}}
    # 引擎级推荐（registry 注入）
    u = eng.compute(a, b, registry=[c1, c2])
    assert u.recommended_alt_path is not None  # A-8: 绕行场景 C 推荐存在
    assert all(isinstance(s, str) for s in u.recommended_alt_path)
    # 契约字段零漂移
    r = adapter.preflight_check(req)
    assert set(r["ns_union"].keys()) >= {"scene_a", "scene_b", "union_set",
                                         "conflict_set", "risk_premium",
                                         "recommended_alt_path",
                                         "computation_time_ms", "nca_ref"}


# ---- A-9 接口稳定性（10000 次零异常）+ 零漂移 ----

def test_a9_stability_10000_calls():
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    t0 = time.perf_counter()
    for i in range(10000):
        r = adapter.preflight_check(_req(
            [{"rule_id": f"E{i}", "ns_type": "ETHICAL", "operator": "ALLOW"}],
            [{"rule_id": f"E{i}b", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
        assert r["status"] in (PreflightStatus.PASS, PreflightStatus.FAIL,
                               PreflightStatus.TRIGGERED, PreflightStatus.REJECTED)
        assert set(r["ns_union"].keys()) == {"scene_a", "scene_b", "union_set",
                                             "conflict_set", "risk_premium",
                                             "recommended_alt_path",
                                             "computation_time_ms", "nca_ref"}
    dt = (time.perf_counter() - t0) * 1000
    assert dt / 10000 < 100.0  # 单次调用 avg <100ms（Step-2 <500ms 远裕量）


def test_a9_validate_consistency_zero_drift():
    """validate_consistency：同输入同输出 100% 一致（参考=自身，零漂移）。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    report = adapter.validate_consistency(sample_size=100)
    assert report.consistency == 100.0
    assert report.errors == 0
    assert report.max_latency_ms < 500.0  # Step-2 <500ms


# ---- H-C2-005 mock 与真实接口格式对齐（字段级）----

def test_h_c2_005_format_parity():
    """mock（R-CSCP-001）与真实 adapter 输出契约键集一致（格式零漂移）。"""
    from nsfl_union import NSFLUnionEngine
    real = CSCPNSFLAdapter(NSFLUnionEngine())
    mock = MockNSFLUnionAdapter()

    contract_keys = {"status", "risk_premium", "ns_union", "alt_paths", "nca_ref", "next_step"}
    req = _req([{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
               [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}])
    real_out = real.preflight_check(req)
    mock_out = mock.preflight_check(req)
    # 真实输出包含契约键集（mock 输出为子集）
    assert contract_keys <= set(real_out.keys())
    assert contract_keys <= set(mock_out.keys())
    # ns_union 形状键对齐（真实 = mock 超集；下游消费者按真实契约）
    real_union = set(real_out["ns_union"].keys())
    mock_union = set(mock_out["ns_union"].keys())
    assert real_union >= mock_union


# ---- LOW 分支（R-5 裁决）与兜底 REJECTED 覆盖 ----

def test_low_conflict_passes_with_credit():
    """L1 自律冲突（ETHICAL 允许域互斥）→ LOW → PASS + credit_impact（DCD-CSCP-CHANGE-001）。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    r = adapter.preflight_check(_req(
        [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW", "parameter": "EU"}],
        [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW", "parameter": "US"}]))
    assert r["status"] == PreflightStatus.PASS
    assert r.get("credit_impact") is True      # 违约方信用降信记录（软约束）
    assert r["next_step"] == "sandbox_verify"  # 不阻断协作


def test_review_queue_rejected():
    """LEGAL×LEGAL 一致禁止 + 空 conflict_set → 兜底 REJECTED(REQUIRES_REVIEW)。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    r = adapter.preflight_check(_req(
        [{"rule_id": "L1", "ns_type": "LEGAL", "operator": "FORBID"}],
        [{"rule_id": "L2", "ns_type": "LEGAL", "operator": "FORBID"}]))
    assert r["status"] == PreflightStatus.REJECTED
    assert r["reason"] == "REQUIRES_REVIEW"


def test_validate_consistency_custom_scenes():
    """自定义场景集（含 MEDIUM/LEGAL 专项）一致性 100% + 无异常。"""
    from nsfl_union import NSFLUnionEngine, NS_Operator, NS_Rule, NS_Type, SceneNSFL
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    scenes = [
        SceneNSFL(scene_id="S1", rules=[NS_Rule("R1", NS_Type.ETHICAL, NS_Operator.ALLOW)]),
        SceneNSFL(scene_id="S2", rules=[
            NS_Rule("R2", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX,
                    Decimal("100"), unit="CNY")]),
        SceneNSFL(scene_id="S3", rules=[NS_Rule("R3", NS_Type.LEGAL, NS_Operator.FORBID)]),
        SceneNSFL(scene_id="S4", rules=[
            NS_Rule("R4", NS_Type.ETHICAL, NS_Operator.ALLOW, parameter="EU")]),
    ]
    report = adapter.validate_consistency(sample_size=200, scenes=scenes)
    assert report.consistency == 100.0
    assert report.errors == 0


# ---- 红队复审 N1: 输入超限 fail-closed（不得静默截断误判 PASS）----

def test_n1_rule_flood_fail_closed():
    """101 条规则（第 101 条为 LEGAL）→ REJECTED(INVALID_SCHEMA)，而非 PASS（熔断不可绕过）。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    rules = [{"rule_id": f"E{i}", "ns_type": "ETHICAL", "operator": "ALLOW"} for i in range(100)]
    rules.append({"rule_id": "LEGAL-1", "ns_type": "LEGAL", "operator": "FORBID"})
    r = adapter.preflight_check(_req(rules, [{"rule_id": "E2", "ns_type": "ETHICAL", "operator": "ALLOW"}]))
    assert r["status"] == PreflightStatus.REJECTED
    assert r["reason"].startswith("INVALID_SCHEMA")   # detail 并入 reason（FIN-7）
    assert r["nca_ref"] == "NCA-INVALID-INPUT"


def test_n7_full_operator_support():
    """LIMIT_EQ / RESTRICT_TIER parameter 正常传递（不再 INVALID_SCHEMA）。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    r = adapter.preflight_check(_req(
        [{"rule_id": "Q1", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_EQ",
          "parameter": "80", "unit": "CNY"}],
        [{"rule_id": "Q2", "ns_type": "TRANSACTION_LIMIT", "operator": "LIMIT_EQ",
          "parameter": "50", "unit": "CNY"}]))
    assert r["status"] in (PreflightStatus.FAIL, PreflightStatus.REJECTED)  # 定值矛盾 → 冲突
    r2 = adapter.preflight_check(_req(
        [{"rule_id": "T1", "ns_type": "TECH_CONSTRAINT", "operator": "RESTRICT_TIER",
          "parameter": "SUSPEND"}],
        [{"rule_id": "T2", "ns_type": "TECH_CONSTRAINT", "operator": "RESTRICT_TIER",
          "parameter": "OBSERVE"}]))
    assert r2["status"] == PreflightStatus.FAIL  # 档位取严冲突 → MEDIUM FAIL


def test_n8_cross_type_review_queue_not_blocking():
    """普通跨类型 review_queue 不阻断（无 LEGAL/高档位 → PASS，§5.3 仅审计面）。"""
    from nsfl_union import NSFLUnionEngine
    adapter = CSCPNSFLAdapter(NSFLUnionEngine())
    r = adapter.preflight_check(_req(
        [{"rule_id": "E1", "ns_type": "ETHICAL", "operator": "ALLOW"}],
        [{"rule_id": "B1", "ns_type": "BELIEF", "operator": "ALLOW"}]))
    assert r["status"] == PreflightStatus.PASS  # 跨类型 → review_queue 但 PASS（不阻断）


# ---- 红队 FIN-1: 判定表对称性 + UNKNOWN 强制复核 ----

def test_decision_table_symmetric():
    """同对规则交换 A/B 方向 → 结果一致（FORBID×ALLOW ≡ ALLOW×FORBID，消除顺序博弈面）。"""
    from nsfl_union import NSFLUnionEngine
    eng = NSFLUnionEngine()
    from nsfl_union import NS_Operator, NS_Rule, NS_Type, SceneNSFL
    forbid = NS_Rule("F1", NS_Type.DATA_CROSS_BORDER, NS_Operator.FORBID)
    allow = NS_Rule("A1", NS_Type.DATA_CROSS_BORDER, NS_Operator.ALLOW)
    a = SceneNSFL(scene_id="A", rules=[allow])
    b = SceneNSFL(scene_id="B", rules=[forbid])
    u1 = eng.compute(a, b)
    u2 = eng.compute(b, a)
    assert len(u1.conflict_set) == len(u2.conflict_set) == 1
    assert u1.conflict_set[0].resolution.value == u2.conflict_set[0].resolution.value == "FORBID"
    # 数值对称（空域冲突：下界 100 > 上界 50）
    lim_a = SceneNSFL(scene_id="A", rules=[
        NS_Rule("L1", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX,
                Decimal("50"), unit="CNY")])
    lim_b = SceneNSFL(scene_id="B", rules=[
        NS_Rule("L2", NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MIN,
                Decimal("100"), unit="CNY")])
    v1 = eng.compute(lim_a, lim_b)
    v2 = eng.compute(lim_b, lim_a)
    assert len(v1.conflict_set) == len(v2.conflict_set) == 1
    assert v1.conflict_set[0].resolution.value == v2.conflict_set[0].resolution.value == "EMPTY_DOMAIN"


def test_decision_table_complete_no_unknown():
    """6×6 operator 组合穷举：对称转调后判定表完备，无 UNKNOWN 残留（FIN-1）。"""
    from decimal import Decimal as D
    from nsfl_union.conflict import _compare_same_type
    from nsfl_union import (FuseLevel, NS_Operator, NS_Rule, NS_Type,
                             Resolution)
    LIMIT_OPS = {NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN, NS_Operator.LIMIT_EQ}
    seen_unknown = 0
    for oa in NS_Operator:
        for ob in NS_Operator:
            def _mk(op, tag):
                kw = {}
                if op in LIMIT_OPS:
                    kw = {"parameter": D("100"), "unit": "CNY"}
                elif op is NS_Operator.RESTRICT_TIER:
                    kw = {"parameter": FuseLevel.OBSERVE}
                return NS_Rule(f"{tag}-{op.value}", NS_Type.TRANSACTION_LIMIT, op, **kw)
            c = _compare_same_type(_mk(oa, "A"), _mk(ob, "B"))
            if c is not None and c.resolution == Resolution.UNKNOWN:
                seen_unknown += 1
    assert seen_unknown == 0  # 全部组合已定义（对称转调后完备）
