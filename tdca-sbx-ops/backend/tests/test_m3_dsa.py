# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-6 DSA 契约测试——SBX-SUSPENDED/BANNED 扩展字段 + SV-9 + 回退三档
# 约束矩阵:     FC-SBX-OPS-001 SV-9 + DSA-001（回退三档）+ 接口熵=0
# 先验分布:     dsa_extension.py + TDCA-PRINCIPLE-DSA-001
# 配置权边界:   L2；仅测试环境
# 预期分配:     DSA 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-6 DSA 契约测试（扩展字段先行，SV-9 语义）。

制度锚定: FC-SBX-OPS-001 M3-6 | SPDX-License-Identifier: TDCA-Internal

测试策略:
  - inproc 扩展字段桥接（沙盒 dsa_status 扩展字段，不动 Phase 枚举）
  - SV-9 断言: 熔断落地 100ms 内 SUSPENDED（延迟测量 + sv9_compliant）
  - DSA-001 §3.4 断言: MINOR 可 resume / MODERATE 需人类裁决 / SEVERE→BANNED 不可逆
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.dsa_extension as dsa_extension  # noqa: E402
from app.dsa_extension import (  # noqa: E402
    DsaExtension, DsaLinkError,
    BREAK_LEVEL_MINOR, BREAK_LEVEL_MODERATE, BREAK_LEVEL_SEVERE,
    DSA_ACTIVE, DSA_SUSPENDED, DSA_BANNED,
)


def _mk_sandbox(phase: str = "P0", dsa_status: str = None) -> str:
    """创建测试沙盒并返回 sandbox_id（dsa_status 扩展字段可预设）。"""
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"},
                 phase=phase)
    if dsa_status:
        sb.dsa_status = dsa_status
    st.save_sandbox(sb)
    return sid


@pytest.fixture()
def adapter():
    """inproc DsaExtension（每测试独立）。"""
    return DsaExtension()


# ---------------------------------------------------------------- 熔断落地（SV-9）

def test_dsa_suspend_minor(adapter):
    """DSA: MINOR 熔断 → SBX-SUSPENDED（SV-9 + 扩展字段回写 + NCA 存证）。"""
    sid = _mk_sandbox()
    r = adapter.suspend(sid, "轻微越界", BREAK_LEVEL_MINOR)
    assert r["dsa_status"] == DSA_SUSPENDED
    assert r["break_level"] == BREAK_LEVEL_MINOR
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    # 扩展字段回写验证
    from app import store as st
    sb = st.load_sandbox(sid)
    assert sb.dsa_status == DSA_SUSPENDED
    assert sb.dsa_break_level == BREAK_LEVEL_MINOR


def test_dsa_suspend_sv9_compliant(adapter):
    """SV-9: 熔断落地延迟 ≤100ms → sv9_compliant=True。"""
    sid = _mk_sandbox()
    r = adapter.suspend(sid, "熔断", BREAK_LEVEL_MINOR)
    assert r["sv9_compliant"] is True


def test_dsa_suspend_terminal_rejected(adapter):
    """DSA: 终态沙盒（Closed）不可迁移 SUSPENDED。"""
    sid = _mk_sandbox(phase="Closed")
    with pytest.raises(ValueError, match="终态"):
        adapter.suspend(sid, "熔断", BREAK_LEVEL_MINOR)


def test_dsa_suspend_invalid_level(adapter):
    """DSA: 非法 break_level 拒绝。"""
    sid = _mk_sandbox()
    with pytest.raises(ValueError, match="break_level"):
        adapter.suspend(sid, "熔断", "BOGUS")


# ---------------------------------------------------------------- 永久休眠（SEVERE）

def test_dsa_ban_severe(adapter):
    """DSA: SEVERE（法律负空间）→ SBX-BANNED 永久休眠（不可逆，I-5 须人类签批）。"""
    sid = _mk_sandbox()
    r = adapter.ban(sid, "触及法律负空间", human_signatory="did:tdca:HUMAN-FOUNDER-001")
    assert r["dsa_status"] == DSA_BANNED
    assert r["break_level"] == BREAK_LEVEL_SEVERE
    from app import store as st
    sb = st.load_sandbox(sid)
    assert sb.dsa_status == DSA_BANNED
    assert sb.dsa_banned_at  # 不可逆标记


def test_dsa_ban_clears_config_right_price(adapter):
    """M4-3（tdca-pricer）: BANNED 配置权价格强制归零（DSA-001 §3.4）+ S-Right 失效。"""
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"},
                 config_right_price=100.0)
    sb.s_rights = [{"scene": "community", "level": "L1", "price": 50.0}]
    st.save_sandbox(sb)
    adapter.ban(sid, "触及法律负空间", human_signatory="did:tdca:HUMAN-FOUNDER-001")
    reloaded = st.load_sandbox(sid)
    assert reloaded.config_right_price == 0.0  # 价格强制归零
    assert reloaded.s_rights[0]["frozen"] is True  # S-Right 失效
    assert reloaded.s_rights[0]["price"] == 0.0


def test_dsa_suspend_clears_config_right_price(adapter):
    """M4-3: SUSPENDED 配置权价格归零 + 调用停止（DSA-001 §3.4 回退路径）。"""
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="t", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={"目标函数": "x", "约束矩阵": "x",
                                                            "先验分布": "x", "配置权边界": "x",
                                                            "预期分配": "x", "审计轨迹": "x"},
                 config_right_price=80.0)
    sb.pucr = {"amount": 1000}
    st.save_sandbox(sb)
    adapter.suspend(sid, "轻微越界", BREAK_LEVEL_MINOR)
    reloaded = st.load_sandbox(sid)
    assert reloaded.config_right_price == 0.0  # 价格归零
    assert reloaded.pucr.get("price_cleared") is True  # 持价重置


def test_dsa_ban_requires_human_signatory(adapter):
    """I-5: 永久休眠无人类签批 → 拒绝（L0 法律负空间最重裁决）。"""
    sid = _mk_sandbox()
    with pytest.raises(ValueError, match="人类裁决签批"):
        adapter.ban(sid, "触及法律负空间")


def test_dsa_ban_irreversible(adapter):
    """DSA: BANNED 不可恢复（resume 拒绝）。"""
    sid = _mk_sandbox(dsa_status=DSA_BANNED)
    with pytest.raises(ValueError, match="不可恢复"):
        adapter.resume(sid)


def test_dsa_ban_double_rejected(adapter):
    """DSA: 已 BANNED 沙盒再 ban 拒绝。"""
    sid = _mk_sandbox(dsa_status=DSA_BANNED)
    with pytest.raises(ValueError, match="已 BANNED"):
        adapter.ban(sid, "再次触及", human_signatory="did:tdca:HUMAN-FOUNDER-001")


# ---------------------------------------------------------------- I-1/I-2/T-2 修复回归

def test_dsa_banned_not_overridable_by_suspend(adapter):
    """I-1: BANNED 不可被 suspend 覆盖（ID86 永久休眠不可逆）。"""
    sid = _mk_sandbox(dsa_status=DSA_BANNED)
    with pytest.raises(ValueError, match="不可覆盖"):
        adapter.suspend(sid, "尝试覆盖", BREAK_LEVEL_MINOR)


def test_dsa_suspend_severe_rejected(adapter):
    """I-2: suspend 拒绝 SEVERE（法律负空间须走 ban 端点，防绕过 BANNED）。"""
    sid = _mk_sandbox()
    with pytest.raises(ValueError, match="必须经 ban"):
        adapter.suspend(sid, "严重越界", BREAK_LEVEL_SEVERE)


def test_dsa_resume_non_suspended_rejected(adapter):
    """T-2: 仅 SUSPENDED 可 resume（ACTIVE 直接 resume 拒绝）。"""
    sid = _mk_sandbox()  # 默认 dsa_status=None
    with pytest.raises(ValueError, match="仅 SBX-SUSPENDED"):
        adapter.resume(sid)


# ---------------------------------------------------------------- 恢复（回退三档）

def test_dsa_resume_minor_ok(adapter):
    """DSA: MINOR 越界限期重整后恢复 → SBX-ACTIVE。"""
    sid = _mk_sandbox()
    adapter.suspend(sid, "轻微越界", BREAK_LEVEL_MINOR)
    r = adapter.resume(sid)
    assert r["dsa_status"] == DSA_ACTIVE
    from app import store as st
    sb = st.load_sandbox(sid)
    assert sb.dsa_status == DSA_ACTIVE


def test_dsa_resume_moderate_requires_human(adapter):
    """DSA: MODERATE 越界恢复须人类裁决（DSA-001 §3.4）。"""
    sid = _mk_sandbox()
    adapter.suspend(sid, "中度越界", BREAK_LEVEL_MODERATE)
    with pytest.raises(ValueError, match="人类裁决"):
        adapter.resume(sid)
    r = adapter.resume(sid, human_approval="did:tdca:HUMAN-FOUNDER-001")
    assert r["dsa_status"] == DSA_ACTIVE


# ---------------------------------------------------------------- 状态查询

def test_dsa_status_query(adapter):
    """DSA: 状态查询返回 dsa_status/break_level/phase。"""
    sid = _mk_sandbox()
    adapter.suspend(sid, "熔断", BREAK_LEVEL_MINOR)
    r = adapter.status(sid)
    assert r["dsa_status"] == DSA_SUSPENDED
    assert r["phase"] == "P0"  # Phase 枚举不动（扩展字段先行）


# ---------------------------------------------------------------- fail-closed

def test_dsa_fail_closed_generates_error_nca(adapter):
    """fail-closed 异常路径生成 ERROR NCA（C01/SV-7）。"""
    from app import nca_logger
    before = len(nca_logger.list_nca())
    with pytest.raises(ValueError, match="不存在"):
        adapter.suspend("did:tdca:sandbox:ffffffffffffffffffffffffffffffff", "x", BREAK_LEVEL_MINOR)
    after = nca_logger.list_nca()
    assert len(after) == before + 1
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- 路由层

@pytest.fixture()
def route_client(monkeypatch):
    """路由层测试客户端（注入 inproc 适配器 + monkeypatch 自动还原）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    a = DsaExtension()
    monkeypatch.setattr(dsa_extension, "ADAPTER", a)
    return TestClient(app), a


def test_route_suspend_ok(route_client):
    """路由层: 熔断落地 200（SV-9）。"""
    client, a = route_client
    sid = _mk_sandbox()
    r = client.post(f"/api/v1/dsa/{sid}/suspend",
                    json={"reason": "轻微越界", "break_level": "MINOR"})
    assert r.status_code == 200
    assert r.json()["dsa_status"] == DSA_SUSPENDED


def test_route_suspend_invalid_level_409(route_client):
    """路由层: 非法档位 → 409。"""
    client, a = route_client
    sid = _mk_sandbox()
    r = client.post(f"/api/v1/dsa/{sid}/suspend", json={"reason": "非法档位", "break_level": "BOGUS"})
    assert r.status_code == 409


def test_route_ban_ok(route_client):
    """路由层: 永久休眠 200（不可逆，I-5 人类签批）。"""
    client, a = route_client
    sid = _mk_sandbox()
    r = client.post(f"/api/v1/dsa/{sid}/ban",
                    json={"reason": "触及法律负空间", "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
    assert r.status_code == 200
    assert r.json()["dsa_status"] == DSA_BANNED


def test_route_resume_moderate_no_human_409(route_client):
    """路由层: MODERATE 恢复无人类裁决 → 409。"""
    client, a = route_client
    sid = _mk_sandbox()
    client.post(f"/api/v1/dsa/{sid}/suspend",
                json={"reason": "中度越界", "break_level": "MODERATE"})
    r = client.post(f"/api/v1/dsa/{sid}/resume", json={"human_approval": ""})
    assert r.status_code == 409


def test_route_status_ok(route_client):
    """路由层: DSA 状态查询 200。"""
    client, a = route_client
    sid = _mk_sandbox()
    client.post(f"/api/v1/dsa/{sid}/suspend", json={"reason": "轻微越界", "break_level": "MINOR"})
    r = client.get(f"/api/v1/dsa/{sid}/status")
    assert r.status_code == 200
    assert r.json()["dsa_status"] == DSA_SUSPENDED
