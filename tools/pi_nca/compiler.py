"""pi_nca · Pi agent toolkit → TDCA 制度编译适配器（DCD-PI-COMPOUND-001 M1a，MIT 层）

Pi（earendil-works/pi，MIT，95,303 stars）是 AI agent toolkit——
智能体构建工具。TDCA 主张"制度即代码"（Compile 非蒸馏）——Pi 的构建协议在此有原生落点。

⚠️ **Fair Source 风险管控（硬约束）**：化合仅限 MIT 开放层；Fair Source 核心层
不内化/不依赖/不传播（许可证边界即化合边界，DCD §七）。

M1a 功能:
  - parse_agent_spec: 解析 Pi agent 构建规格（MIT 层，build steps）
  - compile_to_tdca: 构建协议 → TDCA 制度语义（配置权边界/负空间声明映射）
  - build_compile_nca: 构建轨迹 → NCA 存证
  - fair_source_guard: Fair Source 隔离校验（许可证边界守卫）

制度锚定: ID 化合（Compile 非蒸馏）/ BIDIR-001 / AUDIT-001 / ID92
NSFL-Declaration:
  - 化合零触碰 Fair Source 核心层（许可证边界即化合边界）
  - 不修改 Pi 核心（仓库优先 + 双向赋能纪律）
  - 合成/演示数据标注 SIMULATED（ID92）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Fair Source 边界（Pi 化合仅限 MIT 层）
MIT_LAYER = "mit"
FAIR_SOURCE_LAYER = "fair-source"
ALLOWED_LAYERS = {MIT_LAYER}


@dataclass(frozen=True)
class CompiledStep:
    """构建步骤 → TDCA 制度语义。"""
    step_id: str
    layer: str                  # mit / fair-source
    action: str                 # 构建动作
    tdca_semantics: str         # TDCA 制度语义映射
    status: str

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "layer": self.layer,
            "action": self.action,
            "tdca_semantics": self.tdca_semantics,
            "status": self.status,
        }


@dataclass(frozen=True)
class FairSourceGuard:
    """Fair Source 隔离校验结果。"""
    blocked: bool
    blocked_steps: List[str]
    allowed_steps: int
    message: str

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "blocked_steps": self.blocked_steps,
            "allowed_steps": self.allowed_steps,
            "message": self.message,
        }


class PiCompiler:
    """Pi → TDCA 制度编译适配器（M1a，MIT 层）。"""

    def __init__(self, provenance: str = "SIMULATED"):
        self._provenance = provenance

    # ---- 解析 ----

    def parse_agent_spec(self, raw: str) -> dict:
        """解析 Pi agent 构建规格（MIT 层）。"""
        if not raw or not raw.strip():
            raise ValueError("[NSFL-TRIGGER] 空构建规格")
        data = json.loads(raw)
        if "steps" not in data or not isinstance(data["steps"], list):
            raise ValueError("[NSFL-TRIGGER] 构建规格缺 steps 数组")
        return data

    # ---- Fair Source 守卫（硬约束）----

    def fair_source_guard(self, spec: dict) -> FairSourceGuard:
        """隔离校验：Fair Source 层步骤被拦截（许可证边界守卫）。"""
        blocked = []
        allowed = 0
        for step in spec["steps"]:
            layer = step.get("layer", MIT_LAYER)
            if layer not in ALLOWED_LAYERS:
                blocked.append(step["step_id"])
            else:
                allowed += 1
        return FairSourceGuard(
            blocked=bool(blocked), blocked_steps=blocked,
            allowed_steps=allowed,
            message=("化合仅限 MIT 层——Fair Source 核心层不内化/不依赖/不传播（许可证边界即化合边界）"
                     if blocked else "全部步骤在 MIT 层内，可化合"),
        )

    # ---- 编译（M1a 核心：构建 → 制度语义）----

    def compile_to_tdca(self, spec: dict) -> List[CompiledStep]:
        """构建协议 → TDCA 制度语义（配置权边界/负空间声明映射）。"""
        guard = self.fair_source_guard(spec)
        if guard.blocked:
            raise ValueError(
                f"[NSFL-TRIGGER] Fair Source 隔离拦截: {guard.blocked_steps}——"
                "化合仅限 MIT 层（许可证边界即化合边界）")
        out = []
        for step in spec["steps"]:
            action = step.get("action", "build")
            semantics = self._map_semantics(action)
            out.append(CompiledStep(
                step_id=step["step_id"], layer=MIT_LAYER,
                action=action, tdca_semantics=semantics,
                status=step.get("status", "compiled"),
            ))
        return out

    @staticmethod
    def _map_semantics(action: str) -> str:
        """构建动作 → TDCA 制度语义（Compile 非蒸馏）。"""
        mapping = {
            "configure": "配置权边界声明（L2 配置权市场层）",
            "install": "能力注册（NCA 确权前置）",
            "test": "验收门禁（六要素校验）",
            "publish": "发布即契约（NS-007 第七要素负空间声明）",
            "invoke": "协作即调用（ID21）",
            "audit": "审计轨迹落链（NCA 存证）",
        }
        return mapping.get(action, f"制度语义映射: {action}")

    # ---- NCA 存证（M1b）----

    def build_compile_ncas(self, steps: List[CompiledStep],
                           spec_id: str = "agent-1") -> List[dict]:
        """构建轨迹 → NCA 存证（每次编译步骤落链）。"""
        ts = datetime.now(timezone.utc)
        date_str = ts.strftime("%Y%m%d")
        ncas = []
        for i, s in enumerate(steps, start=1):
            ncas.append({
                "NCA-ID": f"NCA-PI-{date_str}-{i:03d}",
                "Function-Call-ID": f"pi-compile-{spec_id}-{s.step_id}",
                "Operation-Type": "Agent-Compile",
                "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Scope": f"Pi agent 构建编译存证（MIT 层，{spec_id}）",
                "Compiled-Step": s.to_dict(),
                "Layer": MIT_LAYER,
                "Provenance": self._provenance,
            })
        return ncas
