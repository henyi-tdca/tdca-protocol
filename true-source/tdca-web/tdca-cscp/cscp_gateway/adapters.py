# -*- coding: utf-8 -*-
"""
CSCP 跨场景协作握手协议 · 外部依赖适配器（抽象 + 模拟态实现）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §三（内部接口 P2/P3/P4/P5）+ R-CSCP-001（mock 并集引擎占位）
     + D-011 裁决（CBDC 用 cbdc_anchor 模拟参数）+ CCP T4 escrowRefund（M-4）
模拟态严格遵循真实接口形状，仅替换底层实现（R-CSCP-004: 差异 >10% 重设计）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .state_machine import PreflightStatus


# ---------------------------------------------------------------------------
# P2 并集引擎适配（Step-2）
# ---------------------------------------------------------------------------

class NSFLUnionAdapter(ABC):
    @abstractmethod
    def preflight_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """调 P2 /nsfl/preflight/check → PreflightResult（DCD-CSCP-CHANGE-001 映射）。"""


class MockNSFLUnionAdapter(NSFLUnionAdapter):
    """R-CSCP-001 mock 占位（不依赖 D-2，等待 D-2 W2 输出后联调替换）。"""

    def __init__(self, forced: Optional[PreflightStatus] = None, premium: float = 0.2):
        self._forced = forced
        self._premium = premium

    def preflight_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        rules_a = request.get("caller_scene", {}).get("rules", [])
        rules_b = request.get("callee_scene", {}).get("rules", [])
        if self._forced is not None:
            return {"status": self._forced, "risk_premium": self._premium,
                    "ns_union": {"scene_a": request.get("caller_scene", {}).get("scene_id"),
                                 "scene_b": request.get("callee_scene", {}).get("scene_id"),
                                 "union_set": [], "conflict_set": []},
                    "alt_paths": ["SCN-C-MOCK"] if self._forced == PreflightStatus.FAIL else None,
                    "next_step": "sandbox_verify" if self._forced == PreflightStatus.PASS else "rejected",
                    "nca_ref": "NCA-MOCK-PREFLIGHT"}
        # 模拟判定: 含 LEGAL → TRIGGERED（熔断）；规则级冲突 → FAIL；否则 PASS
        has_legal = any(r.get("ns_type") == "LEGAL" for r in rules_a + rules_b)
        if has_legal:
            return {"status": PreflightStatus.TRIGGERED, "risk_premium": 1.0,
                    "ns_union": {"conflict_set": [{"severity": "HIGH"}]},
                    "alt_paths": [], "nca_ref": "NCA-MOCK-PREFLIGHT",
                    "next_step": "rejected"}
        conflict = self._simulate_conflict(rules_a, rules_b)
        if conflict:
            return {"status": PreflightStatus.FAIL, "risk_premium": self._premium + 0.2,
                    "ns_union": {"conflict_set": [conflict]}, "alt_paths": ["SCN-C-MOCK"],
                    "nca_ref": "NCA-MOCK-PREFLIGHT", "next_step": "rejected"}
        return {"status": PreflightStatus.PASS, "risk_premium": self._premium,
                "ns_union": {"conflict_set": []}, "alt_paths": None,
                "nca_ref": "NCA-MOCK-PREFLIGHT", "next_step": "sandbox_verify"}

    @staticmethod
    def _simulate_conflict(rules_a: list, rules_b: list) -> Optional[dict]:
        ops_a = {r.get("ns_type"): r.get("operator") for r in rules_a}
        for rb in rules_b:
            op_a = ops_a.get(rb.get("ns_type"))
            if op_a == "ALLOW" and rb.get("operator") == "FORBID":
                return {"ns_type": rb.get("ns_type"), "severity": "MEDIUM",
                        "resolution": "FORBID", "reason": "mock 例 1 形态"}
        return None


# ---------------------------------------------------------------------------
# P3 沙盒校验适配（Step-3）
# ---------------------------------------------------------------------------

class SandboxAdapter(ABC):
    @abstractmethod
    def verify(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """sandbox_status==ACTIVE 才继续（任务书 §2.1 Step-3）。"""


class MockSandboxAdapter(SandboxAdapter):
    def __init__(self, active: bool = True):
        self._active = active

    def verify(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ACTIVE" if self._active else "INACTIVE",
                "sandbox_id": request.get("sandbox_id", "SBX-MOCK")}


# ---------------------------------------------------------------------------
# P4 翻译器匹配适配（Step-3）
# ---------------------------------------------------------------------------

class TranslatorAdapter(ABC):
    @abstractmethod
    def match(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """翻译器匹配 + 翻译费用=复杂度×risk_premium。"""


class MockTranslatorAdapter(TranslatorAdapter):
    def __init__(self, matched: bool = True, cost: float = 0.5):
        self._matched = matched
        self._cost = cost

    def match(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"matched": self._matched, "translator_id": "TR-MOCK-001" if self._matched else None,
                "translation_cost": self._cost if self._matched else None}


# ---------------------------------------------------------------------------
# CBDC 合约适配（Step-4）—— cbdc_anchor 模拟（D-011）
# ---------------------------------------------------------------------------

class CBDCContractAdapter(ABC):
    @abstractmethod
    def lock(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """CBDC 合约 lock（pcr_budget + mou_split_ratio Shapley 预计算）→ escrow + NCA。"""

    @abstractmethod
    def refund(self, escrow_id: str) -> Dict[str, Any]:
        """escrowRefund（M-4 权限修复: 仅系统网关，程序化退还）。"""


class MockCBDCContractAdapter(CBDCContractAdapter):
    """W5: CBDC escrow 锁定升级——lock 支持场景贡献 → Shapley 分割 escrow（MOU 分割模拟态落地）。"""

    def __init__(self, locked: bool = True, budget_ok: bool = True,
                 mou_enabled: bool = True):
        self._locked = locked
        self._budget_ok = budget_ok
        self._mou_enabled = mou_enabled
        self.refunded: list = []

    def lock(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self._budget_ok:
            return {"locked": False, "reason": "INSUFFICIENT_BUDGET"}
        if not self._locked:
            return {"locked": False, "reason": "CONTRACT_FAILURE"}
        budget = float(request.get("pcr_budget", 0.0))
        contributions = request.get("contributions")
        mou_split = None
        if self._mou_enabled and contributions:
            from .mou_escrow import MOUEscrowVerifier
            split = MOUEscrowVerifier().compute_split(
                list(contributions.keys()), contributions)
            escrow_total = round(sum(r * budget for r in split.values()), 4)
            mou_split = {s: round(r, 6) for s, r in split.items()}
        else:
            ratio = float(request.get("mou_split_ratio", 0.5))
            escrow_total = round(budget * ratio, 4)
        return {"locked": True, "lock_tx_hash": "0xMOCKLOCK",
                "escrow_id": f"ESC-{len(self.refunded) + 1:04d}",
                "escrow_total": escrow_total,
                "mou_split": mou_split}

    def refund(self, escrow_id: str) -> Dict[str, Any]:
        self.refunded.append(escrow_id)
        return {"refunded": True, "escrow_id": escrow_id, "nca_ref": "NCA-REFUND-MOCK"}


# ---------------------------------------------------------------------------
# P5 Workbuddy 调度适配（Step-5）
# ---------------------------------------------------------------------------

class WorkbuddyAdapter(ABC):
    @abstractmethod
    def create_work_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """生成 WorkOrder 推送 P5 Workbuddy + 执行授权。"""


class MockWorkbuddyAdapter(WorkbuddyAdapter):
    def __init__(self, created: bool = True):
        self._created = created

    def create_work_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self._created:
            return {"created": False, "reason": "WORKBUDDY_BUSY"}
        return {"created": True, "work_order_id": "WO-MOCK-001",
                "execution_plan": request.get("plan")}


class RealWorkbuddyAdapter(WorkbuddyAdapter):
    """F-5 缺口 II 关闭: CSCP Step-5 真实对接 P5 CrossSceneWorkflowEngine（T-P5-001）。
    由 dispatch 的 plan 构造 WorkflowDSL 执行（模拟态：默认三步 DSL + 签名门禁）。"""

    def __init__(self):
        from workbuddy.engine import CrossSceneWorkflowEngine, WorkflowDSL
        self._engine = CrossSceneWorkflowEngine()
        self._WorkflowDSL = WorkflowDSL

    def create_work_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        plan = request.get("plan") or {}
        template = plan.get("workflow_template") or {
            "workflow_id": f"WF-CSCP-{plan.get('scene_a', 'A')[:6]}-{plan.get('scene_b', 'B')[:6]}",
            "steps": [
                {"scene": plan.get("scene_a", "A"), "function": f"f_{plan.get('scene_a', 'A')[:4]}",
                 "role": "L", "config_right": "S-Right", "output": "m1"},
                {"scene": plan.get("scene_b", "B"), "function": "translator_cross",
                 "role": "L", "config_right": "S-Right", "input": "m1", "output": "m2",
                 "nsfl_check": True},
                {"scene": plan.get("scene_b", "B"), "function": f"g_{plan.get('scene_b', 'B')[:4]}",
                 "role": "L", "config_right": "S-Right", "input": "m2", "output": "final"},
            ],
            "human_gates": [{"before": "step_2"}, {"after": "workflow_complete"}],
        }
        wf = self._WorkflowDSL.from_dict(template)
        sig = request.get("human_signature_2") or "HUMAN-SIG-P5-BRIDGE"
        try:
            ex = self._engine.execute(wf, sig)
        except PermissionError:
            return {"created": False, "reason": "HUMAN_GATE_BLOCKED"}
        return {"created": ex.status == "COMPLETED", "work_order_id": ex.execution_id,
                "execution_plan": {"workflow_id": wf.workflow_id,
                                   "nca_refs": ex.nca_refs,
                                   "nsfl_status": ex.nsfl_status}}
