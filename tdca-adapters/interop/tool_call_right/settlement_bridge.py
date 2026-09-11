# -*- coding: utf-8 -*-
"""Shapley 分配落地结算（M2 / #2）——分配表 → CLS 闭环结算 / 分润管线

**动机（SRIGHT-001 §九-2）**：V1.1 的 Shapley 分配仅"随授予存证"，**未落地记账**。
本模块把分配表接到 **CLS 闭环结算管线**（净额 / 定向支付 + 同刻计税 + 台账 + NCA），
使"分配比例 → 实际记账"闭环可核。

两种模式:
  - `mode="direct"`（默认）**逐方定向支付**（DPI 语义）：每方一笔，逐笔计税/记账/存证
  - `mode="netting"`  走 `CLSEngine`（GIM 环销 → RTN 净额 → DVP → 计税 → NCA），
                      并回报 CLS 五不变量 I-1~I-5（口径以 CLS 侧为准，本模块不复算）

纪律:
  - 正和前置：`outcome.granted=False` 或 `positive_sum_delta <= 0` ⇒ 拒（fail-closed）
  - 守恒三律：① Σ分配 = 联盟总效用（按分配表精度容差）② Σ税后净额 + Σ税 = Σ分配
              ③ 各参与方分配额 ≥ 0（负额即拒）
  - **只读复用 CLS**：本模块仅调用 CLS 适配器/引擎，不修改 CLS 任何实现
  - 数据性质: **模拟态**（税率/台账/存证均为模拟态口径）

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

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

DEFAULT_TOLERANCE = 0.01          # 分配表按 4 位小数舍入 → 守恒核验容差（元）
SETTLEMENT_MODES = ("direct", "netting")


class SettlementBridgeError(Exception):
    """分配落地结算纪律违例（正和前置 / 守恒 / 表结构）。"""


@dataclass
class ShareSettlement:
    """单参与方结算明细。"""
    party: str
    gross: float
    tax: float
    net: float
    tx_id: str
    nca_ref: str = ""
    mou_ok: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"party": self.party, "gross": self.gross, "tax": self.tax, "net": self.net,
                "tx_id": self.tx_id, "nca_ref": self.nca_ref, "mou_ok": self.mou_ok,
                "simulated": True}


def _check_allocation(shares: Dict[str, float], expected_total: float,
                      tolerance: float) -> float:
    if not shares:
        raise SettlementBridgeError("分配表为空：无可结算份额（fail-closed）")
    for party, amount in shares.items():
        if not party:
            raise SettlementBridgeError("分配表含空参与方标识")
        if float(amount) < 0:
            raise SettlementBridgeError(f"分配额不得为负（{party}={amount}）")
    total = round(float(sum(float(v) for v in shares.values())), 6)
    if abs(total - float(expected_total)) > tolerance:
        raise SettlementBridgeError(
            f"守恒校验失败：Σ分配={total} 与联盟总效用={expected_total} 不符（容差 {tolerance}）")
    return total


def settle_shares(outcome: Any, *, mode: str = "direct", scene: str = "tool-call",
                  payer: Optional[str] = None, tolerance: float = DEFAULT_TOLERANCE,
                  tax_adapter: Optional[CLSTaxAdapter] = None,
                  ledger: Optional[CLSLedgerAdapter] = None,
                  nca_adapter: Optional[CLSNCAAdapter] = None,
                  engine: Optional[CLSEngine] = None) -> Dict[str, Any]:
    """把 S-Right 授予的 Shapley 分配表落地结算（CLS 定向支付 / 净额）。

    目标函数: 分配比例 → 实际记账（计税 + 台账 + NCA），闭环可核
    约束矩阵: 须 granted 且正和（delta>0）；分配表非空、无负额、Σ=联盟总效用；
              税后净额 + 税 = 分配额（逐方与合计双向核验）
    先验分布: SRIGHT-001 §五（v(S)=Σuᵢ+delta×|S|/n；Σ分配=联盟总效用）｜ CLS 适配器
    配置权边界: L2 场景层（结算映射层；不改变分配与税制）
    预期分配: {"settled","mode","entries","total_gross","total_tax","total_net",
              "conservation_ok","netting_invariants","nca_refs","simulated"}
    审计轨迹: CLS NCA（from_settlement）+ 台账（record_settlement）
    """
    if mode not in SETTLEMENT_MODES:
        raise SettlementBridgeError(f"结算模式须为 {SETTLEMENT_MODES}（当前 {mode!r}）")
    if not getattr(outcome, "granted", False):
        raise SettlementBridgeError("未授予的调用不得落地结算（正和前置 fail-closed）")
    delta = getattr(outcome, "positive_sum_delta", None)
    if delta is None or float(delta) <= 0:
        raise SettlementBridgeError(f"非正和（delta={delta}）不得落地结算")

    shares: Dict[str, float] = {str(k): float(v) for k, v in (outcome.shapley or {}).items()}
    expected = float(getattr(outcome, "coalition_utility", 0.0) or 0.0)
    if expected <= 0:
        raise SettlementBridgeError(
            "缺少联盟总效用锚定值（CallOutcome.coalition_utility）——无法做守恒核验")
    total = _check_allocation(shares, expected, tolerance)
    payer = payer or getattr(outcome, "caller_tdid", None) or "platform"

    tax_adapter = tax_adapter or CLSTaxAdapter()
    ledger = ledger or CLSLedgerAdapter()
    nca_adapter = nca_adapter or CLSNCAAdapter()

    if mode == "direct":
        entries: List[ShareSettlement] = []
        for i, (party, gross) in enumerate(sorted(shares.items()), start=1):
            tx_id = f"SRT-{getattr(outcome, 'grant_id', None) or 'NA'}-{i}"
            tax_res = tax_adapter.compute_for_settlement(payer, party, gross, scene=scene)
            nca = nca_adapter.from_settlement(tx_id, payer, party, gross, tax_res,
                                              cycle_ref="M2-SRIGHT")
            ledger.record_settlement(tx_id, party, float(tax_res.total_tax))
            entries.append(ShareSettlement(party=party, gross=round(gross, 6),
                                           tax=round(float(tax_res.total_tax), 6),
                                           net=round(float(tax_res.net_value), 6),
                                           tx_id=tx_id, nca_ref=nca.nca_id,
                                           mou_ok=bool(tax_res.mou_ok)))
        invariants: Dict[str, Any] = {}
    else:                                     # netting：走 CLS 引擎（GIM → RTN → DVP → 计税 → NCA）
        eng = engine or CLSEngine()
        eng.add_debt_edges([(payer, party, gross) for party, gross in sorted(shares.items())])
        # I-3 基准 = **环销前**全量债务的 T_net（环销不改变 T_net）
        full_t_net = eng.rtn.net(list(eng.network.nodes), dict(eng.network.debt)).t_net
        outcomes = eng.run_settlement()
        entries = []
        for i, o in enumerate(outcomes, start=1):
            dpi = o.dpi
            entries.append(ShareSettlement(
                party=dpi.payee, gross=round(float(dpi.amount), 6), tax=round(float(o.tax), 6),
                net=round(float(dpi.amount) - float(o.tax), 6), tx_id=f"CLS-{i}",
                nca_ref=o.nca_id, mou_ok=True))
        invariants = dict(eng.invariants(t_net_before=full_t_net))
        invariants["all_pass"] = all(bool(v) for v in invariants.values())

    total_gross = round(sum(e.gross for e in entries), 6)
    total_tax = round(sum(e.tax for e in entries), 6)
    total_net = round(sum(e.net for e in entries), 6)
    conservation = {
        "allocation_matches_target": abs(total - expected) <= tolerance,
        "gross_matches_allocation": abs(total_gross - total) <= tolerance,
        "tax_plus_net_equals_gross": abs(total_net + total_tax - total_gross) <= tolerance,
        "non_negative": all(e.gross >= 0 and e.net >= 0 for e in entries),
    }
    ok = all(conservation.values()) and (not invariants or bool(invariants.get("all_pass")))
    return {
        "settled": ok, "mode": mode, "scene": scene, "payer": payer,
        "grant_id": getattr(outcome, "grant_id", None),
        "expected_total": expected, "allocation_total": total,
        "total_gross": total_gross, "total_tax": total_tax, "total_net": total_net,
        "entries": [e.to_dict() for e in entries],
        "conservation": conservation, "conservation_ok": all(conservation.values()),
        "netting_invariants": invariants,
        "nca_refs": [e.nca_ref for e in entries if e.nca_ref],
        "ledger_total_settled": (ledger.total_settled() if mode == "direct" else None),
        "simulated": True,
    }
