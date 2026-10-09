# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-3 PM-IF 契约测试——PM-IF-001 激活系数达标→PhaseMachine 阶段推进
# 约束矩阵:     FC-SBX-OPS-001 SV-1（α>1.2 必要非充分）/ SV-8 + 接口熵=0
# 先验分布:     phase_adapter.py + tdca-flow-orchestrator phase_machine.py（FC-012 只读 inproc）
# 配置权边界:   L2；仅测试环境
# 预期分配:     PM-IF 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-3 PM-IF-001 契约测试（inproc PhaseMachine 桥接，FC-012 只读）。

制度锚定: FC-SBX-OPS-001 M3-3 | SPDX-License-Identifier: TDCA-Internal

测试策略:
  - inproc PhaseMachine 桥接（tdca_flow_src 别名），确定性隔离
  - SV-1 断言: α≤1.2 拒绝推进（必要非充分）；sandbox_pass/delta 消费真实评估记录
  - 穿越条件断言: P3->P4 sandbox_pass + positive_sum；FUSE 透传
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.phase_adapter as phase_adapter  # noqa: E402
from app.phase_adapter import PhaseAdapter, PhaseLinkError  # noqa: E402

SID = "did:tdca:sandbox:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _sbx(alpha: float = 1.25, delta: float = 10.0, fuse: bool = False,
         no_logs: bool = False, ns_flags: list = None) -> mock.Mock:
    """构造沙盒桩（携带真实评估记录，模拟 Sandbox 实例）。"""
    sb = mock.Mock()
    sb.negative_space_refs = list(ns_flags or [])
    if no_logs:
        sb.activation_logs = []
        sb.positive_sum_logs = []
    else:
        sb.activation_logs = [{"coefficient": alpha, "status": "财政自给性达成"}]
        sb.positive_sum_logs = [{"delta": delta, "fuse": fuse}]
    return sb


@pytest.fixture()
def adapter():
    """inproc PhaseAdapter（每测试独立，PhaseMachine 内存态隔离）。"""
    return PhaseAdapter()


# ---------------------------------------------------------------- PM-IF-001 阶段推进

def test_pmif001_advance_p3_to_p4(adapter):
    """PM-IF-001: α>1.2 + 正和过 → P3→P4 穿越（sandbox_pass 消费真实记录）。"""
    r = adapter.advance_signal(SID, _sbx(alpha=1.25, delta=10.0), current_phase="P3")
    assert r["contract"] == "PM-IF-001"
    assert r["operation"] == "advance"
    assert r["alpha"] == 1.25  # 来自沙盒 activation_logs
    assert r["phase"] == "P4"
    assert r["fuse"] is None
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # SV-10


def test_pmif001_alpha_le_12_rejected(adapter):
    """PM-IF-001: α≤1.2 拒绝推进（SV-1 必要非充分）。"""
    with pytest.raises(ValueError, match="SV-1"):
        adapter.advance_signal(SID, _sbx(alpha=1.2, delta=0.0), current_phase="P3")


def test_pmif001_no_activation_logs_rejected(adapter):
    """PM-IF-001: 无激活系数记录 → ValueError（须先 F3 evaluate，防客户端自报）。"""
    with pytest.raises(ValueError, match="无激活系数评估记录"):
        adapter.advance_signal(SID, _sbx(no_logs=True), current_phase="P3")


def test_pmif001_positive_sum_fused_rejected(adapter):
    """PM-IF-001: 最近正和验证 fuse → 拒绝推进（消费 positive_sum_logs）。"""
    with pytest.raises(ValueError, match="正和验证未通过"):
        adapter.advance_signal(SID, _sbx(alpha=1.3, delta=0.0, fuse=True), current_phase="P3")


def test_pmif001_condition_unmet_fuses(adapter):
    """PM-IF-001: 穿越条件不满足 → PhaseMachine FUSE 透传（不静默推进）。"""
    # P0->P1 需 connection_weight/intent_clear——advance_signal 以 P3 语义构造，P0 起点条件不满足
    r = adapter.advance_signal(SID, _sbx(alpha=1.5, delta=10.0), current_phase="P0")
    # P0->P1 的 context 缺 intent_clear → FUSE（PhaseMachine 原生拦截）
    assert r["phase"] == "FUSE" or r["fuse"] is not None


def test_pmif001_advance_from_p8_completed(adapter):
    """PM-IF-001: P8→COMPLETED 需 mou_closed + human_signature——非 ADVANCE 路径，保持 FUSE 语义。"""
    r = adapter.advance_signal(SID, _sbx(alpha=1.5, delta=10.0), current_phase="P8")
    # P8 ADVANCE 无目标 → LEVEL_1 熔断（已达最终 Phase）
    assert r["fuse"] is not None


# ---------------------------------------------------------------- fail-closed（SV-8/异常 NCA）

def test_pmif001_latency_over_sv8(adapter):
    """SV-8: 联动延迟 ≥1s → PhaseLinkError。"""
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        with pytest.raises(PhaseLinkError, match="SV-8"):
            adapter.advance_signal(SID, _sbx(alpha=1.5), current_phase="P3")


def test_pmif001_fail_closed_generates_error_nca(adapter):
    """fail-closed 异常路径生成 ERROR NCA（C01/SV-7 联动故障可观测）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with pytest.raises(ValueError):
        adapter.advance_signal(SID, _sbx(alpha=1.2), current_phase="P3")
    after = nca_logger.list_nca()
    assert len(after) == before + 1  # ERROR NCA 已落盘
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- PM-IF-001b 条件查询

def test_pmif001b_conditions_query(adapter):
    """PM-IF-001b: 穿越条件查询返回条件名列表。"""
    r = adapter.conditions("P3", "P4")
    assert r["contract"] == "PM-IF-001b"
    assert "sandbox_pass" in r["conditions"]
    assert "positive_sum" in r["conditions"]


def test_pmif_states_table(adapter):
    """状态集合查询（9 Phase + 终态）。"""
    states = adapter.state_table()
    assert "P0" in states and "P8" in states
    assert "COMPLETED" in states and "FUSE" in states


# ---------------------------------------------------------------- 路由层

@pytest.fixture()
def route_client(monkeypatch):
    """路由层测试客户端（注入 inproc 适配器 + monkeypatch 自动还原）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    a = PhaseAdapter()
    monkeypatch.setattr(phase_adapter, "ADAPTER", a)
    return TestClient(app), a


def test_route_advance_invalid_sandbox_422(route_client):
    """路由层: 非法 sandbox_id → 422。"""
    client, _ = route_client
    r = client.post("/api/v1/phase/bad-id/advance", json={"current_phase": "P3"})
    assert r.status_code == 422


def test_route_advance_alpha_le_12_422(route_client):
    """路由层: α≤1.2 → 422（SV-1）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/phase/{sid}/advance", json={"current_phase": "P3"})
    assert r.status_code == 422  # 无评估记录（α 不可自报）


def test_route_conditions_invalid_phase_409(route_client):
    """路由层: 非法 phase → 409。"""
    client, _ = route_client
    r = client.get("/api/v1/phase/conditions", params={"from_phase": "XX", "to_phase": "P4"})
    assert r.status_code == 409


def test_route_conditions_ok(route_client):
    """路由层: 条件查询 200。"""
    client, _ = route_client
    r = client.get("/api/v1/phase/conditions", params={"from_phase": "P3", "to_phase": "P4"})
    assert r.status_code == 200
    assert "sandbox_pass" in r.json()["conditions"]


def test_route_states_ok(route_client):
    """路由层: 状态集合 200。"""
    client, _ = route_client
    r = client.get("/api/v1/phase/states")
    assert r.status_code == 200
    assert "P8" in r.json()["states"]


# ---------------------------------------------------------------- T1/T2/T5/T6 修复回归

def test_pmif001_positive_sum_fused_error_nca(adapter):
    """T1: 正和 fuse 异常路径生成 ERROR NCA（SV-7 全操作存证）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with pytest.raises(ValueError, match="正和验证未通过"):
        adapter.advance_signal(SID, _sbx(alpha=1.3, delta=0.0, fuse=True), current_phase="P3")
    after = nca_logger.list_nca()
    assert len(after) == before + 1
    assert "FAIL_CLOSED" in after[-1]["operation"]


def test_pmif001_delta_backward_search_skips_delivery_confirm(adapter):
    """T6: _real_delta 向后搜索跳过 DELIVERY_CONFIRM 记录（对齐 chem_combine）。"""
    sb = mock.Mock()
    sb.negative_space_refs = []
    sb.activation_logs = [{"coefficient": 1.3, "status": "财政自给性达成"}]
    # 末条为 DELIVERY_CONFIRM（无 delta），前一条才是正和验证记录
    sb.positive_sum_logs = [
        {"delta": 10.0, "fuse": False},
        {"operation": "DELIVERY_CONFIRM", "report": {"ok": True}},
    ]
    r = adapter.advance_signal(SID, sb, current_phase="P3")
    assert r["phase"] == "P4"  # delta 从有效记录取（10.0），非退化 0


def test_pmif001_terminal_start_rejected(adapter):
    """T5: 终态/FUSE 起点拒绝（仅 P0~P8）。"""
    with pytest.raises(ValueError, match="非法起点"):
        adapter.advance_signal(SID, _sbx(alpha=1.5), current_phase="COMPLETED")
    with pytest.raises(ValueError, match="非法起点"):
        adapter.advance_signal(SID, _sbx(alpha=1.5), current_phase="FUSE")


def test_pmif001_phase_mismatch_rejected(adapter):
    """T2: 客户端声明 phase 与沙盒真实 phase 不一致 → ValueError（C03 自证）。"""
    with pytest.raises(ValueError, match="不一致"):
        adapter.advance_signal(SID, _sbx(alpha=1.5), current_phase="P4", real_phase="P1")


def test_pmif001_advance_persists_nca_to_sandbox(adapter):
    """T3: 推进结果回写沙盒 nca_ids + save_sandbox（F8 审计链完整）。"""
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    sb.activation_logs = [{"coefficient": 1.3, "status": "财政自给性达成"}]
    sb.positive_sum_logs = [{"delta": 10.0, "fuse": False}]
    st.save_sandbox(sb)
    r = adapter.advance_signal(sid, sb, current_phase="P3")
    assert r["flow_linked"] is False  # T4: 出盒评估原子信号标注
    # 回写验证：重新加载沙盒含 PHASE_ADVANCE NCA
    reloaded = st.load_sandbox(sid)
    assert r["nca_refs"]["sbx"] in reloaded.nca_ids


def test_route_advance_terminal_start_409(route_client):
    """路由层: COMPLETED 起点 → 409（T5 白名单）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    sb.activation_logs = [{"coefficient": 1.3, "status": "财政自给性达成"}]
    sb.positive_sum_logs = [{"delta": 10.0, "fuse": False}]
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/phase/{sid}/advance", json={"current_phase": "COMPLETED"})
    assert r.status_code == 409


# ---------------------------------------------------------------- V4/V5/V6 修复回归

def test_pmif001_negative_space_fuse_rejected(adapter):
    """V5: 沙盒已触碰负空间（negative_space_refs 含熔断标记）→ 拒绝推进（SV-3/ID86）。"""
    with pytest.raises(PhaseLinkError, match="负空间"):
        adapter.advance_signal(SID, _sbx(alpha=1.5, ns_flags=["NSFuse-001"]),
                               current_phase="P3")


def test_pmif001_sandbox_pass_explicit(adapter):
    """V6: sandbox_pass 显式提取——status 非财政自给性达成 → 拒绝推进。"""
    sb = mock.Mock()
    sb.negative_space_refs = []
    sb.activation_logs = [{"coefficient": 1.3, "status": "基本盈亏平衡"}]
    sb.positive_sum_logs = [{"delta": 10.0, "fuse": False}]
    with pytest.raises(PhaseLinkError, match="财政自给性"):
        adapter.advance_signal(SID, sb, current_phase="P3")


def test_pmif001_c03_verified_flag(adapter):
    """V3: 未挂接 FlowEngine（real_phase 空）→ c03_verified=false 显式标注。"""
    r = adapter.advance_signal(SID, _sbx(alpha=1.5), current_phase="P3")
    assert r["c03_verified"] is False
    assert r["nca_refs"]["pm_fingerprint"]  # V4: 指纹侧链存在
