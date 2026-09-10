# -*- coding: utf-8 -*-
"""S-Right ↔ core-go MCP 工具面适配器（M2 待细化 5）

语义映射（S-Right 调用 → TDCA MCP server 四工具）:
  enforce_check ← 身份 / 边界准入
  nsfl_eval     ← 负空间评估
  nca_append    ← 调用存证（NCA 归档）
  nca_verify    ← 存证链校验

纪律:
  - **如实标注执行状态**：本环境无 Go 工具链（tdcad 不可构建/运行）→ 默认 dry-run 计划态；
    真实执行需发布通道（core-go 构建产物 tdcad.exe mcp serve，stdio）
  - 不虚报执行：dry-run 结果显式 `executed=false`
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MCP_TOOLS = ("enforce_check", "nca_append", "nca_verify", "nsfl_eval")


@dataclass
class McpToolCall:
    tool: str
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"tool": self.tool, "params": self.params}


class McpToolFaceAdapter:
    """把 S-Right 调用映射到 MCP 工具序列（计划态可核，执行态待发布通道）。"""

    def __init__(self, tdcad_command: str = "tdcad"):
        self.tdcad_command = tdcad_command

    # ---------- 映射 ----------
    def plan(self, req, outcome=None) -> Dict[str, Any]:
        """生成 MCP 工具调用计划（顺序：准入 → 负空间 → 存证 → 校验）。"""
        calls: List[McpToolCall] = [
            McpToolCall("enforce_check", {
                "agent_card": {"agent_id": req.caller_tdid, "scene": req.scene},
                "scene": req.scene, "national_agent_id": req.oid}),
            McpToolCall("nsfl_eval", {
                "scene": req.scene, "declared_violation": req.violates_nsfl}),
            McpToolCall("nca_append", {
                "type": "sright-invoke",
                "content": {"caller_tdid": req.caller_tdid, "tool_id": req.tool_id,
                            "scene": req.scene, "coalition_utility": req.coalition_utility,
                            "nca_ref": getattr(outcome, "nca_ref", None),
                            "simulated": True}}),
            McpToolCall("nca_verify", {
                "nca_id": getattr(outcome, "nca_ref", None) or "<pending>"}),
        ]
        return {
            "transport": "stdio",
            "command": f"{self.tdcad_command} mcp serve",
            "tools": list(MCP_TOOLS),
            "calls": [c.to_dict() for c in calls],
            "executed": False,
            "dry_run": True,
            "note": ("计划态：真实执行需 tdcad（core-go 构建产物，经发布通道）；"
                     "本环境无 Go 工具链，如实标注未执行"),
            "simulated": True,
        }

    # ---------- 执行（transport=None → dry-run） ----------
    def execute(self, plan: Dict[str, Any], transport: Optional[Any] = None) -> Dict[str, Any]:
        if transport is None:
            return {"executed": False, "reason": "无传输通道（dry-run）",
                    "plan_calls": len(plan.get("calls", [])),
                    "expected": list(MCP_TOOLS), "simulated": True}
        # 真实传输（如 stdio client）由发布通道环境注入实现
        return transport(plan)  # pragma: no cover

    # ---------- 与 S-Right 结果对照（语义一致性核验） ----------
    def consistency_report(self, outcome) -> Dict[str, Any]:
        """S-Right 判定 ↔ MCP 工具序列的语义一致性（供审计）。"""
        granted = bool(getattr(outcome, "granted", False))
        ccv = getattr(outcome, "ccv", {}) or {}
        layers = ccv.get("layers", {})
        return {
            "sright_granted": granted,
            "mcp_expected_first": "enforce_check",
            "mcp_expected_on_nsfl_deny": "nsfl_eval→reject",
            "ccv_layers_passed": [k for k, v in layers.items() if v.get("ok")],
            "ccv_layers_failed": [k for k, v in layers.items() if not v.get("ok")],
            "consistent": (granted == bool(ccv.get("all_passed", False))),
            "simulated": True,
        }
