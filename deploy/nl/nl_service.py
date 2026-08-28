# FC-ID: DCD-NL-LLM-001 | NL 意图导航边车（GSEQ-0645）
# DeepSeek 真实算力（real 水印）× 规则表 fail 降级 × NSFL 预检 × 算力熔断（日¥2/月¥8）
# 不动 gateway FROZEN 封板包：nginx 精确路由 /api/v1/intent → 本服务，降级时回源 gateway。
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from enforce_entry import scan_nsfl_text  # NSFL 单一事实源（与 mcp 桥同一文件）

APP_VER = "0.1.0"
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


def _fuse_tripped(cost: dict) -> str | None:
    if cost["day_spend"] >= CAP_DAY:
        return f"日累计 ¥{cost['day_spend']:.3f} 已达日上限 ¥{CAP_DAY:.0f}"
    if cost["month_spend"] >= CAP_MONTH:
        return f"月累计 ¥{cost['month_spend']:.3f} 已达月上限 ¥{CAP_MONTH:.0f}"
    return None


def _nsfl_reject(q: str, hits: list) -> JSONResponse:
    FUSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FUSE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[SIMULATED] {_utc()} | nl-llm 熔断 | 命中 {hits} | 输入摘要 {q[:80]}\n")
    payload = {"matched": False, "route": "/", "title": "首页 KPI 总览", "action": "查询",
               "guide": ["该表述触线（NSFL 负空间），已拒绝并存证", "请换用业务相关表述再试"],
               "alternatives": [],
               "note": f"NSFL 熔断：输入含负空间禁项 {hits}，调用已拒绝并落熔断日志（绝不静默通过）"}
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


async def _fallback(q: str, reason: str) -> JSONResponse:
    """fail 降级：回源 gateway 规则表（封板包原样接口）。"""
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
    return {"ok": True, "service": "tdca-nl-llm", "version": APP_VER,
            "llm_key": "present" if DS_KEY else "absent",
            "cost": {"day_spend": round(cost["day_spend"], 4), "cap_day": CAP_DAY,
                     "month_spend": round(cost["month_spend"], 4), "cap_month": CAP_MONTH},
            "fuse": _fuse_tripped(cost) or "ok"}


@app.get("/api/v1/intent")
async def intent(q: str = ""):
    q = (q or "").strip()
    if not q:
        return await _fallback(q, "空查询")
    # ① NSFL 预检（fail-closed，命中即拒并存证）
    hits = scan_nsfl_text(q)
    if hits:
        return _nsfl_reject(q, hits)
    # ② 算力熔断（日/月双闸）
    cost = _load_cost()
    tripped = _fuse_tripped(cost)
    if tripped:
        return await _fallback(q, f"算力熔断：{tripped}，已降级规则表")
    # ③ 无 key → 直接降级（不报错，fail 降级语义）
    if not DS_KEY:
        return await _fallback(q, "DEEPSEEK_API_KEY 未注入，走规则表")
    # ④ DeepSeek 真实调用
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
        return await _fallback(q, f"LLM 调用失败（{type(e).__name__}），已降级规则表")
    # ⑤ 计费与熔断记账（按 usage 实计）
    usage = body.get("usage") or {}
    pin = int(usage.get("prompt_tokens", 0))
    pout = int(usage.get("completion_tokens", 0))
    spend = pin * PRICE_IN / 1e6 + pout * PRICE_OUT / 1e6
    cost["day_spend"] += spend
    cost["month_spend"] += spend
    cost["calls"] += 1
    _save_cost(cost)
    data = _coerce_llm(obj)
    data["note"] = (f"DeepSeek 真实算力（{DS_MODEL}，real 水印）｜本次 ¥{spend:.4f}"
                    f"（in {pin}/out {pout} tok）｜日累计 ¥{cost['day_spend']:.3f}/¥{CAP_DAY:.0f}"
                    f"｜月累计 ¥{cost['month_spend']:.3f}/¥{CAP_MONTH:.0f}")
    return JSONResponse(_watermark(data, "real"))
