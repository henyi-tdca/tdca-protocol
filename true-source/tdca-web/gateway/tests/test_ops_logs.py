# -*- coding: utf-8 -*-
"""乙案 P2 运维日志测试（/api/v1/ops/logs/*——L1SI150-OPS-STORAGE-P2-001）。

覆盖：未登录 401／viewer 403；POST 正例 201＋NCA；同日同值日 409（⛔ 不静默更新）；
V-1/V-2/V-3/V-4/V-5/V-6/V-8 各反例 400；GET 区间列表；today 红点（filled/streak/升级工单幂等）；
export CSV；另案小改两例（升级工单幂等键＝未填起算日 episode 级幂等／CSV 公式注入防护 CWE-1236）。
迁移可回退另由 alembic upgrade/downgrade 验证（回报项 2）。
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)
_PW = "Opslog-2026"
_TZ08 = timezone(timedelta(hours=8))
_SEQ = {"n": 0}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    with get_sessionmaker().begin() as s:
        s.query(M.OpsLog).delete()
        s.query(M.OpsTicket).filter(M.OpsTicket.title.like("运维日志连续%")).delete()
    yield
    api_v1._register_hits.clear()


def _auth(uname=None, role=None):
    if uname is None:
        _SEQ["n"] += 1
        uname = f"opslog{_SEQ['n']:03d}"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    if role:
        with get_sessionmaker().begin() as s:
            s.get(M.User, uname).role = role
    return {"Authorization": r.json()["data"]["token"]}


def _today() -> str:
    return datetime.now(_TZ08).date().isoformat()


def _sections(day: str, bf: bool = False, reason: str = ""):
    not_after = (datetime.fromisoformat(day) + timedelta(days=90)).date().isoformat()
    return {
        "A_基本信息": {
            "date": day, "duty_role": "值班运维+OP-001", "handover_role": "备份运维+OP-002",
            "checklist_done": {"pre_deploy": True, "daily": True, "weekly": False,
                               "per_batch": True},
            "backfill": {"is_backfill": bf, "reason": reason}},
        "B_技术运维": {
            "root_http_status": 200,
            "keypage_probe": [{"path": "/", "status": 200}, {"path": "/ops", "status": 401},
                              {"path": "/library", "status": 200},
                              {"path": "/docs", "status": 200},
                              {"path": "/api/v1/system/overview", "status": 200}],
            "cert_not_after": not_after, "cert_days_left": 90,
            "acme_selftest": "pass",
            "service_health": {"status": "ok", "abnormal_containers": "无"},
            "backup": {"name": "dist-bak", "sha256_16": "0" * 16,
                       "location": "运维端文件区"},
            "swap_today": {"done": False, "build_tree": "n/a", "commit": "n/a",
                           "smoke5": "n/a", "postcheck4": "n/a"},
            "tech_abnormal": False},
        "C_内容运维": {
            "ingest_batch": {"done": False, "batch_id": "无", "item_count": 0},
            "trail_seven_cols": "齐",
            "reject_list": {"hit_count": 0, "empty_list_issued": True},
            "content_probe": {"checked_count": 5, "abnormal": "无"},
            "bulletin": {"state": "无", "doc_id": "无", "authorized": False},
            "public_private_leak": {"state": "无", "location": "无", "handled": True}},
        "D_运营运维": {
            "daily_patrol": {"site_health": "正常", "public_face": "正常",
                             "notify_machine": "正常", "abnormal_log": "无"},
            "user_request_count": 0,
            "appeal_count": {"count": 0, "pair_opened": True},
            "assistant_to_human": {"count": 0, "forwarded": True}},
        "E_安全合规": {
            "three_maintain": {"gate_open_state": "正常", "robots_header": "在位",
                               "ops_401": "正常"},
            "credential_change": {"changed": False, "changed_at": "无"},
            "security_event": {"exists": False, "event_id": "无", "status": "无"},
            "redline_check": {"zero_external": True, "layering": True,
                              "no_semantic_ruling": True},
            "crv_count": {"handoff": 0, "report": 0, "witness": 0}},
        "F_异常与收尾": {
            "exceptions": [], "carry_over": [], "handover_next_day": [],
            "filled_by": "值班运维+OP-001", "filled_at": f"{day}T23:00:00+08:00"},
    }


def _post(day=None, headers=None, **sec_over):
    day = day or _today()
    sec = _sections(day)
    for path, val in sec_over.items():
        grp, key = path.split(".")
        sec[grp][key] = val
    return client.post("/api/v1/ops/logs", json={
        "duty_role": "值班运维", "duty_no": "OP-001", "handover": "备份运维+OP-002",
        "sections": sec}, headers=headers or _auth(role="operator"))


# ── 权限面 ──────────────────────────────────────────────
def test_unauthenticated_401_all():
    body = {"duty_role": "值班运维", "duty_no": "OP-001",
            "handover": "备份运维+OP-002", "sections": _sections(_today())}
    assert client.post("/api/v1/ops/logs", json=body).status_code == 401
    for p in ["", "/today", "/export"]:
        assert client.get(f"/api/v1/ops/logs{p}").status_code == 401


def test_viewer_403():
    h = _auth()
    assert _post(headers=h).status_code == 403
    assert client.get("/api/v1/ops/logs", headers=h).status_code == 403
    assert client.get("/api/v1/ops/logs/today", headers=h).status_code == 403


# ── 正例与幂等 ──────────────────────────────────────────
def test_create_201_and_dup_409():
    r = _post()
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    assert d["log_date"] == _today() and d["unclosed_count"] == 0
    assert _post().status_code == 409  # ⛔ 不静默更新
    with get_session() as s:
        assert s.query(M.OpsLog).count() == 1


def test_list_and_export():
    assert _post().status_code == 201
    h = _auth(role="operator")
    r = client.get(f"/api/v1/ops/logs?from={_today()}&to={_today()}", headers=h)
    assert r.status_code == 200 and r.json()["data"]["total"] == 1
    r = client.get("/api/v1/ops/logs/export", headers=h)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert "root_http_status" in r.text and _today() in r.text


# ── 红点与升级 ──────────────────────────────────────────
def test_today_filled_and_escalation_idempotent():
    h = _auth(role="operator")
    r = client.get("/api/v1/ops/logs/today", headers=h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["filled"] is False and d["missing_streak"] >= 2
    assert d["escalated_now"] is True                       # 首查即入 P7 工单池
    assert client.get("/api/v1/ops/logs/today", headers=h
                      ).json()["data"]["escalated_now"] is False  # 幂等
    with get_session() as s:
        t = s.query(M.OpsTicket).filter(M.OpsTicket.title.like("运维日志连续%")).all()
        assert len(t) == 1 and t[0].status == "INTAKE"
    assert _post().status_code == 201
    d = client.get("/api/v1/ops/logs/today", headers=h).json()["data"]
    assert d["filled"] is True and d["missing_streak"] == 0


# ── V-1~V-8 反例 ────────────────────────────────────────
def test_v1_required():
    r = _post(**{"B_技术运维.acme_selftest": ""})
    assert r.status_code == 400 and "校验项一" in r.text


def test_v2_credential_shape():
    r = _post(**{"B_技术运维.service_health":
                 {"status": "ok", "abnormal_containers": "password=hunter2secret"}})
    assert r.status_code == 400 and "校验项二" in r.text
    r = _post(**{"D_运营运维.daily_patrol":
                 {"site_health": "Bearer abcdef1234567890xyz", "public_face": "正常",
                  "notify_machine": "正常", "abnormal_log": "无"}})
    assert r.status_code == 400 and "校验项二" in r.text


def test_v3_unclosed_needs_next_step():
    ex = [{"id": "OPS-20261017-01", "found_at": "2026-10-17T10:00:00+08:00",
           "symptom": "探针异常", "impact": "无", "action": "重启",
           "actor_role": "值班运维", "closed": False, "verify_method": "无",
           "next_step": "", "deadline": ""}]
    assert _post(**{"F_异常与收尾.exceptions": ex}).status_code == 400
    ex[0]["next_step"] = "观察"; ex[0]["deadline"] = "2026-10-18T12:00:00+08:00"
    r = _post(**{"F_异常与收尾.exceptions": ex})
    assert r.status_code == 201 and r.json()["data"]["unclosed_count"] == 1


def test_v4_swap_done_selftest_na():
    assert _post(**{"B_技术运维.swap_today":
                    {"done": True, "build_tree": "ok", "commit": "abc", "smoke5": "ok",
                     "postcheck4": "ok"},
                    "B_技术运维.acme_selftest": "n/a"}).status_code == 400


def test_v5_bulletin_publish_requires_authorized():
    assert _post(**{"C_内容运维.bulletin":
                    {"state": "发布", "doc_id": "ANN-1", "authorized": False}
                    }).status_code == 400


def test_v6_cert_days_must_be_measured():
    assert _post(**{"B_技术运维.cert_days_left": 89}).status_code == 400


def test_v8_backfill_rule():
    yesterday = (datetime.now(_TZ08).date() - timedelta(days=1)).isoformat()
    assert _post(day=yesterday).status_code == 400      # 未标补记
    sec = _sections(yesterday, bf=True, reason="前日漏填，补记")
    r = client.post("/api/v1/ops/logs", json={
        "duty_role": "值班运维", "duty_no": "OP-001", "handover": "备份运维+OP-002",
        "sections": sec}, headers=_auth(role="operator"))
    assert r.status_code == 201, r.text                 # 合规补记入库
    with get_session() as s:
        row = s.get(M.OpsLog, (yesterday, "OP-001"))
        assert row.backfill == "true" and row.backfill_reason == "前日漏填，补记"
    # 补记亦守 409
    r = client.post("/api/v1/ops/logs", json={
        "duty_role": "值班运维", "duty_no": "OP-001", "handover": "备份运维+OP-002",
        "sections": sec}, headers=_auth(role="operator"))
    assert r.status_code == 409


# ── 另案小改（20261017 创始人「出」）：幂等键＝未填起算日 ──────────
def test_escalation_keyed_by_episode_start():
    """同一未填 episode 的 streak 逐日增长时起算日不变——只开一单，幂等不逐日新开；
    episode 被打断（起算日变化）后才开新单。"""
    from ops_logs_ops import _ensure_escalation
    user = {"username": "opslog-esc001"}
    d0 = datetime.now(_TZ08).date()
    start0 = d0 - timedelta(days=1)                       # streak=2 起算日
    assert _ensure_escalation(2, d0, user) is True        # episode 开单
    # 连续未填逐日增长：起算日同为 start0 ⟹ 幂等返回，不新开
    assert _ensure_escalation(3, d0 + timedelta(days=1), user) is False
    assert _ensure_escalation(4, d0 + timedelta(days=2), user) is False
    with get_session() as s:
        ts = s.query(M.OpsTicket).filter(M.OpsTicket.title.like("运维日志连续%")).all()
        assert len(ts) == 1                                 # 三访只一单
        assert ts[0].ticket_id == f"OPS-esc{start0.strftime('%Y%m%d')}"
        assert ts[0].status == "INTAKE"
    # 起算日变化（新 episode）⟹ 可开新单
    assert _ensure_escalation(2, d0 + timedelta(days=9), user) is True
    with get_session() as s:
        assert s.query(M.OpsTicket).filter(
            M.OpsTicket.title.like("运维日志连续%")).count() == 2


# ── 另案小改（20261017 创始人「出」）：CSV 公式注入防护 ──────────
def test_export_csv_formula_injection_guard():
    """CWE-1236：前导 = + - @ 的单元格导出时前置单引号中和；普通值原样。"""
    assert _post(**{"B_技术运维.tech_abnormal": "=cmd|'/c calc'!"}).status_code == 201
    h = _auth(role="operator")
    r = client.get("/api/v1/ops/logs/export", headers=h)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert "'=cmd|'/c calc'!" in r.text                    # 已前置单引号
    assert "\n=cmd" not in r.text                          # 无前导裸公式格
    assert "tech_abnormal" in r.text and "pass" in r.text   # 表头与正常值原样
