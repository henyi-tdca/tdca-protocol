# -*- coding: utf-8 -*-
"""TDCA 合约 × 国标交互对接（Contract Interop）——GB/Z 185.6 交互 → 合约 → 计税触发

制度依据:
  - 内化白皮书 §2.2（185.6 交互 → NCA 生成协议的通信层：点对点/群组/混合 → 单/多/网络嵌套 NCA）
  - 内化白皮书 §4.1（智能合约预计算：**国标交互日志 = 税收事件触发器**）
  - M4（重排 内部存证）：D+14a 智能合约 × 国标交互协议对接；验收「交互日志=税收事件触发器」用例通过

三模式（185.6）:
  p2p（点对点）/ group（群组）/ hybrid（混合）

纪律:
  - **交互日志即税收事件触发器**：每次交互产生纳税事实（value=0 亦记录事实，不因归零丢失）
  - **幂等**：同 event_id 不重复计税/不重复生成合约意图
  - 负空间声明 → 熔断拒绝（不记录为纳税事实）
  - 合约结算须存证（fail-closed）；MOU 模拟态更新
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


MODES = ("p2p", "group", "hybrid")


@dataclass
class InteractionEvent:
    """国标 185.6 交互事件（三模式）。"""
    event_id: str
    mode: str                      # p2p / group / hybrid
    from_agent: str                # TDID
    to_agents: List[str] = field(default_factory=list)
    action: str = "invoke"
    value: float = 0.0             # 交互经济价值（计税基数）
    oid: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    violates_nsfl: bool = False


@dataclass
class ContractCall:
    """合约调用意图（对接智能合约层）。"""
    contract_id: str
    kind: str                      # tax-prepay / tax-settle
    params: Dict[str, Any] = field(default_factory=dict)
    at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"contract_id": self.contract_id, "kind": self.kind,
                "params": self.params, "at": self.at, "simulated": True}


class ContractInteropGateway:
    """185.6 交互 → 合约 → 计税触发网关。"""

    def __init__(self, tax_rate: float = 0.02, nca_generator=None):
        self.tax_rate = float(tax_rate)
        self._log: List[Dict[str, Any]] = []
        self._tax_events: List[Dict[str, Any]] = []
        self._calls: Dict[str, ContractCall] = {}
        self._by_event: Dict[str, Dict[str, Any]] = {}     # 幂等索引
        if nca_generator is None:
            from tdca_nca.generator import NCAGenerator  # type: ignore
            nca_generator = NCAGenerator()
        self._gen = nca_generator

    # ---------- 交互 → 日志 + 计税 + 合约意图 + 存证 ----------
    def on_interaction(self, ev: InteractionEvent) -> Dict[str, Any]:
        if ev.mode not in MODES:
            raise ValueError(f"未知交互模式: {ev.mode}（期望 {MODES}）")
        from identity_bridge import IdentityBridge  # type: ignore
        try:
            IdentityBridge.validate_tdid(ev.from_agent)
            for t in ev.to_agents:
                IdentityBridge.validate_tdid(t)
        except Exception as exc:
            return {"accepted": False, "reason": f"身份不合法：{exc}", "event_id": ev.event_id}

        # 幂等
        if ev.event_id in self._by_event:
            prev = self._by_event[ev.event_id]
            return {"accepted": True, "idempotent": True, **prev}

        if ev.violates_nsfl:
            self._log.append({"event_id": ev.event_id, "mode": ev.mode,
                              "from_agent": ev.from_agent, "to_agents": list(ev.to_agents),
                              "action": ev.action, "accepted": False,
                              "reason": "负空间违规——熔断（不计纳税事实）",
                              "at": self._now(), "simulated": True})
            return {"accepted": False, "reason": "负空间违规——熔断", "event_id": ev.event_id}

        # ① 交互日志（= 税收事件触发器）
        log_row = {"event_id": ev.event_id, "mode": ev.mode, "from_agent": ev.from_agent,
                   "to_agents": list(ev.to_agents), "action": ev.action, "value": ev.value,
                   "oid": ev.oid, "at": self._now(), "accepted": True, "simulated": True}
        self._log.append(log_row)

        # ② 计税（交互即纳税事实；value=0 亦记录事实）
        tax = round(ev.value * self.tax_rate, 2)
        tax_event = {"event_id": ev.event_id, "tax": tax, "rate": self.tax_rate,
                     "tax_fact_recorded": True, "mou_status": "Simulated",
                     "at": self._now(), "simulated": True}
        self._tax_events.append(tax_event)

        # ③ 合约调用意图（税收预计算）
        call = ContractCall(contract_id=f"C-TAX-PREPAY-{ev.event_id}",
                            kind="tax-prepay",
                            params={"event_id": ev.event_id, "tax": tax,
                                    "from_agent": ev.from_agent, "value": ev.value},
                            at=self._now())
        self._calls[call.contract_id] = call

        # ④ 存证
        nca = self._gen.generate(type="interop-contract-intent", layer=2,
                                 content={"log": log_row, "tax_event": tax_event,
                                          "call": call.to_dict()})
        result = {"log": log_row, "tax_event": tax_event, "contract_call": call.to_dict(),
                  "nca_ref": nca.nca_id}
        self._by_event[ev.event_id] = {k: v for k, v in result.items()}
        return {"accepted": True, "idempotent": False, **result}

    # ---------- 合约结算（模拟执行 + 存证 + MOU 模拟态更新） ----------
    def settle(self, contract_id: str) -> Dict[str, Any]:
        call = self._calls.get(contract_id)
        if call is None:
            raise KeyError(f"未知合约调用: {contract_id}")
        if call.kind != "tax-prepay":
            raise ValueError("仅 tax-prepay 可结算")
        settle_call = ContractCall(contract_id=f"C-TAX-SETTLE-{call.params['event_id']}",
                                   kind="tax-settle", params=dict(call.params), at=self._now())
        self._calls[settle_call.contract_id] = settle_call
        nca = self._gen.generate(type="interop-contract-settle", layer=3,
                                 content={"prepay": call.to_dict(), "settle": settle_call.to_dict(),
                                          "mou": {"status": "Simulated", "updated": True}})
        return {"settled": True, "contract_call": settle_call.to_dict(),
                "mou": {"status": "Simulated", "updated": True},
                "nca_ref": nca.nca_id, "simulated": True}

    # ---------- 观测 ----------
    def interaction_log(self) -> List[Dict[str, Any]]:
        return list(self._log)

    def tax_events(self) -> List[Dict[str, Any]]:
        """交互日志 = 税收事件触发器（验收口径）。"""
        return list(self._tax_events)

    def contract_calls(self) -> List[ContractCall]:
        return list(self._calls.values())

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")
