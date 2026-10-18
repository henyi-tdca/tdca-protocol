"""CLS 结算引擎编排器（R-CLS-5 E-3 端到端）

全链路: 债务流到达（DRAFTING）→ GIM 环销（MATCHED）→ RTN 净额（NETTED）
        → DPI 定向支付（SETTLED 条件）→ DVP 执行 + 同刻计税 → NCA 存证（RECONCILED）
五不变量 I-1~I-5 全断言
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .models import DebtNetwork, Qualification
from .gim import GIMOnCycle
from .rtn import RTNNetting, NettingResult
from .dpi import CLSStateMachine, DPI, State
from .dvp import DVPExecutor
from .adapters import CLSTaxAdapter, CLSLedgerAdapter, CLSNCAAdapter


@dataclass
class SettlementOutcome:
    """单笔净额结算结果"""
    dpi: DPI
    state: State
    tax: float
    nca_id: str


class CLSEngine:
    """CLS 引擎编排（GIM → RTN → DPI → DVP → NCA）"""

    def __init__(self):
        self.network = DebtNetwork()
        self.gim = GIMOnCycle()
        self.rtn = RTNNetting()
        self.sm = CLSStateMachine()
        self.dvp = DVPExecutor()
        self.tax_adapter = CLSTaxAdapter()
        self.ledger = CLSLedgerAdapter()
        self.nca_adapter = CLSNCAAdapter()
        self.outcomes: List[SettlementOutcome] = []
        self.tx_counter = 0

    def add_debt_edges(self, edges: List[Tuple[str, str, float]]) -> None:
        """债务边批量到达（DRAFTING + GIM 增量环销）"""
        for (u, v, w) in edges:
            self.network.add_debt(u, v, w)
            self.gim.add_edge(u, v, w)

    def run_settlement(self, mou_map: Optional[Dict[str, float]] = None,
                       delivery_map: Optional[Dict[str, bool]] = None,
                       settle_all: bool = True) -> List[SettlementOutcome]:
        """RTN 净额 → DPI → DVP 条件支付 → NCA（全链路结算）
        mou_map: 主体 → MOU 值（缺省全部 >0）
        delivery_map: 主体 → 交付验收（缺省全部 True）
        """
        mou_map = mou_map or {}
        delivery_map = delivery_map or {}
        nodes = list(self.network.nodes)
        r = self.rtn.net(nodes, self.gim.residual_debt())
        outcomes = []
        for (payer, payee, amt) in r.payment_orders:
            self.tx_counter += 1
            tx_id = f"CLS-{self.tx_counter}"
            self.sm.new_transaction(tx_id)
            # DRAFTING → MATCHED → NETTED（全链前段）
            self.sm.transition(tx_id, {"cycle": True})
            self.sm.transition(tx_id, {"netted": True})
            # DPI 定向支付（conditions: C_MOU ∧ C_delivery ∧ C_dpi）
            mou = mou_map.get(payer, 1.0)
            delivery = delivery_map.get(payer, True)
            dpi = DPI(payer=payer, payee=payee, amount=amt,
                      conditions={"C_MOU": mou > 0, "C_delivery": delivery, "C_dpi": True},
                      ref=f"NCA:{tx_id}")
            self.sm.dpis.append(dpi)   # I-1/I-2 断言数据源
            # DVP 条件支付 + 同刻计税（适配器）
            tax = self.tax_adapter.compute_for_settlement(payer, payee, amt)
            dvp_res = self.dvp.conditional_pay(tx_id, dpi, {"mou": mou, "delivery": delivery})
            if dvp_res.state == State.SETTLED:
                self.sm.transition(tx_id, {"settle": True})
                self.sm.transition(tx_id, {"reconciled": True})
                nca = self.nca_adapter.from_settlement(tx_id, payer, payee, amt, tax, cycle_ref="E3")
                self.ledger.record_settlement(tx_id, payer, float(tax.total_tax))
                outcomes.append(SettlementOutcome(dpi, State.RECONCILED, float(tax.total_tax), nca.nca_id))
            else:
                self.sm.transition(tx_id, {"held": True})   # I-5: 异常不中断其他结算
                outcomes.append(SettlementOutcome(dpi, State.HELD, 0.0, ""))
        self.outcomes.extend(outcomes)
        return outcomes

    # ---- 五不变量（I-1~I-5）----
    def invariants(self, t_net_before: Optional[float] = None) -> Dict[str, bool]:
        r = {}
        # I-1 定向性: DPI payer/payee 固定、金额>0、无自由转账
        r["I-1"] = all(d.payer != d.payee and d.amount > 0 for d in self.sm.dpis)
        # I-2 流动性 ≤ T_net: DPI 总额 = T_net（RTN 闭式）
        dpi_total = sum(d.amount for d in self.sm.dpis)
        t_net = self.rtn.net(list(self.network.nodes), self.gim.residual_debt()).t_net
        r["I-2"] = abs(dpi_total - t_net) < 1e-6
        # I-3 净额正确: 环销不改变 T_net（G-1——用全量债务 vs 残余债务）
        if t_net_before is not None:
            r["I-3"] = abs(t_net_before - t_net) < 1e-6
        else:
            full_t_net = self.rtn.net(list(self.network.nodes), dict(self.network.debt)).t_net
            r["I-3"] = abs(full_t_net - t_net) < 1e-6
        # I-4 可审计: 每笔结算有 NCA
        r["I-4"] = len(self.nca_adapter.all_ncas()) >= sum(1 for o in self.outcomes if o.state == State.RECONCILED)
        # I-5 快慢隔离: HELD 存在时仍有 RECONCILED（异常不中断常规）
        settled = sum(1 for o in self.outcomes if o.state == State.RECONCILED)
        held = sum(1 for o in self.outcomes if o.state == State.HELD)
        r["I-5"] = settled > 0 and (held == 0 or settled >= held)
        return r
