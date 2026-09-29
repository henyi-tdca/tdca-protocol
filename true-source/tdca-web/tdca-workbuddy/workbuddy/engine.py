# -*- coding: utf-8 -*-
"""
P5 T-P5-001 · CrossSceneWorkflowEngine（跨场景智能体工作流引擎）
锚定: TDCA-TASKBOOK-5CC-P5-WB T-P5-001（工作流编排 DSL：场景切换/配置权层级切换/负空间边界切换）
     + P5 接口契约（/workflow/create·execute·status + /signature/request·confirm）
     + P5 绝对负空间（L 级不直接跨场景 / 人类签名不可绕过 / 日志 WORM 不可篡改 / 数据未经翻译器不直传）
DSL: 步骤（scene/function/role/config_right/input/output/nsfl_check）+ human_gates（before/after）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

WORKFLOW_TIME_LIMIT_S = 10.0   # 验收: 端到端执行 <10s（不含人类签名等待）


@dataclass
class WorkflowStep:
    scene: str
    function: str
    role: str = "L"
    config_right: str = "S-Right"
    input: Optional[str] = None
    output: Optional[str] = None
    nsfl_check: bool = False
    nca_ref: str = ""
    status: str = "PENDING"          # PENDING | RUNNING | DONE | BLOCKED

    @property
    def is_cross_scene(self) -> bool:
        return self.nsfl_check  # 跨场景边界步骤（负空间检查强制）


@dataclass
class WorkflowDSL:
    workflow_id: str
    steps: List[WorkflowStep]
    human_gates: List[Dict[str, str]] = field(default_factory=list)  # [{before/after: step}]

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "WorkflowDSL":
        steps = [WorkflowStep(**s) for s in raw["steps"]]
        return cls(workflow_id=raw.get("workflow_id", f"WF-{uuid.uuid4().hex[:8]}"),
                   steps=steps, human_gates=raw.get("human_gates", []))


@dataclass
class WorkflowExecution:
    workflow_id: str
    execution_id: str
    status: str = "RUNNING"          # RUNNING | COMPLETED | BLOCKED | FAILED
    current_step: int = 0
    nsfl_status: str = "CLEAR"
    nca_refs: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    results: Dict[str, Any] = field(default_factory=dict)   # output 中间件


class CrossSceneWorkflowEngine:
    """工作流引擎：步骤执行 + 跨场景负空间检查 + 人类签名门禁 + NCA 审计 + WORM 日志。"""

    def __init__(self, nca_fn=None, nsfl_check_fn=None, gate_fn=None):
        self._nca = nca_fn
        self._nsfl_check = nsfl_check_fn or (lambda step: True)   # 负空间检查（D-2 联调可注入）
        self._gate = gate_fn or (lambda gate_id, sig: bool(sig))  # 签名门禁（P5 /signature 对接）
        self._executions: Dict[str, WorkflowExecution] = {}
        self._log: List[str] = []          # WORM 日志（一次写入，哈希链）

    # ---- 创建 + 执行 ----

    def create(self, workflow: WorkflowDSL) -> Dict[str, Any]:
        """创建工作流（P5 契约: status=PENDING_HUMAN_GATE）。"""
        self._worm_log(f"CREATE {workflow.workflow_id} steps={len(workflow.steps)}")
        return {"workflow_id": workflow.workflow_id, "status": "PENDING_HUMAN_GATE"}

    def execute(self, workflow: WorkflowDSL, human_signature: str) -> WorkflowExecution:
        """执行（人类签名门禁 + 步骤执行 + 负空间检查 + NCA 审计）。<10s 硬指标。"""
        start = time.perf_counter()
        if not human_signature or len(human_signature) < 8:
            raise PermissionError("HUMAN_SIGNATURE_REQUIRED（人类签名权不可绕过，P5 绝对负空间）")
        ex = WorkflowExecution(workflow_id=workflow.workflow_id,
                               execution_id=f"EX-{uuid.uuid4().hex[:10]}")
        self._executions[ex.execution_id] = ex
        ex.nca_refs.append(self._nca_or(f"WORKFLOW_START {workflow.workflow_id}"))
        self._worm_log(f"EXECUTE {ex.execution_id} gate={human_signature[:4]}...")

        for idx, step in enumerate(workflow.steps):
            ex.current_step = idx
            step.status = "RUNNING"
            # 跨场景步骤：负空间检查（强制，P5 绝对负空间 4 条）
            if step.is_cross_scene:
                nsfl_ok = self._nsfl_check(step)
                if not nsfl_ok:
                    step.status = "BLOCKED"
                    ex.status = "BLOCKED"
                    ex.nsfl_status = "TRIGGERED"
                    ex.nca_refs.append(self._nca_or(f"NSFL_BLOCK {step.function}"))
                    self._worm_log(f"NSFL_BLOCK {ex.execution_id} step={idx}")
                    return ex
                ex.nsfl_status = "CHECKED"
            # 人类签名门禁（before 该步骤）
            if self._gate_required_before(workflow, idx, step):
                gate_id = f"GATE-before-{idx}"
                if not self._gate(gate_id, human_signature):
                    step.status = "BLOCKED"
                    ex.status = "BLOCKED"
                    ex.nca_refs.append(self._nca_or(f"GATE_BLOCK {gate_id}"))
                    self._worm_log(f"GATE_BLOCK {ex.execution_id} {gate_id}")
                    return ex
            # 数据中间件流转（input → output；跨场景数据经翻译器，未经翻译不直传——模拟语义）
            self._transfer(step, ex)
            step.status = "DONE"
            ex.nca_refs.append(self._nca_or(f"STEP_DONE {step.function}"))
            self._worm_log(f"STEP_DONE {ex.execution_id} {step.function}")

        # after workflow_complete 门禁
        if self._gate_required_after(workflow):
            if not self._gate("GATE-complete", human_signature):
                ex.status = "BLOCKED"
                return ex
        ex.status = "COMPLETED"
        ex.nca_refs.append(self._nca_or(f"WORKFLOW_COMPLETE {workflow.workflow_id}"))
        elapsed = (time.perf_counter() - start) * 1000.0
        self._worm_log(f"COMPLETE {ex.execution_id} elapsed_ms={round(elapsed, 1)}")
        if elapsed > WORKFLOW_TIME_LIMIT_S * 1000.0:
            ex.status = "FAILED"   # 超时（模拟态不触发，标注硬指标）
        return ex

    def status(self, execution_id: str) -> WorkflowExecution:
        return self._executions[execution_id]

    # ---- 内部 ----

    def _transfer(self, step: WorkflowStep, ex: WorkflowExecution) -> None:
        """数据中间件流转（模拟）：input 依赖前步 output；结果入 ex.results。"""
        if step.input is not None:
            if step.input not in ex.results:
                raise KeyError(f"依赖 {step.input} 未就绪（DSL 顺序错误）")
            payload = ex.results[step.input]
        else:
            payload = {"function": step.function, "scene": step.scene}
        # 跨场景数据须经翻译器（P5 绝对负空间 4）——nsfl_check 步骤即翻译边界
        if step.is_cross_scene:
            payload = {"translated": True, "source": step.scene, **payload}
        ex.results[step.output or step.function] = payload

    def _gate_required_before(self, wf: WorkflowDSL, idx: int, step: WorkflowStep) -> bool:
        return any(g.get("before") == f"step_{idx + 1}" or
                   (g.get("before") == step.function) for g in wf.human_gates)

    def _gate_required_after(self, wf: WorkflowDSL) -> bool:
        return any(g.get("after") == "workflow_complete" for g in wf.human_gates)

    def _nca_or(self, event: str) -> str:
        if self._nca is not None:
            return str(self._nca(type="OPERATIONAL", layer=3, content={"event": event}))
        return f"NCA-MOCK-{event.replace(' ', '_')}"

    def _worm_log(self, entry: str) -> None:
        """WORM 日志（一次写入多次读取，哈希链防篡改，P5 绝对负空间 3）。"""
        prev = self._log[-1] if self._log else ""
        digest = hashlib.sha256(f"{prev}|{entry}".encode("utf-8")).hexdigest()[:16]
        self._log.append(f"{entry} :: {digest}")

    def verify_log_integrity(self) -> bool:
        """WORM 日志完整性校验（哈希链）。"""
        prev = ""
        for entry in self._log:
            body, _, digest = entry.rpartition(" :: ")
            if hashlib.sha256(f"{prev}|{body}".encode("utf-8")).hexdigest()[:16] != digest:
                return False
            prev = f"{body} :: {digest}"
        return True
