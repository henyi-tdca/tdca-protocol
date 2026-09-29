# -*- coding: utf-8 -*-
"""
D-2 · P2 /nsfl/preflight/check HTTP 端点（前端 CP-1 数据源，可用性缺口修复）
锚定: D2-NSFL-INTERFACE-CONTRACT-001（P2 /nsfl/preflight/check 契约）+ TDCA-INTERFACE-CSCP-NSFL-001（FROZEN 映射）
实现: NSFLUnionEngine.compute → NegativeSpaceUnion（DCD-CSCP-CHANGE-001 状态映射）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .engine import NSFLUnionEngine
from .schema import FuseLevel, NS_Operator, NS_Rule, NS_Type, SceneNSFL

app = FastAPI(title="D-2 NSFL Union Engine API", version="P2")

_engine = NSFLUnionEngine()


class RuleIn(BaseModel):
    rule_id: str = ""
    ns_type: str
    operator: str
    parameter: str | None = None
    unit: str | None = None


class SceneIn(BaseModel):
    scene_id: str = ""
    rules: list[RuleIn] = Field(default_factory=list)


class PreflightRequest(BaseModel):
    caller_scene: SceneIn
    callee_scene: SceneIn
    caller_tier: str = "L2"
    cross_scene_flag: bool = True


def _build_scene(scene_in: SceneIn, default_id: str) -> SceneNSFL:
    from decimal import Decimal
    rules = []
    for r in scene_in.rules:
        op = NS_Operator(r.operator)
        kw: Dict[str, Any] = {}
        if op in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN, NS_Operator.LIMIT_EQ):
            kw = {"parameter": Decimal(str(r.parameter)), "unit": r.unit or "CNY"}
        elif op is NS_Operator.RESTRICT_TIER:
            kw = {"parameter": FuseLevel(str(r.parameter).upper())}
        elif op in (NS_Operator.ALLOW, NS_Operator.FORBID) and r.parameter is not None:
            kw = {"parameter": r.parameter}
        rules.append(NS_Rule(r.rule_id or f"R{len(rules)}", NS_Type(r.ns_type), op, **kw))
    return SceneNSFL(scene_id=scene_in.scene_id or default_id, rules=rules)


@app.post("/nsfl/preflight/check")
def preflight_check(req: PreflightRequest) -> Dict[str, Any]:
    """P2 /nsfl/preflight/check（CP-1）：负空间预检，返回 NegativeSpaceUnion 形状。"""
    scene_a = _build_scene(req.caller_scene, "A")
    scene_b = _build_scene(req.callee_scene, "B")
    tier = None
    try:
        tier = FuseLevel(req.caller_tier.upper()) if req.caller_tier else None
    except ValueError:
        tier = None
    u = _engine.compute(scene_a, scene_b, tier_a=tier)
    return {
        "scene_a": u.scene_a,
        "scene_b": u.scene_b,
        "union_set": [t.value for t in u.union_set],
        "conflict_set": [
            {"ns_type": c.ns_type.value, "severity": c.severity.value,
             "resolution": c.resolution.value, "reason": c.reason,
             "resolution_value": _norm(c.resolution_value)}
            for c in u.conflict_set
        ],
        "risk_premium": u.risk_premium,
        "recommended_alt_path": u.recommended_alt_path,
        "computation_time_ms": u.computation_time_ms,
        "nca_ref": u.nca_ref,
        "review_queue": u.review_queue,
    }


def _norm(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, FuseLevel):
        return v.value
    return str(v)
