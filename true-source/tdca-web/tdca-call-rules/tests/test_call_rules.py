# -*- coding: utf-8 -*-
# TDCA 制度水印: TDCA-FC-20260811-003-CALL-RULES | NSFL-V0.2 | ID92 模拟态
"""call_rules_engine 测试：商业调用规则引擎。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from call_rules_engine import CallRequest, CallRulesEngine, CallType, CallVerdict  # noqa: E402


@pytest.fixture
def engine():
    return CallRulesEngine()


def test_disposable_call_when_stackable(engine):
    """物理叠加可覆盖 → 日抛调用。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000, tax_receipt=200))
    assert rec.call_type == CallType.DISPOSABLE
    assert rec.verdict == CallVerdict.APPROVED


def test_compound_call_when_not_stackable(engine):
    """物理叠加不可覆盖 + ID90 三条件全过 → 化合调用。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          can_stack=False, tax_receipt=200,
                                          indivisibility=True, emergence=True, nonlinearity=True))
    assert rec.call_type == CallType.COMPOUND
    assert "royalty" in rec.taxes  # 化合调用计版税


def test_compound_rejected_when_conditions_not_met(engine):
    """ID90 三条件未全过 → 拒绝化合（不触发过度设计违规）。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          can_stack=False, tax_receipt=200,
                                          indivisibility=True, emergence=True, nonlinearity=False))
    assert rec.verdict == CallVerdict.REJECTED
    assert rec.net_value == 0.0


def test_overdesign_violation_when_stackable_forced_compound(engine):
    """可用物理叠加却强制化合（is_disposable=False + can_stack=True）= 过度设计违规拒绝。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          can_stack=True, is_disposable=False, tax_receipt=200))
    # 显式 is_disposable=False 走化合路径（三条件未传全过 → 拒绝）
    assert rec.verdict == CallVerdict.REJECTED


def test_mou_zeroing_rule(engine):
    """ID79 归零规则：T(y_t) <= 0 → 价格强制归零。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000, tax_receipt=0))
    assert rec.verdict == CallVerdict.ZEROED
    assert rec.net_value == 0.0


def test_nsfl_fuse(engine):
    """NSFL 熔断：触碰负空间 → FUSED。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          tax_receipt=200, violates_nsfl=True))
    assert rec.verdict == CallVerdict.FUSED


def test_non_positive_sum_rejected(engine):
    """非正和（价值 < 成本）→ REJECTED。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=100,
                                          tax_receipt=200), cost=500)
    assert rec.verdict == CallVerdict.REJECTED


def test_tax_computation_default_rates(engine):
    """L3 税收计算：调度税 2% + 版税 7.5%（化合）。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          can_stack=False, tax_receipt=200,
                                          indivisibility=True, emergence=True, nonlinearity=True))
    assert rec.taxes["dispatch_tax"] == pytest.approx(20.0)
    assert rec.taxes["royalty"] == pytest.approx(75.0)
    assert rec.net_value == pytest.approx(905.0)


def test_record_field_isomorphism(engine):
    """字段同构（REV-CALL-001 M2）：CallRecord 含 mou_anchor/nsfl_version/data_nature。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          tax_receipt=200))
    assert rec.mou_anchor["status"] == "Simulated"
    assert rec.nsfl_version == "V0.2"
    assert rec.data_nature == "simulated"


def test_summary_counts(engine):
    """审计汇总。"""
    engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000, tax_receipt=200))
    engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000, tax_receipt=0))  # 归零
    engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                    tax_receipt=200, violates_nsfl=True))  # 熔断
    s = engine.summary()
    assert s["total_calls"] == 3
    assert s["approved"] == 1
    assert s["zeroed"] == 1
    assert s["fused"] == 1


def test_explicit_disposable_flag(engine):
    """显式日抛标记覆盖 ID90 判定。"""
    rec = engine.execute_call(CallRequest(caller="u1", scene="s1", call_value=1000,
                                          can_stack=False, is_disposable=True, tax_receipt=200))
    assert rec.call_type == CallType.DISPOSABLE
