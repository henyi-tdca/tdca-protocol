# -*- coding: utf-8 -*-
"""
W4 T-P4-002 · SceneTranslator 市场（场景翻译器注册中心 + 匹配 + 定价）
锚定: TDCA-TASK-CSCP-HANDSHAKE-001 §4.2（SceneTranslator 匹配引擎：源-目标场景双向索引检索
     ≥10 对注册[S-CSCP-001] + <500ms）+ 翻译费用 = 复杂度 × risk_premium（D-2 RiskPremium 输出）
     + W4 翻译器市场（GET /translator/match 真实数据驱动定价，TDCA-PLAN-5CC-PHASE-C §六）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# 阶段 1 最小注册集（S-CSCP-001: ≥10 对）——文旅/农产品/教育/健康/供应链 双向组合
DEFAULT_REGISTRY: List[Dict[str, Any]] = [
    {"translator_id": "TR-TOUR-AGRI", "src": "SCN-TOUR", "dst": "SCN-AGRI", "complexity": 1.0, "desc": "文旅→农产品 需求翻译"},
    {"translator_id": "TR-AGRI-TOUR", "src": "SCN-AGRI", "dst": "SCN-TOUR", "complexity": 1.0},
    {"translator_id": "TR-TOUR-EDU", "src": "SCN-TOUR", "dst": "SCN-EDU", "complexity": 1.2},
    {"translator_id": "TR-EDU-TOUR", "src": "SCN-EDU", "dst": "SCN-TOUR", "complexity": 1.2},
    {"translator_id": "TR-AGRI-EDU", "src": "SCN-AGRI", "dst": "SCN-EDU", "complexity": 0.8},
    {"translator_id": "TR-EDU-AGRI", "src": "SCN-EDU", "dst": "SCN-AGRI", "complexity": 0.8},
    {"translator_id": "TR-TOUR-HEALTH", "src": "SCN-TOUR", "dst": "SCN-HEALTH", "complexity": 1.5},
    {"translator_id": "TR-HEALTH-TOUR", "src": "SCN-HEALTH", "dst": "SCN-TOUR", "complexity": 1.5},
    {"translator_id": "TR-AGRI-SUPPLY", "src": "SCN-AGRI", "dst": "SCN-SUPPLY", "complexity": 1.1},
    {"translator_id": "TR-SUPPLY-AGRI", "src": "SCN-SUPPLY", "dst": "SCN-AGRI", "complexity": 1.1},
    {"translator_id": "TR-EDU-HEALTH", "src": "SCN-EDU", "dst": "SCN-HEALTH", "complexity": 1.3},
    {"translator_id": "TR-HEALTH-EDU", "src": "SCN-HEALTH", "dst": "SCN-EDU", "complexity": 1.3},
]


@dataclass
class TranslatorEntry:
    translator_id: str
    src: str
    dst: str
    complexity: float
    desc: str = ""
    registered_at: float = field(default_factory=time.time)


class SceneTranslatorMarket:
    """翻译器市场：源-目标双向索引 + 匹配 + 定价（费用 = 复杂度 × risk_premium）。"""

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None):
        self._entries: List[TranslatorEntry] = []
        self._by_src: Dict[str, List[TranslatorEntry]] = {}
        self._by_dst: Dict[str, List[TranslatorEntry]] = {}
        for e in entries or DEFAULT_REGISTRY:
            self.register(e)

    def register(self, entry: Dict[str, Any]) -> TranslatorEntry:
        """注册翻译器（双向索引）。"""
        te = TranslatorEntry(translator_id=entry.get("translator_id") or f"TR-{uuid.uuid4().hex[:8]}",
                             src=entry["src"], dst=entry["dst"],
                             complexity=float(entry.get("complexity", 1.0)),
                             desc=entry.get("desc", ""))
        self._entries.append(te)
        self._by_src.setdefault(te.src, []).append(te)
        self._by_dst.setdefault(te.dst, []).append(te)
        return te

    def count(self) -> int:
        return len(self._entries)   # 注册总条数（S-CSCP-001: ≥10 对）

    def match(self, src: str, dst: str, risk_premium: float = 0.2) -> Dict[str, Any]:
        """源→目标翻译器匹配 + 定价（<500ms 硬指标；费用 = 复杂度 × risk_premium）。"""
        start = time.perf_counter()
        candidates = self._by_src.get(src, [])
        found = next((t for t in candidates if t.dst == dst), None)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if found is None:
            # 反向检索（双向索引）：无正向翻译器时查反向（逆翻译复用，阶段 1 简化）
            reverse = next((t for t in self._by_dst.get(src, []) if t.src == dst), None)
            return {"matched": False, "translator": None,
                    "reason": "NO_TRANSLATOR" if reverse is None else "REVERSE_ONLY",
                    "reverse_translator": reverse.translator_id if reverse else None,
                    "latency_ms": round(elapsed_ms, 3)}
        cost = round(found.complexity * risk_premium, 4)
        return {"matched": True, "translator": found.translator_id,
                "src": src, "dst": dst,
                "complexity": found.complexity,
                "risk_premium": risk_premium,
                "translation_cost": cost,
                "latency_ms": round(elapsed_ms, 3)}
