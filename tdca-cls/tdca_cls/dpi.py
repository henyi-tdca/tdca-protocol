"""DPI 定向支付指令 + CLS 协议状态机（R-CLS-1 FROZEN）

DPI 原语（定义 4）: (payer, payee, amount, conditions, ref)——payer/payee 固定（I-1 定向性）
状态机（§3.1-3.2）: DRAFTING→MATCHED→NETTED→SETTLED→RECONCILED + HELD/ESCALATED/DISPUTED/INSURED/PENALIZED
条件: C_MOU(>0, ID79) ∧ C_delivery ∧ C_dpi（M3 修订：MOU>0 统一）
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class State(str, Enum):
    DRAFTING = "DRAFTING"      # 债务登记（GIM 待检测）
    MATCHED = "MATCHED"        # 环匹配（GIM-OnCycle 命中）
    NETTED = "NETTED"          # RTN 净额（DPI 生成）
    SETTLED = "SETTLED"        # DVP 定向支付完成
    RECONCILED = "RECONCILED"  # 对账 + NCA（终态）
    HELD = "HELD"              # 条件不满足挂起
    ESCALATED = "ESCALATED"    # 转慢系统（超时/异常上报）
    DISPUTED = "DISPUTED"      # 争议（M3 修订：HELD/ESCALATED 进入源）
    INSURED = "INSURED"        # 保险介入
    PENALIZED = "PENALIZED"    # T-037 资格惩罚


@dataclass
class DPI:
    """定向支付指令（定义 4 · 清算动作原语）"""
    payer: str
    payee: str
    amount: float
    conditions: Dict[str, bool]   # 可编程条件（C_MOU/C_delivery/C_dpi/...）
    ref: str = ""                 # 关联环/NCA 编号

    def check(self) -> bool:
        """条件求值（可编程布尔表达式——本原型为字段布尔合取）"""
        return all(self.conditions.values())


class CLSStateMachine:
    """CLS 交易级状态机（R-CLS-1 §3.1-3.2）"""

    def __init__(self):
        self.states: Dict[str, State] = {}
        self.dpis: List[DPI] = []
        self.nca_log: List[str] = []          # I-4 可审计（NCA 存证轨迹）

    def new_transaction(self, tx_id: str) -> None:
        self.states[tx_id] = State.DRAFTING
        self.nca_log.append(f"NCA:{tx_id}:DRAFTING")

    def transition(self, tx_id: str, cond: Dict[str, bool]) -> State:
        """按条件转移（cond: 触发条件集）"""
        s = self.states.get(tx_id, State.DRAFTING)
        if s == State.DRAFTING and cond.get("cycle"):
            self.states[tx_id] = State.MATCHED
            self.nca_log.append(f"NCA:{tx_id}:MATCHED")
        elif s == State.MATCHED and cond.get("netted"):
            self.states[tx_id] = State.NETTED
            self.nca_log.append(f"NCA:{tx_id}:NETTED")
        elif s == State.NETTED and cond.get("settle"):
            self.states[tx_id] = State.SETTLED
            self.nca_log.append(f"NCA:{tx_id}:SETTLED")
        elif s == State.NETTED and cond.get("held"):
            self.states[tx_id] = State.HELD
            self.nca_log.append(f"NCA:{tx_id}:HELD")
        elif s == State.SETTLED and cond.get("reconciled"):
            self.states[tx_id] = State.RECONCILED
            self.nca_log.append(f"NCA:{tx_id}:RECONCILED")
        elif s == State.SETTLED and cond.get("mismatch"):
            self.states[tx_id] = State.ESCALATED
            self.nca_log.append(f"NCA:{tx_id}:ESCALATED")
        elif s in (State.HELD, State.ESCALATED) and cond.get("dispute"):
            self.states[tx_id] = State.DISPUTED        # M3 修订：DISPUTED 进入源补全
            self.nca_log.append(f"NCA:{tx_id}:DISPUTED")
        elif s == State.DISPUTED and cond.get("fault"):
            self.states[tx_id] = State.PENALIZED       # 过错方 → T-037
            self.nca_log.append(f"NCA:{tx_id}:PENALIZED")
        elif s == State.DISPUTED and cond.get("no_fault"):
            self.states[tx_id] = State.INSURED         # 非过错 → 保险
            self.nca_log.append(f"NCA:{tx_id}:INSURED")
        return self.states[tx_id]

    def state_of(self, tx_id: str) -> State:
        return self.states.get(tx_id, State.DRAFTING)

    # ---- 五不变量（I-1~I-5）----
    def invariant_directionality(self) -> bool:
        """I-1 定向性: 所有支付为 DPI（payer/payee 固定），无自由转账"""
        return all(d.payer != d.payee and d.amount > 0 for d in self.dpis)

    def invariant_auditability(self) -> bool:
        """I-4 可审计: 每步 NCA 存证"""
        return len(self.nca_log) >= len(self.states) * 1  # 每交易至少 1 条

    def settle_via_dpi(self, dpi: DPI) -> State:
        """DPI 定向支付（SETTLED 步）：条件全部满足才放行"""
        self.dpis.append(dpi)
        if dpi.check():
            return State.SETTLED
        return State.HELD
