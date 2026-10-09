# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-4 GE-IF 契约测试——GE-IF-001 正和评估实时回调 + GE-IF-001b 快路径
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 / SV-8 + 接口熵=0
# 先验分布:     genie_callback.py + tdca-utility-genie（ID24 只读 inproc）
# 配置权边界:   L2；仅测试环境
# 预期分配:     GE-IF 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-4 GE-IF-001/001b 契约测试（inproc 效用精灵真实桥接，ID24 只读）。

制度锚定: FC-SBX-OPS-001 M3-4 | SPDX-License-Identifier: TDCA-Internal

测试策略:
  - inproc 效用精灵桥接（tdca-utility-genie 只读，正和验证不可 mock）
  - GE-IF-001: solve_positive_sum 完整求解（正和通过/非正和 FUSE/NSFL 熔断）
  - GE-IF-001b: positive_sum_check 快路径（S_synergy > 0）
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.genie_callback as genie_callback  # noqa: E402
from app.genie_callback import GenieCallback, GenieLinkError  # noqa: E402

SID = "did:tdca:sandbox:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.fixture()
def adapter():
    """inproc GenieCallback（效用精灵真实桥接，ID24 只读）。"""
    return GenieCallback()


def _participants(n: int = 3) -> list:
    return [{"agent_id": f"agent-{i}", "capability": 1.0} for i in range(n)]


def _obj_fns(n: int = 3, factor: float = 1.2) -> list:
    """目标函数公式描述（T1 修复后：REST 可序列化 dict，非 callable）。"""
    return [{"type": "linear", "factor": factor} for _ in range(n)]


def _reservations(n: int = 3) -> list:
    return [2.0] * n


# ---------------------------------------------------------------- GE-IF-001 实时回调

def test_geif001_evaluate_positive_sum(adapter):
    """GE-IF-001: 正和求解通过（S_synergy > 0）+ NCA 存证（SV-10）。"""
    r = adapter.evaluate(SID, _participants(), _obj_fns(), _reservations(), time_budget=5.0)
    assert r["contract"] == "GE-IF-001"
    assert r["operation"] == "evaluate"
    assert r["fuse"] is False
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    assert r["latency_ms"] < 1000  # SV-8


def test_geif001_evaluate_params_length_mismatch(adapter):
    """GE-IF-001: 三方数组长度不一致 → ValueError（422 语义）。"""
    with pytest.raises(ValueError, match="长度须一致"):
        adapter.evaluate(SID, _participants(3), _obj_fns(2), _reservations(3))


def test_geif001_evaluate_empty_params(adapter):
    """GE-IF-001: 空参数 → ValueError。"""
    with pytest.raises(ValueError, match="必填"):
        adapter.evaluate(SID, [], [], [])


def test_geif001_evaluate_touched_nsfl_fuses(adapter):
    """GE-IF-001: NSFL 边界触碰 → fuse=True（touched_nsfl，ID86 熔断语义）。"""
    r = adapter.evaluate(SID, _participants(), _obj_fns(), _reservations(),
                         nsfl_boundaries=["autonomous_repair"])  # NSFL 关键字
    assert r["touched_nsfl"] is True
    assert r["fuse"] is True


def test_geif001_evaluate_non_positive_fuses(adapter):
    """GE-IF-001: 非正和 → GenieLinkError（效用精灵 validate 熔断，fail-closed）。"""
    # factor=0（零产出）→ 非正和 → solver.validate 抛异常 → 包装为 GenieLinkError
    with pytest.raises(GenieLinkError, match="非正和"):
        adapter.evaluate(SID, _participants(), _obj_fns(factor=0.0),
                         [100.0] * 3, time_budget=1.0)


def test_geif001_latency_over_sv8(adapter):
    """SV-8: 联动延迟 ≥1s → GenieLinkError。"""
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        with pytest.raises(GenieLinkError, match="SV-8"):
            adapter.evaluate(SID, _participants(), _obj_fns(), _reservations())


# ---------------------------------------------------------------- GE-IF-001b 快路径

def test_geif001b_check_positive(adapter):
    """GE-IF-001b: 正和快路径通过（S_synergy > 0）。"""
    r = adapter.check(SID, coalition_utility=300.0, independent_utilities=[80.0, 90.0, 50.0])
    assert r["contract"] == "GE-IF-001b"
    assert r["is_positive_sum"] is True
    assert r["fuse"] is False
    assert r["delta"] == 80.0
    assert r["nca_refs"]["sbx"].startswith("NCA-")


def test_geif001b_check_non_positive_fuses(adapter):
    """GE-IF-001b: 非正和 → fuse=True。"""
    r = adapter.check(SID, coalition_utility=100.0, independent_utilities=[80.0, 90.0, 50.0])
    assert r["is_positive_sum"] is False
    assert r["fuse"] is True


def test_geif001b_check_invalid_params(adapter):
    """GE-IF-001b: 非法参数（空列表/负值）→ ValueError。"""
    with pytest.raises(ValueError):
        adapter.check(SID, coalition_utility=100.0, independent_utilities=[])


# ---------------------------------------------------------------- fail-closed NCA

def test_geif001_fail_closed_generates_error_nca(adapter):
    """fail-closed 异常路径生成 ERROR NCA（C01/SV-7 联动故障可观测）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with pytest.raises(ValueError):
        adapter.evaluate(SID, [], [], [])
    after = nca_logger.list_nca()
    assert len(after) == before + 1
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- 路由层

@pytest.fixture()
def route_client(monkeypatch):
    """路由层测试客户端（注入 inproc 适配器 + monkeypatch 自动还原）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    a = GenieCallback()
    monkeypatch.setattr(genie_callback, "ADAPTER", a)
    return TestClient(app), a


def test_route_evaluate_invalid_sandbox_422(route_client):
    """路由层: 非法 sandbox_id → 422。"""
    client, _ = route_client
    r = client.post("/api/v1/genie/bad-id/evaluate", json={
        "participants": _participants(), "objective_functions": [], "reservation_utilities": []})
    assert r.status_code == 422


def test_route_check_ok(route_client):
    """路由层: 快路径校验 200。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/genie/{sid}/check",
                    json={"coalition_utility": 300.0, "independent_utilities": [80.0, 90.0, 50.0]})
    assert r.status_code == 200
    assert r.json()["is_positive_sum"] is True


# ---------------------------------------------------------------- P1/T1 修复回归

def test_geif001b_check_inf_rejected(adapter):
    """P1: coalition_utility=inf 拒绝（S_synergy 不可被 inf 伪造，C02/KB-ECON-001 §3）。"""
    import math
    with pytest.raises(ValueError, match="有限"):
        adapter.check(SID, coalition_utility=math.inf, independent_utilities=[1.0, 2.0])


def test_route_check_nonpositive_422(route_client):
    """P1 路由层: coalition_utility≤0 → 422（Field gt=0 校验）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/genie/{sid}/check",
                    json={"coalition_utility": 0.0, "independent_utilities": [1.0, 2.0]})
    assert r.status_code == 422


def test_route_evaluate_ok_with_formula(route_client):
    """T1: 路由 evaluate 200（objective_functions 为可序列化公式描述）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/genie/{sid}/evaluate", json={
        "participants": [{"agent_id": "a1", "capability": 1.0},
                         {"agent_id": "a2", "capability": 1.0},
                         {"agent_id": "a3", "capability": 1.0}],
        "objective_functions": [{"type": "linear", "factor": 1.2}] * 3,
        "reservation_utilities": [2.0, 2.0, 2.0],
        "time_budget": 3.0,
    })
    assert r.status_code == 200
    assert r.json()["is_positive_sum"] is True


def test_route_evaluate_invalid_formula_422(route_client):
    """T1 路由层: 非法公式描述 → 422（REST 契约校验）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/genie/{sid}/evaluate", json={
        "participants": [{"agent_id": "a1"}],
        "objective_functions": [{"type": "quadratic"}],  # 非法类型
        "reservation_utilities": [1.0],
    })
    assert r.status_code == 422


# ---------------------------------------------------------------- #2/#3/#11 修复回归

def test_geif001_evaluate_fingerprint_sidechain(adapter):
    """#2: SV-10 双向存证——evaluate 返回 genie_fingerprint（nca_trace 侧链）。"""
    r = adapter.evaluate(SID, _participants(), _obj_fns(), _reservations(), time_budget=3.0)
    assert r["nca_refs"]["genie_fingerprint"]  # 效用精灵侧 nca_trace 指纹


def test_route_evaluate_persists_logs(route_client):
    """#3: evaluate 结果回写沙盒 positive_sum_logs（实时记录契约核心）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/genie/{sid}/evaluate", json={
        "participants": [{"agent_id": "a1"}, {"agent_id": "a2"}, {"agent_id": "a3"}],
        "objective_functions": [{"type": "linear", "factor": 1.2}] * 3,
        "reservation_utilities": [2.0, 2.0, 2.0],
        "time_budget": 3.0,
    })
    assert r.status_code == 200
    reloaded = st.load_sandbox(sid)
    assert any("GENIE_EVALUATE" == lg.get("operation") for lg in reloaded.positive_sum_logs)


def test_geif001_evaluate_inf_reservation_rejected(adapter):
    """#5: evaluate reservation_utilities=inf → ValueError（C02 不可伪造正和）。"""
    import math
    with pytest.raises(ValueError, match="有限"):
        adapter.evaluate(SID, _participants(), _obj_fns(),
                         [math.inf, 2.0, 2.0], time_budget=3.0)
