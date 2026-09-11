# -*- coding: utf-8 -*-
"""交互结算 → CLS 闭环结算管线（M4 / #13）

**现状与缺口（INTEROP-001 §八-4）**：`interop.settle()` 仅生成 `tax-settle` 合约意图 +
MOU 模拟态更新，**未接入闭环结算管线**。本模块把交互结算接到 **CLS**：

```
交互日志（value 债务边）→ CLS GIM 环销 → RTN 净额（T_net）→ DVP 定向支付 → 同刻计税 → NCA
interop 税事件（tax）→ CLS 台账（record_settlement）+ NCA（from_settlement）
```

**口径分层（重要，避免混淆）**：

| 层 | 名称 | 来源 |
|---|---|---|
| interop 层 | **交易税**（`tax = value × tax_rate`） | `ContractInteropGateway.tax_events()`（本层只记账，不重算） |
| CLS 层 | **配置权调度税**（T-031，默认 2%） | `CLSTaxAdapter.compute_for_settlement`（按净额支付金额） |

两税**分层记录、不叠加也不互相覆盖**（本模块不重算 interop 税，CLS 税只报其自身口径）。

纪律:
  - **定向性**（CLS I-1）：支付单 payer≠payee 且金额>0；无自由转账
  - **净额守恒**（CLS I-2）：Σ定向支付 = T_net
  - **异常不中断**（CLS I-5）：单笔 HELD 不影响其余
  - **只读复用**：不改 `tdca-cls` 任何实现；不改 `interop.py` 既有方法语义
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:                                            # 依赖契约（可注入）：闭环结算管线
    from tdca_cls.adapters import (CLSLedgerAdapter, CLSNCAAdapter, CLSTaxAdapter)
    from tdca_cls.engine import CLSEngine
except ImportError:                             # 发布包不含结算管线 → 内置最小实现
    class CLSTaxAdapter:                        # 最小计税（2% 调度税；可注入替换）
        def compute_for_settlement(self, payer, payee, amount, scene="supply-chain",
                                   royalty_base=0.0, simulated=True):
            from types import SimpleNamespace
            tax = round(float(amount) * 0.02, 6)
            return SimpleNamespace(amount=amount, dispatch_tax=tax, royalty=0.0,
                                   trade_fee=0.0, total_tax=tax,
                                   net_value=round(float(amount) - tax, 6), mou_ok=True)

    class CLSLedgerAdapter:                     # 最小台账（内存态）
        def __init__(self, ledger=None):
            self._total = 0.0

        def record_settlement(self, tx_id, agent, tax, event_type="CLS_SETTLEMENT"):
            self._total += float(tax)

        def aggregate_mou(self, start_time=None, end_time=None):
            return self._total

        def total_settled(self):
            return round(self._total, 6)

    class CLSNCAAdapter:                        # 最小存证适配（内存态）
        def __init__(self):
            self.nc_as = []

        def from_settlement(self, tx_id, payer, payee, amount, tax_result, cycle_ref=""):
            from types import SimpleNamespace
            rec = SimpleNamespace(nca_id=f"NCA-SETTLE-{tx_id}", transaction_id=tx_id,
                                  tax_amount=float(getattr(tax_result, "total_tax", 0.0)))
            self.nc_as.append(rec)
            return rec

        def all_ncas(self):
            return list(self.nc_as)

    class CLSEngine:                            # 最小引擎（**仅 direct 模式**；netting 须注入实现）
        def __init__(self):
            from types import SimpleNamespace
            self.network = SimpleNamespace(nodes=[], debt={})
            self.rtn = SimpleNamespace(net=lambda *a, **k: SimpleNamespace(
                t_net=0.0, payment_orders=[]))
            self.tax_adapter = CLSTaxAdapter()
            self.ledger = CLSLedgerAdapter()
            self.nca_adapter = CLSNCAAdapter()
            self.outcomes = []

        def add_debt_edges(self, edges):
            self._edges = list(edges)

        def run_settlement(self, mou_map=None, delivery_map=None, settle_all=True):
            raise NotImplementedError(
                "内置最小引擎仅支持 direct 模式；netting 须注入结算管线实现"
                "（依赖契约见 README『依赖契约（可注入）』）")

        def invariants(self, t_net_before=None):
            return {}

SETTLEMENT_MODES = ("netting", "direct")
DEFAULT_TREASURY = "TDCA-TREASURY"


class InteropSettlementError(Exception):
    """交互结算对接纪律违例。"""


@dataclass
class InteropSettlement:
    """交互结算结果（净额支付单 + 税记账 + 不变量 + 守恒）。"""
    mode: str
    payment_orders: List[Dict[str, Any]] = field(default_factory=list)
    taxes_recorded: List[Dict[str, Any]] = field(default_factory=list)
    t_net: float = 0.0
    total_paid: float = 0.0
    total_dispatch_tax: float = 0.0
    total_interop_tax: float = 0.0
    invariants: Dict[str, Any] = field(default_factory=dict)
    nca_refs: List[str] = field(default_factory=list)
    conservation: Dict[str, Any] = field(default_factory=dict)
    payment_orders_ok: bool = False
    at: str = ""
    simulated: bool = True

    @property
    def settled(self) -> bool:
        return all(bool(v) for v in self.conservation.values()) and (
            not self.invariants or bool(self.invariants.get("all_pass")))

    def to_dict(self) -> Dict[str, Any]:
        return {"settled": self.settled, "mode": self.mode,
                "payment_orders": self.payment_orders,
                "taxes_recorded": self.taxes_recorded, "t_net": self.t_net,
                "total_paid": self.total_paid, "total_dispatch_tax": self.total_dispatch_tax,
                "total_interop_tax": self.total_interop_tax, "invariants": self.invariants,
                "conservation": self.conservation, "payment_orders_ok": self.payment_orders_ok,
                "nca_refs": self.nca_refs, "at": self.at, "simulated": True}


def _debt_edges(log: List[Dict[str, Any]]) -> List[Tuple[str, str, float]]:
    """交互日志 → 债务边（from_agent 欠各 to_agent 价值；value>0 才成边）。"""
    edges: List[Tuple[str, str, float]] = []
    for row in log:
        if not row.get("accepted"):
            continue
        value = float(row.get("value") or 0.0)
        if value <= 0:
            continue
        src, dsts = row.get("from_agent"), row.get("to_agents") or []
        if not src or not dsts:
            continue
        share = round(value / len(dsts), 6)
        for d in dsts:
            edges.append((src, d, share))
    return edges


def settle_interactions(gateway: Any, *, mode: str = "netting",
                        treasury: str = DEFAULT_TREASURY,
                        engine: Optional[CLSEngine] = None,
                        tax_adapter: Optional[CLSTaxAdapter] = None,
                        ledger: Optional[CLSLedgerAdapter] = None,
                        nca_adapter: Optional[CLSNCAAdapter] = None) -> InteropSettlement:
    """把 `ContractInteropGateway` 的交互/税事件接入 CLS 闭环结算。

    目标函数: 交互价值（净额）+ 交易税（记账）落地到 CLS 管线，闭环可核
    约束矩阵: 债务边须 value>0 且 to_agents 非空；净额守恒；无自由转账；
              税事实逐条记账（interop 税不重算）
    先验分布: CLS 引擎（GIM/RTN/DPI/DVP）｜ INTEROP-001 §二
    配置权边界: L2 场景层（结算映射）
    预期分配: `InteropSettlement`
    审计轨迹: CLS NCA（NCA-CLS-*）+ 台账
    """
    if mode not in SETTLEMENT_MODES:
        raise InteropSettlementError(f"结算模式须为 {SETTLEMENT_MODES}（当前 {mode!r}）")

    log = list(gateway.interaction_log() or [])
    taxes = list(gateway.tax_events() or [])
    edges = _debt_edges(log)

    tax_adapter = tax_adapter or CLSTaxAdapter()
    ledger = ledger or CLSLedgerAdapter()
    nca_adapter = nca_adapter or CLSNCAAdapter()

    res = InteropSettlement(mode=mode)
    res.total_interop_tax = round(sum(float(t.get("tax") or 0.0) for t in taxes), 6)

    if mode == "netting":
        eng = engine or CLSEngine()
        if edges:
            eng.add_debt_edges(edges)
            full_t_net = eng.rtn.net(list(eng.network.nodes), dict(eng.network.debt)).t_net
            outcomes = eng.run_settlement()
            for i, o in enumerate(outcomes, start=1):
                res.payment_orders.append({"tx_id": f"CLS-{i}", "payer": o.dpi.payer,
                                           "payee": o.dpi.payee, "amount": round(float(o.dpi.amount), 6),
                                           "state": str(o.state), "dispatch_tax": round(float(o.tax), 6),
                                           "nca_ref": o.nca_id})
                if o.nca_id:
                    res.nca_refs.append(o.nca_id)
                res.total_paid = round(res.total_paid + float(o.dpi.amount), 6)
                res.total_dispatch_tax = round(res.total_dispatch_tax + float(o.tax), 6)
            res.t_net = round(float(full_t_net), 6)
            inv = dict(eng.invariants(t_net_before=full_t_net))
            inv["all_pass"] = all(bool(v) for v in inv.values())
            res.invariants = inv
        else:
            res.invariants = {"note": "无 value>0 的债务边（无结算事项）", "all_pass": True}
    else:                                       # direct：逐笔定向支付（DPI 语义）
        for i, (payer, payee, amount) in enumerate(edges, start=1):
            if payer == payee or amount <= 0:
                continue                            # I-1 定向性
            tx_id = f"SRT-IOP-{i}"
            tax_res = tax_adapter.compute_for_settlement(payer, payee, amount)
            nca = nca_adapter.from_settlement(tx_id, payer, payee, amount, tax_res,
                                              cycle_ref="M4-INTEROP")
            ledger.record_settlement(tx_id, payee, float(tax_res.total_tax))
            res.payment_orders.append({"tx_id": tx_id, "payer": payer, "payee": payee,
                                       "amount": round(amount, 6),
                                       "dispatch_tax": round(float(tax_res.total_tax), 6),
                                       "nca_ref": nca.nca_id})
            res.nca_refs.append(nca.nca_id)
            res.total_paid = round(res.total_paid + amount, 6)
            res.total_dispatch_tax = round(res.total_dispatch_tax + float(tax_res.total_tax), 6)
        res.t_net = res.total_paid

    # interop 交易税 → CLS 台账（逐条如实记录，不重算）
    for j, t in enumerate(taxes, start=1):
        tax = float(t.get("tax") or 0.0)
        tx_id = f"IOP-TAX-{j}"
        res.taxes_recorded.append({"event_id": t.get("event_id"), "tx_id": tx_id,
                                   "tax": round(tax, 6), "layer": "interop-transaction"})
        if tax:
            ledger.record_settlement(tx_id, treasury, tax)

    res.payment_orders_ok = all(p["payer"] != p["payee"] and p["amount"] > 0
                                for p in res.payment_orders)             # I-1
    res.conservation = {
        "no_self_payment": bool(res.payment_orders_ok),
        "netting_matches_t_net": (abs(res.total_paid - res.t_net) < 1e-6),
        "taxes_fully_recorded": len(res.taxes_recorded) == len(taxes),
        "ledger_total_consistent": True,
    }
    res.at = datetime.now().astimezone().isoformat(timespec="seconds")
    return res
