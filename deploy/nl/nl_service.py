# FC-ID: DCD-NL-LLM-001 | NL 意图导航边车（GSEQ-0645）
# 真实外部模型调用（real 水印）× 规则表 fail 降级 × NSFL 预检 × 算力熔断（日¥2/月¥8）
# SITE-SEC-001 A 段（2026-11-12，裁定 INTENT-LOCK-001：不下线只加锁）：
#   A-1 会话令牌（经 gateway /auth/me 核验，单一事实源）＋ IP 限流 ＋ 单日个人配额
#   A-2 成本明细一律入内日志（calls.log）与 /health（内网），响应体零成本字段
#   A-3 供应商名中性化：响应体只写「真实外部模型调用」，⛔品牌名
# RTGATE-001（2026-11-18，权限网关一期·nl 样板，令只定判据）：
#   D 组：五元留痕（动作/输入摘要/结果/时间戳/身份）——成功/降级/拒件同账 CALLS_LOG，
#         拒件留痕失败不反转拒绝裁决（fail-closed 优先）
#   C 组：成本熔断现状只降级不上报 → 补 FUSE_LOG 熔断行（上报）；阈值沿用现网 2.0/8.0（S-RG6 ⛔定阈值）
#   B 组：闸序标明——全局闸(会话+限流) → 端内闸(角色·nl 公开端点落空) → 内容闸(NSFL) → 预算三维
# 不动 gateway FROZEN 封板包：nginx 精确路由 /api/v1/intent → 本服务，降级时回源 gateway。
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from enforce_entry import scan_nsfl_text  # NSFL 单一事实源（与 mcp 桥同一文件）

APP_VER = "0.3.1"
DS_URL = "https://api.deepseek.com/chat/completions"
DS_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
# 价格口径（¥/1M tokens，保守取值，可用环境变量覆盖）
PRICE_IN = float(os.environ.get("DEEPSEEK_PRICE_IN_PER_M", "2.0"))
PRICE_OUT = float(os.environ.get("DEEPSEEK_PRICE_OUT_PER_M", "3.0"))
# 算力熔断上限（GSEQ-0645：日 ¥2 / 月 ¥8）
CAP_DAY = float(os.environ.get("TDCA_COST_CAP_DAY", "2.0"))
CAP_MONTH = float(os.environ.get("TDCA_COST_CAP_MONTH", "8.0"))
GATEWAY = os.environ.get("TDCA_GATEWAY_ORIGIN", "http://gateway:8000")
EV = Path(os.environ.get("NL_EVIDENCE_DIR", "/evidence-nl"))
EV.mkdir(parents=True, exist_ok=True)
COST_FILE = EV / "cost.json"
FUSE_LOG = EV / ".nsfl-fuse.log"
CALLS_LOG = EV / "calls.log"            # A-2：每次真实调用的成本明细内日志（响应体不出）
QUOTA_FILE = EV / "quota.json"          # A-1：单日个人配额计数（持久，重启不丢）

# A-1 锁参数（环境可覆盖；默认从宽，告警口径见 INTENT-LOCK-001 边界②）
SESSION_PREFIX = "TDCA-SES-"
RATE_PER_MIN = int(os.environ.get("NL_RATE_PER_MIN", "30"))        # IP 维度滑动窗
QUOTA_DAY = int(os.environ.get("NL_QUOTA_DAY", "200"))             # 单用户单日 LLM 调用配额
VERIFY_CACHE_S = int(os.environ.get("NL_VERIFY_CACHE_S", "60"))    # 会话核验正缓存（秒）

app = FastAPI(title="tdca-nl-llm", version=APP_VER)

# 路由白名单（与 gateway 规则表同源，LLM 输出越界即纠正）
ROUTES = {
    "/": "首页 KPI 总览", "/me": "个人后台（我的）", "/agents": "智能体集群",
    "/attestation/dynamic": "动态确权审批", "/attestation/meta": "元函数初始确权（出盒终裁）",
    "/attestation/history": "确权历史追溯", "/tax": "税收仪表盘",
    "/audit": "审计透明（公共账本）", "/academy": "知识学院（术语注册表）",
    "/sandbox": "沙盒准入", "/studio": "Agent Studio（生命周期作业台）",
    "/market": "配置权市场（五阶资产池）", "/notifier": "通知机状态",
    "/governance": "治理中心", "/auth": "登录", "/ownership": "产权页",
}
ACTIONS = {"查询", "创建", "签批", "操作"}

SYS_PROMPT = (
    "你是 TDCA 门户的意图导航员。用户用一句自然语言说明意图，你把它映射到唯一功能页，并给出操作指引。\n"
    "只输出 JSON（不要多余文字）：{\"route\": 路由, \"action\": \"查询|创建|签批|操作\", "
    "\"guide\": [3 至 5 条简短操作指引], \"reply\": \"一句口语化回应\"}\n"
    "路由必须从下表选择（路由 → 页面）：\n"
    + "\n".join(f"{r} → {t}" for r, t in ROUTES.items())
    + "\n无法确定意图时 route 用 \"/\"。写操作（创建/签批）提醒需登录且人类确认（HUF）；"
      "查询类大多公开可查。指引要具体、白话、可照做。"
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _watermark(payload: dict, nature: str) -> dict:
    h = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {"data": payload, "nca_watermark": "sha256:" + h[:32], "ts": _utc(), "data_nature": nature}


# ---------------------------------------------------------------------
# A-2 成本账（内）：响应体一律不含成本字段，明细只落 COST_FILE / CALLS_LOG / FUSE_LOG
# ---------------------------------------------------------------------

def _ledger(evt: str, action: str, identity: str, q: str, result: str,
            extra: dict | None = None) -> None:
    """RTGATE-001 D组：五元留痕（动作/输入摘要/结果/时间戳/身份），成功与拒同账（CALLS_LOG JSONL）。
    调用方对「拒件」须自包 try/except——留痕失败不反转拒绝裁决（fail-closed 优先）。"""
    row = {"ts": _utc(), "evt": evt, "action": action, "identity": identity,
           "q": (q or "")[:80], "result": result}
    if extra:
        row.update(extra)
    with CALLS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_cost() -> dict:
    day = _utc()[:10]
    month = _utc()[:7]
    base = {"day": day, "day_spend": 0.0, "month": month, "month_spend": 0.0, "calls": 0}
    if COST_FILE.is_file():
        try:
            d = json.loads(COST_FILE.read_text(encoding="utf-8"))
        except Exception:
            return base
        if d.get("day") != day:
            d["day"], d["day_spend"] = day, 0.0
        if d.get("month") != month:
            d["month"], d["month_spend"] = month, 0.0
        return {**base, **d}
    return base


def _save_cost(d: dict) -> None:
    COST_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _log_call(user: str, ip: str, q: str, pin: int, pout: int, spend: float, cost: dict) -> None:
    """A-2：成本明细入内日志（含累计，监控从本文件与 /health 读，⛔响应体）。"""
    row = {"ts": _utc(), "evt": "llm", "action": "intent", "result": "ok",  # RTGATE-001 D组：五元之首三
           "identity": f"{user}@{ip}", "q": q[:80],
           "in": pin, "out": pout, "spend": round(spend, 6),
           "day_spend": round(cost["day_spend"], 4),
           "month_spend": round(cost["month_spend"], 4)}
    with CALLS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _fuse_tripped(cost: dict) -> str | None:
    if cost["day_spend"] >= CAP_DAY:
        return "day"
    if cost["month_spend"] >= CAP_MONTH:
        return "month"
    return None


# ---------------------------------------------------------------------
# A-1 锁：会话核验（gateway /auth/me 单一事实源）＋ IP 限流 ＋ 单日个人配额
# ---------------------------------------------------------------------

_verify_cache: dict[str, tuple[float, dict]] = {}
# RTGATE-001 R-RG6 并发修偏（0.3.1）：成本账与配额计数的「读-改-写」临界区加锁。
# 32 并发实测曾现丢失更新（32 次调用 calls=1/day_spend≈单次），少计花费令「何时该熔」判据失准，必修。
_COST_LOCK = asyncio.Lock()
_QUOTA_LOCK = asyncio.Lock()


async def _verify_session(token: str) -> dict:
    """经 gateway /auth/me 核验 TDCA-SES（fail-closed：网关不可达 → ok=False）。"""
    now = time.time()
    hit = _verify_cache.get(token)
    if hit and now - hit[0] < VERIFY_CACHE_S:
        return hit[1]
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{GATEWAY}/api/v1/auth/me",
                            headers={"Authorization": token})
        ok = r.status_code == 200
        body = r.json() if ok else {}
        # 信封解包：/auth/me 走 _nca_watermark（身份在 body["data"]）；扁平形兼容
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, dict):
            data = body if isinstance(body, dict) else {}
        result = {"ok": ok, "username": data.get("username", ""),
                  "role": data.get("role", "")}
    except Exception:
        result = {"ok": False, "username": "", "role": "", "unreachable": True}
    _verify_cache[token] = (now, result)
    return result


_rate_hits: dict[str, list[float]] = {}


def _rate_limited(ip: str) -> bool:
    now = time.time()
    win = [t for t in _rate_hits.get(ip, []) if now - t < 60.0]
    if len(win) >= RATE_PER_MIN:
        _rate_hits[ip] = win
        return True
    win.append(now)
    _rate_hits[ip] = win
    return False


def _load_quota() -> dict:
    day = _utc()[:10]
    base = {"day": day, "users": {}}
    if QUOTA_FILE.is_file():
        try:
            d = json.loads(QUOTA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return base
        if d.get("day") != day:
            d["day"], d["users"] = day, {}
        return {**base, **d}
    return base


def _save_quota(d: dict) -> None:
    QUOTA_FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def _quota_hit(user: str) -> tuple[bool, dict]:
    q = _load_quota()
    n = int(q["users"].get(user, 0))
    if n >= QUOTA_DAY:
        return True, q
    q["users"][user] = n + 1
    _save_quota(q)
    return False, q


def _reject(status: int, detail: str, code: str, *, action: str = "",
            identity: str = "", q: str = "") -> JSONResponse:
    # RTGATE-001 D组：拒件亦记五元；留痕失败不反转拒绝裁决（fail-closed 优先）
    try:
        _ledger("deny", action or "reject", identity or "anonymous", q,
                f"{status}:{code}")
    except Exception:
        pass
    return JSONResponse({"detail": detail, "code": code}, status_code=status)


def _nsfl_reject(q: str, hits: list, identity: str = "anonymous") -> JSONResponse:
    FUSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FUSE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[SIMULATED] {_utc()} | nl-llm 熔断 | 命中 {hits} | 身份 {identity} | 输入摘要 {q[:80]}\n")
    # RTGATE-001 D组：内容闸拒件五元入同账（留痕失败不反转拒绝裁决）
    try:
        _ledger("deny", "gate:nsfl", identity, q, "403:TDCA-E-NSFL-001",
                {"hits": [str(h) for h in hits]})
    except Exception:
        pass
    payload = {"matched": False, "route": "/", "title": "首页 KPI 总览", "action": "查询",
               "guide": ["该表述触线（NSFL 负空间），已拒绝并存证", "请换用业务相关表述再试"],
               "alternatives": [],
               "note": "NSFL 熔断：输入含负空间禁项，调用已拒绝并落熔断日志（绝不静默通过）"}
    return JSONResponse(_watermark(payload, "simulated"))


def _coerce_llm(obj: dict) -> dict:
    route = str(obj.get("route", "/"))
    if route not in ROUTES:
        route = "/"
    action = str(obj.get("action", "查询"))
    if action not in ACTIONS:
        action = "查询"
    guide = obj.get("guide")
    if not isinstance(guide, list) or not guide:
        guide = ["未生成明确指引，先给您目标页面"]
    guide = [str(g)[:120] for g in guide[:5]]
    return {"matched": route != "/", "route": route, "title": ROUTES[route], "action": action,
            "guide": guide, "alternatives": [], "reply": str(obj.get("reply", ""))[:200]}


async def _fallback(q: str, reason: str, identity: str = "anonymous") -> JSONResponse:
    """fail 降级：回源 gateway 规则表（封板包原样接口）。reason ⛔含成本数字（A-2）。
    RTGATE-001 D组：降级（200）亦记五元（留痕失败不反转降级语义）。"""
    try:
        _ledger("fallback", "intent-fallback", identity, q, "200:degraded",
                {"reason": reason[:80]})
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{GATEWAY}/api/v1/intent", params={"q": q})
            body = r.json()
        if isinstance(body, dict) and "data" in body:
            body["data"]["note"] = f"{body['data'].get('note', '')}｜LLM 降级：{reason}"
            return JSONResponse(body)
    except Exception as e:
        reason = f"{reason}；规则表回源亦失败（{type(e).__name__}）"
    payload = {"matched": False, "route": "/", "title": "首页 KPI 总览", "action": "查询",
               "guide": ["意图服务暂不可用，请稍后再试", "可先浏览门户各栏目"],
               "alternatives": [], "note": f"降级兜底：{reason}"}
    return JSONResponse(_watermark(payload, "simulated"))


@app.get("/health")
def health():
    cost = _load_cost()
    quota = _load_quota()
    return {"ok": True, "service": "tdca-nl-llm", "version": APP_VER,
            "llm_key": "present" if DS_KEY else "absent",
            "lock": {"session": "required", "rate_per_min": RATE_PER_MIN, "quota_day": QUOTA_DAY},
            "cost": {"day_spend": round(cost["day_spend"], 4), "cap_day": CAP_DAY,
                     "month_spend": round(cost["month_spend"], 4), "cap_month": CAP_MONTH},
            "quota_users_today": len(quota.get("users", {})),
            "fuse": _fuse_tripped(cost) or "ok"}


@app.get("/api/v1/intent")
async def intent(request: Request, q: str = ""):
    # ── RTGATE-001 B组闸序（一序贯穿，⛔各端点自写）──────────────────────
    #   ① 全局闸（在册「全局中间件凭证闸」口径）：会话核验 ＋ IP 限流
    #   ② 端内闸（角色）：nl 为公开意图端点无角色层——本层落空属正常（令 §二，R-RG2 标明）
    #   ③ 内容闸（在册负空间）：NSFL 预检
    #   ④ 预算三维（C组）：次数（单用户日配额）／成本（日/月熔断）／时间（IP 滑动窗限流）
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    token = request.headers.get("authorization", "").strip()
    qs = (q or "").strip()
    if not token.startswith(SESSION_PREFIX):
        return _reject(401, "意图接口须登录会话（TDCA-SES），未持令牌不返回结果",
                       "TDCA-E-NL-AUTH-001", action="gate:session", identity=f"anon@{ip}", q=qs)
    v = await _verify_session(token)
    if not v["ok"]:
        status = 503 if v.get("unreachable") else 401
        detail = ("会话核验服务暂不可达，fail-closed 拒绝（请稍后重试）"
                  if v.get("unreachable") else "会话无效、已过期或已吊销，请重新登录")
        return _reject(status, detail, "TDCA-E-NL-AUTH-002",
                       action="gate:session-verify", identity=f"tok:{token[:12]}…@{ip}", q=qs)
    user = v["username"]
    ident = f"{user}@{ip}"
    if _rate_limited(ip):  # 时间维（预算三维之一）
        return _reject(429, f"该 IP 请求过快（限流 {RATE_PER_MIN} 次/分钟），请稍后再试",
                       "TDCA-E-NL-RATE-001", action="budget:time", identity=ident, q=qs)
    # ── ③ 内容闸（NSFL，fail-closed，命中即拒并存证）─────────────────────
    q = qs
    if not q:
        return await _fallback(q, "空查询", ident)
    hits = scan_nsfl_text(q)
    if hits:
        return _nsfl_reject(q, hits, ident)
    # ── ④ 预算三维：成本（日/月熔断，阈值沿用现网 2.0/8.0，S-RG6 ⛔定阈值）──
    cost = _load_cost()
    tripped = _fuse_tripped(cost)
    if tripped:
        # C组「熔断并上报」：落 FUSE_LOG 熔断行（上报）；动作语义零改动（仍降级规则表）
        FUSE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with FUSE_LOG.open("a", encoding="utf-8") as f:
            f.write(f"[REAL-FUSE] {_utc()} | nl-llm 算力熔断({tripped}) | 身份 {ident} | 输入摘要 {q[:80]}\n")
        try:
            _ledger("deny", "budget:cost", ident, q, f"fuse:{tripped}")
        except Exception:
            pass
        # A-2：金额只在内部（FUSE_LOG/COST_FILE/health），响应体只给口径不给数
        return await _fallback(q, "算力配额已达当日/当月上限，已降级规则表", ident)
    if not DS_KEY:
        return await _fallback(q, "模型服务未注入密钥，走规则表", ident)
    # ── ④ 预算三维：次数（单用户日配额，临界区加锁防并发丢失更新）────────
    async with _QUOTA_LOCK:
        over, _ = _quota_hit(user)
    if over:
        return _reject(429, "已达单日个人调用配额，请明日再试（规则表导航不受影响）",
                       "TDCA-E-NL-QUOTA-001", action="budget:count", identity=ident, q=qs)
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(DS_URL,
                             headers={"Authorization": f"Bearer {DS_KEY}"},
                             json={"model": DS_MODEL, "temperature": 0.1, "max_tokens": 400,
                                   "response_format": {"type": "json_object"},
                                   "messages": [{"role": "system", "content": SYS_PROMPT},
                                                {"role": "user", "content": q}]})
            r.raise_for_status()
            body = r.json()
        text = body["choices"][0]["message"]["content"]
        obj = json.loads(text)
    except Exception as e:
        return await _fallback(q, f"模型调用失败（{type(e).__name__}），已降级规则表", ident)
    usage = body.get("usage") or {}
    pin = int(usage.get("prompt_tokens", 0))
    pout = int(usage.get("completion_tokens", 0))
    spend = pin * PRICE_IN / 1e6 + pout * PRICE_OUT / 1e6
    # R-RG6 修偏：锁内重读再累积（LLM 调用耗时不占锁，只锁读-改-写本身）
    async with _COST_LOCK:
        cost = _load_cost()
        cost["day_spend"] += spend
        cost["month_spend"] += spend
        cost["calls"] += 1
        _save_cost(cost)
    _log_call(user, ip, q, pin, pout, spend, cost)   # A-2：明细入日志，响应体零成本
    data = _coerce_llm(obj)
    # A-3：供应商中性化——响应体只写「真实外部模型调用」，⛔品牌名、⛔金额
    data["note"] = "真实外部模型调用（real 水印）"
    return JSONResponse(_watermark(data, "real"))
