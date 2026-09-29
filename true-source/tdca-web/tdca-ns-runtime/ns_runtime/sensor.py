# -*- coding: utf-8 -*-
"""
L2-R5 · NS-Boundary Sensor（四态输入 + 进化轨迹图）
====================================================
对 SEA 进化计划 Δ 做负空间拓扑检测——对齐 ICD §3.1 对外接口
与 §3.3 Δ-Analysis 共享接口。

四态输入（DCD-NSFL-M1-FROZEN-001 §一 裁决定档）:
  SAFE      进化轨迹远离负空间邻域 → 通行
  WARNING   轨迹出现负空间梯度趋近 → Soft 熔断（限频/限域）
  BLOCKED   轨迹落入负空间拓扑边界 → Hard 熔断（即时阻断）
  CRYOGENIC SEA 出现自我修改意图但尚未形成可判定轨迹 → Atomic 熔断（全量冻结等人类签名 HUF）

设计:
  - 不可算计: 不试图理解 SEA 进化意图，只做 Δ 模式匹配 + 拓扑距离度量
  - Δ-Analysis 复用编译器 C6 语义（ICD §3.3 共享接口，同一输入同一输出）
  - 进化轨迹图（轻量）: 记录 Δ 序列 → 梯度趋近检测（Warning/Blocked 判定输入）
  - 输出: verdict + confidence + distance + mapped_fuse + nca_ref + audit_trail

锚定: DCD-NSFL-M2-001（L2-R5）+ NSFL-M2-ICD-001 §3.1/§3.3
     + DCD-NSFL-M1-FROZEN-001（四态定义）+ TDCA-NS-RUNTIME-001（L2-R5）
     + ID71（快慢）/ HUF（Cryogenic → Atomic 等人类签名）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Δ-Analysis 共享接口（ICD §3.3）——与编译器 C6 同一语义，本地 import 解耦
try:  # 编译器包在 workspace 内（sys.path 注入模式，同 tdca-fos 惯例）
    from nsfl_compiler.delta_analysis import SelfModificationAnalyzer
except ImportError:  # pragma: no cover - 独立部署降级
    SelfModificationAnalyzer = None  # type: ignore

# 四态枚举（DCD-NSFL-M1-FROZEN-001 裁决定档）
SENSOR_STATES = ("SAFE", "WARNING", "BLOCKED", "CRYOGENIC")

# 四态 → 熔断档位映射（对齐 C2 FuseDirective 档位）
STATE_TO_FUSE = {
    "SAFE": "PASS",
    "WARNING": "SOFT",       # 限频/限域
    "BLOCKED": "HARD",       # 即时阻断
    "CRYOGENIC": "ATOMIC",   # 全量冻结，等待人类签名（HUF）
}


@dataclass(frozen=True)
class SensorVerdict:
    """L2-R5 Sensor 输出（对齐 ICD §3.1 响应契约）。"""
    verdict: str                     # SAFE / WARNING / BLOCKED / CRYOGENIC
    confidence: float
    distance: float                  # 与负空间拓扑距离（越大越安全）
    mapped_fuse: str                 # PASS / SOFT / HARD / ATOMIC
    nca_ref: str
    ns_type_inferred: Optional[str] = None
    audit_trail: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "distance": self.distance,
            "mapped_fuse": self.mapped_fuse,
            "nca_ref": self.nca_ref,
            "ns_type_inferred": self.ns_type_inferred,
            "audit_trail": list(self.audit_trail),
        }


@dataclass
class _TrajectoryRecord:
    """单次 Δ 观测（进化轨迹记录）。"""
    timestamp: float
    verdict: str
    distance: float


_AUTO = object()  # 哨兵：默认自动构建 analyzer


class NSBoundarySensor:
    """NS-Boundary Sensor（L2-R5，纯只读检测 + 轨迹记录）。"""

    def __init__(self, nca_prefix: str = "NCA-SENSOR",
                 trajectory_window: int = 20,
                 warning_distance: float = 0.35,
                 blocked_distance: float = 0.15,
                 analyzer: object = _AUTO):
        self._nca_prefix = nca_prefix
        self._window = trajectory_window
        self._warning_dist = warning_distance
        self._blocked_dist = blocked_distance
        if analyzer is _AUTO:
            self._analyzer = SelfModificationAnalyzer() if SelfModificationAnalyzer else None
        else:
            self._analyzer = analyzer  # None 显式传入 = 禁用分析器（fail-closed 路径）
        self._trajectory: Dict[str, List[_TrajectoryRecord]] = {}   # subject -> 轨迹
        self._locked = True

    # ---- 主入口（对齐 ICD §3.1: POST /v1/ns-boundary-sensor/analyze）----

    def analyze(self, agent_state: dict, delta: dict) -> SensorVerdict:
        """Δ 分析 → 四态判定（对齐 ICD §3.1 响应契约）。

        安全约束（fail-closed）: Δ-Analysis 不可用（analyzer 缺失/异常）→
        一律判定 BLOCKED（硬阻断 + 上报），禁止降级放行。
        """
        subject = agent_state.get("S_agent_cog", {})
        subject_id = subject.get("id", "S_agent_cog")
        nca_ref = f"{self._nca_prefix}-{int(time.time() * 1000)}"
        trail: List[dict] = []

        # 1. Δ-Analysis（ICD §3.3 共享接口——与编译器 C6 同一语义）
        #    不可用 → fail-closed: BLOCKED（禁止 SAFE 放行）
        if self._analyzer is None:
            return SensorVerdict(
                verdict="BLOCKED",
                confidence=0.5,
                distance=0.0,
                mapped_fuse="HARD",
                nca_ref=nca_ref,
                ns_type_inferred=None,
                audit_trail=[{"step": "fail_closed",
                              "note": "Δ-Analysis 不可用，禁止降级放行"}],
            )
        try:
            delta_res = self._analyzer.delta_analyze(agent_state, delta)
        except Exception as exc:  # 分析器异常 → fail-closed（BV-3: 安全组件禁 fail-open）
            return SensorVerdict(
                verdict="BLOCKED",
                confidence=0.5,
                distance=0.0,
                mapped_fuse="HARD",
                nca_ref=nca_ref,
                ns_type_inferred=None,
                audit_trail=[{"step": "fail_closed",
                              "note": f"Δ-Analysis 异常，禁止降级放行: {type(exc).__name__}"}],
            )
        trail.append({
            "step": "delta_analysis",
            "verdict": delta_res.verdict,
            "distance": delta_res.distance,
            "ns_type_inferred": delta_res.ns_type_inferred,
        })

        # 2. 轨迹梯度趋近检测（Warning/Blocked 判定输入）
        dist = delta_res.distance
        base_verdict = delta_res.verdict
        trend = self._update_trajectory(subject_id, base_verdict, dist)
        trail.append({"step": "trajectory", "trend": trend, "distance": round(dist, 3)})

        # 3. 四态合成（DCD 裁决定档语义）
        verdict, confidence = self._synthesize(base_verdict, dist, trend, delta, trail)

        # 4. Cryogenic 强制 HUF 语义（Atomic + 等待人类签名）
        if verdict == "CRYOGENIC":
            trail.append({"step": "huf", "note": "Atomic 全量冻结，等待人类签名（不可绕过）"})

        return SensorVerdict(
            verdict=verdict,
            confidence=confidence,
            distance=dist,
            mapped_fuse=STATE_TO_FUSE[verdict],
            nca_ref=nca_ref,
            ns_type_inferred=delta_res.ns_type_inferred if delta_res else None,
            audit_trail=trail,
        )

    # ---- 四态合成 ----

    def _synthesize(self, base_verdict: str, dist: float, trend: str,
                    delta: dict, trail: List[dict]) -> tuple:
        # 危险模式命中 → BLOCKED（拓扑距离 < 阈值）
        if base_verdict == "BLOCKED" or dist <= self._blocked_dist:
            return "BLOCKED", 0.95

        # 自我修改意图（无危险模式命中）→ 保持 CRYOGENIC（Atomic 冻结，等人类签名）
        # 不依赖轨迹条数降级——意图持续存在即持续冻结（防第 3 次观测跳变为 SAFE）
        if self._has_self_modification_intent(delta):
            return "CRYOGENIC", 0.7

        # 梯度趋近（轨迹连续下降）→ WARNING
        if trend == "descending" or dist <= self._warning_dist:
            return "WARNING", 0.65

        # 权重修改（非危险）→ WARNING（可观测进化）
        if base_verdict == "WARNING":
            return "WARNING", 0.6

        return "SAFE", 0.85

    @staticmethod
    def _has_self_modification_intent(delta: dict) -> bool:
        """Δ 是否含自我修改意图（type 为权重/代码修改且带 self 标签）。"""
        d = delta.get("delta_c", "")
        if isinstance(d, str) and ("self" in d.lower() or "modify" in d.lower()):
            return True
        labels = delta.get("labels", [])
        return any("self" in str(x).lower() for x in labels) if isinstance(labels, list) else False

    # ---- 轨迹记录 ----

    def _update_trajectory(self, subject: str, verdict: str, dist: float) -> str:
        recs = self._trajectory.setdefault(subject, [])
        recs.append(_TrajectoryRecord(time.time(), verdict, dist))
        if len(recs) > self._window:
            del recs[: len(recs) - self._window]
        # 趋势: 最近 3 点距离单调下降 → descending
        if len(recs) >= 3:
            recent = [r.distance for r in recs[-3:]]
            if recent[0] > recent[1] > recent[2]:
                return "descending"
        return "stable"

    def trajectory_of(self, subject: str) -> List[dict]:
        return [
            {"timestamp": r.timestamp, "verdict": r.verdict, "distance": r.distance}
            for r in self._trajectory.get(subject, [])
        ]

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"Sensor 不可变（{name}）")
        super().__setattr__(name, value)
