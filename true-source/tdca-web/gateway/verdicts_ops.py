# -*- coding: utf-8 -*-
"""L1SI218-ACCTABLE-001（乙路·账不动）：验收结论三支端点。

口径（裁定 TDCA-RULING-L1SI218-ACCTABLE-001）：
  - 公示端点 GET /api/v1/acceptance/verdicts：匿名可读，只返公示四字段
    （verdict/decided_at/subject_ref/evidence_nca_id）——查公开视图
    acceptance_verdicts_public，私域五字段由视图层即不可见（⛔前端隐藏代隔离）；
  - 私域端点 GET /api/v1/ops/acceptance-verdicts：会话（照 /ops 惯例）或机面 O-1，
    查运维视图 acceptance_verdicts_ops（全列）；
  - 登记口 POST /api/v1/acceptance/verdicts/register：「谁判谁登」——只给智库侧
    （或受权智能体），guard = 环境变量 TDCA_VERDICT_REG_KEY（fail-closed：未设即拒），
    请求头 X-TDCA-Verdict-Reg-Key 匹配方可登记；⛔开放站点管理面手填；
    decided_at 系统取（⛔手填）；evidence_nca_id 须在 nca_chain 存在（可回链判据）；
  - 首批数据：台账无验收结论字段可派生（-414 S-AC1），空表为常态，如实标；
  - C-3 交付验收单链归入 subject_type=batch_construction（⛔另建套）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402

_REG_KEY_ENV = "TDCA_VERDICT_REG_KEY"
_REG_HEADER = "x-tdca-verdict-reg-key"

_PUBLIC_COLS = ("subject_type", "subject_ref", "verdict", "decided_at", "evidence_nca_id")

SUBJECT_TYPES = ("institution_effective", "doc_ingest", "site_function",
                 "batch_construction", "agent_network")
VERDICTS = ("passed", "conditional", "failed")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 公示端点（匿名·公开视图四字段） ─────────────────────────────────────────
public_router = APIRouter(prefix="/api/v1/acceptance", tags=["acceptance-verdicts"])


@public_router.get("/verdicts")
def verdicts_public():
    """公示结论面（甲型全共享：人面页面/机取接口同源同数，⛔只给壳）。"""
    with get_session() as s:
        rows = s.execute(M.AcceptanceVerdict.__table__.select().with_only_columns(
            *(getattr(M.AcceptanceVerdict, c) for c in _PUBLIC_COLS)
        ).order_by(M.AcceptanceVerdict.decided_at.desc())).all()
    return {"count": len(rows),
            "verdicts": [dict(zip(_PUBLIC_COLS, r)) for r in rows],
            "note": "验收结论公示面（五字段·含存证号可回溯核证件）；作业/处置/留痕在私域面 /ops/acceptance-records（登录或O-1）"}


# ── 登记口（只给智库侧/受权智能体·fail-closed key guard） ──────────────────
class VerdictRegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: str
    subject_type: str
    subject_ref: str
    evidence_nca_id: str
    ops_process: str | None = None
    ops_actions: str | None = None
    ops_trace: str | None = None
    credential_ref: str | None = None
    internal_ref: str | None = None


@public_router.post("/verdicts/register", status_code=201)
def verdict_register(body: VerdictRegisterIn, request: Request):
    key = os.environ.get(_REG_KEY_ENV, "").strip()
    presented = request.headers.get(_REG_HEADER, "").strip()
    if not key or presented != key:
        raise HTTPException(403, "登记口不开放：须智库侧登记密钥（谁判谁登，⛔站点管理面手填）")
    if body.verdict not in VERDICTS:
        raise HTTPException(422, f"verdict 须为 {VERDICTS} 之一")
    if body.subject_type not in SUBJECT_TYPES:
        raise HTTPException(422, f"subject_type 须为 {SUBJECT_TYPES} 之一")
    with get_session() as s:
        if s.get(M.NcaChain, body.evidence_nca_id) is None:
            raise HTTPException(422, "evidence_nca_id 在 NCA 台账不存在（无存证不登记）")
        row = M.AcceptanceVerdict(
            verdict=body.verdict, decided_at=_utcnow(),  # 系统取，⛔手填
            subject_type=body.subject_type, subject_ref=body.subject_ref,
            evidence_nca_id=body.evidence_nca_id,
            ops_process=body.ops_process, ops_actions=body.ops_actions,
            ops_trace=body.ops_trace, credential_ref=body.credential_ref,
            internal_ref=body.internal_ref,
            data_provenance="real", created_at=_utcnow())
        s.add(row)
        s.commit()
    return {"status": "registered", "decided_at": row.decided_at}


# ── 私域端点（会话或机面 O-1·运维视图全列） ─────────────────────────────────
# 丙案授权闸（ops_auth_gate）在站机已部署、仓 main 待并；未并前机面 fail-closed 拒，
# 人类会话照原路（_require_session_user），并后 O-1 自动生效。
try:
    from ops_auth_gate import require_ops_caller as _require_ops_caller  # noqa: E402
except ImportError:  # pragma: no cover - 闸未合并前的 fail-closed 兜底
    from api_v1 import _require_session_user as _session_user  # noqa: E402

    def _require_ops_caller(request: Request) -> dict:
        auth_id = request.headers.get("x-tdca-ops-auth", "").strip()
        if auth_id:
            raise HTTPException(403, "机面 O-1 授权闸（丙案）仓内未合并前，机面一律拒（fail-closed）")
        return _session_user(request)

ops_router = APIRouter(prefix="/api/v1/ops/acceptance-verdicts",
                       tags=["ops-acceptance-verdicts"])


@ops_router.get("")
def verdicts_ops(request: Request):
    """私域全量（含作业五字段）：人类会话照原路；机面 O-1 只读放行（闸内校验）。"""
    _require_ops_caller(request)
    with get_session() as s:
        rows = s.execute(M.AcceptanceVerdict.__table__.select().order_by(
            M.AcceptanceVerdict.decided_at.desc())).all()
        cols = M.AcceptanceVerdict.__table__.columns.keys()
    return {"count": len(rows),
            "verdicts": [dict(zip(cols, r)) for r in rows],
            "note": "私域运维面（含作业/处置/留痕）；公示结论面 /api/v1/acceptance/verdicts（匿名四字段）"}
