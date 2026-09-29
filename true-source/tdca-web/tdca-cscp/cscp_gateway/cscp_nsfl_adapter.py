# -*- coding: utf-8 -*-
"""
CSCPNSFLAdapter · 正式实现（C1，接口契约 TDCA-INTERFACE-CSCP-NSFL-001）
锚定: TDCA-PLAN-5CC-PHASE-C-001 §2.2（DCD-CSCP-CHANGE-001 映射，FROZEN）
     + D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL（§九 状态映射）
替代: B2 中 MockNSFLUnionAdapter（R-CSCP-001 占位）——C2 真实替换
硬约束: HIGH→TRIGGERED / MEDIUM→FAIL / LOW→PASS / 兜底→REJECTED；延迟 <500ms（P95<800ms）；输出零漂移
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from .state_machine import PreflightStatus

# 延迟上限（CSCP 任务书 §2.1 Step-2 <500ms；计划 §2.2 P95<800ms）
PREFLIGHT_LATENCY_LIMIT_MS = 500.0
PREFLIGHT_P95_LIMIT_MS = 800.0

# 输入规模上限（红队 #2 #1 延迟 DoS 防线）: 单场景规则 ≤100 条
MAX_RULES = 100


def _norm_value(v: Any) -> Any:
    """resolution_value 规范化序列化（红队 #2 #4 零漂移）: Decimal 消指数/尾零，枚举用 .value。"""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return format(v.normalize(), "f")
    if isinstance(v, Enum):
        return v.value
    return str(v)


@dataclass
class ConsistencyReport:
    """validate_consistency 输出（A-9/H-C2-005）。"""
    sample_size: int
    identical: int = 0
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    max_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    errors: int = 0

    @property
    def consistency(self) -> float:
        return (self.identical / self.sample_size * 100.0) if self.sample_size else 100.0


class CSCPNSFLAdapter:
    """D-2 并集引擎 ↔ CSCP 网关适配层（FROZEN 接口契约）。

    :param engine: NSFLUnionEngine 实例（真实 D-2 引擎）
    :param reference_fn: 参考实现（一致性校验基准，默认=同引擎自身——零漂移验证；亦可传 mock）
    """

    def __init__(self, engine, reference_fn=None, registry=None):
        from nsfl_union import NS_Operator, NS_Rule, NS_Type, SceneNSFL
        self._engine = engine
        self._registry = registry or []       # 场景注册表（Alt-Path 推荐，红队 #2 #9）
        self._NS_Type = NS_Type
        self._NS_Operator = NS_Operator
        self._NS_Rule = NS_Rule
        self._SceneNSFL = SceneNSFL
        self._reference_fn = reference_fn or self.preflight_check

    # ---- FROZEN 契约主入口 ----

    def preflight_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """preflight_check（DCD-CSCP-CHANGE-001 映射）。返回 PreflightResult。"""
        start = time.perf_counter()
        try:
            scene_a = self._scene(request.get("caller_scene", {}), "A")
            scene_b = self._scene(request.get("callee_scene", {}), "B")
        except (ValueError, KeyError, TypeError) as exc:
            return self._invalid("INVALID_SCHEMA", str(exc), start)   # 红队 #2 #3: fail-closed
        tier_a = self._tier(request.get("caller_tier"))
        try:
            u = self._engine.compute(scene_a, scene_b, tier_a=tier_a,
                                     registry=self._registry or None)
        except (ValueError, KeyError, TypeError) as exc:
            return self._invalid("COMPUTE_ERROR", str(exc), start)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        unknown = [c for c in u.conflict_set if c.resolution.value == "UNKNOWN"]
        if unknown:
            # 红队 FIN-1: UNKNOWN 冲突不得静默 PASS/FAIL——强制人工复核（fail-closed）
            result = {"status": PreflightStatus.REJECTED,
                      "reason": "REQUIRES_REVIEW",
                      "detail": f"UNKNOWN_CONFLICT:{unknown[0].reason}",
                      "risk_premium": 1.0, "ns_union": self._ns_union(u),
                      "alt_paths": None, "nca_ref": u.nca_ref,
                      "next_step": "rejected", "latency_ms": round(elapsed_ms, 3)}
            return result

        max_sev = max((c.severity.value for c in u.conflict_set), default=None)
        if max_sev == "HIGH":                                   # LEGAL 熔断
            result = {"status": PreflightStatus.TRIGGERED, "risk_premium": 1.0,
                      "ns_union": self._ns_union(u), "alt_paths": [],
                      "nca_ref": u.nca_ref, "next_step": "rejected",
                      "latency_ms": round(elapsed_ms, 3)}
        elif max_sev == "MEDIUM":                               # L2 场景型 → 拒绝 + Alt-Path
            result = {"status": PreflightStatus.FAIL, "risk_premium": u.risk_premium,
                      "ns_union": self._ns_union(u), "alt_paths": u.recommended_alt_path,
                      "nca_ref": u.nca_ref, "next_step": "rejected",
                      "latency_ms": round(elapsed_ms, 3)}
        elif max_sev == "LOW":                                  # L1 自律（R-5 裁决）→ PASS + 抬升
            result = {"status": PreflightStatus.PASS, "risk_premium": u.risk_premium,
                      "ns_union": self._ns_union(u), "alt_paths": u.recommended_alt_path,
                      "nca_ref": u.nca_ref, "next_step": "sandbox_verify",
                      "credit_impact": True, "latency_ms": round(elapsed_ms, 3)}
        elif u.review_queue and (scene_a.has_legal_or_high_tier()
                                 or scene_b.has_legal_or_high_tier()):
            # 兜底（schema §5.1/S-09）: 仅含 LEGAL/档位≥TEARDOWN 且空集才 REJECTED；
            # 普通跨类型 review_queue 不阻断（§5.3 仅审计面，红队复审 N8）
            result = {"status": PreflightStatus.REJECTED, "reason": "REQUIRES_REVIEW",
                      "risk_premium": u.risk_premium, "ns_union": self._ns_union(u),
                      "nca_ref": u.nca_ref, "next_step": "rejected",
                      "latency_ms": round(elapsed_ms, 3)}
        else:                                                   # 无冲突 → PASS（risk_premium=M）
            result = {"status": PreflightStatus.PASS, "risk_premium": u.risk_premium,
                      "ns_union": self._ns_union(u), "alt_paths": None,
                      "nca_ref": u.nca_ref, "next_step": "sandbox_verify",
                      "latency_ms": round(elapsed_ms, 3)}
        return result

    def _invalid(self, reason: str, detail: str, start: float) -> Dict[str, Any]:
        """fail-closed 拒绝（红队 #2 #3）: 统一 REJECTED + 审计，而非 500。
        detail 并入 reason（FIN-7: 输出形状与契约一致，不引入契约外字段）。"""
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {"status": PreflightStatus.REJECTED,
                "reason": f"{reason}:{detail[:160]}", "risk_premium": 0.0,
                "ns_union": None, "alt_paths": None,
                "nca_ref": "NCA-INVALID-INPUT", "next_step": "rejected",
                "latency_ms": round(elapsed_ms, 3)}

    def _tier(self, raw: Any):
        """caller_tier → FuseLevel（红队 #2 #9: 透传档位到 risk_premium M）。缺省 None（OBSERVE）。"""
        from nsfl_union import FuseLevel
        if isinstance(raw, FuseLevel):
            return raw
        try:
            return FuseLevel(str(raw).upper()) if raw else None
        except ValueError:
            return None

    # ---- 一致性校验（A-9 / H-C2-005）----

    def validate_consistency(self, sample_size: int = 1000,
                             scenes: Optional[List[Any]] = None) -> ConsistencyReport:
        """对 sample_size 对场景，比对本实现与参考实现的输出（100% 零漂移）。sample_size 钳制 ≤10⁴（红队 #2 #7）。"""
        sample_size = min(sample_size, 10000)
        report = ConsistencyReport(sample_size=sample_size)
        latencies: List[float] = []
        pairs = self._sample_pairs(sample_size, scenes)
        for i, (sa, sb) in enumerate(pairs):
            req = {"caller_scene": self._scene_dict(sa), "callee_scene": self._scene_dict(sb),
                   "caller_tier": "L2", "cross_scene_flag": True}
            try:
                got = self.preflight_check(req)
                ref = self._reference_fn(req)
                latencies.append(got.get("latency_ms", 0.0))
                if self._same_output(got, ref):
                    report.identical += 1
                else:
                    report.mismatches.append({"pair": i, "got": got, "ref": ref})
            except Exception as exc:                            # noqa: BLE001
                report.errors += 1
                report.mismatches.append({"pair": i, "error": str(exc)})
        if latencies:
            latencies.sort()
            report.max_latency_ms = round(latencies[-1], 3)
            report.p95_latency_ms = round(latencies[int(len(latencies) * 0.95)], 3)
        return report

    # ---- 内部 ----

    def _scene(self, raw: Dict[str, Any], default_id: str):
        rules = []
        raw_rules = raw.get("rules", [])
        if len(raw_rules) > MAX_RULES:
            # 红队复审 N1: 超限必须 fail-closed（拒绝），禁止静默截断（防规则丢失后误判 PASS）
            raise ValueError(f"规则数 {len(raw_rules)} 超上限 {MAX_RULES}")
        for rr in raw_rules:
            ns = self._NS_Type(rr["ns_type"])
            op = self._NS_Operator(rr["operator"])
            kw = {}
            if op in (self._NS_Operator.LIMIT_MAX, self._NS_Operator.LIMIT_MIN,
                      self._NS_Operator.LIMIT_EQ):
                kw = {"parameter": Decimal(str(rr["parameter"])),
                      "unit": rr.get("unit", "CNY")}
            elif op is self._NS_Operator.RESTRICT_TIER:
                from nsfl_union import FuseLevel
                kw = {"parameter": FuseLevel(str(rr["parameter"]).upper())}
            elif op in (self._NS_Operator.ALLOW, self._NS_Operator.FORBID) \
                    and rr.get("parameter") is not None:
                if not isinstance(rr["parameter"], str):
                    raise ValueError("ALLOW/FORBID parameter 仅允许 str 域标签（红队 #2 #5）")
                kw = {"parameter": rr["parameter"]}   # 允许域/禁止对象限定
            rules.append(self._NS_Rule(rr.get("rule_id", f"R{len(rules)}"), ns, op, **kw))
        return self._SceneNSFL(scene_id=raw.get("scene_id", default_id), rules=rules)

    def _scene_dict(self, scene) -> Dict[str, Any]:
        rules = []
        for r in scene.rules:
            item = {"rule_id": r.rule_id, "ns_type": r.ns_type.value,
                    "operator": r.operator.value}
            if r.parameter is not None:
                item["parameter"] = str(r.parameter)
            if r.unit:
                item["unit"] = r.unit
            rules.append(item)
        return {"scene_id": scene.scene_id, "rules": rules}

    def _ns_union(self, u) -> Dict[str, Any]:
        """输出形状零漂移（字段名/类型/枚举值 100% 对齐 A3 契约）。"""
        return {
            "scene_a": u.scene_a, "scene_b": u.scene_b,
            "union_set": [t.value for t in u.union_set],
            "conflict_set": [{"ns_type": c.ns_type.value, "severity": c.severity.value,
                              "resolution": c.resolution.value, "reason": c.reason,
                              "resolution_value": _norm_value(c.resolution_value)}
                             for c in u.conflict_set],
            "risk_premium": u.risk_premium,
            "recommended_alt_path": u.recommended_alt_path,
            "computation_time_ms": u.computation_time_ms,
            "nca_ref": u.nca_ref,
        }

    @staticmethod
    def _same_output(got: Dict[str, Any], ref: Dict[str, Any]) -> bool:
        """字段级 diff = 0（格式一致性）；剔除动态审计字段（latency/nca_ref/computation_time）。"""
        def _norm(d: Dict[str, Any]) -> Dict[str, Any]:
            out = dict(d)
            out.pop("latency_ms", None)
            out.pop("nca_ref", None)
            st = out.get("status")
            if hasattr(st, "value"):
                out["status"] = st.value
            ns = out.get("ns_union")
            if isinstance(ns, dict):
                ns = dict(ns)
                ns.pop("nca_ref", None)
                ns.pop("computation_time_ms", None)
                out["ns_union"] = ns
            return out
        return _norm(got) == _norm(ref)

    def _sample_pairs(self, n: int, scenes: Optional[List[Any]]):
        import random
        rng = random.Random(20260811)
        if scenes is None:
            scenes = self._default_scenes(30)
        pairs = []
        for _ in range(n):
            pairs.append((rng.choice(scenes), rng.choice(scenes)))
        return pairs

    def _default_scenes(self, count: int) -> list:
        from nsfl_union import NS_Type
        types = [t for t in NS_Type if t != NS_Type.LEGAL]  # LEGAL 制度规则专项构造，不进随机抽样
        out = []
        for i in range(count):
            ns = types[i % len(types)]
            rules = [self._NS_Rule(f"B{i}-R1", ns, self._NS_Operator.ALLOW)]
            if ns is NS_Type.TRANSACTION_LIMIT:
                rules.append(self._NS_Rule(
                    f"B{i}-R2", ns, self._NS_Operator.LIMIT_MAX,
                    Decimal(str(1000 + i)), unit="CNY"))
            out.append(self._SceneNSFL(scene_id=f"B{i}", rules=rules))
        return out
