"""RTN 净额引擎（R-CLS-2 FROZEN：定理 R2-1 P3*=T_net）

净头寸闭式：T_net = Σmax(0, −N_i)（最小流动性，无需 LP）
净额指令：净应付者 → 净应收者的定向支付（DPI 输入）
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class NettingResult:
    """RTN 净额结果"""
    net_positions: Dict[str, float]          # N_i
    t_net: float                             # 最小流动性 P3* = T_net
    t_full: float                            # 全额结算流动
    utilization: float                       # 资金利用率提升率 U = 1 − T_net/T_full
    payment_orders: List[Tuple[str, str, float]]  # (净应付者, 净应收者, 金额) 定向支付


class RTNNetting:
    """RTN 实时轧差引擎（R-CLS-2）"""

    def net(self, nodes, debt) -> NettingResult:
        n = {x: 0.0 for x in nodes}
        for (u, v), w in debt.items():
            n[u] -= w          # u 应付
            n[v] += w          # v 应收
        t_net = sum(max(0.0, -v) for v in n.values())
        t_full = sum(debt.values())
        # 净额定向支付：净应付者总额 = 净应收者总额（守恒）
        payers = [(x, -v) for x, v in n.items() if v < -1e-9]     # 净应付
        receivers = [(x, v) for x, v in n.items() if v > 1e-9]    # 净应收
        orders = []
        i = j = 0
        # 简单配对（多对多净额：payer 群 → receiver 群）
        while i < len(payers) and j < len(receivers):
            p_name, p_amt = payers[i]
            r_name, r_amt = receivers[j]
            pay = min(p_amt, r_amt)
            orders.append((p_name, r_name, round(pay, 6)))
            payers[i] = (p_name, round(p_amt - pay, 6))
            receivers[j] = (r_name, round(r_amt - pay, 6))
            if payers[i][1] <= 1e-9:
                i += 1
            if receivers[j][1] <= 1e-9:
                j += 1
        u = 1 - t_net / t_full if t_full > 0 else 1.0
        return NettingResult(net_positions=n, t_net=t_net, t_full=t_full,
                             utilization=u, payment_orders=orders)
