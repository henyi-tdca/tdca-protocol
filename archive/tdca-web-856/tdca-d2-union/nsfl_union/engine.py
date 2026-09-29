# -*- coding: utf-8 -*-
"""
TDCA D-2 NSFLUnionEngine · 跨场景负空间并集运算引擎（NSFL V0.2）
锚定: TDCA-TASK-D2-NSFL-V02-001 §二/§三 + D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL
核心: 并集 O(|A|+|B|) + 规则级冲突检测 + risk_premium 权重表 + Alt-Path 五元拓扑 + NCA 审计
禁止项（继承 MASTER §3.1）: 缓存 >5min / 绕过人类签名 / 非 CBDC 结算 / 蒸馏 / L 级跨场景
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple

from .alt_path import AltPathPlanner
from .conflict import ConflictDetector
from .schema import (FuseLevel, NegativeSpaceUnion, NS_Rule, NS_Type,
                     SceneNSFL, Severity)
from .weights import RiskPremiumCalculator

NcaGenerator = Callable[..., str]


class NSFLUnionEngine:
    """NSFLUnionEngine 并集引擎（D-2 任务书核心交付物）。

    :param nca_generator: NCA 生成器（对齐 fuse_engine 注入模式，generate 接口）
    :param enable_cache: 并集缓存开关（默认关；开启时 TTL 强制 ≤300s，禁止 >5min）
    :param cache_ttl_seconds: 缓存 TTL（上限 300，超限钳制）
    """

    CACHE_TTL_MAX = 300  # 5min 硬上限（MASTER 禁止项）

    def __init__(self, nca_generator: Optional[NcaGenerator] = None,
                 enable_cache: bool = False,
                 cache_ttl_seconds: int = 300):
        self.detector = ConflictDetector()
        self.pricer = RiskPremiumCalculator()
        self.planner = AltPathPlanner()
        self.nca = nca_generator
        self.enable_cache = enable_cache
        self.cache_ttl = min(cache_ttl_seconds, self.CACHE_TTL_MAX)  # 钳制 ≤5min
        self._cache: Dict[Tuple[str, str, Optional[str], Optional[str]],
                          Tuple[float, NegativeSpaceUnion]] = {}

    def compute(self, scene_a: SceneNSFL, scene_b: SceneNSFL,
                tier_a: Optional[FuseLevel] = None,
                tier_b: Optional[FuseLevel] = None,
                registry: Optional[List[SceneNSFL]] = None,
                compute_alt_path: bool = True) -> NegativeSpaceUnion:
        """任意两场景负空间并集运算（<100ms 硬指标，P95<150ms）。"""
        cache_key = self._cache_key(scene_a, scene_b, tier_a, tier_b)
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        start = time.perf_counter()

        # 1. 并集运算 O(|NS_A|+|NS_B|)（集合运算，无字符串匹配）
        union_set = sorted(
            {r.ns_type for r in scene_a.rules} | {r.ns_type for r in scene_b.rules},
            key=lambda t: t.value)

        # 2. 规则级冲突检测（L0 基底 + 判定表 + review_queue + 兜底）
        result = self.detector.compare(scene_a, scene_b)

        # 3. 风险溢价（权重表，抗稀释）
        premium = self.pricer.compute(result.conflict_set, tier_a, tier_b)

        # 4. 替代路径推荐（五元拓扑绕行）
        alt_paths: Optional[List[str]] = None
        if compute_alt_path and registry:
            candidates = self.planner.find_alt_paths(
                scene_a, scene_b, registry, self,
                base_conflicts=len(result.conflict_set), base_premium=premium)
            alt_paths = [c.scene_c_id for c in candidates] or None

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        nca_ref = self._record_nca(scene_a, scene_b, union_set, result.conflict_set, elapsed_ms)

        out = NegativeSpaceUnion(
            scene_a=scene_a.scene_id,
            scene_b=scene_b.scene_id,
            union_set=union_set,
            conflict_set=result.conflict_set,
            risk_premium=premium,
            recommended_alt_path=alt_paths,
            computation_time_ms=round(elapsed_ms, 3),
            nca_ref=nca_ref,
            review_queue=result.review_queue,
        )
        if self.enable_cache:
            self._put_cache(cache_key, out)
        return out

    def clear_cache(self) -> None:
        self._cache.clear()

    # ---- 内部 ----

    def _cache_key(self, a: SceneNSFL, b: SceneNSFL,
                   ta: Optional[FuseLevel], tb: Optional[FuseLevel]) -> Tuple:
        fp = lambda s: (s.scene_id, tuple(sorted((r.rule_id, r.operator.value,
                                                  str(r.parameter), r.unit,
                                                  r.severity.value, r.enabled)
                                                 for r in s.rules)))
        return (fp(a), fp(b), ta.value if ta else None, tb.value if tb else None)

    def _get_cache(self, key: Tuple) -> Optional[NegativeSpaceUnion]:
        if not self.enable_cache:
            return None
        item = self._cache.get(key)
        if item is None:
            return None
        ts, val = item
        if time.monotonic() - ts > self.cache_ttl:
            self._cache.pop(key, None)
            return None
        return val

    def _put_cache(self, key: Tuple, val: NegativeSpaceUnion) -> None:
        self._cache[key] = (time.monotonic(), val)

    def _record_nca(self, scene_a: SceneNSFL, scene_b: SceneNSFL,
                    union_set: List[NS_Type], conflicts, elapsed_ms: float) -> str:
        """A-5 审计轨迹: 输入场景 ID / 输出并集 / 冲突明细 / 计算耗时（+ schema/判定表版本 + UNKNOWN 记录）。"""
        if self.nca is not None:
            ref = self.nca(
                type="INSTITUTIONAL", layer=3,
                content={
                    "event": "NSFL_UNION_COMPUTED",
                    "scene_a": scene_a.scene_id, "scene_b": scene_b.scene_id,
                    "union_set": [t.value for t in union_set],
                    "conflict_set": [{"ns_type": c.ns_type.value, "severity": c.severity.value,
                                      "resolution": c.resolution.value, "reason": c.reason}
                                     for c in conflicts],
                    "computation_time_ms": round(elapsed_ms, 3),
                    "schema_version": "D2-NSFL-UNION-SCHEMA-001-V0.1-REV2-FINAL",
                    "decision_table_version": "dt-v1.0",
                    "unknown_conflicts": [c.reason for c in conflicts
                                          if c.resolution.value == "UNKNOWN"],
                },
            )
            return str(ref)
        return f"NCA-MOCK-{uuid.uuid4().hex[:12]}"
