# -*- coding: utf-8 -*-
"""
L1SI218-DUALCH-001-001/-002 运维授权前置闸（/api/v1/ops/* 机面，SITEDEP-001 核对清单第 4 项）。

口径（后件 8487 为准：平台只管形式，不判内容选择）：
- 人类通道不变：TDCA-SES 会话照常校验，operator/founder 权限照既有端内守卫。
- 机面（智能体等非会话调用）：须携两头发：
    X-TDCA-Ops-Auth: AR-xxxx   授权件标识（登记册 authorization_records）
    X-TDCA-Agent-Id: <具名智能体标识>   被授权者具名校验用
  平台三判：
    ① 授权件存在：record 命中且 status == 'active'
    ② 形式合规：四要件（req_scene/req_five_forms/req_full_grant/req_legal_signature）
       全 True ＋ template_fields 为非空 JSON 对象（八字段透传，内容用户自定不代判）
       ＋ nca_ref 存证在（制度底线：无存证不视为有效授权）
    ③ 级别达 O-1：scope 声明含只读运维——template_fields 全键值文本或 scope_note
       含 'O-1'／'只读'／'read' 任一标记（形式判，不判是否合理、不判该多授否）
  被授权者须具名且与调用身份一致：grantee_ref == X-TDCA-Agent-Id。
- 级别行为：O-1 ⟹ 只读放行（GET/HEAD）；写端点对机面一律 403（O-2 须人类在场、
  O-3 逐次明示，均归动作发生时限制，⛔前置校验可代）。
- fail-closed：机面无授权／校验不过 ⟹ 403 ＋ 留痕（ops_auth_denials 表）。
- 平台 ⛔建默认授权 ⛔指定被授权者 ⛔强推搭配 ⛔以建议变相限定。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from db import models as M  # noqa: E402
from auth import SESSION_PREFIX, validate_session  # noqa: E402
from db import get_session  # noqa: E402

OPS_AUTH_HEADER = "x-tdca-ops-auth"
AGENT_ID_HEADER = "x-tdca-agent-id"
_O1_MARKERS = ("O-1", "o-1", "只读", "read", "READ")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _deny(request: Request, reason: str, caller: str, auth_id: str | None) -> None:
    """fail-closed：403 ＋ 留痕（每次拒绝一行，含路径/方法/调用方/所携授权件/原因）。"""
    try:
        with get_session() as s:
            s.add(M.OpsAuthDenial(
                ts=_utcnow().isoformat(),
                path=request.url.path,
                method=request.method,
                caller=caller,
                auth_id_presented=auth_id,
                reason=reason,
            ))
            s.commit()
    except Exception:
        pass  # 留痕失败不反转拒绝裁决（fail-closed 优先）
    raise HTTPException(403, f"机面运维须人授权前置：{reason}")


def _artifact_ok(auth_id: str, agent_id: str) -> str | None:
    """三判。返回 None=通过，否则=不过之原因（⛔改代码外语义）。"""
    with get_session() as s:
        r = s.get(M.AuthorizationRecord, auth_id)
        if r is None:
            return "授权件不存在"
        if r.status != "active":
            return f"授权件状态非 active（现为 {r.status}）"
        if not (r.req_scene and r.req_five_forms and r.req_full_grant and r.req_legal_signature):
            return "四要件未齐（形式不合规）"
        try:
            tpl = json.loads(r.template_fields or "{}")
        except (ValueError, TypeError):
            return "模板八字段非合法 JSON（形式不合规）"
        if not isinstance(tpl, dict) or not tpl:
            return "模板八字段为空（形式不合规）"
        if not r.nca_ref:
            return "无 NCA 存证（制度底线）"
        if agent_id and r.grantee_ref != agent_id:
            return "被授权者与调用身份不符（须具名一致）"
        hay = " ".join(str(v) for v in tpl.values()) + " " + (r.scope_note or "")
        if not any(mk in hay for mk in _O1_MARKERS):
            return "级别未达 O-1（无只读运维声明）"
    return None


def require_ops_caller(request: Request) -> dict:
    """/api/v1/ops/* 统一入口判定：人类会话照原路；机面走授权前置闸。"""
    raw = request.headers.get("authorization", "").strip()
    if raw.startswith(SESSION_PREFIX):
        v = validate_session(raw)
        if not v["ok"]:
            raise HTTPException(401, "会话已过期，请重新登录" if v.get("expired") else "会话无效或已吊销")
        return v
    auth_id = request.headers.get(OPS_AUTH_HEADER, "").strip()
    if not auth_id:
        # 无授权件头 ⟹ 维持既有 401 语义（匿名/旧 CRT 调用方行为不变）
        from api_v1 import _require_session_user  # noqa: E402  延迟导入避环
        return _require_session_user(request)
    agent_id = request.headers.get(AGENT_ID_HEADER, "").strip()
    caller = agent_id or "machine-anonymous"
    if not agent_id:
        _deny(request, "被授权者未具名（缺 X-TDCA-Agent-Id）", caller, auth_id)
    bad = _artifact_ok(auth_id, agent_id)
    if bad:
        _deny(request, bad, caller, auth_id)
    return {"role": "agent-ops-o1", "machine": True, "auth_id": auth_id, "agent_id": agent_id}


def ops_guard(user: dict, request: Request, action: str) -> None:
    """端内权限守卫（替换既有 operator/founder 行内检查）：人类照原；机面 O-1 只读放行。"""
    if user.get("role") in ("operator", "founder"):
        return
    if user.get("machine"):
        if request.method in ("GET", "HEAD"):
            return  # O-1 只读观测放行
        raise HTTPException(403, "机面 O-1 只读授权：写操作须人类在场或可即时叫停（O-2）／逐次明示（O-3）")
    raise HTTPException(403, f"仅 operator / founder 可{action}")

def require_write_privilege(role: str = "operator", action: str = "执行此操作", owner_getter=None):
    """统一写鉴权依赖（四档）——UNIFYAUTH-001/AUTHFOUR-001。

    档语义（等价既有端内行内检查，零行为变更）：
    - operator：登录 且 role ∈ {operator, founder}
    - founder：登录 且 role == founder
    - login：仅要求登录
    - owner_or_operator：登录 且（本人 或 role ∈ {operator, founder}）；
      owner_getter(payload, user) -> 属主名——入参为已解析 JSON 体（依赖内 await
      request.body() 读取，Starlette 缓存 _body，端点 body 参数解析不受影响）；
      查无档须自行 raise 404 以复刻原「先 404 后 403」顺序。
    403 文案沿用原端点行内检查口径（action 传原文）。
    """
    async def _dep(request: Request) -> dict:
        from api_v1 import _require_session_user  # noqa: E402  延迟导入避环
        user = _require_session_user(request)
        r = user.get("role")
        if role == "login":
            return user
        if role == "operator":
            if r in ("operator", "founder"):
                return user
            raise HTTPException(403, f"仅 operator / founder 可{action}")
        if role == "founder":
            if r == "founder":
                return user
            raise HTTPException(403, f"仅 founder 可{action}")
        if role == "owner_or_operator":
            if r in ("operator", "founder"):
                return user
            try:
                payload = await request.json()
            except Exception:  # noqa: BLE001  无体/非法体：按无属主处理，端点解析随后兜底
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            owner = owner_getter(payload, user) if owner_getter else None
            if owner and user.get("username") and owner == user["username"]:
                return user
            raise HTTPException(403, "非本人 ⛔ 判定——验收人须与登单人同一登录主体")
        raise HTTPException(500, f"未知写鉴权档：{role}")
    _dep.__name__ = f"require_write_{role}"
    return _dep
