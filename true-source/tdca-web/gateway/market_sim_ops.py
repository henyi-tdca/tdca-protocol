# -*- coding: utf-8 -*-
"""
P9 配置权市场沙盒最小链：/api/v1/market-sim/* —— 发布→准入审查→撮合→结算。

口径（组四 P9 要件 4/5）：
  - 期一承诺＝规范入册＋最小可用挂接，⛔ 不承诺 L2 市场全功能上线；
  - 全程 SIMULATED 硬标注：结算＝站内积分模拟（⛔ 不冒充真实 e-CNY），
    税务＝金税四期功能模拟（⛔ 不冒充真实税务申报）；
  - 准入审查复用 P2 准入闸门之授权件机验结果（查 active 授权件），⛔ 不重做；
    无有效授权件即 deny（无授权不得调用）；
  - 逐步 NCA 全链留痕（发布／准入／撮合／结算各一条）；
  - 「不依赖外部」口径：外部依赖形态按「自足形态＋预留平移位」处理。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/market-sim", tags=["market-sim"])

_SIM_NOTE = ("结算＝SIMULATED（站内积分模拟，⛔ 不冒充真实 e-CNY）；"
             "税务＝SIMULATED（金税四期功能模拟，⛔ 不冒充真实税务申报）")


class OfferIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_ref: str              # 出让方主体引用（P2 授权件 subject_agent 对齐）
    asset_summary: str           # 标的摘要（五阶资产形态说明，文字面）
    scene: str                   # 场景（准入审查按授权件场景约束比对）
    price_points: int = 0        # 报价（站内积分·SIMULATED；⛔ 非真实货币）


@router.post("/chain", status_code=201)
def market_sim_chain(req: OfferIn, request: Request):
    """沙盒最小链：发布→准入审查→撮合→结算（全程 SIMULATED，逐步 NCA 留痕）。"""
    user = _require_session_user(request)
    if not req.seller_ref.strip() or not req.asset_summary.strip() or not req.scene.strip():
        raise HTTPException(400, "seller_ref／asset_summary／scene 为必填（最小链要约）")
    if req.price_points < 0:
        raise HTTPException(400, "price_points 不得为负（站内积分·SIMULATED）")
    offer = {"seller_ref": req.seller_ref.strip(),
             "asset_summary": req.asset_summary.strip(),
             "scene": req.scene.strip(), "price_points": req.price_points}
    steps = []

    def _step(name: str, action: str, ok: bool, detail: str) -> str:
        nca_ref = _nca_append(action, user["username"],
                              artifact_path=f"market-sim:{run_id}")
        steps.append({"step": name, "ok": ok, "detail": detail,
                      "nca_ref": nca_ref, "simulated": True})
        return nca_ref

    run_id = f"MS-{uuid.uuid4().hex[:10]}"
    # ① 发布
    _step("发布", "MARKETSIM_PUBLISH", True, "要约已发布（沙盒最小链·SIMULATED）")
    # ② 准入审查（复用 P2 授权件机验结果：active 且场景约束匹配）
    with get_session() as s:
        grants = (s.query(M.AuthGrant)
                  .filter_by(subject_agent=offer["seller_ref"], status="active")
                  .all())
    matched = [g for g in grants if g.scene_constraint == offer["scene"]]
    if not matched:
        _step("准入审查", "MARKETSIM_ADMISSION", False,
              "deny：无有效授权件（无授权不得调用——P2 准入闸门口径）")
        result, final_action = "denied", "MARKETSIM_DENIED"
        nca_ref = _nca_append(final_action, user["username"],
                              artifact_path=f"market-sim:{run_id}")
    else:
        _step("准入审查", "MARKETSIM_ADMISSION", True,
              f"admit：授权件 {matched[0].grant_id}（场景约束匹配；P2 机验复用）")
        # ③ 撮合（站内对手方·SIMULATED）
        _step("撮合", "MARKETSIM_MATCH", True,
              "撮合成功（站内对手方模拟·SIMULATED）")
        # ④ 结算（站内积分模拟＋税模拟）
        _step("结算", "MARKETSIM_SETTLE", True,
              f"结算完成（{offer['price_points']} 站内积分）；" + _SIM_NOTE)
        result, final_action = "settled", "MARKETSIM_SETTLED"
        nca_ref = _nca_append(final_action, user["username"],
                              artifact_path=f"market-sim:{run_id}")
    with get_sessionmaker().begin() as s:
        s.add(M.MarketSimRun(
            run_id=run_id, offer_json=json.dumps(offer, ensure_ascii=False),
            steps_json=json.dumps(steps, ensure_ascii=False),
            result=result, nca_ref=nca_ref, created_at=_utc()))
    return _nca_watermark({
        "run_id": run_id, "result": result, "steps": steps, "nca_ref": nca_ref,
        "simulated": True,
        "note": ("沙盒最小链完成（发布→准入→撮合→结算）；"
                 if result == "settled" else
                 "准入审查 deny（无有效授权件）——链止于此，全程留痕；") + _SIM_NOTE})


@router.get("/chains")
def market_sim_chains(request: Request, result: str = ""):
    """最小链运行清单（内部呈现；SIMULATED 硬标注）。"""
    _require_session_user(request)
    if result and result not in ("settled", "denied"):
        raise HTTPException(400, "result 过滤值非法")
    with get_session() as s:
        q = s.query(M.MarketSimRun).order_by(M.MarketSimRun.created_at)
        if result:
            q = q.filter_by(result=result)
        rows = q.all()
    return _nca_watermark({
        "simulated": True, "count": len(rows),
        "runs": [{"run_id": r.run_id, "result": r.result,
                  "offer": json.loads(r.offer_json),
                  "steps": json.loads(r.steps_json), "nca_ref": r.nca_ref,
                  "created_at": r.created_at} for r in rows],
        "note": "沙盒最小链清单（发布→准入审查→撮合→结算；全程 SIMULATED）"})


@router.get("/chain/{run_id}")
def market_sim_chain_one(run_id: str, request: Request):
    """单条运行留痕（逐步 NCA refs 可查）。"""
    _require_session_user(request)
    with get_session() as s:
        row = s.get(M.MarketSimRun, run_id)
    if row is None:
        raise HTTPException(404, "run_id 不存在")
    return _nca_watermark({
        "simulated": True,
        "run": {"run_id": row.run_id, "result": row.result,
                "offer": json.loads(row.offer_json),
                "steps": json.loads(row.steps_json), "nca_ref": row.nca_ref,
                "created_at": row.created_at},
        "note": "最小链单条留痕（NCA 全链可追溯）"})
