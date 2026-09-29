# -*- coding: utf-8 -*-
"""
W6 · CrossSceneWorkflowOrchestrator 跨场景工作流编排器
锚定: 5CC 阶段 1 关键路径 W6（跨场景工作流，W6-7）——CSCP 握手结果 → Workbuddy 执行 → NCA 全链路
     + P5 T-P5-001（工作流引擎）+ M2 CSCP FROZEN（握手结果）+ W4（翻译/MOU escrow）
编排语义: 握手 COMPLETED → 自动生成 WorkflowDSL（含翻译步骤/escrow 步骤/人类签名门禁）
          → P5 执行 → 全链路 NCA；跨场景步骤强制 nsfl_check（绝对负空间）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from workbuddy.engine import CrossSceneWorkflowEngine, WorkflowDSL, WorkflowStep


@dataclass
class OrchestrationResult:
    """编排结果（全链路视图）。"""
    handshake_id: str
    workflow_id: str
    execution_id: str
    status: str                       # RUNNING | COMPLETED | BLOCKED
    nca_refs: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    mou_split: Optional[Dict[str, float]] = None
    escrow_id: Optional[str] = None


class CrossSceneWorkflowOrchestrator:
    """跨场景工作流编排：握手结果 → DSL 生成 → P5 执行。"""

    def __init__(self, engine: Optional[CrossSceneWorkflowEngine] = None,
                 nca_fn=None):
        self._engine = engine or CrossSceneWorkflowEngine(nca_fn=nca_fn)
        self._nca = nca_fn

    def orchestrate(self, handshake_result: Dict[str, Any],
                    human_signature: str) -> OrchestrationResult:
        """编排一次跨场景协作。

        :param handshake_result: CSCP 握手 COMPLETED 结果
            {handshake_id, scene_a, scene_b, risk_premium, translator_id,
             mou_split(可选), escrow_id(可选), ns_union}
        """
        hs_id = handshake_result["handshake_id"]
        scene_a = handshake_result.get("scene_a", "SCN-A")
        scene_b = handshake_result.get("scene_b", "SCN-B")
        risk_premium = handshake_result.get("risk_premium", 0.2)
        translator = handshake_result.get("translator_id", "translator_cross")
        mou_split = handshake_result.get("mou_split")
        escrow_id = handshake_result.get("escrow_id")

        # 自动生成 WorkflowDSL（翻译步骤 + escrow 步骤 + 结果步骤，跨场景强制 nsfl_check）
        steps = [
            WorkflowStep(scene=scene_a, function=f"f_{scene_a[:4]}", role="L",
                         config_right="S-Right", output="m1",
                         nca_ref=self._nca_or(f"W6_STEP1 {scene_a}")),
            WorkflowStep(scene=scene_b, function=translator, role="L",
                         config_right="S-Right", input="m1", output="m2",
                         nsfl_check=True, nca_ref=self._nca_or("W6_STEP2 翻译跨场景")),
            WorkflowStep(scene=scene_b, function="escrow_apply", role="L",
                         config_right="S-Right", input="m2", output="final",
                         nca_ref=self._nca_or(f"W6_STEP3 escrow={escrow_id}")),
        ]
        wf = WorkflowDSL(
            workflow_id=f"WF-W6-{hs_id[:10]}",
            steps=steps,
            human_gates=[{"before": "step_2"}, {"after": "workflow_complete"}],
        )
        ex = self._engine.execute(wf, human_signature)
        result = OrchestrationResult(
            handshake_id=hs_id, workflow_id=wf.workflow_id,
            execution_id=ex.execution_id, status=ex.status,
            nca_refs=ex.nca_refs,
            steps=[{"step": i + 1, "function": s.function, "status": s.status,
                    "nca_ref": s.nca_ref} for i, s in enumerate(wf.steps)],
            mou_split=mou_split, escrow_id=escrow_id,
        )
        return result

    def _nca_or(self, event: str) -> str:
        if self._nca is not None:
            return str(self._nca(type="OPERATIONAL", layer=3, content={"event": event}))
        return f"NCA-W6-{event.replace(' ', '_')}"
