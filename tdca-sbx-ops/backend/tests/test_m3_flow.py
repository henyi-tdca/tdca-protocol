# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-2 FE-IF 契约测试——FE-IF-001 状态同步 + FE-IF-002 阶段推进信号
# 约束矩阵:     FC-SBX-OPS-001 SV-1（α>1.2 必要非充分）/ SV-8 + 接口熵=0
# 先验分布:     flow_adapter.py + tdca-flow-orchestrator（FC-012 只读 inproc）
# 配置权边界:   L2；仅测试环境
# 预期分配:     FE-IF 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-2 FE-IF-001/002 契约测试（inproc 桥接真实 FlowEngine + http monkeypatch）。

制度锚定: FC-SBX-OPS-001 M3-2 | SPDX-License-Identifier: TDCA-Internal

测试策略:
  - inproc 模式: 真实 FlowEngine 桥接（tdca_flow_src 别名，FC-012 只读），确定性隔离
  - http 模式: monkeypatch _http_call 模拟 8001 服务（不依赖常驻）
  - SV-1 断言: α≤1.2 拒绝推进信号（必要非充分——须消费沙盒真实评估记录）
  - I-1 断言: sync_phase 以沙盒真实 Phase 为输入，服务端构造穿越 context
  - I-2 断言: activation_signal 消费 activation_logs/positive_sum_logs，不接受客户端自报
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.flow_adapter as flow_adapter  # noqa: E402
from app.flow_adapter import FlowAdapter, FlowLinkError  # noqa: E402

SID = "did:tdca:sandbox:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _sbx_stub(phase: str = "P0", alpha: float = 1.25, delta: float = 10.0,
              fuse: bool = False, no_logs: bool = False) -> mock.Mock:
    """构造沙盒桩（携带真实评估记录，模拟 Sandbox 实例）。"""
    sb = mock.Mock()
    if no_logs:
        sb.activation_logs = []
        sb.positive_sum_logs = []
    else:
        sb.activation_logs = [{"coefficient": alpha, "status": "财政自给性达成"}]
        sb.positive_sum_logs = [{"delta": delta, "fuse": fuse}]
    return sb


@pytest.fixture()
def adapter():
    """inproc 适配器（每测试独立，FlowEngine 内存态隔离）。"""
    return FlowAdapter(mode="inproc")


@pytest.fixture()
def hooked(adapter):
    """挂接一个沙盒。"""
    return adapter.hook_sandbox(SID, {"type": "test"})


# ---------------------------------------------------------------- FE-IF-001 挂接

def test_feif001_hook_starts_lifecycle(adapter):
    """FE-IF-001: 挂接启动 FlowEngine 生命周期（Phase P0）+ NCA 回引（SV-10）。"""
    r = adapter.hook_sandbox(SID, {"type": "sbx"})
    assert r["contract"] == "FE-IF-001"
    assert r["operation"] == "hook"
    assert r["flow_id"].startswith("FLOW-")
    assert r["phase"] == "P0"
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # I-3: 真实 nca_id 回引
    assert SID in adapter._hooks


def test_feif001_duplicate_hook_rejected(adapter, hooked):
    """FE-IF-001: 重复挂接拒绝（409 语义）。"""
    with pytest.raises(ValueError, match="已挂接"):
        adapter.hook_sandbox(SID, {"type": "sbx"})


def test_feif001_status_query(adapter, hooked):
    """FE-IF-001: 状态查询返回 phase/phase_seq。"""
    r = adapter.status(SID)
    assert r["contract"] == "FE-IF-001"
    assert r["operation"] == "status"
    assert r["phase"] == "P0"
    assert r["phase_seq"] == ["P0"]


def test_feif001_status_unhooked_raises(adapter):
    """FE-IF-001: 未挂接沙盒状态查询 → KeyError（404 语义）。"""
    with pytest.raises(KeyError, match="未挂接"):
        adapter.status("did:tdca:sandbox:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")


# ---------------------------------------------------------------- FE-IF-001 阶段同步（I-1）

def test_feif001_sync_sbx_p0_to_p1(adapter, hooked):
    """FE-IF-001: 沙盒 P0 → FlowEngine P1（服务端构造 context，I-1 映射）。"""
    r = adapter.sync_phase(SID, "P0", real_phase="P0")
    assert r["contract"] == "FE-IF-001"
    assert r["operation"] == "sync"
    assert r["phase"] == "P1"
    assert r["phase_seq"] == ["P0", "P1"]
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # I-3


def test_feif001_sync_sbx_p1_to_p3(adapter, hooked):
    """FE-IF-001: 沙盒 P1（评估）→ FlowEngine P3（映射跳级，I-1）。"""
    adapter.sync_phase(SID, "P0", real_phase="P0")  # → P1
    r = adapter.sync_phase(SID, "P1", real_phase="P1")  # P1 映射 → 逐段推进 P3
    assert r["phase"] == "P3"


def test_feif001_sync_unmapped_phase_rejected(adapter, hooked):
    """FE-IF-001: 无映射沙盒 Phase → KeyError（拒绝未知状态）。"""
    with pytest.raises(KeyError, match="无 FlowEngine 映射"):
        adapter.sync_phase(SID, "Closed", real_phase="Phase0")


# ---------------------------------------------------------------- FE-IF-002 阶段推进信号（I-2）

def test_feif002_activation_signal_consumes_real_records(adapter, hooked):
    """FE-IF-002: 消费沙盒真实评估记录（α>1.2 + 正和过）→ advance P3→P4。"""
    # 推进到 P3（沙盒 Phase 同步路径）
    adapter.sync_phase(SID, "P0", real_phase="P0")  # → P1
    adapter.sync_phase(SID, "P1", real_phase="P1")  # → P3
    sb = _sbx_stub(alpha=1.25, delta=10.0)
    r = adapter.activation_signal(SID, sb)
    assert r["contract"] == "FE-IF-002"
    assert r["operation"] == "advance"
    assert r["alpha"] == 1.25  # 来自沙盒 activation_logs，非客户端
    assert r["phase"] == "P4"
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # I-3


def test_feif002_activation_alpha_le_12_rejected(adapter, hooked):
    """FE-IF-002: α≤1.2 拒绝推进信号（SV-1 必要非充分，I-2 真实记录）。"""
    sb = _sbx_stub(alpha=1.2, delta=0.0)
    with pytest.raises(ValueError, match="SV-1"):
        adapter.activation_signal(SID, sb)


def test_feif002_no_activation_logs_rejected(adapter, hooked):
    """FE-IF-002: 沙盒无激活系数记录 → ValueError（须先 F3 evaluate，I-2 防客户端自报）。"""
    with pytest.raises(ValueError, match="无激活系数评估记录"):
        adapter.activation_signal(SID, _sbx_stub(no_logs=True))


def test_feif002_positive_sum_fused_rejected(adapter, hooked):
    """FE-IF-002: 最近正和验证 fuse → 拒绝推进（I-2 消费 positive_sum_logs）。"""
    adapter.sync_phase(SID, "P0", real_phase="P0")
    adapter.sync_phase(SID, "P1", real_phase="P1")
    sb = _sbx_stub(alpha=1.3, delta=0.0, fuse=True)
    with pytest.raises(ValueError, match="正和验证未通过"):
        adapter.activation_signal(SID, sb)


def test_feif002_activation_signal_unhooked(adapter):
    """FE-IF-002: 未挂接沙盒 → KeyError。"""
    with pytest.raises(KeyError, match="未挂接"):
        adapter.activation_signal("did:tdca:sandbox:cccccccccccccccccccccccccccccccc",
                                  _sbx_stub(alpha=1.5))


# ---------------------------------------------------------------- fail-closed（I-5/I-6）

def test_feif_sync_latency_over_sv8(adapter, hooked):
    """I-5: 联动延迟 ≥1s 违反 SV-8 → FlowLinkError。"""
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        with pytest.raises(FlowLinkError, match="SV-8"):
            adapter.sync_phase(SID, "P0", real_phase="P0")


def test_feif_fail_closed_generates_error_nca(adapter, hooked):
    """I-6: fail-closed 异常路径生成 ERROR NCA（C01/SV-7 联动故障可观测）。"""
    from app import nca_logger

    before = len(nca_logger.list_nca())
    sb = _sbx_stub(alpha=1.2)  # SV-1 拒绝 → fail-closed
    with pytest.raises(ValueError):
        adapter.activation_signal(SID, sb)
    after = nca_logger.list_nca()
    assert len(after) == before + 1  # ERROR NCA 已落盘
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- http 模式（monkeypatch）

def _stub_http(responses: list) -> mock.Mock:
    seq = iter(responses)

    def fake(method, path, body=None, params=None):
        try:
            return next(seq)
        except StopIteration:
            return (200, {})

    return mock.Mock(side_effect=fake)


def test_http_mode_hook(monkeypatch):
    """http 模式: hook 调用 8001 /api/v1/flow/start（契约断言）。"""
    monkeypatch.setattr(flow_adapter.FlowAdapter, "_http_call",
                        _stub_http([(200, {"flow_id": "FLOW-abc12345", "phase": "P0",
                                           "phase_seq": ["P0"]})]))
    a = FlowAdapter(mode="http")
    r = a.hook_sandbox(SID, {"type": "sbx"})
    assert r["flow_id"] == "FLOW-abc12345"
    assert r["phase"] == "P0"


def test_http_mode_flow_unreachable(monkeypatch):
    """http 模式: FlowEngine 8001 不可达 → FlowLinkError（fail-closed）。"""
    def boom(method, path, body=None, params=None):
        raise FlowLinkError("[FE-IF] FlowEngine 服务不可达")
    monkeypatch.setattr(flow_adapter.FlowAdapter, "_http_call", boom)
    a = FlowAdapter(mode="http")
    with pytest.raises(FlowLinkError, match="不可达"):
        a.hook_sandbox(SID, {"type": "sbx"})


def test_http_mode_response_missing_phase(monkeypatch):
    """T-2: http 响应缺 phase → FlowLinkError（契约破坏 fail-closed，不静默降级）。"""
    monkeypatch.setattr(flow_adapter.FlowAdapter, "_http_call",
                        _stub_http([(200, {"flow_id": "FLOW-abc12345"})]))
    a = FlowAdapter(mode="http")
    with pytest.raises(FlowLinkError, match="契约破坏"):
        a.hook_sandbox(SID, {"type": "sbx"})


# ---------------------------------------------------------------- 路由层（T-3/T-5/T-8）

@pytest.fixture()
def route_client(monkeypatch):
    """路由层测试客户端（注入 inproc 适配器 + monkeypatch 自动还原，T-8）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    a = FlowAdapter(mode="inproc")
    monkeypatch.setattr(flow_adapter, "ADAPTER", a)
    return TestClient(app), a


def test_route_hook_invalid_sandbox_id_422(route_client):
    """T-3: 非法 sandbox_id 格式 → 422（非 500）。"""
    client, _ = route_client
    r = client.post("/api/v1/flow/hook", json={"sandbox_id": "bad-id"})
    assert r.status_code == 422


def test_route_hook_404_unhooked(route_client):
    """T-3/T-5: 不存在沙盒 → 404。"""
    client, _ = route_client
    r = client.post("/api/v1/flow/hook",
                    json={"sandbox_id": "did:tdca:sandbox:deadbeefdeadbeefdeadbeefdeadbeef"})
    assert r.status_code == 404


def test_route_sync_unhooked_404(route_client):
    """T-5: 未挂接沙盒 sync → 404。"""
    client, a = route_client
    r = client.post("/api/v1/flow/did:tdca:sandbox:deadbeefdeadbeefdeadbeefdeadbeef/sync",
                    json={"sbx_phase": "P0"})
    assert r.status_code == 404


def test_route_advance_no_records_422(route_client):
    """T-4: 沙盒无评估记录 → 422（非 500，I-2 真实记录消费）。"""
    client, a = route_client
    # 创建真实沙盒（经 store）
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    a.hook_sandbox(sid, {"type": "t"})
    r = client.post(f"/api/v1/flow/{sid}/advance", json={"sandbox_id": sid})
    assert r.status_code == 422  # 无评估记录


def test_route_hooks_endpoint_ok(route_client):
    """I-7: hooks 台账端点 200。"""
    client, a = route_client
    sid = "did:tdca:sandbox:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    a.hook_sandbox(sid, {"type": "t"})
    r = client.get("/api/v1/flow/hooks")
    assert r.status_code == 200
    assert len(r.json()["hooks"]) == 1


# ---------------------------------------------------------------- V3 修复：真实 phase 核对

def test_feif001_sync_phase_mismatch_rejected(adapter, hooked):
    """V3: 客户端声明 phase 与沙盒真实 phase 不一致 → ValueError（C03 自证）。"""
    with pytest.raises(ValueError, match="不一致"):
        adapter.sync_phase(SID, "P1", real_phase="Phase0")  # 沙盒实为 Phase0，声明 P1


def test_route_sync_phase_mismatch_409(route_client):
    """V3 路由层: phase 不一致 → 409（非静默放行）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    a.hook_sandbox(sid, {"type": "t"})
    r = client.post(f"/api/v1/flow/{sid}/sync", json={"sbx_phase": "P1"})  # 沙盒实为 Phase0
    assert r.status_code == 409


# ---------------------------------------------------------------- V1/V2 修复：http NCA 存证

def test_http_mode_sync_generates_new_nca(monkeypatch):
    """V1: http 模式 sync 成功后生成新 NCA（不复用 hook NCA，C01/SV-7）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    monkeypatch.setattr(
        flow_adapter.FlowAdapter, "_http_call",
        _stub_http([
            (200, {"flow_id": "FLOW-abc12345", "phase": "P0", "phase_seq": ["P0"]}),  # start
            (200, {"flow_id": "FLOW-abc12345", "phase": "P0", "phase_seq": ["P0"]}),  # status
            (200, {"flow_id": "FLOW-abc12345", "phase": "P1", "phase_seq": ["P0", "P1"],
                   "nca_records": [{"nca_id": "FLOW-NCA-1"}]}),  # advance
        ]),
    )
    a = FlowAdapter(mode="http")
    a.hook_sandbox(SID, {"type": "sbx"})
    r = a.sync_phase(SID, "P0", real_phase="P0")
    after = nca_logger.list_nca()
    assert len(after) > before  # 本次 sync 生成新 NCA
    assert r["nca_refs"]["sbx"] == after[-1]["nca_id"]
    assert r["nca_refs"]["flow"] == "FLOW-NCA-1"  # V2: flow 侧引用
