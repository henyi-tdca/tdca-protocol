"""
TDCA 站点 API 路由（v3 · 期 1 内部真跑 · SQLite 实装）
======================================================
挂载方式（gateway app.py，compose override 注入）：
    sys.path.insert(0, "/app/tdca-site/gateway")
    from tdca_site_routes import router as site_router
    app.include_router(site_router, prefix="/api/site")

设计依据：Web 2.5 三体可视化中心 · 合规前置三阶 · 双通道鉴权
硬约束：
  ⛔ 凭据值不入件/日志；token 只存哈希
  ⛔ 人类会话与智能体令牌互不通用（双通道中间件）
  ⛔ 计量/积分只记智能体通道
  ⛔ 内部替代件一律模拟态，不得冒充真实外部系统
接缝说明（期 1）：
  · 写端点（POST）经 gateway B-4 中间件：须 TDCA-SES 会话或 TDCA-CRT 令牌
    （与 M3 鉴权一致）；公网期是否豁免缔约写入口，另案裁定
  · require_reviewer 期 1 取 x-tdca-reviewer 头（B-4 已挡未持凭证者），加固另案
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from nsfl_config import NsflConfigError, forbidden_tokens, load_nsfl_config

router = APIRouter()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:////data/tdca.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "/", 1) if DATABASE_URL.startswith("sqlite:///") else "/data/tdca.db"

# ────────────────────────────────────────────────────────────────────────────
# 基础件
# ────────────────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ════════════════════════════════════════════════════════════════════════════
# 期 1 最小访问控制：全 API 口令门（fail-closed）
# ════════════════════════════════════════════════════════════════════════════
GATE_KEY_ENV = "TDCA_SITE_GATE_KEY"


def gate_key_configured() -> bool:
    return bool(os.environ.get(GATE_KEY_ENV))


def check_gate(x_tdca_site_gate: str | None = Header(default=None)):
    expected = os.environ.get(GATE_KEY_ENV)
    if not expected or x_tdca_site_gate != expected:
        raise HTTPException(401, "gate required")
    return True


def startup_self_check() -> list[str]:
    """启动自检：非空则拒服（接入时于 app startup 调用）。"""
    problems: list[str] = []
    if not gate_key_configured():
        problems.append(f"{GATE_KEY_ENV} 未配置（口令门 fail-closed：拒服）")
    if _NSFL_LOAD_ERROR:
        problems.append(f"负空间清单未载入（fail-closed）：{_NSFL_LOAD_ERROR}")
    try:
        conn = get_db()
        conn.execute("SELECT 1 FROM join_requests LIMIT 0")
        conn.close()
    except sqlite3.Error as e:
        problems.append(f"数据库不可达：{type(e).__name__}")
    return problems


# ════════════════════════════════════════════════════════════════════════════
# 负空间准入（fail-closed，清单同源载入 config/nsfl.yaml）
# ════════════════════════════════════════════════════════════════════════════
try:
    _NSFL_CFG = load_nsfl_config()
    NEGATIVE_PATTERNS: list[str] = forbidden_tokens(_NSFL_CFG)
    _NSFL_LOAD_ERROR: str | None = None
except NsflConfigError as e:
    _NSFL_CFG = None
    NEGATIVE_PATTERNS = []
    _NSFL_LOAD_ERROR = str(e)


def nsfl_scan(payload: dict) -> tuple[str, list[str]]:
    """行粒度扫描：命中 forbidden 且同行无豁免前缀词才触负。
    fail-closed：清单未载入一律 blocked 待审。"""
    if not NEGATIVE_PATTERNS:
        return ("blocked", ["<negative-list-unloaded>"])
    text = json.dumps(payload, ensure_ascii=False)
    flags = 0 if (_NSFL_CFG or {}).get("case_sensitive", True) else re.IGNORECASE
    exempts = (_NSFL_CFG or {}).get("negation_exempt", [])
    hits: list[str] = []
    for line in text.splitlines():
        for token in NEGATIVE_PATTERNS:
            if re.search(re.escape(token), line, flags):
                if any(re.search(re.escape(ex), line, flags) for ex in exempts):
                    continue
                hits.append(token)
    return ("blocked", hits) if hits else ("pass", [])


def check_general_rule(payload: dict) -> tuple[bool, str | None]:
    """总纲条 NSFL-C-1 独立校验位（on_miss=block）：准入/沙盒/转正三阶各验。
    词面落实：载荷须含 required_declaration 声明词，缺即拦。"""
    if _NSFL_CFG is None:
        return False, "nsfl-c1-unloaded"
    text = json.dumps(payload, ensure_ascii=False)
    required = _NSFL_CFG.get("required_declaration") or []
    if required and not any(r in text for r in required):
        return False, "nsfl-c1-missing-declaration"
    return True, None


def _history_append(history: list, to_status: str, by: str, note: str | None) -> str:
    history.append({"at": now_iso(), "from": history[-1]["to"] if history else None,
                    "to": to_status, "by": by, "note": note})
    return json.dumps(history, ensure_ascii=False)


# ════════════════════════════════════════════════════════════════════════════
# 双通道中间件
# ════════════════════════════════════════════════════════════════════════════
AGENT_TOKEN_HEADER = "x-tdca-agent-token"


def get_channel(
    x_tdca_channel: str = Header(default="human"),
    x_tdca_agent_token: str | None = Header(default=None),
) -> tuple[str, str | None]:
    if x_tdca_agent_token:
        return "agent", x_tdca_agent_token
    if x_tdca_channel not in ("human", "agent"):
        raise HTTPException(400, "unknown channel")
    return "human", None


def require_agent_card(token: str | None) -> sqlite3.Row:
    if not token:
        raise HTTPException(401, "agent token required")
    conn = get_db()
    card = conn.execute(
        "SELECT * FROM agent_cards WHERE card_token_hash = ? AND revoked_at IS NULL",
        (token_hash(token),)).fetchone()
    conn.close()
    if card is None:
        raise HTTPException(401, "invalid or revoked agent token")
    return card


def require_reviewer(x_tdca_reviewer: str | None = Header(default=None)) -> str:
    """期 1：B-4 中间件已挡未持凭证者，此处取审核人标识留痕；加固另案。"""
    if not x_tdca_reviewer:
        raise HTTPException(401, "reviewer identity required")
    return x_tdca_reviewer


# ════════════════════════════════════════════════════════════════════════════
# 1) 缔约申请（双通道共用入口，各走各的鉴权）
# ════════════════════════════════════════════════════════════════════════════
class JoinRequest(BaseModel):
    applicant_kind: str = Field(pattern="^(human|agent|org)$")
    display_name: str = Field(min_length=1, max_length=120)
    contact: str | None = Field(default=None, max_length=200)
    agent_card: dict | None = None
    payload: dict = Field(default_factory=dict)


@router.post("/join", status_code=201, dependencies=[Depends(check_gate)])
def submit_join(body: JoinRequest, request: Request,
                channel_meta: tuple = Depends(get_channel)):
    channel, agent_token = channel_meta

    if channel == "agent":
        if not body.agent_card:
            raise HTTPException(401, "agent channel requires valid agent_card")

    scan_result, hits = nsfl_scan(body.model_dump())
    c1_ok, c1_why = check_general_rule(body.model_dump())
    status = "pending" if (scan_result == "pass" and c1_ok) else "nsfl_rejected"
    if not c1_ok and c1_why not in hits:
        hits.append(f"<c1:{c1_why}>")

    public_token = secrets.token_urlsafe(24)
    conn = get_db()
    conn.execute(
        "INSERT INTO join_requests (public_token_hash, channel, applicant_kind,"
        " display_name, contact, agent_card, payload, nsfl_scan_at, nsfl_result,"
        " nsfl_hits, nca_anchor, status, status_history) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (token_hash(public_token), channel, body.applicant_kind, body.display_name,
         body.contact, json.dumps(body.agent_card, ensure_ascii=False),
         json.dumps(body.payload, ensure_ascii=False), now_iso(), scan_result,
         json.dumps(hits, ensure_ascii=False), "nca-anchor:simulated", status,
         _history_append([], status, "system", None)))
    conn.commit()
    conn.close()
    return {"ok": True, "status": status, "public_token": public_token,
            "nsfl": {"result": scan_result, "hits": hits},
            "data_nature": "simulated"}


@router.get("/join/status", dependencies=[Depends(check_gate)])
def join_status(token: str):
    conn = get_db()
    row = conn.execute(
        "SELECT status, status_history FROM join_requests WHERE public_token_hash = ?",
        (token_hash(token),)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "not found")
    return {"status": row["status"], "history": json.loads(row["status_history"]),
            "data_nature": "simulated"}


@router.get("/join/list", dependencies=[Depends(check_gate)])
def join_list(reviewer: str = Depends(require_reviewer)):
    """审核列表（内部面）：只回脱敏摘要，不回令牌哈希/联系方式原文之外字段。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, channel, applicant_kind, display_name, status, nsfl_result,"
        " reviewer_note, created_at FROM join_requests"
        " ORDER BY id DESC LIMIT 200").fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "data_nature": "simulated"}


# ════════════════════════════════════════════════════════════════════════════
# 2) 三阶流转（人审；每次 approve 复验 nsfl_scan ＋ C-1）
# ════════════════════════════════════════════════════════════════════════════
class StageAdvance(BaseModel):
    join_request_id: int
    action: str = Field(pattern="^(approve|reject)$")
    note: str | None = None


@router.post("/join/review", dependencies=[Depends(check_gate)])
def review_join(body: StageAdvance, request: Request,
                reviewer: str = Depends(require_reviewer)):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM join_requests WHERE id = ?", (body.join_request_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(404, "join request not found")
    current, history = row["status"], json.loads(row["status_history"] or "[]")
    payload = json.loads(row["payload"] or "{}")

    if body.action == "approve":
        # 三阶校验位：沙盒升阶与转正阶各复验一次（准入阶已在提交时验）
        scan_result, hits = nsfl_scan(payload)
        c1_ok, c1_why = check_general_rule(payload)
        if scan_result != "pass" or not c1_ok:
            note = f"nsfl-reblock:{hits},{c1_why}"
            conn.execute(
                "UPDATE join_requests SET status_history = ?, updated_at = datetime('now')"
                " WHERE id = ?",
                (_history_append(history, current, reviewer, note), body.join_request_id))
            conn.commit()
            conn.close()
            raise HTTPException(409, f"approve blocked: {note}")

    transitions = {("approve", "pending"): "sandbox", ("approve", "sandbox"): "active",
                   ("reject", "pending"): "rejected", ("reject", "sandbox"): "rejected"}
    nxt = transitions.get((body.action, current))
    if nxt is None:
        conn.close()
        raise HTTPException(409, f"invalid transition: {body.action} from {current}")

    conn.execute(
        "UPDATE join_requests SET status = ?, status_history = ?, reviewer_note = ?,"
        " updated_at = datetime('now') WHERE id = ?",
        (nxt, _history_append(history, nxt, reviewer, body.note), body.note,
         body.join_request_id))
    if nxt == "active":
        conn.execute(
            "INSERT OR IGNORE INTO members (join_request_id, channel, display_name, kind,"
            " status) VALUES (?,?,?,?,?)",
            (body.join_request_id, row["channel"], row["display_name"],
             row["applicant_kind"], "active"))
    conn.commit()
    conn.close()
    return {"ok": True, "from": current, "to": nxt, "by": reviewer}


# ════════════════════════════════════════════════════════════════════════════
# 3) 智能体对接卡
# ════════════════════════════════════════════════════════════════════════════
class AgentCard(BaseModel):
    identity: dict
    capabilities: list[str] = Field(default_factory=list)
    endpoint: str | None = None


@router.post("/agent-card/handshake", status_code=201, dependencies=[Depends(check_gate)])
def agent_handshake(body: AgentCard):
    if not body.identity:
        raise HTTPException(422, "agent_card.identity required")
    raw_token = secrets.token_urlsafe(32)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO agent_cards (card_token_hash, card) VALUES (?,?)",
        (token_hash(raw_token),
         json.dumps({"identity": body.identity, "tier": "sandbox",
                     "endpoints": ["/api/site/directory", "/api/site/weekly",
                                   "/api/site/meter", "/api/site/credits"]},
                    ensure_ascii=False)))
    conn.commit()
    conn.close()
    return {"ok": True, "card_id": cur.lastrowid,
            "card": {"identity": body.identity, "tier": "sandbox"},
            "token": raw_token, "data_nature": "simulated"}


@router.get("/agent-card/{card_id}", dependencies=[Depends(check_gate)])
def get_agent_card(card_id: int):
    conn = get_db()
    row = conn.execute("SELECT card FROM agent_cards WHERE id = ? AND revoked_at IS NULL",
                       (card_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "not found")
    card = json.loads(row["card"])
    card.pop("token", None)
    return {"card": card, "data_nature": "simulated"}


# ════════════════════════════════════════════════════════════════════════════
# 4) 计量（仅智能体通道）
# ════════════════════════════════════════════════════════════════════════════
class MeterEvent(BaseModel):
    endpoint: str
    units: float = 1.0
    detail: dict = Field(default_factory=dict)


@router.post("/meter", status_code=202, dependencies=[Depends(check_gate)])
def meter(event: MeterEvent, channel_meta: tuple = Depends(get_channel)):
    channel, agent_token = channel_meta
    if channel != "agent":
        raise HTTPException(403, "metering is agent-channel only")
    card = require_agent_card(agent_token)
    conn = get_db()
    conn.execute(
        "INSERT INTO api_calls (agent_card_id, member_id, endpoint, units, nca_anchor,"
        " detail) VALUES (?,?,?,?,?,?)",
        (card["id"], card["member_id"], event.endpoint, event.units,
         "nca-anchor:simulated", json.dumps(event.detail, ensure_ascii=False)))
    conn.commit()
    conn.close()
    return {"ok": True, "recorded_at": now_iso(), "data_nature": "simulated"}


# ════════════════════════════════════════════════════════════════════════════
# 5) 积分（内部替代①：模拟记账单位，⛔ 非法偿，期 1 不结算）
# ════════════════════════════════════════════════════════════════════════════
class CreditEvent(BaseModel):
    member_id: int
    delta: float
    reason: str = Field(min_length=1, max_length=200)


@router.post("/credits", status_code=202, dependencies=[Depends(check_gate)])
def credit(event: CreditEvent, channel_meta: tuple = Depends(get_channel)):
    channel, agent_token = channel_meta
    if channel != "agent":
        raise HTTPException(403, "credits ledger is agent-channel only")
    require_agent_card(agent_token)
    conn = get_db()
    conn.execute(
        "INSERT INTO credits_ledger (member_id, delta, reason, nca_anchor) VALUES (?,?,?,?)",
        (event.member_id, event.delta, event.reason, "nca-anchor:simulated"))
    conn.commit()
    conn.close()
    return {"ok": True, "data_nature": "simulated",
            "notice": "积分=模拟记账单位（非法偿），期 1 不结算"}


@router.get("/credits/{member_id}", dependencies=[Depends(check_gate)])
def credits_balance(member_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(SUM(delta),0) AS bal FROM credits_ledger WHERE member_id = ?",
        (member_id,)).fetchone()
    conn.close()
    return {"member_id": member_id, "balance": row["bal"], "data_nature": "simulated",
            "notice": "积分=模拟记账单位（非法偿），期 1 不结算"}


# ════════════════════════════════════════════════════════════════════════════
# 6) 云通知机令牌登记（内部替代③：⛔ 值不入件/日志，只存哈希）
# ════════════════════════════════════════════════════════════════════════════
class NotifyTokenRegister(BaseModel):
    member_id: int
    token: str = Field(min_length=16)


@router.post("/notify-token", status_code=202, dependencies=[Depends(check_gate)])
def register_notify_token(body: NotifyTokenRegister,
                          channel_meta: tuple = Depends(get_channel)):
    channel, agent_token = channel_meta
    if channel != "agent":
        raise HTTPException(403, "notify token registration is agent-channel only")
    require_agent_card(agent_token)
    conn = get_db()
    conn.execute("UPDATE members SET notify_token_hash = ?, updated_at = datetime('now')"
                 " WHERE id = ?", (token_hash(body.token), body.member_id))
    conn.commit()
    conn.close()
    return {"ok": True, "stored_as": "sha256-hash", "data_nature": "simulated"}


# ════════════════════════════════════════════════════════════════════════════
# 7) 公开只读面
# ════════════════════════════════════════════════════════════════════════════
@router.get("/weekly", dependencies=[Depends(check_gate)])
def weekly_latest():
    conn = get_db()
    rows = conn.execute(
        "SELECT issue_no, title, published_at FROM weekly"
        " ORDER BY published_at DESC LIMIT 20").fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "data_nature": "simulated"}


@router.get("/directory", dependencies=[Depends(check_gate)])
def directory():
    conn = get_db()
    rows = conn.execute(
        "SELECT display_name, kind, status FROM members WHERE status = 'active'").fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "data_nature": "simulated"}


@router.get("/docs/{family}", dependencies=[Depends(check_gate)])
def docs_family(family: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT slug, title, synced_at FROM docs WHERE family = ?", (family,)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows], "data_nature": "simulated"}


@router.get("/docs/{family}/{slug}", dependencies=[Depends(check_gate)])
def docs_detail(family: str, slug: str):
    conn = get_db()
    row = conn.execute(
        "SELECT slug, title, body_md, source_path, data_nature, synced_at"
        " FROM docs WHERE family = ? AND slug = ?", (family, slug)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "doc not found")
    return dict(row)
