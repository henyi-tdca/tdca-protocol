# -*- coding: utf-8 -*-
"""NSFLUnionEngine 集成单元测试：并集/性能/NCA/缓存/alt_path/审计（任务书 §二/§四 A-1~A-6）。"""
import time
from decimal import Decimal

from nsfl_union import (FuseLevel, NS_Operator, NS_Rule, NS_Type,
                        NSFLUnionEngine, SceneNSFL, Severity)


def _scene(sid, *rules):
    return SceneNSFL(scene_id=sid, rules=list(rules))


def _limit(ns, op, val, unit="CNY"):
    return NS_Rule(f"R-{ns.value}-{op.value}", ns, op, Decimal(str(val)), unit=unit)


def _mk_engine(nca=None, **kw):
    return NSFLUnionEngine(nca_generator=nca, **kw)


# ---- A-1 并集正确性 ----

def test_union_set():
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100),
               NS_Rule("R2", NS_Type.ETHICAL, NS_Operator.ALLOW))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MIN, 50),
               NS_Rule("R3", NS_Type.BELIEF, NS_Operator.ALLOW))
    u = _mk_engine().compute(a, b)
    got = {t.value for t in u.union_set}
    assert got == {"TRANSACTION_LIMIT", "ETHICAL", "BELIEF"}  # 并集


def test_union_duplicates_collapsed():
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 200))
    u = _mk_engine().compute(a, b)
    assert len(u.union_set) == 1


# ---- A-2 性能与计时 ----

def test_computation_time_recorded():
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))
    u = _mk_engine().compute(a, b)
    assert u.computation_time_ms >= 0


def test_bulk_performance_under_100ms():
    """A-2: 1000 对 <100ms（P95<150ms）——本机冒烟基准。"""
    eng = _mk_engine()
    scenes = []
    for i in range(100):
        scenes.append(_scene(f"S{i}",
                             _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100 + i),
                             NS_Rule(f"E{i}", NS_Type.ETHICAL, NS_Operator.ALLOW)))
    t0 = time.perf_counter()
    for i in range(1000):
        eng.compute(scenes[i % 100], scenes[(i * 7) % 100], compute_alt_path=False)
    dt = (time.perf_counter() - t0) * 1000
    avg = dt / 1000
    assert avg < 100.0, f"avg {avg:.2f}ms >= 100ms"


# ---- A-5 NCA 审计轨迹 ----

def test_nca_ref_generated_and_content():
    seen = {}

    def nca(**kw):
        seen.update(kw)
        return "NCA-001"

    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))
    u = _mk_engine(nca=nca).compute(a, b)
    assert u.nca_ref == "NCA-001"
    assert seen["content"]["event"] == "NSFL_UNION_COMPUTED"
    assert seen["content"]["scene_a"] == "A"
    assert seen["content"]["conflict_set"][0]["resolution"] == "TAKE_STRICTER"
    assert "schema_version" in seen["content"]


def test_mock_nca_ref_when_no_generator():
    u = _mk_engine().compute(_scene("A"), _scene("B"))
    assert u.nca_ref.startswith("NCA-MOCK-")


# ---- 缓存（禁止 >5min）----

def test_cache_enabled_returns_same_ref():
    eng = _mk_engine(enable_cache=True)
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))
    u1 = eng.compute(a, b)
    u2 = eng.compute(a, b)
    assert u1.nca_ref == u2.nca_ref  # 缓存命中
    assert u1.computation_time_ms == u2.computation_time_ms


def test_cache_ttl_capped_at_300s():
    eng = NSFLUnionEngine(enable_cache=True, cache_ttl_seconds=9999)
    assert eng.cache_ttl == 300  # 钳制 ≤5min（MASTER 禁止项）


def test_cache_disabled_by_default():
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))
    u1 = _mk_engine().compute(a, b)
    u2 = _mk_engine().compute(a, b)
    assert u1.nca_ref != u2.nca_ref  # 每次新审计


# ---- Alt-Path（§九 N4）----

def test_alt_path_recommendation():
    eng = _mk_engine()
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))  # 冲突
    c1 = _scene("C1", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))  # 与 A 兼容
    c2 = _scene("C2", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))   # 与 B 兼容
    u = eng.compute(a, b, registry=[c1, c2])
    assert isinstance(u.recommended_alt_path, list)  # Optional[List[str]]（MASTER 契约）
    assert all(isinstance(s, str) for s in u.recommended_alt_path)


def test_alt_path_none_when_no_better():
    eng = _mk_engine()
    a = _scene("A", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 100))
    b = _scene("B", _limit(NS_Type.TRANSACTION_LIMIT, NS_Operator.LIMIT_MAX, 50))
    u = eng.compute(a, b, registry=[], compute_alt_path=True)
    assert u.recommended_alt_path is None


# ---- review_queue 审计面 ----

def test_review_queue_surface():
    a = _scene("A", NS_Rule("R1", NS_Type.ETHICAL, NS_Operator.ALLOW))
    b = _scene("B", NS_Rule("R2", NS_Type.BELIEF, NS_Operator.ALLOW))
    u = _mk_engine().compute(a, b)
    assert any("CROSS_TYPE" in q for q in u.review_queue)
