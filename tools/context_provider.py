# -*- coding: utf-8 -*-
"""COP 动态数据流 M1 · context provider 抽象层（TDCA-HANDOFF-KIMI-DATAFLOW-M1-001 / DCD-COP-DATAFLOW-001）

实时状态数据 → context: Situation 实际值（抽象接口 + 注册机制）。
与律三 v2 新鲜度门（data_feed_gate, GSEQ-0612）联动：快照缺失/断流/超 SLA → fail-closed 拒动态决策。

制度锚定:
  - 数据性质: real 设备流标 real；模拟流标 simulated（ID92）——标注强制，不可省略
  - 无数据流 fail-closed: 拒动态决策，降级为仅静态推理（unverified）
  - NSFL 熔断联动: 实时状态触发负空间禁区 → frozen
  - API 外部依赖: 优先免费开放 API，收费 API 禁用（预算纪律）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from data_feed_gate import freshness_gate

# 数据性质标注（ID92）
PROVENANCE_REAL = "real"
PROVENANCE_SIMULATED = "simulated"
_VALID_PROVENANCE = {PROVENANCE_REAL, PROVENANCE_SIMULATED}


class NoContextError(RuntimeError):
    """无数据流 fail-closed：拒绝动态决策（降级为仅静态推理）。"""


@dataclass(frozen=True)
class ContextSnapshot:
    """实时状态快照（→ COP context: Situation 实际值）。"""
    source: str                     # provider 标识（可追溯）
    values: Dict[str, Any]          # 实时状态键值
    timestamp: float                # epoch 秒（机读证据）
    stream_ok: bool                 # 数据流健康标志
    provenance: str                 # real | simulated（ID92 标注强制）

    def __post_init__(self):
        if self.provenance not in _VALID_PROVENANCE:
            raise ValueError(
                f"[NSFL-TRIGGER] provenance 必须标注 real/simulated（ID92），当前: {self.provenance!r}")

    def freshness_payload(self) -> dict:
        """对接律三 v2 新鲜度门（data_feed_gate.freshness_gate）。"""
        return {"timestamp": self.timestamp, "stream_ok": self.stream_ok}


class ContextProvider:
    """context provider 抽象接口：fetch() -> ContextSnapshot。"""

    name: str = "abstract"

    def fetch(self) -> ContextSnapshot:  # pragma: no cover - 抽象接口
        raise NotImplementedError


class ProviderRegistry:
    """provider 注册机制（fail-closed：未注册即拒）。"""

    def __init__(self):
        self._providers: Dict[str, ContextProvider] = {}

    def register(self, provider: ContextProvider) -> None:
        if not getattr(provider, "name", None):
            raise ValueError("[NSFL-TRIGGER] provider 缺 name——不可注册")
        self._providers[provider.name] = provider

    def get(self, name: str) -> ContextProvider:
        if name not in self._providers:
            raise NoContextError(
                f"[NSFL-TRIGGER] provider 未注册: {name}——无数据流 fail-closed（拒动态决策）")
        return self._providers[name]

    def list(self) -> List[str]:
        return sorted(self._providers)


def resolve_context(registry: ProviderRegistry, provider_name: str,
                    sla: Optional[dict] = None, now: Optional[float] = None) -> dict:
    """取快照 → 新鲜度门 → 注入 context。

    pass: 返回 {"context": values, "provenance": ..., "gate": "pass", ...}
    frozen/无数据: raise NoContextError（拒动态决策，降级仅静态推理 unverified）
    """
    provider = registry.get(provider_name)  # 未注册即 NoContextError
    snapshot = provider.fetch()
    if not isinstance(snapshot, ContextSnapshot):
        raise NoContextError(
            f"[NSFL-TRIGGER] provider {provider_name} 返回非快照——数据流异常 fail-closed")
    verdict = freshness_gate(snapshot.freshness_payload(),
                             sla or {"max_staleness_s": 15}, now=now)
    if verdict["gate"] != "pass":
        raise NoContextError(
            f"[NSFL-TRIGGER] 新鲜度门冻结: {verdict['reason']}")
    return {
        "context": dict(snapshot.values),
        "provenance": snapshot.provenance,
        "source": snapshot.source,
        "gate": verdict["gate"],
        "staleness_s": verdict["staleness_s"],
    }


# ---- NSFL 熔断联动（实时状态触发负空间熔断） ----

_OPS: Dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
}


def nsfl_dynamic_check(values: Dict[str, Any], rules: List[dict]) -> dict:
    """实时状态 → 负空间熔断判定。

    rules: [{"key": "alarm", "op": "==", "value": "critical", "reason": "..."}...]
    任一规则命中 → {"decision": "frozen", "hit": rule}；无命中 → {"decision": "pass"}
    """
    for rule in rules or []:
        key, op, expect = rule.get("key"), rule.get("op"), rule.get("value")
        if key not in values or op not in _OPS:
            continue
        try:
            if _OPS[op](values[key], expect):
                return {"decision": "frozen",
                        "hit": {"key": key, "op": op, "value": expect},
                        "reason": rule.get("reason", f"实时状态触发负空间禁区: {key} {op} {expect}")}
        except TypeError:
            continue  # 类型不可比 → 不命中（保守不误熔）
    return {"decision": "pass"}


class CallableProvider(ContextProvider):
    """可注入数据源的通用 provider（免费公开 API 通道 / 测试桩共用）。"""

    def __init__(self, name: str, source_fn: Callable[[], Dict[str, Any]],
                 provenance: str = PROVENANCE_SIMULATED):
        self.name = name
        self._fn = source_fn
        self._provenance = provenance

    def fetch(self) -> ContextSnapshot:
        payload = self._fn()  # None/异常 → 断流（stream_ok=False），由门控 fail-closed
        if not isinstance(payload, dict) or not payload:
            return ContextSnapshot(source=self.name, values={}, timestamp=time.time(),
                                   stream_ok=False, provenance=self._provenance)
        ts = payload.pop("timestamp", time.time())
        ok = bool(payload.pop("stream_ok", True))
        return ContextSnapshot(source=self.name, values=payload, timestamp=float(ts),
                               stream_ok=ok, provenance=self._provenance)
