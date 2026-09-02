# -*- coding: utf-8 -*-
"""Coalition Feasibility Checker — 合作可行性校验器（研发治理包通用版 GK-12 配套）

核心：在协作/联盟正式成立（签发记录）之前，数学证明
      ∀成员 φ_i ≥ BATNA_i（φ=Shapley 贡献分配，BATNA=成员的保留收益/外部选择）。
φ < BATNA 的成员必须在可行性校验阶段被拦截（NOT_FEASIBLE），
不得「计算但放行」——事后发现亏方正是协作失败最常见根因。

浮点容差：EPS = 1e-9（实测 IEEE754 噪声 ~1e-14；EPS 仅吸收尾差，
真实亏方 φ 低于 BATNA 超 1e-9 仍被拦截——误拦消除且不牺牲拦截能力）。

语义：地板不是天花板——可验证收益下限是协作可持续的最低信号；
不满足即拦截（fail-closed：宁可误拦不可漏放）。
"""
from itertools import combinations
from math import factorial
from dataclasses import dataclass, field
from typing import Callable, Dict, Set, FrozenSet
import sys
sys.stdout.reconfigure(encoding='utf-8')

EPS = 1e-9


@dataclass
class FeasibilityResult:
    status: str                     # FEASIBLE / NOT_FEASIBLE / MEMBER_DENIED
    shares: Dict[str, float] = field(default_factory=dict)
    below_reservation: Set[str] = field(default_factory=set)
    suggestion: str = ""
    record_emitted: bool = False    # φ<BATNA 时必为 False
    marker: str = ""                # [FAILED] / [ACTIVE] / [DENIED]


def exact_shapley(v: Callable[[FrozenSet], float], players: Set[str]) -> Dict[str, float]:
    """精确 Shapley 值（|N|=n），协作贡献公平分配"""
    n = len(players)
    phi = {p: 0.0 for p in players}
    for p in players:
        others = [q for q in players if q != p]
        for r in range(len(others) + 1):
            for S in combinations(others, r):
                S = frozenset(S)
                w = factorial(len(S)) * factorial(n - len(S) - 1) / factorial(n)
                phi[p] += w * (v(S | {p}) - v(S))
    return phi


def _membership_check(admitted: Set[str] | None, candidates: Set[str]) -> Set[str]:
    """准入层：未准入（未通过资格预检）的候选被拒绝"""
    return {c for c in candidates if c not in admitted} if admitted is not None else set()


def check_coalition(
    candidates: Set[str],
    batna: Dict[str, float],
    v: Callable[[FrozenSet], float],
    admitted: Set[str] | None = None,
) -> FeasibilityResult:
    """合作可行性硬约束网关。

    四步不可断裂：
      1. 准入预检（未准入成员拒绝）
      2. 计算精确 Shapley 贡献分配
      3. 逐成员校验 φ_i ≥ BATNA_i（带 EPS 容差）
      4. φ<BATNA → 拒绝签发记录（不可「计算但放行」）
    """
    # 1. 准入预检
    denied = _membership_check(admitted, candidates)
    if denied:
        return FeasibilityResult(
            status="MEMBER_DENIED",
            below_reservation=denied,
            suggestion="未通过资格预检的成员不可入盟",
            record_emitted=False,
            marker="[DENIED]",
        )

    # 2. 精确 Shapley
    phi = exact_shapley(v, candidates)

    # 3. 逐成员硬校验（带 EPS 容差）
    infeasible = {i for i in candidates if phi[i] < batna[i] - EPS}

    # 4. φ<BATNA → 拦截，不签发
    if infeasible:
        return FeasibilityResult(
            status="NOT_FEASIBLE",
            shares=phi,
            below_reservation=infeasible,
            suggestion="调整价值函数 / 剔除高保留收益成员 / 引入新互补维度",
            record_emitted=False,
            marker="[FAILED]",
        )

    return FeasibilityResult(
        status="FEASIBLE",
        shares=phi,
        record_emitted=True,
        marker="[ACTIVE]",
    )


if __name__ == "__main__":
    # ===== 自测（smoke）：边界语义 + 拦截能力 + 真实数据回归 =====
    def additive_V(phi: dict):
        def V(S):
            return float(sum(phi[i] for i in S))
        return V

    n_pass = n_fail = 0

    def check(name, cond, detail=""):
        global n_pass, n_fail
        if cond:
            n_pass += 1
            print(f"  ✅ {name}")
        else:
            n_fail += 1
            print(f"  ❌ {name} — {detail}")

    print("== A. 边界语义（严格小于 + EPS 容差）==")
    r = check_coalition({"a", "b"}, {"a": 150.0, "b": 150.0}, additive_V({"a": 150.0, "b": 150.0}))
    check("A1 φ=BATNA 恰好相等 → FEASIBLE", r.status == "FEASIBLE" and r.record_emitted, r.status)
    r = check_coalition({"a", "b"}, {"a": 150.1, "b": 150.0}, additive_V({"a": 150.0, "b": 150.0}))
    check("A2 φ=BATNA−0.1 真实亏方 → NOT_FEASIBLE", r.status == "NOT_FEASIBLE" and not r.record_emitted, r.status)
    r = check_coalition({"a", "b"}, {"a": 150.0 + 1e-9, "b": 150.0}, additive_V({"a": 150.0, "b": 150.0}))
    check("A3 φ=BATNA−1e-9 EPS 边界内 → FEASIBLE", r.status == "FEASIBLE", r.status)

    print("== B. 准入预检 + 熔断语义 ==")
    r = check_coalition({"a", "b"}, {"a": 100.0, "b": 100.0}, additive_V({"a": 150.0, "b": 150.0}), admitted={"a"})
    check("B1 未准入成员 → MEMBER_DENIED", r.status == "MEMBER_DENIED" and not r.record_emitted, r.status)
    r = check_coalition({"a", "b"}, {"a": 100.0, "b": 100.0}, additive_V({"a": 150.0, "b": 40.0}))
    check("B2 亏方联盟 → NOT_FEASIBLE", r.status == "NOT_FEASIBLE" and not r.record_emitted, r.status)

    print("== C. 真实数据回归（三方协作实测值）==")
    pr = {"A": 54.20, "B": 67.40, "C": 47.70}
    br = {"A": 50.0, "B": 42.0, "C": 38.0}
    r = check_coalition(set(pr), br, additive_V(pr))
    check("C1 三方均≥保留收益 → FEASIBLE（与实测结论一致）", r.status == "FEASIBLE", r.status)
    bcf = dict(br); bcf["C"] = 50.0
    r = check_coalition(set(pr), bcf, additive_V(pr))
    check("C2 反事实（C 保留收益抬升）→ NOT_FEASIBLE", r.status == "NOT_FEASIBLE" and "C" in r.below_reservation, r.status)

    print(f"\n== 自测结果: {n_pass}/{n_pass + n_fail} 通过 ==")
    raise SystemExit(1 if n_fail else 0)
