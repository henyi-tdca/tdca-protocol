# -*- coding: utf-8 -*-
"""
P5 CI 手动触发入口（A-16）：/api/v1/ci/* —— 两段走之第一段（手动先行）。

口径（组三 P5 要件 3）：在册机验 suite＝lake build ＋ core-go 测试 ＋ 网关回归；
自动门禁闭环待官方 CI 白名单（期一后半再补，⛔ 不自启门禁、⛔ 不阻断期一）。
绿灯徽章：GET /badge 供 P3 页面（/formal）展示最近一回结果。
suite 命令经环境变量 CI_SUITE_COMMANDS（JSON）可覆盖，默认指向仓内真源树；
执行为 subprocess 同步跑（手动入口，非并发队列）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/ci", tags=["ci"])

_ROOT = Path(__file__).resolve().parents[3]          # 仓根
_GATEWAY_DIR = Path(__file__).resolve().parent
_LEAN_DIR = _ROOT / "core-go" / "docs" / "formal-proofs" / "lean-tdca"
_CORE_GO = _ROOT / "core-go"

_DEFAULT_SUITES: dict = {
    "lake-build": {"cmd": ["lake", "build"], "cwd": str(_LEAN_DIR), "timeout": 1800},
    "core-go-tests": {"cmd": ["go", "test", "./..."], "cwd": str(_CORE_GO), "timeout": 900},
    "gateway-regression": {"cmd": [sys.executable, "-m", "pytest", "tests", "-q"],
                           "cwd": str(_GATEWAY_DIR), "timeout": 900},
}
_TAIL = 2000  # 输出尾部留痕上限


def _suites() -> dict:
    raw = os.environ.get("CI_SUITE_COMMANDS", "")
    if raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(500, "CI_SUITE_COMMANDS 非合法 JSON")
    return _DEFAULT_SUITES


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suites: list[str] = []          # 空 = 全部
    timeout_override: int = 0       # 0 = 用 suite 默认（测试可缩短）


@router.post("/run", status_code=201)
def ci_run(req: RunRequest, request: Request):
    """手动触发机验（operator/founder；逐 suite 落 ci_runs，最后一笔状态入徽章）。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可触发机验")
    suites = _suites()
    names = req.suites or list(suites.keys())
    for n in names:
        if n not in suites:
            raise HTTPException(400, f"未知 suite：{n}（在册：{sorted(suites)}）")
    results = []
    for name in names:
        spec = suites[name]
        timeout = req.timeout_override or int(spec.get("timeout", 600))
        run_id = f"CI-{uuid.uuid4().hex[:10]}"
        started = _utc()
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(spec["cmd"], cwd=spec.get("cwd") or str(_GATEWAY_DIR),
                                  capture_output=True, text=True, timeout=timeout)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            detail = (proc.stdout + proc.stderr)[-_TAIL:] or "(无输出)"
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            status, detail, exit_code = "ERROR", f"TIMEOUT>{timeout}s", None
        except OSError as exc:
            status, detail, exit_code = "ERROR", f"LAUNCH_FAIL:{exc}", None
        elapsed = round(time.perf_counter() - t0, 1)
        with get_sessionmaker().begin() as s:
            s.add(M.CiRun(run_id=run_id, suite=name, status=status,
                          exit_code=exit_code, detail=detail,
                          operator=user["username"],
                          started_at=started, finished_at=_utc()))
        results.append({"suite": name, "run_id": run_id, "status": status,
                        "exit_code": exit_code, "elapsed_s": elapsed})
    return _nca_watermark({"results": results,
                           "note": "手动机验入口（两段走·第一段；自动门禁待官方 CI 白名单）"})


@router.get("/runs")
def ci_runs(request: Request, suite: str = "", limit: int = 20):
    _require_session_user(request)
    with get_session() as s:
        q = s.query(M.CiRun).order_by(M.CiRun.started_at.desc())
        if suite:
            q = q.filter_by(suite=suite)
        rows = q.limit(min(limit, 100)).all()
    return _nca_watermark({"count": len(rows), "runs": [
        {"run_id": r.run_id, "suite": r.suite, "status": r.status,
         "exit_code": r.exit_code, "operator": r.operator,
         "started_at": r.started_at, "finished_at": r.finished_at} for r in rows]})


@router.get("/badge")
def ci_badge(request: Request, suite: str = "gateway-regression"):
    """绿灯徽章（P3 页面展示最近一回机验状态；无记录 → none）。

    匿名可读（L1SI175-B1 S1-3）：仅 suite/status/run_id/finished_at/note 一行状态，
    ⛔ 不含日志详情；触发（POST /run）与历史（GET /runs）仍须登录。"""

    with get_session() as s:
        row = s.query(M.CiRun).filter_by(suite=suite) \
               .order_by(M.CiRun.started_at.desc()).first()
    if row is None:
        return _nca_watermark({"suite": suite, "status": "none",
                               "note": "尚无机验记录（手动入口待首次触发）"})
    return _nca_watermark({"suite": suite, "status": row.status,
                           "run_id": row.run_id, "finished_at": row.finished_at,
                           "note": "绿灯徽章＝最近一回手动机验结果（非自动门禁）"})
