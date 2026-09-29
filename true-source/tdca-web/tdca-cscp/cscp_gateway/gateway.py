# -*- coding: utf-8 -*-
"""
CSCP 跨场景协作握手协议 · 网关 API（T-CSCP-001，FastAPI）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §三（5 POST + 1 GET）+ §2.1 人类签名插入点 #1/#2
端到端 <3s（Step 分解 500ms/1s/1.5s/500ms）；HumanGate 双签名不可绕过（H-CSCP-005）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import sys
from pathlib import Path

# 运行时路径注入（可用性修复）: 跨项目依赖（tdca-d2-union / translator-market / workbuddy）
# 加入 sys.path，使 uvicorn 直接可启动（测试 conftest 已注入；运行时此前缺失致 /handshake/list 500）
_SIBLINGS = ("tdca-d2-union", "tdca-translator-market", "tdca-workbuddy")
_ROOT = Path(__file__).resolve().parents[2]
for _sub in _SIBLINGS:
    _p = _ROOT / _sub
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .adapters import (MockCBDCContractAdapter, MockNSFLUnionAdapter,
                       MockSandboxAdapter, MockTranslatorAdapter,
                       MockWorkbuddyAdapter, RealWorkbuddyAdapter)
from .human_gate import HumanGate
from .saga import Saga
from .state_machine import HandshakeStateMachine, HandshakeStatus

app = FastAPI(title="CSCP Handshake Gateway", version="T-CSCP-001")


# ---------------------------------------------------------------------------
# 依赖装配（模拟态: R-CSCP-001 mock 占位；D-2 W2 输出后替换 NSFLUnionAdapter）
# ---------------------------------------------------------------------------

def build_state_machine(use_real_engine: bool = True,
                        use_real_workbuddy: bool = True) -> HandshakeStateMachine:
    """依赖装配（C2: 默认真实 D-2 引擎；F-5: 默认真实 P5 Workbuddy；mock 保留 fallback）。

    :param use_real_engine: True → CSCPNSFLAdapter（真实 NSFLUnionEngine，FROZEN 契约）
    :param use_real_workbuddy: True → RealWorkbuddyAdapter（P5 T-P5-001 真实执行，F-5 缺口 II 关闭）
    """
    saga = Saga(
        refund_fn=lambda: None,
        unlock_fn=lambda: None,
        cancel_fn=lambda: None,
        release_fn=lambda: None,
    )
    if use_real_engine:
        from nsfl_union import NSFLUnionEngine
        from .cscp_nsfl_adapter import CSCPNSFLAdapter
        adapter = CSCPNSFLAdapter(NSFLUnionEngine())
        preflight_fn = adapter.preflight_check
    else:
        preflight_fn = MockNSFLUnionAdapter().preflight_check
    workbuddy_fn = RealWorkbuddyAdapter().create_work_order if use_real_workbuddy \
        else MockWorkbuddyAdapter().create_work_order
    human_gate = HumanGate()   # T-CSCP-008: 真实级签名验证（challenge-response + HMAC + 防重放）
    return HandshakeStateMachine(
        preflight_fn=preflight_fn,
        sandbox_fn=MockSandboxAdapter().verify,
        translator_fn=MockTranslatorAdapter().match,
        cbdclock_fn=MockCBDCContractAdapter().lock,
        workbuddy_fn=workbuddy_fn,
        saga=saga, human_gate=human_gate,
    )


_state_machine: Optional[HandshakeStateMachine] = None
_use_real_engine: bool = True   # C2 默认真实引擎（可经 build_state_machine(use_real_engine=False) 回退 mock）


def _sm() -> HandshakeStateMachine:
    global _state_machine
    if _state_machine is None:
        _state_machine = build_state_machine(use_real_engine=_use_real_engine)
    return _state_machine


# ---------------------------------------------------------------------------
# 请求/响应模型（对齐 CSCP 任务书 §三 接口形状）
# ---------------------------------------------------------------------------

class InitiateRequest(BaseModel):
    caller_scene: Dict[str, Any]
    callee_scene: Dict[str, Any]
    caller_tier: str = "L2"
    cross_scene_flag: bool = True
    requested_right: str = "CONFIG"   # E2E-004: 请求权利（P_RIGHT 需 L0/L1）


class MatchRequest(BaseModel):
    human_signature_1: str


class LockRequest(BaseModel):
    mou_split_ratio: float = Field(gt=0.0, le=1.0, description="MOU 分割比例 (0,1]（红队 #2 #10）")


class DispatchRequest(BaseModel):
    human_signature_2: str


class ChallengeRequest(BaseModel):
    action: str   # MATCH | DISPATCH（T-CSCP-008）


@app.post("/handshake/challenge/{handshake_id}", status_code=201)
def challenge(handshake_id: str, req: ChallengeRequest) -> Dict[str, Any]:
    """T-CSCP-008: 签发一次性 challenge（nonce），供人类签名设备/测试签发签名。"""
    try:
        _sm().status(handshake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="handshake_id 不存在")
    ch = _sm()._human_gate.issue_challenge(handshake_id, req.action)
    return {"handshake_id": handshake_id, "action": req.action,
            "nonce": ch["nonce"], "expires_in": ch["expires_in"]}


def _state_view(h) -> Dict[str, Any]:
    return {
        "handshake_id": h.handshake_id,
        "current_step": h.current_step.value if h.current_step else None,
        "status": h.status.value,
        "step_durations": h.step_durations,
        "nca_refs": h.nca_refs,
        "human_gates": h.human_gates,
        "risk_premium": h.risk_premium,
        "rejection_reason": h.rejection_reason,
        "rejection_step": h.rejection_step,
        "alt_paths": h.alt_paths,
        "preflight_status": h.preflight_status,   # 红队复审 N6
        "escrow_id": h.escrow_id,
        "work_order_id": h.work_order_id,
    }


# ---------------------------------------------------------------------------
# 端点（Step-1 ~ Step-5）
# ---------------------------------------------------------------------------

@app.post("/handshake/initiate", status_code=201)
def initiate(req: InitiateRequest) -> Dict[str, Any]:
    h = _sm().initiate(req.model_dump())
    return {"handshake_id": h.handshake_id, "status": h.status.value}


@app.post("/handshake/preflight")
def preflight(handshake_id: str, req: InitiateRequest) -> Dict[str, Any]:
    h = _sm().preflight(handshake_id, req.model_dump())
    if h.status == HandshakeStatus.REJECTED:
        # 契约层状态（红队 #2 #8）: 返回 preflight_status（PASS/FAIL/TRIGGERED/REJECTED）
        return {"handshake_id": handshake_id, "status": h.preflight_status or h.status.value,
                "rejection_reason": h.rejection_reason, "rejection_step": h.rejection_step,
                "alt_paths": h.alt_paths, "nca_ref": h.nca_refs[-1] if h.nca_refs else None}
    return {"handshake_id": handshake_id, "status": h.preflight_status or h.status.value,
            "ns_union": h.ns_union, "risk_premium": h.risk_premium,
            "next_step": "sandbox_verify", "nca_ref": h.nca_refs[-1] if h.nca_refs else None}


@app.post("/handshake/match")
def match(handshake_id: str, req: MatchRequest) -> Dict[str, Any]:
    h = _sm().match(handshake_id, req.human_signature_1)
    if h.status == HandshakeStatus.REJECTED:
        return {"status": "REJECTED", "reason": h.rejection_reason, "nca_ref": h.nca_refs[-1] if h.nca_refs else None}
    return {"status": "MATCHED", "sandbox_status": "ACTIVE",
            "human_gate_1": h.human_gates["gate1"], "nca_ref": h.nca_refs[-1] if h.nca_refs else None}


@app.post("/handshake/lock")
def lock(handshake_id: str, req: LockRequest) -> Dict[str, Any]:
    h = _sm().lock(handshake_id, req.mou_split_ratio)
    if h.status == HandshakeStatus.REJECTED:
        return {"status": "REJECTED", "reason": h.rejection_reason, "nca_ref": h.nca_refs[-1] if h.nca_refs else None}
    return {"status": "LOCKED", "lock_tx_hash": h.lock_tx_hash, "escrow_id": h.escrow_id,
            "nca_ref": h.nca_refs[-1] if h.nca_refs else None}


@app.post("/handshake/dispatch")
def dispatch(handshake_id: str, req: DispatchRequest) -> Dict[str, Any]:
    h = _sm().dispatch(handshake_id, req.human_signature_2)
    if h.status == HandshakeStatus.COMPLETED:
        return {"status": "DISPATCHED", "work_order_id": h.work_order_id,
                "nca_ref": h.nca_refs[-1] if h.nca_refs else None}
    return {"status": "REJECTED", "reason": h.rejection_reason, "nca_ref": h.nca_refs[-1] if h.nca_refs else None}


@app.post("/handshake/cancel/{handshake_id}")
def cancel(handshake_id: str) -> Dict[str, Any]:
    """E2E-010: Step-5 执行前取消 → Saga 逆序回滚（ESCROW_REFUND 等）。"""
    try:
        h = _sm().cancel(handshake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="handshake_id 不存在")
    return {"handshake_id": handshake_id, "status": h.status.value,
            "reason": h.rejection_reason,
            "nca_ref": h.nca_refs[-1] if h.nca_refs else None}


@app.get("/handshake/status/{handshake_id}")
def status(handshake_id: str) -> Dict[str, Any]:
    try:
        h = _sm().status(handshake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="handshake_id 不存在")
    return _state_view(h)


# ---- W7 前端契约端点（只读，LifecycleDashboard）----

@app.get("/handshake/list")
def handshake_list(page: int = 1, limit: int = 20,
                   status_filter: Optional[str] = None) -> Dict[str, Any]:
    """W7: 握手会话列表（分页/状态过滤）——LifecycleDashboard 数据源。"""
    states = _sm()._states.values()
    if status_filter:
        states = [s for s in states if s.status.value == status_filter.upper()]
    items = sorted(states, key=lambda s: s.handshake_id, reverse=True)
    start = (page - 1) * limit
    page_items = items[start:start + limit]
    return {"total": len(items),
            "items": [{"handshake_id": s.handshake_id, "status": s.status.value,
                       "current_step": s.current_step.value if s.current_step else None,
                       "preflight_status": s.preflight_status,
                       "risk_premium": s.risk_premium,
                       "escrow_id": s.escrow_id,
                       "work_order_id": s.work_order_id,
                       "nca_count": len(s.nca_refs),
                       "human_gates": s.human_gates}
                      for s in page_items]}


@app.get("/handshake/detail")
def handshake_detail(handshake_id: str) -> Dict[str, Any]:
    """W7: 握手详情（全链路展开）——LifecycleDashboard 详情面板。"""
    try:
        h = _sm().status(handshake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="handshake_id 不存在")
    return {**_state_view(h),
            "ns_union": h.ns_union,
            "escrow_id": h.escrow_id,
            "lock_tx_hash": h.lock_tx_hash,
            "work_order_id": h.work_order_id,
            "caller_tier": h.caller_tier,
            "requested_right": h.requested_right}


@app.get("/nca/chain")
def nca_chain(handshake_id: str) -> Dict[str, Any]:
    """W7: NCA 链追踪（全链路 NCA 引用）——LifecycleDashboard NCA 链。"""
    try:
        h = _sm().status(handshake_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="handshake_id 不存在")
    chain = [{"index": i + 1, "nca_ref": ref,
              "link": f"nca://tdca/{h.handshake_id}/{i + 1:03d}"}
             for i, ref in enumerate(h.nca_refs)]
    return {"handshake_id": handshake_id, "chain": chain,
            "total": len(chain)}
