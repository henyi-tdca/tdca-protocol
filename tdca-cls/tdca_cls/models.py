"""CLS 多边债务网络图模型（R-CLS-1 定义 1-3/5/6）

G = (V, E, W, S)：主体集 / 债务边 / 边权 / 场景标签
节点资格状态 q ∈ {ACTIVE, FROZEN(T-036-L2), DEMOTED(T-037), REVOKED(T-037)}
微交付域边界（定义 5）: 微交付不在 CLS 场景——本引擎只处理 CLS 核心域（B 端供应链金融）
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple


class Qualification(str, Enum):
    ACTIVE = "ACTIVE"          # 正常参与
    FROZEN = "FROZEN"          # T-036-L2 账户冻结（连续 3 笔 MOU≤0）
    DEMOTED = "DEMOTED"        # T-037 降级（L2 整改不合格升级 / 重大过错）
    REVOKED = "REVOKED"        # T-037 取消资格


@dataclass
class DebtNetwork:
    """多边债务网络（定义 1-3）"""
    nodes: set = field(default_factory=set)
    debt: Dict[Tuple[str, str], float] = field(default_factory=dict)   # (u,v) -> w, u 欠 v
    scenes: Dict[str, str] = field(default_factory=dict)               # node -> scene 标签
    qualification: Dict[str, Qualification] = field(default_factory=dict)

    def add_node(self, node: str, scene: str = "default") -> None:
        self.nodes.add(node)
        self.scenes.setdefault(node, scene)
        self.qualification.setdefault(node, Qualification.ACTIVE)

    def add_debt(self, u: str, v: str, w: float) -> None:
        """债务边 u→v 到达（DRAFTING）"""
        assert w > 0, "债务金额必须为正"
        self.add_node(u)
        self.add_node(v)
        # 资格校验：REVOKED 主体不能产生新债务（R-CLS-1 待批判点 5：PENALIZED 与新债务互斥）
        assert self.qualification[u] != Qualification.REVOKED, f"主体 {u} 已取消清算资格（T-037）"
        assert self.qualification[v] != Qualification.REVOKED, f"主体 {v} 已取消清算资格（T-037）"
        self.debt[(u, v)] = self.debt.get((u, v), 0.0) + w

    def net_position(self, node: str) -> float:
        """净头寸 N_i = 应收 - 应付（定义 2）"""
        recv = sum(w for (a, b), w in self.debt.items() if b == node)
        pay = sum(w for (a, b), w in self.debt.items() if a == node)
        return recv - pay

    def t_full(self) -> float:
        """全额结算流动 T_full = ΣD_ij"""
        return sum(self.debt.values())

    def t_net(self) -> float:
        """净额轧差 T_net = Σmax(0,−N_i)（定理 R2-1：P3*=T_net）"""
        return sum(max(0.0, -self.net_position(n)) for n in self.nodes)
