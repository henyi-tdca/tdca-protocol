# -*- coding: utf-8 -*-
"""
TDCA 统一网关 WebSocket 实时端点（B-5）

用途: 前端实时观测——通知机消息流速率 / 握手生命周期 / 税务-MOU 事件流
      （前端 V-2/V-4/V-9 实时化的传输通道）

设计:
- 连接: ws://host:8100/ws/events?channel={channel}
  channel ∈ {handshake, tax_mou, notifier, audit}
- 广播: 网关内部事件经 broadcast() 推送到订阅该 channel 的全部连接
- 心跳: 服务端每 30s 发 {"type":"ping"}（可被前端用于断线检测）
- 鉴权: 与 B-4 一致——启用 TDCA_GATEWAY_AUTH=1 时握手须 token 参数
- fail-closed: 未知 channel 拒绝连接
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# channel -> set[WebSocket]
_SUBSCRIBERS: Dict[str, Set[WebSocket]] = {}
# 事件序号（审计）
_event_seq = 0

ALLOWED_CHANNELS = {"handshake", "tax_mou", "notifier", "audit"}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def broadcast(channel: str, event_type: str, payload: dict) -> dict:
    """网关内部事件广播入口（同步调用；异步推送由各自连接任务执行）。"""
    global _event_seq
    _event_seq += 1
    message = {
        "seq": _event_seq,
        "type": event_type,
        "channel": channel,
        "ts": _utc(),
        "payload": payload,
    }
    # 投递至订阅者（尽力而为：断开的连接在接收任务中清理）
    for ws in list(_SUBSCRIBERS.get(channel, set())):
        try:
            asyncio.get_event_loop().create_task(ws.send_text(json.dumps(message, ensure_ascii=False)))
        except Exception:
            pass
    return message


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket, channel: str = "handshake"):
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4404, reason="unknown channel")
        return

    # B-4 联动: 启用鉴权时握手须携带 token 查询参数
    from auth import _auth_enabled, _valid_token
    if _auth_enabled():
        token = websocket.query_params.get("token", "")
        if not _valid_token(token):
            await websocket.close(code=4401, reason="unauthorized")
            return

    await websocket.accept()
    _SUBSCRIBERS.setdefault(channel, set()).add(websocket)
    try:
        # 心跳循环 + 接收（保持连接）
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping", "ts": _utc()}, ensure_ascii=False))
                continue
            if data:  # 客户端消息回显（简单 echo，预留控制通道）
                await websocket.send_text(json.dumps(
                    {"type": "echo", "channel": channel, "data": data, "ts": _utc()}, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    finally:
        _SUBSCRIBERS.setdefault(channel, set()).discard(websocket)
