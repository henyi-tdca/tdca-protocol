# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-5 CB-IF 契约测试——CB-IF-001 MOU 锚定 + CB-IF-001b 状态查询
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 / SV-8 + ID79/ID92 + 接口熵=0
# 先验分布:     cbdc_anchor.py + tdca-fos/tdca_adapters（mou_pipeline/dcep_adapter 只读 inproc）
# 配置权边界:   L2；仅测试环境
# 预期分配:     CB-IF 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-5 CB-IF-001/001b 契约测试（inproc MOU 锚定管线真实桥接，tdca-fos 只读）。

制度锚定: FC-SBX-OPS-001 M3-5 | SPDX-License-Identifier: TDCA-Internal

测试策略:
  - inproc MOUPipeline 桥接（SimulatedTaxAuthority + DCEPAdapter + 模拟客户端）
  - ID92 断言: simulated 显式标记；无税收/负税收拒绝（NSFL）
  - ID79 断言: MOU = Tax_in + Tax_out
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.cbdc_anchor as cbdc_anchor  # noqa: E402
from app.cbdc_anchor import CbdcAnchor, CbdcLinkError  # noqa: E402

SID = "did:tdca:sandbox:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.fixture()
def adapter():
    """inproc CbdcAnchor（MOU 锚定管线真实桥接，tdca-fos 只读）。"""
    return CbdcAnchor()


# ---------------------------------------------------------------- CB-IF-001 MOU 锚定

def test_cbif001_anchor_simulated(adapter):
    """CB-IF-001: MOU 锚定成功（模拟过渡，simulated 显式标记 + ID79 MOU=和）。"""
    r = adapter.anchor(SID, tax_in=100, tax_out=50)
    assert r["contract"] == "CB-IF-001"
    assert r["operation"] == "anchor"
    assert r["mou"] == 150  # ID79: Tax_in + Tax_out
    assert r["verified"] is True
    assert r["simulated"] is True  # ID92: 显式标记
    assert r["source"] == "SIMULATED-TAX-AUTHORITY"
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    assert r["latency_ms"] < 1000  # SV-8


def test_cbif001_anchor_negative_tax_rejected(adapter):
    """CB-IF-001: 负税收 → ValueError（NSFL 无数据/负值禁止伪造 MOU）。"""
    with pytest.raises(ValueError, match="非负"):
        adapter.anchor(SID, tax_in=-1, tax_out=50)


def test_cbif001_anchor_none_tax_rejected(adapter):
    """CB-IF-001: 税收缺失 → ValueError（NSFL 禁止伪造 MOU）。"""
    with pytest.raises(ValueError, match="伪造"):
        adapter.anchor(SID, tax_in=None, tax_out=50)


def test_cbif001_anchor_zero_tax_ok(adapter):
    """CB-IF-001: 零税收锚定（MOU=0 合法——真实零税收映射，非伪造）。"""
    r = adapter.anchor(SID, tax_in=0, tax_out=0)
    assert r["mou"] == 0
    assert r["verified"] is True


def test_cbif001_latency_over_sv8(adapter):
    """SV-8: 联动延迟 ≥1s → CbdcLinkError。"""
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        with pytest.raises(CbdcLinkError, match="SV-8"):
            adapter.anchor(SID, tax_in=100, tax_out=50)


# ---------------------------------------------------------------- CB-IF-001b 状态查询

def test_cbif001b_mou_status(adapter):
    """CB-IF-001b: MOU 状态查询（沙盒 mou_logs）。"""
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    sb.mou_logs = [{"transaction_id": "TX-1", "mou": 150, "verified": True, "simulated": True}]
    st.save_sandbox(sb)
    r = adapter.mou_status(sid)
    assert r["contract"] == "CB-IF-001b"
    assert r["mou"] == 150
    assert r["count"] == 1


# ---------------------------------------------------------------- fail-closed NCA

def test_cbif001_fail_closed_generates_error_nca(adapter):
    """fail-closed 异常路径生成 ERROR NCA（C01/SV-7 联动故障可观测）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with pytest.raises(ValueError):
        adapter.anchor(SID, tax_in=-1, tax_out=50)
    after = nca_logger.list_nca()
    assert len(after) == before + 1
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- 路由层

@pytest.fixture()
def route_client(monkeypatch):
    """路由层测试客户端（注入 inproc 适配器 + monkeypatch 自动还原）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    a = CbdcAnchor()
    monkeypatch.setattr(cbdc_anchor, "ADAPTER", a)
    return TestClient(app), a


def test_route_anchor_invalid_sandbox_422(route_client):
    """路由层: 非法 sandbox_id → 422。"""
    client, _ = route_client
    r = client.post("/api/v1/cbdc/bad-id/anchor", json={"tax_in": 100, "tax_out": 50})
    assert r.status_code == 422


def test_route_anchor_ok(route_client):
    """路由层: MOU 锚定 200（simulated 显式标记 + 回写沙盒 mou_logs）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"},
                 phase="P1")
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/cbdc/{sid}/anchor", json={"tax_in": 100, "tax_out": 50})
    assert r.status_code == 200
    assert r.json()["simulated"] is True
    assert r.json()["mou"] == 150
    reloaded = st.load_sandbox(sid)
    assert len(reloaded.mou_logs) == 1  # 回写验证


def test_route_anchor_negative_tax_422(route_client):
    """路由层: 负税收 → 422（pydantic ge=0）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)
    r = client.post(f"/api/v1/cbdc/{sid}/anchor", json={"tax_in": -5, "tax_out": 50})
    assert r.status_code == 422


def test_route_mou_status_ok(route_client):
    """路由层: MOU 状态查询 200。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"},
                 phase="P1")
    st.save_sandbox(sb)
    client.post(f"/api/v1/cbdc/{sid}/anchor", json={"tax_in": 100, "tax_out": 50})
    r = client.get(f"/api/v1/cbdc/{sid}/mou")
    assert r.status_code == 200
    assert r.json()["mou"] == 150


# ---------------------------------------------------------------- V1/V2 修复回归

def test_cbif001_id79_window_declaration(adapter):
    """V1: ID79 窗口判定显式声明（TP 层承担，锚定链路不重复实现——模拟过渡语义）。"""
    r = adapter.anchor(SID, tax_in=100, tax_out=50)
    wc = r["id79_window_check"]
    assert wc["enforced_by"] == "TP-EVALUATION-GATEWAY"
    assert wc["in_anchor_link"] is False  # M3-5 模拟过渡：M4 桥接窗口判定


def test_cbif001_dcep_layer_nca(adapter):
    """V2: DCEP 合约层生成独立 NCA（nca_generator 注入，SV-10 双向存证）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    r = adapter.anchor(SID, tax_in=100, tax_out=50)
    after = nca_logger.list_nca()
    assert len(after) >= before + 1  # CBDC_ANCHOR（SBX 侧）
    assert any("CBDC_DCEP_ANCHOR" == n["operation"] for n in after)  # DCEP 合约层（V2）\n

# ---------------------------------------------------------------- code-reviewer #1/#2/#11 修复回归

def test_cbif001_sv8_timeout_generates_error_nca(adapter):
    """#1: SV-8 超时路径生成 ERROR NCA（C01/SV-7 存证闭合）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        with pytest.raises(CbdcLinkError, match="SV-8"):
            adapter.anchor(SID, tax_in=100, tax_out=50)
    after = nca_logger.list_nca()
    assert len(after) > before  # FAIL_CLOSED NCA 已落盘（pipeline 可能已生成 DCEP NCA）
    assert any("FAIL_CLOSED" in n["operation"] for n in after[before:])


def test_cbif001_real_anchor_guard(monkeypatch):
    """#2: ID92 真实锚定守卫——管线返回 simulated=False → 拒绝（真实锚定未经授权）。"""
    fake_pipeline = mock.Mock()
    fake_pipeline.run.return_value = {
        "mou": 150, "contract_tx": "TX-REAL", "verified": True, "simulated": False,
        "nca": {"NCA-ID": "DCEP-NCA-1"},
    }
    a = CbdcAnchor()
    monkeypatch.setattr(a, "_pipeline", fake_pipeline)
    with pytest.raises(CbdcLinkError, match="真实锚定未经授权"):
        a.anchor(SID, tax_in=100, tax_out=50)


def test_cbif001_simulated_missing_fail_closed(monkeypatch):
    """#3: 管线结果缺 simulated 标记 → CbdcLinkError（ID92 守卫 fail-closed，非缺省 True）。"""
    fake_pipeline = mock.Mock()
    fake_pipeline.run.return_value = {
        "mou": 150, "contract_tx": "TX-X", "verified": True, "nca": {"NCA-ID": "DCEP-NCA-1"},
    }  # 无 simulated 字段
    a = CbdcAnchor()
    monkeypatch.setattr(a, "_pipeline", fake_pipeline)
    with pytest.raises(CbdcLinkError, match="缺 simulated"):
        a.anchor(SID, tax_in=100, tax_out=50)


def test_route_anchor_non_p1_phase_409(route_client):
    """#10: 非评估期（Phase0）沙盒锚定 → 409（MOU 锚定限评估期 P1）。"""
    client, a = route_client
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"})
    st.save_sandbox(sb)  # 默认 Phase0
    r = client.post(f"/api/v1/cbdc/{sid}/anchor", json={"tax_in": 100, "tax_out": 50})
    assert r.status_code == 409
    assert "评估期" in r.json()["detail"]


def test_cbif001_dcep_nca_ref(adapter):
    """#13: nca_refs 含 DCEP 合约层引用（SV-10 双向）。"""
    r = adapter.anchor(SID, tax_in=100, tax_out=50)
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    assert r["nca_refs"]["dcep"].startswith("NCA-")  # DCEP 合约层存证回传
