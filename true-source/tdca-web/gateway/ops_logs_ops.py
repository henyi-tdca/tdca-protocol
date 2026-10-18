# -*- coding: utf-8 -*-
"""
乙案 P2 运维日志（L1SI150-OPS-STORAGE-P2-001）：/api/v1/ops/logs/* —— 每日运维日志表单化。

- 建表迁移 0013（ops_logs）；六组 sections JSON 键名与 TDCA-TPL-OPS-LOG-001-MACHINE 1:1；
- 四端点：POST 写（V-1~V-8 服务端全量校验）／GET 区间列表／GET today（红点+连续未填升级）／GET export（CSV）；
- 一人一日一行（log_date+duty_no 主键）；同日同值日已存在 ⟹ 409（⛔ 不做静默更新，更正另令）；
- 连续 2 日未填 ⟹ 写入既有 P7 工单池（INTAKE，operator/founder 必查面）⛔ 不新建通知通道；
  幂等键＝未填起算日（另案小改①，20261017）：同一未填 episode 只开一单，streak 逐日增长不再逐日新开；
- ⛔ 不建 ops_files 表（防双源漂移）；⛔ 表单无口令/令牌/密钥字段；凭据形内容 V-2 双扫拒绝；
- 归档：不删行（delete_allowed=false），月区间读取 + CSV 导出（周汇总/月报）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/ops/logs", tags=["ops-logs"])

_TZ08 = timezone(timedelta(hours=8))  # +08 自然日（模板口径）
_GROUPS = ("A_基本信息", "B_技术运维", "C_内容运维", "D_运营运维", "E_安全合规", "F_异常与收尾")
_NA = ("无", "n/a")

# ── V-2：凭据形双扫（正则形态 + 关键词形态；中文类别词不扫——「口令门」等运维常词会误伤）──
_CRED_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|"
               r"authorization|private[_-]?key|client[_-]?secret)\s*[:=]\s*[^\s，。；]+"),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

# 必填键镜像（照 TDCA-TPL-OPS-LOG-001-MACHINE groups；map 字段列子键）
_REQUIRED = {
    "A_基本信息": ("date", "duty_role", "handover_role", "checklist_done"),
    "B_技术运维": ("root_http_status", "keypage_probe", "cert_not_after", "cert_days_left",
                "acme_selftest", "service_health", "backup", "swap_today", "tech_abnormal"),
    "C_内容运维": ("ingest_batch", "trail_seven_cols", "reject_list", "content_probe",
                "bulletin", "public_private_leak"),
    "D_运营运维": ("daily_patrol", "user_request_count", "appeal_count", "assistant_to_human"),
    "E_安全合规": ("three_maintain", "credential_change", "security_event", "redline_check",
                "crv_count"),
    "F_异常与收尾": ("exceptions", "carry_over", "handover_next_day", "filled_by", "filled_at"),
}


def _today08() -> date:
    return datetime.now(_TZ08).date()


# ── CSV 公式注入防护（CWE-1236：单元格首字符为 = + - @ / 制表符 / 回车时，
#    Excel 类表格软件会当公式执行——导出统一前置单引号中和，肉眼可核、可逆）──
_CSV_FORMULA_LEAD = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(v):
    if isinstance(v, str) and v[:1] in _CSV_FORMULA_LEAD:
        return "'" + v
    return v


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def _filled(v) -> bool:
    """V-1：必填不得为空；「无」/「n/a」为合规填充值。"""
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    return True  # 数值/bool/非空容器


def _validate_log(log_date: date, sections: dict, now08: datetime) -> None:
    """V-1~V-8 服务端全量校验（⛔ 不只靠前端的同源 schema）。"""
    # V-1 必填齐
    for g, keys in _REQUIRED.items():
        grp = sections.get(g)
        if not isinstance(grp, dict):
            raise HTTPException(400, f"校验项一（必填齐）：缺组 {g}")
        for k in keys:
            if not _filled(grp.get(k)):
                raise HTTPException(400, f"校验项一（必填）：{g}.{k} 不得为空（无则填「无」，不适用填 n/a）")
    a, b, c, e, f = (sections[g] for g in
                     ("A_基本信息", "B_技术运维", "C_内容运维", "E_安全合规", "F_异常与收尾"))

    # V-7：+08 自然日且不晚于填写日
    if log_date > now08.date():
        raise HTTPException(400, "校验项七（日期）：log_date 不得晚于今日（+08）")

    # V-8：补记口径
    backfill = a.get("backfill") or {}
    is_bf = bool(backfill.get("is_backfill"))
    if log_date < now08.date() and not is_bf:
        raise HTTPException(400, "校验项八（补记）：非当日填写须标 backfill.is_backfill=true 并写 reason")
    if is_bf and not str(backfill.get("reason") or "").strip():
        raise HTTPException(400, "校验项八（补记）：补记须写 reason")

    # V-2：凭据形双扫（六组全量文本）
    for s in _walk_strings(sections):
        for pat in _CRED_PATTERNS:
            if pat.search(s):
                raise HTTPException(400, "校验项二（凭据形）：内容含凭据形串（⛔ 口令/令牌/密钥值不入日志）")

    # V-3：异常三段齐；未闭合须 next_step+deadline
    for ex in f.get("exceptions") or []:
        if not (_filled(ex.get("found_at")) and _filled(ex.get("action"))):
            raise HTTPException(400, "校验项三（异常三段）：异常项须含 发现/处置 段")
        if ex.get("closed") is True:
            continue
        if not (_filled(ex.get("next_step")) and _filled(ex.get("deadline"))):
            raise HTTPException(400, "校验项三（异常三段）：未闭合异常须填 下一步+时限")

    # V-4：acme_selftest 与 swap_today.done 互斥
    if b.get("swap_today", {}).get("done") is True and b.get("acme_selftest") == "n/a":
        raise HTTPException(400, "校验项四（互斥）：当日有换发则 acme_selftest 不得为 n/a")

    # V-5：bulletin.state=发布 ⟹ authorized=true
    if c.get("bulletin", {}).get("state") == "发布" and \
            c.get("bulletin", {}).get("authorized") is not True:
        raise HTTPException(400, "校验项五（公告授权）：公告 state=发布 时 authorized 必须为 true")

    # V-6：cert_days_left 为实测（与 cert_not_after − log_date 一致，容差 0 天）
    try:
        not_after = date.fromisoformat(str(b["cert_not_after"]))
        days_left = int(b["cert_days_left"])
    except (ValueError, TypeError):
        raise HTTPException(400, "校验项六（证书实测）：cert_not_after/cert_days_left 格式非法")
    if (not_after - log_date).days != days_left:
        raise HTTPException(400, "校验项六（证书实测）：cert_days_left 须为实测值（= cert_not_after − log_date）")

    # E 组凭据变更口径：⛔ 记值（凭据形双扫已覆盖；此处再守 changed 时 changed_at 必填）
    if e.get("credential_change", {}).get("changed") is True and \
            not _filled(e["credential_change"].get("changed_at")):
        raise HTTPException(400, "E.credential_change：changed=true 须填 changed_at（⛔ 记值）")


def _require_ops_admin(request: Request) -> dict:
    """运维门内：会话（401 fail-closed）＋ operator/founder（403）——照 /api/v1/ops/* 既有惯例。"""
    user = _require_session_user(request)
    if user.get("role") not in ("operator", "founder"):
        raise HTTPException(403, "仅 operator / founder 可访问运维日志")
    return user


def _row_to_dict(r: M.OpsLog) -> dict:
    return {
        "log_date": r.log_date, "duty_no": r.duty_no, "duty_role": r.duty_role,
        "handover": r.handover, "sections": json.loads(r.sections),
        "exceptions_count": r.exceptions_count, "unclosed_count": r.unclosed_count,
        "backfill": r.backfill == "true", "backfill_reason": r.backfill_reason,
        "filled_by": r.filled_by, "filled_at": r.filled_at,
    }


class LogIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    duty_role: str
    duty_no: str
    handover: str
    sections: dict


@router.post("", status_code=201)
def create_log(req: LogIn, request: Request):
    """提交当日/补记日志（V-1~V-8 服务端校验；同日同值日已存在 ⟹ 409）。"""
    user = _require_ops_admin(request)
    now08 = datetime.now(_TZ08)
    try:
        log_date = date.fromisoformat(str(req.sections.get("A_基本信息", {}).get("date", "")))
    except ValueError:
        raise HTTPException(400, "A_基本信息.date 须为 YYYY-MM-DD")
    sections = req.sections

    # 顶层与 A 组一致性（防拼装漂移）
    a = sections.get("A_基本信息", {})
    if str(a.get("date", "")) != log_date.isoformat():
        raise HTTPException(400, "A_基本信息.date 与顶层日期不一致")
    if a.get("duty_role") != f"{req.duty_role}+{req.duty_no}":
        raise HTTPException(400, "A_基本信息.duty_role 须为「角色+工号」且与顶层一致")
    if a.get("handover_role") != req.handover:
        raise HTTPException(400, "A_基本信息.handover_role 与顶层 handover 不一致")

    _validate_log(log_date, sections, now08)

    f = sections["F_异常与收尾"]
    exceptions = f.get("exceptions") or []
    unclosed = sum(1 for ex in exceptions if ex.get("closed") is not True)
    backfill = a.get("backfill") or {}
    is_bf = bool(backfill.get("is_backfill"))

    with get_session() as s:
        if s.get(M.OpsLog, (log_date.isoformat(), req.duty_no.strip())) is not None:
            raise HTTPException(409, "同日同值日日志已存在（更正走另令；⛔ 不做静默更新）")

    nca_ref = _nca_append("OPS_LOG_FILLED", user["username"],
                          artifact_path=f"ops-logs:{log_date.isoformat()}:{req.duty_no.strip()}")
    row = M.OpsLog(
        log_date=log_date.isoformat(), duty_no=req.duty_no.strip(),
        duty_role=req.duty_role.strip(), handover=req.handover.strip(),
        sections=json.dumps(sections, ensure_ascii=False),
        exceptions_count=len(exceptions), unclosed_count=unclosed,
        backfill="true" if is_bf else "false",
        backfill_reason=(str(backfill.get("reason")).strip() or None) if is_bf else None,
        filled_by=str(f.get("filled_by") or user["username"]),
        filled_at=now08.isoformat(), data_provenance="real")
    with get_sessionmaker().begin() as s:
        s.add(row)
        s.flush()
        out = {"log_date": row.log_date, "duty_no": row.duty_no,
               "exceptions_count": row.exceptions_count,
               "unclosed_count": row.unclosed_count}
    return _nca_watermark({**out, "nca_ref": nca_ref,
                           "note": "日志已入库（NCA 存证；保留 12 个月不删行）"})


@router.get("")
def list_logs(request: Request,
              from_: str = Query("", alias="from"), to: str = Query(""),
              duty_no: str = "", page: int = 1, page_size: int = 31):
    """区间列表（分页；含 sections 明细；仅运维门内）。"""
    _require_ops_admin(request)
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    with get_session() as s:
        q = s.query(M.OpsLog).order_by(M.OpsLog.log_date.desc(), M.OpsLog.duty_no)
        if from_:
            q = q.filter(M.OpsLog.log_date >= from_)
        if to:
            q = q.filter(M.OpsLog.log_date <= to)
        if duty_no:
            q = q.filter(M.OpsLog.duty_no == duty_no)
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return _nca_watermark({"total": total, "page": page, "page_size": page_size,
                           "logs": [_row_to_dict(r) for r in rows]})


def _missing_streak(today: date) -> int:
    """自今日往前连续未填天数（遇已填即停；上限 31）。"""
    with get_session() as s:
        filled_dates = {r.log_date for r in s.query(M.OpsLog.log_date).distinct()}
    streak = 0
    for i in range(0, 31):
        d = today - timedelta(days=i)
        if d.isoformat() in filled_dates:
            break
        streak += 1
    return streak


def _ensure_escalation(streak: int, today: date, user: dict) -> bool:
    """连续≥2 日未填 ⟹ 写 P7 工单池。幂等键＝未填起算日（episode 起点＝上次已填日次日）：
    同一 episode 的 streak 逐日增长时起算日不变，只开一单；episode 被打断后重新起算才开新单。
    返回是否本次新建。"""
    if streak < 2:
        return False
    start = today - timedelta(days=streak - 1)
    tid = f"OPS-esc{start.strftime('%Y%m%d')}"
    title = f"运维日志连续 {streak} 日未填（{start.isoformat()} 起）——请值班人补记并说明"
    with get_session() as s:
        if s.get(M.OpsTicket, tid) is not None:
            # 同 episode 已有单：未结 ⟹ 幂等返回不重复写；已结（RELEASED）而再升级 ⟹ 后缀顺延，避免主键冲突
            if s.query(M.OpsTicket).filter_by(ticket_id=tid).filter(
                    M.OpsTicket.status != "RELEASED").first():
                return False
            seq = s.query(M.OpsTicket).filter(
                M.OpsTicket.ticket_id.like(f"{tid}-r%")).count() + 1
            tid = f"{tid}-r{seq}"
    nca_ref = _nca_append("OPS_LOG_ESCALATION", user["username"],
                          artifact_path=f"ops-logs:escalation:{start.isoformat()}")
    with get_sessionmaker().begin() as s:
        s.add(M.OpsTicket(
            ticket_id=tid,
            title=title,
            description="运维日志表单化红点升级：连续未填≥2 日，自动入 P7 工单池（⛔ 非静默）",
            status="INTAKE", nca_ref=nca_ref, created_at=_utc(), updated_at=_utc()))
    return True


@router.get("/today")
def today_status(request: Request):
    """红点用：{filled, date, missing_streak, escalation}（轻量、无敏感明细）。"""
    user = _require_ops_admin(request)
    today = _today08()
    with get_session() as s:
        filled = s.query(M.OpsLog).filter_by(log_date=today.isoformat()).count() > 0
    streak = 0 if filled else _missing_streak(today)
    escalated = _ensure_escalation(streak, today, user)
    return _nca_watermark({"date": today.isoformat(), "filled": filled,
                           "missing_streak": streak, "escalated_now": escalated,
                           "note": "streak≥2 即入 P7 工单池（operator/founder 必查面）"})


@router.get("/export")
def export_logs(request: Request,
                from_: str = Query("", alias="from"), to: str = Query(""),
                duty_no: str = ""):
    """导出 CSV（区间；供周汇总/月报；⛔ 不含凭据值——入库已过 V-2；
    CWE-1236 公式注入防护：前导 = + - @ 等单元格经 _csv_safe 前置单引号）。"""
    _require_ops_admin(request)
    with get_session() as s:
        q = s.query(M.OpsLog).order_by(M.OpsLog.log_date, M.OpsLog.duty_no)
        if from_:
            q = q.filter(M.OpsLog.log_date >= from_)
        if to:
            q = q.filter(M.OpsLog.log_date <= to)
        if duty_no:
            q = q.filter(M.OpsLog.duty_no == duty_no)
        rows = q.all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["log_date", "duty_role", "duty_no", "handover", "exceptions_count",
                "unclosed_count", "backfill", "backfill_reason", "filled_by", "filled_at",
                "root_http_status", "acme_selftest", "tech_abnormal", "trail_seven_cols",
                "sections_json"])
    for r in rows:
        sec = json.loads(r.sections)
        b = sec.get("B_技术运维", {})
        c = sec.get("C_内容运维", {})
        w.writerow([_csv_safe(v) for v in (
            r.log_date, r.duty_role, r.duty_no, r.handover, r.exceptions_count,
            r.unclosed_count, r.backfill, r.backfill_reason or "",
            r.filled_by, r.filled_at,
            b.get("root_http_status", ""), b.get("acme_selftest", ""),
            b.get("tech_abnormal", ""), c.get("trail_seven_cols", ""),
            json.dumps(sec, ensure_ascii=False))])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             f"attachment; filename=ops_logs_{from_ or 'all'}_{to or 'all'}.csv"})
