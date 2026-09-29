# -*- coding: utf-8 -*-
"""
W4 翻译器市场 API（FastAPI）
锚定: TDCA-PLAN-5CC-PHASE-C §六（GET /translator/match 真实数据驱动定价）+ T-P4-002/003
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .market import SceneTranslatorMarket
from .mou_split import MOUSplitContract, default_mou_value_fn

app = FastAPI(title="W4 Translator Market", version="T-P4-002/003")

_market = SceneTranslatorMarket()
_mou = MOUSplitContract()


class MatchRequest(BaseModel):
    src: str
    dst: str
    risk_premium: float = Field(default=0.2, ge=0.0, le=1.0)


class RegisterRequest(BaseModel):
    translator_id: str = ""
    src: str
    dst: str
    complexity: float = Field(default=1.0, gt=0)
    desc: str = ""


class MOUPreviewRequest(BaseModel):
    scene_ids: List[str] = Field(min_length=2)
    contributions: Dict[str, float]


@app.get("/translator/match")
def match(src: str, dst: str, risk_premium: float = 0.2) -> Dict[str, Any]:
    """GET /translator/match（query params，CSCP 计划 §六 接口）。"""
    return _market.match(src, dst, risk_premium=risk_premium)


@app.post("/translator/register", status_code=201)
def register(req: RegisterRequest) -> Dict[str, Any]:
    te = _market.register(req.model_dump())
    return {"translator_id": te.translator_id, "src": te.src, "dst": te.dst,
            "complexity": te.complexity, "registered": True}


@app.get("/translator/count")
def count() -> Dict[str, Any]:
    return {"count": _market.count(), "min_required": 10, "pass": _market.count() >= 10}


@app.post("/mou/split-preview")
def mou_preview(req: MOUPreviewRequest) -> Dict[str, Any]:
    """MOU 分割预演（Shapley，CCP T3 对齐，近似 <1%）。"""
    if any(s not in req.contributions for s in req.scene_ids):
        raise HTTPException(status_code=400, detail="contributions 须覆盖全部 scene_ids")
    fn = default_mou_value_fn(req.contributions)
    split = _mou.split(req.scene_ids, fn)
    total = round(sum(split.values()), 4)
    return {"scene_ids": req.scene_ids, "shapley_split": split,
            "total_mou": total,
            "method": "exact" if len(req.scene_ids) <= 6 else "monte_carlo",
            "synergy": "scale_effect"}
