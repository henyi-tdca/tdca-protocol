# -*- coding: utf-8 -*-
"""
CSCP 跨场景协作握手协议 · 五步状态机（T-CSCP-001 核心）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §2.1/§2.2（状态机 + 超时回滚 + 人类签名强制插入点 #1/#2）
     + DCD-CSCP-CHANGE-001（preflight 映射: HIGH→TRIGGERED / MEDIUM→FAIL / LOW→PASS / 兜底→REJECTED）
术语基线: 注册表 V1.1 + 防火墙 V1.0
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .human_gate import ACTION_DISPATCH, ACTION_MATCH, HumanGate
from .saga import Saga


class Step(Enum):
    STEP1 = "STEP1"   # 调用发起
    STEP2 = "STEP2"   # 负空间预检（D-2）
    STEP3 = "STEP3"   # 沙盒校验 + 配置权匹配（人类签名 #1 插入点）
    STEP4 = "STEP4"   # CBDC 锁定 escrow
    STEP5 = "STEP5"   # 调度指令（人类签名 #2 插入点）


class HandshakeStatus(Enum):
    INIT = "INIT"
    PENDING_NSFL = "PENDING_NSFL"
    PENDING_SANDBOX = "PENDING_SANDBOX"
    PENDING_LOCK = "PENDING_LOCK"
    PENDING_DISPATCH = "PENDING_DISPATCH"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class PreflightStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    TRIGGERED = "TRIGGERED"
    REJECTED = "REJECTED"


# Step 延迟上限（秒）: 2<500ms / 3<1s / 4<1.5s / 5<500ms（CSCP 任务书 §2.1）
STEP_TIME_LIMITS: Dict[Step, float] = {
    Step.STEP2: 0.5,
    Step.STEP3: 1.0,
    Step.STEP4: 1.5,
    Step.STEP5: 0.5,
}


def _tier_rank(tier: str) -> int:
    """E2E-004: 配置权层级排名（L0 最高）。"""
    return {"L0": 0, "L1": 1, "L2": 2, "L3": 3}.get(str(tier).upper(), 99)


@dataclass
class HandshakeState:
    """握手会话状态（GET /handshake/status 视图）。"""
    handshake_id: str
    status: HandshakeStatus = HandshakeStatus.INIT
    current_step: Optional[Step] = None
    step_started_at: float = 0.0
    step_durations: Dict[str, float] = field(default_factory=dict)
    nca_refs: List[str] = field(default_factory=list)
    human_gates: Dict[str, bool] = field(default_factory=lambda: {"gate1": False, "gate2": False})
    rejection_reason: Optional[str] = None
    rejection_step: Optional[str] = None
    alt_paths: Optional[List[str]] = None
    preflight_status: Optional[str] = None      # 契约层状态（PASS/FAIL/TRIGGERED/REJECTED，红队 #2 #8）
    caller_tier: str = "L2"                     # E2E-004: 配置权层级（Step-3 effectiveTier 检查）
    requested_right: str = "CONFIG"             # E2E-004: 请求权利（P_RIGHT 需高级别层级）
    ns_union: Optional[dict] = None
    risk_premium: float = 0.0
    escrow_id: Optional[str] = None
    lock_tx_hash: Optional[str] = None
    work_order_id: Optional[str] = None


class HandshakeStateMachine:
    """五步状态机 + 超时检测 + 人类门禁（不可绕过）+ Saga 补偿链。"""

    def __init__(self, preflight_fn, sandbox_fn, translator_fn, cbdclock_fn,
                 workbuddy_fn, saga=None, human_gate=None, nca_fn=None, now=time.monotonic):
        self._preflight = preflight_fn      # Step-2: P2 并集引擎（或 mock）
        self._sandbox = sandbox_fn          # Step-3: P3 沙盒校验
        self._translator = translator_fn    # Step-3: P4 翻译器匹配
        self._cbdclock = cbdclock_fn        # Step-4: CBDC escrow 锁定
        self._workbuddy = workbuddy_fn      # Step-5: P5 Workbuddy 调度
        self._saga = saga or Saga()
        self._human_gate = human_gate       # T-CSCP-008: 真实签名验证（None → 回退模拟级）
        self._nca = nca_fn
        self._now = now
        self._states: Dict[str, HandshakeState] = {}

    # ---- 对外动作 ----

    def initiate(self, request: dict) -> HandshakeState:
        """Step-1 调用发起 → PENDING_NSFL。记录 tier/right（E2E-004）。"""
        h = HandshakeState(handshake_id=f"HS-{uuid.uuid4().hex[:12]}")
        h.caller_tier = request.get("caller_tier", "L2")
        h.requested_right = request.get("requested_right", "CONFIG")
        h.status = HandshakeStatus.PENDING_NSFL
        h.current_step = Step.STEP2
        h.step_started_at = self._now()
        self._states[h.handshake_id] = h
        self._record_nca(h, "STEP1_INITIATED", {"caller": request.get("caller_scene"),
                                                "tier": h.caller_tier,
                                                "right": h.requested_right})
        return h

    def preflight(self, handshake_id: str, request: dict) -> HandshakeState:
        """Step-2 负空间预检（DCD-CSCP-CHANGE-001 映射）。仅 PENDING_NSFL 可进入（红队复审 N4）。"""
        h = self._get(handshake_id)
        if h.status != HandshakeStatus.PENDING_NSFL:
            return self._reject(h, "STEP2", f"非法状态转换: {h.status.value}（仅 PENDING_NSFL 可 preflight）")
        if self._expired(h):
            return self._rollback(h, f"STEP2 超时 >{STEP_TIME_LIMITS[Step.STEP2]}s")
        result = self._preflight(request)
        h.ns_union = result.get("ns_union")
        h.risk_premium = result.get("risk_premium", 0.0)
        status = result["status"]
        if isinstance(status, str):
            status = PreflightStatus(status)   # 兼容真实接口字符串形状
        if status == PreflightStatus.PASS:
            h.status = HandshakeStatus.PENDING_SANDBOX
            h.preflight_status = status.value      # FIN-5: PASS 分支也设契约状态
            h.current_step = Step.STEP3
            h.step_started_at = self._now()
        else:
            # 终态 barrier（红队 #2 #2）: 任何拒绝/熔断 → 清 current_step，后续 match/lock/dispatch 不可推进
            h.status = HandshakeStatus.REJECTED
            h.current_step = None
            h.preflight_status = status.value
            if status == PreflightStatus.REJECTED:
                h.rejection_reason = result.get("reason", "REQUIRES_REVIEW")
                h.rejection_step = "STEP2"
            else:  # FAIL / TRIGGERED
                h.rejection_reason = f"预检未通过({status.value})"
                h.rejection_step = "STEP2"
                h.alt_paths = result.get("alt_paths")
        self._record_nca(h, "STEP2_PREFLIGHT", {"status": status.value,
                                                "premium": h.risk_premium})
        return h

    def match(self, handshake_id: str, human_signature_1: str) -> HandshakeState:
        """Step-3 沙盒校验 + 配置权匹配。人类签名 #1 强制插入（不可绕过）。"""
        h = self._get(handshake_id)
        # 终态 barrier（红队 #2 #2）: 仅 PENDING_SANDBOX 可进入 Step-3
        if h.status != HandshakeStatus.PENDING_SANDBOX:
            return self._reject(h, "STEP3", f"非法状态转换: {h.status.value}（仅 PENDING_SANDBOX 可 match）")
        if not self._valid_signature(human_signature_1, handshake_id, ACTION_MATCH):
            h.status = HandshakeStatus.REJECTED
            h.rejection_reason = "HUMAN_GATE_1_MISSING（人类签名 #1 不可绕过）"
            h.rejection_step = "STEP3"
            h.current_step = None
            return h
        if self._expired(h):
            return self._rollback(h, f"STEP3 超时 >{STEP_TIME_LIMITS[Step.STEP3]}s")
        sb = self._sandbox(request={"sandbox_id": h.ns_union.get("sandbox_id") if h.ns_union else None})
        if sb["status"] != "ACTIVE":
            return self._reject(h, "STEP3", f"SANDBOX_NOT_ACTIVE: {sb['status']}")
        # E2E-004: effectiveTier 检查（Tier-3 不可持有 P-Right，任务书 §2.1 Step-3）
        if h.requested_right == "P_RIGHT" and _tier_rank(h.caller_tier) >= 2:
            return self._reject(h, "STEP3",
                                f"TIER_INSUFFICIENT: {h.caller_tier} 不可持有 P_RIGHT")
        tr = self._translator(request={})
        if not tr["matched"]:
            return self._reject(h, "STEP3", "NO_TRANSLATOR")
        h.human_gates["gate1"] = True
        # Saga 注册（Step-3 补偿面）
        self._saga.register("SANDBOX_UNLOCK")
        self._saga.register("TRANSLATOR_RESERVE_RELEASE")
        h.status = HandshakeStatus.PENDING_LOCK
        h.current_step = Step.STEP4
        h.step_started_at = self._now()
        self._record_nca(h, "STEP3_MATCHED", {"translator": tr.get("translator_id"),
                                              "cost": tr.get("translation_cost")})
        return h

    def lock(self, handshake_id: str, mou_split_ratio: float) -> HandshakeState:
        """Step-4 CBDC escrow 锁定（cbdc_anchor 模拟）。"""
        h = self._get(handshake_id)
        if h.status != HandshakeStatus.PENDING_LOCK:
            return self._reject(h, "STEP4", f"非法状态转换: {h.status.value}（仅 PENDING_LOCK 可 lock）")
        if not (0.0 < mou_split_ratio <= 1.0):
            # FIN-9: 状态机层入口校验（防直连绕过 gateway pydantic 约束）
            return self._reject(h, "STEP4", f"INVALID_RATIO: {mou_split_ratio}")
        if not h.human_gates["gate1"]:
            return self._reject(h, "STEP4", "HUMAN_GATE_1 未通过（签名 #1 缺失）")
        if self._expired(h):
            return self._rollback(h, f"STEP4 超时 >{STEP_TIME_LIMITS[Step.STEP4]}s")
        res = self._cbdclock(request={"mou_split_ratio": mou_split_ratio})
        if not res["locked"]:
            return self._reject(h, "STEP4", res["reason"])
        h.lock_tx_hash = res["lock_tx_hash"]
        h.escrow_id = res["escrow_id"]
        # Saga 注册（Step-4 补偿面: escrowRefund，CCP T4 M-4）
        self._saga.register("ESCROW_REFUND")
        h.status = HandshakeStatus.PENDING_DISPATCH
        h.current_step = Step.STEP5
        h.step_started_at = self._now()
        self._record_nca(h, "STEP4_LOCKED", {"escrow": h.escrow_id,
                                             "tx": h.lock_tx_hash})
        return h

    def dispatch(self, handshake_id: str, human_signature_2: str) -> HandshakeState:
        """Step-5 调度指令生成。人类签名 #2 强制插入（不可绕过）。"""
        h = self._get(handshake_id)
        if h.status != HandshakeStatus.PENDING_DISPATCH:
            return self._reject(h, "STEP5", f"非法状态转换: {h.status.value}（仅 PENDING_DISPATCH 可 dispatch）")
        if not self._valid_signature(human_signature_2, handshake_id, ACTION_DISPATCH):
            h.status = HandshakeStatus.REJECTED
            h.rejection_reason = "HUMAN_GATE_2_MISSING（人类签名 #2 不可绕过）"
            h.rejection_step = "STEP5"
            h.current_step = None
            return h
        if self._expired(h):
            return self._rollback(h, f"STEP5 超时 >{STEP_TIME_LIMITS[Step.STEP5]}s")
        wo = self._workbuddy(request={"plan": h.ns_union})
        if not wo["created"]:
            return self._reject(h, "STEP5", wo["reason"])
        h.human_gates["gate2"] = True
        h.work_order_id = wo["work_order_id"]
        # Saga 注册（Step-5 补偿面）
        self._saga.register("WORKORDER_CANCEL")
        h.status = HandshakeStatus.COMPLETED
        h.current_step = None
        self._record_nca(h, "STEP5_DISPATCHED", {"work_order": h.work_order_id})
        return h

    def status(self, handshake_id: str) -> HandshakeState:
        return self._get(handshake_id)

    # ---- 内部 ----

    def cancel(self, handshake_id: str, reason: str = "USER_CANCELLED") -> HandshakeState:
        """E2E-010: Step-5 执行前取消 → Saga 逆序回滚（ESCROW_REFUND 等）+ NCA 记录。终态不可取消。"""
        h = self._get(handshake_id)
        if h.status in (HandshakeStatus.COMPLETED, HandshakeStatus.REJECTED,
                        HandshakeStatus.FAILED):
            return self._reject(h, "CANCEL", f"终态不可取消: {h.status.value}")
        compensated = self._saga.rollback(reason)
        if self._human_gate is not None:
            self._human_gate.invalidate(handshake_id)   # FIN-6: 清理会话未用 nonce
        h.status = HandshakeStatus.FAILED
        h.current_step = None
        h.rejection_reason = reason
        self._record_nca(h, "HANDSHAKE_CANCELLED", {"reason": reason,
                                                    "compensated": compensated})
        return h

    def _valid_signature(self, sig: str, handshake_id: str, action: str) -> bool:
        """签名验证（T-CSCP-008）: HumanGate 注入时走真实级（HMAC+nonce+TTL+动作绑定）；
        未注入回退模拟级（非空 + 长度 ≥8 + 会话前缀绑定）。
        """
        if self._human_gate is not None:
            return self._human_gate.verify(handshake_id, action, sig)
        return bool(sig) and len(sig) >= 8 and handshake_id[:6] in sig

    def _get(self, handshake_id: str) -> HandshakeState:
        if handshake_id not in self._states:
            raise KeyError(f"未知 handshake_id: {handshake_id}")
        return self._states[handshake_id]

    def _expired(self, h: HandshakeState) -> bool:
        if h.current_step is None:
            return False
        limit = STEP_TIME_LIMITS.get(h.current_step)
        if limit is None:
            return False
        return (self._now() - h.step_started_at) > limit

    def _reject(self, h: HandshakeState, step: str, reason: str) -> HandshakeState:
        """任何拒绝 → RejectionNCA（理由 + Step + 建议处置，任务书 §2.2）；终态清 current_step（红队复审 N6）。"""
        h.status = HandshakeStatus.REJECTED
        h.current_step = None
        h.rejection_reason = reason
        h.rejection_step = step
        self._record_nca(h, "HANDSHAKE_REJECTED", {"step": step, "reason": reason})
        return h

    def _rollback(self, h: HandshakeState, reason: str) -> HandshakeState:
        """超时 → Saga 补偿链逆序回滚（saga.py），状态置 FAILED。"""
        compensated = self._saga.rollback(reason)
        if self._human_gate is not None:
            self._human_gate.invalidate(h.handshake_id)   # FIN-6: 超时回滚同样清理 nonce
        h.status = HandshakeStatus.FAILED
        h.rejection_reason = reason
        self._record_nca(h, "STEP_TIMEOUT_ROLLBACK", {"reason": reason,
                                                      "compensated": compensated})
        return h

    def _record_nca(self, h: HandshakeState, event: str, detail: dict) -> None:
        if self._nca is None:
            h.nca_refs.append(f"NCA-MOCK-{uuid.uuid4().hex[:8]}")
            return
        ref = self._nca(type="OPERATIONAL", layer=3,
                        content={"event": event, "handshake_id": h.handshake_id, **detail})
        h.nca_refs.append(str(ref))
