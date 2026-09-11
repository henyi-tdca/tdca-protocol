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

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

MCP_TOOLS = ("enforce_check", "nca_append", "nca_verify", "nsfl_eval")
_CHANNEL_HINT = ("通道未就绪：本环境无 Go 工具链/构建产物（tdcad mcp serve）——"
                 "如实标注未执行，不虚报")


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

    # ---------- 发布通道就绪探测（#4，只读） ----------
    def probe_channel(self, extra_candidates: Optional[List[str]] = None) -> Dict[str, Any]:
        """探测发布通道就绪度（**只读**，不执行任何工具、不建连接）。

        判定依据：① `tdcad` 是否在 PATH；② core-go 构建产物候选路径是否存在。
        探就绪 ≠ 可执行：实执仍须显式注入 transport（见 `execute_with_channel`）。
        """
        on_path = shutil.which(self.tdcad_command)
        ws = Path(__file__).resolve().parents[2]
        candidates = [str(p) for p in (extra_candidates or [])]
        candidates += [
            str(ws / "tdca-core-go" / "bin" / f"{self.tdcad_command}.exe"),
            str(ws / "tdca-core-go" / "dist" / f"{self.tdcad_command}.exe"),
            str(ws / "tdca-core-go" / f"{self.tdcad_command}.exe"),
            str(ws / "tdca-core-go" / "bin" / self.tdcad_command),
        ]
        artifacts = [c for c in candidates if os.path.exists(c)]
        ready = bool(on_path) or bool(artifacts)
        return {"command": self.tdcad_command, "transport": "stdio",
                "on_path": on_path, "artifacts": artifacts, "ready": ready,
                "hint": "" if ready else _CHANNEL_HINT,
                "probed_at_epoch": None, "simulated": True}

    def execute_with_channel(self, plan: Dict[str, Any],
                             transport: Optional[Any] = None,
                             probe: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """按通道就绪度分流执行：注入 transport ⇒ 实执；否则 **如实 dry-run**。

        纪律：`executed=true` 仅当确有 transport 承接；通道"就绪"但无 transport 时
        亦返回 `executed=false`（不得以探测就绪冒充已执行）。
        """
        probe = probe if probe is not None else self.probe_channel()
        if transport is not None:
            try:
                res = transport(plan)
            except Exception as exc:                       # noqa: BLE001
                return {"executed": False, "channel": "injected-transport",
                        "reason": f"传输执行失败：{type(exc).__name__}: {exc}",
                        "probe": probe, "simulated": True}
            return {"executed": True, "channel": "injected-transport", "probe": probe,
                    "result": res, "simulated": True}
        if not probe.get("ready"):
            out = self.execute(plan, transport=None)
            out.update({"channel": "dry-run", "probe": probe})
            return out
        return {"executed": False, "channel": "ready-but-no-transport",
                "reason": "通道就绪但未注入传输实现（不得虚报执行）",
                "probe": probe, "plan_calls": len(plan.get("calls", [])), "simulated": True}

    def transport_cli(self, **kwargs) -> Any:
        """构造真实 CLI 传输（#4）：未定位构建产物即抛错（**不虚报可执行**）。

        用法：`adapter.execute_with_channel(plan, transport=adapter.transport_cli())`
        """
        from cli_transport import CliTransport, CliTransportError  # noqa: F401
        t = CliTransport(**kwargs)
        t._exe()                                   # 触发定位校验（未就绪即抛）
        return t

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
