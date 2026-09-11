# -*- coding: utf-8 -*-
"""PCR-Token 交换载体（M2 / #1）——签发 → 发布 → 取回 → 校验

**动机（SRIGHT-001 §三 如实边界）**：V1.1 的 PCR-Token 为**同进程签名式**，真实网络
交换"待载体"。本模块把"载体"抽象出来，使：
  1. 交换路径**可测试、可替换**（进程内 / 文件 / 网络三类载体同一接口）
  2. **未就绪载体显式拒绝**（`CarrierUnavailableError`）——绝不虚报执行
  3. 每次发布/取回留 `ExchangeRecord`（载体模式 + 时点 + 结果）

载体清单:
  - `InProcessCarrier`    同进程直传（等价 V1.1 现状；默认载体）
  - `FileExchangeCarrier` 本地文件落盘交换——**跨进程语义的结构等价替身**（仍是本机模拟态）
  - `NetworkCarrierStub`  **真实网络载体占位**：端点/服务未就绪 ⇒ `ready()=False`，调用即拒

纪律:
  - `verify` 一律复用 `SRightGateway.verify_token`（持有人/边界/有效期/预算/签名五项），
    载体不得自造校验口径
  - 取回件与发布件须 `token_id` 一致、`holder_tdid` 一致；不一致即拒
  - 数据性质: **模拟态**（OID 与签名均为模拟占位；真实网络交换仍待发布通道）

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


from sright import PCRToken, SRightGateway  # noqa: E402

CARRIER_MODES = ("in-process", "file-exchange", "network-pending")
NETWORK_READY_HINT = "待发布通道（服务端点/构建产物就绪后切换）"


class CarrierUnavailableError(Exception):
    """载体未就绪或纪律违例（不虚报：未就绪即拒）。"""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class ExchangeRecord:
    """一次发布/取回留痕。"""
    token_id: str
    carrier_mode: str
    action: str                      # publish / fetch
    at: str
    ok: bool
    detail: str = ""
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "carrier_mode": self.carrier_mode,
                "action": self.action, "at": self.at, "ok": self.ok,
                "detail": self.detail, "simulated": True}


def token_to_payload(token: PCRToken) -> Dict[str, Any]:
    """令牌 → 交换负载（**含模拟态标注**；不含任何凭据类字段）。"""
    d = token.to_dict()
    d["carrier_schema"] = "PCR-TOKEN-EXCHANGE-1"
    return d


def token_from_payload(payload: Dict[str, Any]) -> PCRToken:
    return PCRToken(token_id=payload["token_id"], holder_tdid=payload["holder_tdid"],
                    scope=payload["scope"], budget_total=float(payload["budget_total"]),
                    issued_at=payload["issued_at"], expires_at=payload["expires_at"],
                    oid=payload.get("oid"), signature=payload.get("signature", ""))


class TokenExchangeCarrier:
    """载体基类：须自陈 `mode` 与 `ready()`；未就绪者不得发布/取回。"""

    mode = "abstract"

    def ready(self) -> bool:
        raise NotImplementedError

    def descriptor(self) -> Dict[str, Any]:
        return {"mode": self.mode, "ready": self.ready(), "simulated": True}

    # ---- 载体能力（子类实现；未就绪须抛 CarrierUnavailableError） ----
    def publish(self, token: PCRToken) -> ExchangeRecord:
        raise NotImplementedError

    def fetch(self, token_id: str, holder_tdid: str) -> Optional[PCRToken]:
        raise NotImplementedError


class InProcessCarrier(TokenExchangeCarrier):
    """同进程载体（默认）：等价 V1.1 的本地签名式传递。"""

    mode = "in-process"

    def __init__(self) -> None:
        self._store: Dict[str, PCRToken] = {}

    def ready(self) -> bool:
        return True

    def publish(self, token: PCRToken) -> ExchangeRecord:
        self._store[token.token_id] = token
        return ExchangeRecord(token.token_id, self.mode, "publish", _now(), True,
                              "同进程登记（无网络传输）")

    def fetch(self, token_id: str, holder_tdid: str) -> Optional[PCRToken]:
        token = self._store.get(token_id)
        if token is None:
            return None
        if token.holder_tdid != holder_tdid:
            raise CarrierUnavailableError(
                f"取回方与令牌持有人不一致（holder={token.holder_tdid} / fetch={holder_tdid}）")
        return token


class FileExchangeCarrier(TokenExchangeCarrier):
    """本地文件交换载体：**跨进程语义的结构等价替身**（仍是本机模拟态）。

    用途：在不具备网络通道的环境下，验证"发布→落盘→另一进程取回→校验"的完整交换语义。
    """

    mode = "file-exchange"

    def __init__(self, directory: str) -> None:
        self.dir = Path(directory)

    def ready(self) -> bool:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            return self.dir.is_dir()
        except Exception:                                   # noqa: BLE001
            return False

    def _path(self, token_id: str) -> Path:
        return self.dir / f"{token_id}.pcr.json"

    def publish(self, token: PCRToken) -> ExchangeRecord:
        if not self.ready():
            raise CarrierUnavailableError(f"文件载体不可用（目录不可写）：{self.dir}")
        payload = token_to_payload(token)
        path = self._path(token.token_id)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        return ExchangeRecord(token.token_id, self.mode, "publish", _now(), True,
                              f"落盘 {path.name}（{os.path.getsize(path)}B）")

    def fetch(self, token_id: str, holder_tdid: str) -> Optional[PCRToken]:
        path = self._path(token_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("carrier_schema") != "PCR-TOKEN-EXCHANGE-1":
            raise CarrierUnavailableError(f"交换负载模式不符：{payload.get('carrier_schema')!r}")
        token = token_from_payload(payload)
        if token.holder_tdid != holder_tdid:
            raise CarrierUnavailableError(
                f"取回方与令牌持有人不一致（holder={token.holder_tdid} / fetch={holder_tdid}）")
        return token


class NetworkCarrierStub(TokenExchangeCarrier):
    """**真实网络载体占位**（未就绪）：端点就绪前调用即拒，如实标注不虚报。"""

    mode = "network-pending"

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def ready(self) -> bool:
        return False                        # 发布通道未就绪（本环境无服务端点）

    def descriptor(self) -> Dict[str, Any]:
        d = super().descriptor()
        d.update({"endpoint": self.endpoint, "hint": NETWORK_READY_HINT})
        return d

    def _reject(self) -> None:
        raise CarrierUnavailableError(
            f"网络载体未就绪（endpoint={self.endpoint}）：{NETWORK_READY_HINT}；"
            "当前仅同进程/文件载体可用（不得虚报网络交换已完成）")

    def publish(self, token: PCRToken) -> ExchangeRecord:
        self._reject()

    def fetch(self, token_id: str, holder_tdid: str) -> Optional[PCRToken]:
        self._reject()


@dataclass
class RoundTripResult:
    """签发 → 发布 → 取回 → 校验 闭环结果（含载体自陈与逐次留痕）。"""
    token_id: str
    carrier_mode: str
    published: Dict[str, Any]
    fetched: bool
    verify: Dict[str, Any]
    records: List[Dict[str, Any]]
    ok: bool
    reason: str = ""
    simulated: bool = True
    network_exchange: bool = False          # 真实网络交换是否发生（本版恒 False）

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "carrier_mode": self.carrier_mode,
                "published": self.published, "fetched": self.fetched, "verify": self.verify,
                "records": self.records, "ok": self.ok, "reason": self.reason,
                "simulated": True, "network_exchange": self.network_exchange}


def exchange_roundtrip(carrier: TokenExchangeCarrier, token: PCRToken, req, tool) -> RoundTripResult:
    """执行交换闭环：发布 → 取回 → 五项校验（**载体未就绪即拒，不降级虚报**）。

    目标函数: 在给定载体上验证 PCR-Token 的跨主体交换语义（发布/取回/校验全链留痕）
    约束矩阵: 载体须 ready；取回件须 token_id/holder 一致；校验一律走
              `SRightGateway.verify_token`（不得自造口径）
    先验分布: SRIGHT-001 V1.1 §三（五项校验）
    配置权边界: L2 场景层
    预期分配: `RoundTripResult`
    审计轨迹: records（ExchangeRecord 列表）
    """
    records: List[ExchangeRecord] = []
    if not carrier.ready():
        raise CarrierUnavailableError(
            f"载体未就绪（mode={carrier.mode}）：不得执行交换（不虚报）")

    pub = carrier.publish(token)
    records.append(pub)
    fetched = carrier.fetch(token.token_id, token.holder_tdid)
    records.append(ExchangeRecord(token.token_id, carrier.mode, "fetch", _now(),
                                  fetched is not None,
                                  "取回成功" if fetched is not None else "取回为空"))
    if fetched is None:
        return RoundTripResult(token.token_id, carrier.mode, pub.to_dict(), False, {},
                               [r.to_dict() for r in records], False,
                               reason="取回为空（交换未闭环）")
    if fetched.token_id != token.token_id or fetched.holder_tdid != token.holder_tdid:
        raise CarrierUnavailableError("取回件与发布件不一致（token_id/holder 不匹配）")

    verify = SRightGateway.verify_token(fetched, req, tool)
    return RoundTripResult(token.token_id, carrier.mode, pub.to_dict(), True, verify,
                           [r.to_dict() for r in records], bool(verify.get("ok")),
                           reason="交换闭环且五项校验通过" if verify.get("ok") else "校验未通过",
                           network_exchange=(carrier.mode == "network" and carrier.ready()))
