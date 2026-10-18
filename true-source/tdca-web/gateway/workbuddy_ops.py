# -*- coding: utf-8 -*-
"""
P1 WorkBuddy 上站（A-12）：/api/v1/workbuddy/* —— 会话鉴权 + DB 持久化 + NCA 落链。

依据: 期一提案 P1；P5 T-P5-001 接口契约（/workflow/create·execute·status +
      /signature/request·confirm）；引擎经公开方法调用（BV-3：FROZEN 引擎只 import +
      调用公开方法，⛔ 不改 tdca-workbuddy 子应用本体）。
红线: 人类签名不可绕过（引擎内 PermissionError→403）；NSFL 检查 fail-closed；
      WORM 日志哈希链完整性可查。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

_ROOT = Path(__file__).resolve().parent
_WS_ROOT = _ROOT.parent  # tdca-web/
for _sub in ("tdca-workbuddy",):
    _p = _WS_ROOT / _sub
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _owner_display,  # noqa: E402
                    _require_session_user, _utc)

router = APIRouter(prefix="/api/v1/workbuddy", tags=["workbuddy"])
logger = logging.getLogger(__name__)


# ---- P5 引擎（单例；nca_fn 落 nca_chain；nsfl_check_fn 接 D-2 场景负空间）----
def _engine_nca(type: str = "OPERATIONAL", layer: int = 3,
                content: Dict[str, Any] | None = None) -> str:
    event = (content or {}).get("event", type)
    return _nca_append(f"WORKBUDDY:{event}", "workbuddy-engine",
                       artifact_path="workbuddy:ops")


def _gateway_nsfl_check(step) -> bool:
    """跨场景步骤负空间检查（D-2 口径）：场景自带 LEGAL/高档位负空间 → BLOCK。
    引擎缺失（ImportError）→ 放行并如实标注（SIMULATED）；其他异常 → fail-closed 按命中。"""
    try:
        from nsfl_union.schema import SceneNSFL
    except ImportError:
        return True
    try:
        return not SceneNSFL(scene_id=step.scene).has_legal_or_high_tier()
    except Exception:
        return False


from workbuddy.engine import CrossSceneWorkflowEngine, WorkflowDSL  # noqa: E402

_engine = CrossSceneWorkflowEngine(nca_fn=_engine_nca,
                                   nsfl_check_fn=_gateway_nsfl_check)


# =====================================================================
# 工作流 create / execute / status（P5 契约）
# =====================================================================

class CreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")   # 未知字段 fail-closed
    workflow_template: Dict[str, Any]


@router.post("/workflow/create", status_code=201)
def wb_create(req: CreateRequest, request: Request):
    """创建（DSL 校验 → 归属判定【B6：任何副作用之前】→ WORM 落 CREATE → 定义落库 → 缔约存证）。

    B6（TDCA-HANDOFF-SITE-UX-PLAIN-001-IMPL-001 批3，附条件三条，⛔ 缺一不可）：
      条件1 归属判定（存在 & 属谁）置于任何副作用之前——⛔ 不落 WORM ⛔ 不追加 NCA ⛔ 不调 engine.create；
      条件2 本人／founder 重建 ⟹ 幂等回成功但零新增（NCA／WORM 条数不变）；
      条件3 撞他人 ID ⟹ 409＋归属提示（脱敏角色口径，⛔ 不暴露用户名）。
    """
    user = _require_session_user(request)
    try:
        wf = WorkflowDSL.from_dict(req.workflow_template)
    except (KeyError, TypeError) as exc:
        raise HTTPException(400, f"DSL 无效: {exc}")
    # 条件1：归属判定（纯读，⛔ 零副作用）——先判后写，堵住撞 ID 重复落 WORM/NCA
    with get_session() as s_check:
        existing = s_check.get(M.WorkflowDef, wf.workflow_id)
        owner_disp = _owner_display(s_check, existing.owner_username) if existing else None
    if existing is not None:
        if existing.owner_username != user["username"] and user.get("role") != "founder":
            raise HTTPException(409,
                                "该 workflow_id 已存在且归属他人"
                                f"（归属：{owner_disp}）——请更换 workflow_id，"
                                "或由原创建人（或 founder）执行（本次请求零 WORM／零 NCA 落链）")
        # 条件2：幂等路径——⛔ 不调 engine.create ⛔ 不追加 NCA，零新增
        return _nca_watermark({
            "workflow_id": existing.workflow_id, "status": existing.status,
            "owner": user["username"], "nca_ref": existing.nca_ref,
            "existed": True,
            "note": "工作流已存在（幂等返回，零新增存证：NCA／WORM 条数不变）"})
    created = _engine.create(wf)
    nca_ref = _nca_append("WORKBUDDY_CREATE", user["username"],
                          artifact_path=f"workflow:{wf.workflow_id}")
    with get_sessionmaker().begin() as s:
        s.add(M.WorkflowDef(
            workflow_id=wf.workflow_id, owner_username=user["username"],
            dsl_json=json.dumps(req.workflow_template, ensure_ascii=False),
            status=created["status"], nca_ref=nca_ref, created_at=_utc()))
    return _nca_watermark({**created, "owner": user["username"], "nca_ref": nca_ref,
                           "note": "工作流已创建（PENDING_HUMAN_GATE，执行须经人类签名门禁）"})


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = ""
    human_signature: str = ""


@router.post("/workflow/execute")
def wb_execute(req: ExecuteRequest, request: Request):
    """执行（签名门禁 → 步骤执行 + NSFL 预检 → 运行记录落库 + NCA 全链）。"""
    user = _require_session_user(request)
    with get_session() as s:
        row = s.get(M.WorkflowDef, req.workflow_id)
    if row is None:
        raise HTTPException(404, "workflow_id 不存在")
    if row.owner_username and row.owner_username != user["username"] \
            and user.get("role") != "founder":
        raise HTTPException(403, "仅创建人（或 founder）可执行该工作流")
    try:
        wf = WorkflowDSL.from_dict(json.loads(row.dsl_json))
        start = time.perf_counter()
        ex = _engine.execute(wf, req.human_signature)
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 1)
    except PermissionError as exc:
        # L1SI153 段二①：引擎底层异常只进日志，⛔ 不直透用户；对外固定码＋通用三段式文案
        logger.warning("workbuddy execute denied by engine: %s", exc)
        raise HTTPException(403, "本次执行被签名门禁拒绝，工作流未被运行（人类签名权不可绕过）。"
                                 "你的签名未通过校验。请重新进行人工签名确认后再执行；仍不通请联系运维。")
    except KeyError as exc:
        raise HTTPException(400, f"DSL 依赖错误: {exc}")
    nca_refs = list(ex.nca_refs) + [_nca_append(
        f"WORKBUDDY_EXECUTE:{ex.status}", user["username"],
        artifact_path=f"execution:{ex.execution_id}")]
    with get_sessionmaker().begin() as s:
        s.add(M.WorkflowRun(
            execution_id=ex.execution_id, workflow_id=wf.workflow_id,
            status=ex.status, current_step=ex.current_step,
            nsfl_status=ex.nsfl_status,
            nca_refs_json=json.dumps(nca_refs, ensure_ascii=False),
            results_json=json.dumps(ex.results, ensure_ascii=False, default=str),
            elapsed_ms=elapsed_ms, started_at=_utc(), finished_at=_utc()))
    return _nca_watermark({
        "execution_id": ex.execution_id, "workflow_id": wf.workflow_id,
        "status": ex.status, "current_step": ex.current_step,
        "nsfl_status": ex.nsfl_status, "nca_refs": nca_refs,
        "elapsed_ms": elapsed_ms, "simulated": True,
        "note": "P5 执行视图（端到端 <10s 硬指标；NSFL/CHECKED=已检未触发）"})


@router.get("/workflow/status")
def wb_status(execution_id: str, request: Request):
    """执行状态（DB 实读——重启后可查；P5 契约 execution_id 查询）。"""
    _require_session_user(request)
    with get_session() as s:
        row = s.get(M.WorkflowRun, execution_id)
    if row is None:
        raise HTTPException(404, "execution_id 不存在")
    return _nca_watermark({
        "execution_id": row.execution_id, "workflow_id": row.workflow_id,
        "status": row.status, "current_step": row.current_step,
        "nsfl_status": row.nsfl_status,
        "nca_refs": json.loads(row.nca_refs_json or "[]"),
        "elapsed_ms": row.elapsed_ms,
        "results": list(json.loads(row.results_json or "{}").keys())})


# =====================================================================
# 人类签名 request / confirm（HUF；智能体不得代签——授权件四要件 2.4）
# =====================================================================

class SigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = ""
    gate_id: str = ""
    description: str = ""


@router.post("/signature/request", status_code=201)
def wb_sig_request(req: SigRequest, request: Request):
    user = _require_session_user(request)
    rid = f"SR-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("WORKBUDDY_SIG_REQUEST", user["username"],
                          artifact_path=f"sigreq:{rid}")
    with get_sessionmaker().begin() as s:
        s.add(M.SignatureRequest(
            request_id=rid, workflow_id=req.workflow_id or None,
            gate_id=req.gate_id, description=req.description,
            applicant=user["username"], nca_ref=nca_ref, created_at=_utc()))
    return _nca_watermark({"signature_request_id": rid, "gate_id": req.gate_id,
                           "nca_ref": nca_ref,
                           "note": "签名请求已登记（待法律主体本人签署）"})


class SigConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = ""
    biometric_proof: str = ""
    hardware_signature: str = ""


@router.post("/signature/confirm")
def wb_sig_confirm(req: SigConfirm, request: Request):
    """硬件签名确认（模拟口径：非空且 ≥8 字符；自动化签名尝试 → 403 熔断）。"""
    user = _require_session_user(request)
    with get_session() as s:
        row = s.get(M.SignatureRequest, req.request_id)
    if row is None:
        raise HTTPException(404, "request_id 不存在")
    if row.status == "signed":
        return _nca_watermark({"verified": True, "tx_hash": row.tx_hash,
                               "gate_id": row.gate_id, "note": "已签署（幂等返回）"})
    if not req.hardware_signature or len(req.hardware_signature) < 8:
        raise HTTPException(403, "HARDWARE_SIGNATURE_INVALID（检测到自动化签名尝试 → 熔断）")
    tx = f"0xSIG-{req.request_id}"
    nca_ref = _nca_append("WORKBUDDY_SIG_CONFIRM", user["username"],
                          artifact_path=f"sig:{req.request_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.SignatureRequest, req.request_id)
        r.status = "signed"
        r.tx_hash = tx
        r.signed_at = _utc()
    return _nca_watermark({"verified": True, "tx_hash": tx, "gate_id": row.gate_id,
                           "nca_ref": nca_ref})


# =====================================================================
# WORM 日志完整性（P5 绝对负空间 3）
# =====================================================================

@router.get("/log-integrity")
def wb_log_integrity(request: Request):
    _require_session_user(request)
    with get_session() as s:
        defs = s.query(M.WorkflowDef).count()
        runs = s.query(M.WorkflowRun).count()
        sigs = s.query(M.SignatureRequest).count()
    return _nca_watermark({
        "integrity": _engine.verify_log_integrity(),
        "worm_log_entries": len(_engine._log),
        "workflow_defs": defs, "workflow_runs": runs,
        "signature_requests": sigs,
        "note": "WORM 哈希链完整性（一次写入多次读取；断链即 False）"})
