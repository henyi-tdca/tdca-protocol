# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F2 三位一体协调器——创新者/投资者/政府 + Shapley 分配
# 约束矩阵:     任务书 SV-1~7 + KB-ECON-001 §4（Shapley 四性质）+ 开发纪律 3（三方独立审计）
# 先验分布:     任务书 §二 F2 + KB-ECON-001 §4 + 效用精灵 GameTheoryEngine
# 配置权边界:    L2 层；效用精灵只读引用
# 预期分配:     三方协调器 + Shapley 分配 + 审计视图；失败=非法输入拒绝
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F2 三位一体协调器（创新者/投资者/政府 + Shapley 分配）。

制度锚定: 任务书 §二 F2 + KB-ECON-001 §4 | SPDX-License-Identifier: TDCA-Internal

三位一体:
  创新者（技术/场景）：提交场景效用函数、知识产权质押、PUCR 预售
  投资者（资本/资源）：配置权投资、风险分担、收益分配（Shapley）
  政府（制度/PCR）：PCR 初始投入、制度供给、税收锚定、激活系数验收

Shapley 值: φ_i(v) = Σ_{S⊆N\\{i}} [|S|!(|N|−|S|−1)! / |N|!] × [v(S∪{i}) − v(S)]
四性质: 效率性 / 对称性 / Dummy 性 / 可加性（本模块提供验证器）
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, Dict, FrozenSet, List, Optional

TRINITY_ROLES = ("innovator", "investor", "government")
ROLE_LABELS = {"innovator": "创新者", "investor": "投资者", "government": "政府"}


class TrinityCoordinator:
    """三方协调器：配置管理 + Shapley 分配 + 独立审计视图。"""

    def __init__(self) -> None:
        self._profiles: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        role: str,
        did: str,
        contribution: Dict[str, Any],
        reservation_utility: float,
    ) -> Dict[str, Any]:
        """注册三位一体一方（F2 配置）。

        六要素声明:
        目标函数: 注册创新者/投资者/政府三方之一（F2 三位一体配置）
        约束矩阵: 输入——role∈TRINITY_ROLES、did、contribution、reservation_utility≥0；
                  输出——profile；禁止——角色重复注册、负数保留效用、非法角色
        先验分布: 任务书 §二 F2
        配置权边界: L2；注册记录随 NCA 存证
        预期分配: 返回 profile；失败=ValueError
        审计轨迹: 注册动作由调用方 NCA 存证
        """
        if role not in TRINITY_ROLES:
            raise ValueError(f"role 必须为 {'/'.join(TRINITY_ROLES)}，收到 {role!r}")
        if role in self._profiles:
            raise ValueError(f"角色 {role} 已注册（三方独立，不可重复）")
        if not did or not contribution:
            raise ValueError("did 与 contribution 必填")
        if reservation_utility < 0:
            raise ValueError("reservation_utility 必须 ≥ 0")

        profile = {
            "role": role,
            "role_label": ROLE_LABELS[role],
            "did": did,
            "contribution": contribution,
            "reservation_utility": reservation_utility,
        }
        self._profiles[role] = profile
        return profile

    def unregister(self, role: str) -> bool:
        """注销一方（测试用；生产关闭走 SV-4 终止流程）。

        六要素声明:
        目标函数: 移除单方注册（测试/重置用）
        约束矩阵: 输入——role；输出——bool；禁止——生产流程使用（走 SV-4）
        先验分布: 测试隔离需求
        配置权边界: L2；仅测试
        预期分配: 注销成功 True；失败=False（未注册）
        审计轨迹: 测试动作不入 NCA 链
        """
        if role in self._profiles:
            del self._profiles[role]
            return True
        return False

    def profiles(self) -> Dict[str, Dict[str, Any]]:
        """三方配置只读视图（审计用）。

        六要素声明:
        目标函数: 三方配置只读快照（审计）
        约束矩阵: 输入——无；输出——profiles 副本；禁止——直接引用可变内部
        先验分布: 审计需求
        配置权边界: L2；只读
        预期分配: 返回副本；失败=无
        审计轨迹: 只读
        """
        return {k: dict(v) for k, v in self._profiles.items()}

    def audit_view(self, role: str) -> Dict[str, Any]:
        """三方独立审计视图（开发纪律 3：任何一方可独立审计，无单方黑箱）。

        六要素声明:
        目标函数: 提供单方独立审计视图（F2 三方独立审计）
        约束矩阵: 输入——role；输出——该方完整记录 + 其余方摘要；禁止——越权查看他方明细
        先验分布: 任务书 §七（三方独立审计）
        配置权边界: L2；只读
        预期分配: 返回审计视图；失败=ValueError（未注册）
        审计轨迹: 审计动作只读
        """
        if role not in TRINITY_ROLES:
            raise ValueError(f"role 必须为 {'/'.join(TRINITY_ROLES)}")
        if role not in self._profiles:
            raise ValueError(f"角色 {role} 未注册")
        view = {
            "role": role,
            "own": self._profiles[role],
            "peers": [
                {"role": r, "role_label": p["role_label"], "did": p["did"],
                 "reservation_utility": p["reservation_utility"]}
                for r, p in self._profiles.items() if r != role
            ],
        }
        return view

    # ------------------------------------------------------------- Shapley

    def shapley_allocate(
        self,
        coalition_value: Callable[[FrozenSet[str]], float],
    ) -> Dict[str, Any]:
        """Shapley 分配（KB-ECON-001 §4 公式）。

        六要素声明:
        目标函数: 计算三方 Shapley 分配 φ_i（F2 收益分配）
        约束矩阵: 输入——coalition_value（任意子集联合价值函数）；输出——{allocations, total, properties}；
                  禁止——非法子集函数、三方未注册齐
        先验分布: KB-ECON-001 §4（φ_i 公式 + 四性质）
        配置权边界: L2；纯计算
        预期分配: 返回分配 + 四性质验证结果；失败=ValueError
        审计轨迹: 分配过程由调用方 NCA 存证（含 coalition 价值表）
        """
        if set(self._profiles.keys()) != set(TRINITY_ROLES):
            missing = [r for r in TRINITY_ROLES if r not in self._profiles]
            raise ValueError(f"三方未注册齐，缺: {[ROLE_LABELS[r] for r in missing]}")
        players = list(self._profiles.keys())
        n = len(players)

        allocations: Dict[str, float] = {}
        for i in players:
            others = [p for p in players if p != i]
            phi = 0.0
            for r in range(n):
                for subset in itertools.combinations(others, r):
                    s = frozenset(subset)
                    w = (math.factorial(r) * math.factorial(n - r - 1)) / math.factorial(n)
                    phi += w * (coalition_value(s | {i}) - coalition_value(s))
            allocations[i] = round(phi, 6)

        total_value = coalition_value(frozenset(players))
        props = self._verify_properties(allocations, coalition_value, total_value)
        return {
            "allocations": allocations,
            "total_value": round(total_value, 6),
            "sum_allocations": round(sum(allocations.values()), 6),
            "properties": props,
        }

    def verify_additivity(self, v1: Callable[[FrozenSet[str]], float], v2: Callable[[FrozenSet[str]], float]) -> bool:
        """可加性验证（Shapley 四性质之一）：φ(v1+v2) = φ(v1) + φ(v2)。

        六要素声明:
        目标函数: 独立验证可加性（KB-ECON-001 §4）
        约束矩阵: 输入——v1/v2 两个联合价值函数；输出——bool；禁止——单函数验证
        先验分布: KB-ECON-001 §4 四性质
        配置权边界: L2；纯计算
        预期分配: 返回可加性是否成立；失败=ValueError（三方未注册齐）
        审计轨迹: 验证结果由调用方 NCA 存证
        """
        r1 = self.shapley_allocate(v1)
        r2 = self.shapley_allocate(v2)

        def v12(s: FrozenSet[str]) -> float:
            return v1(s) + v2(s)

        r12 = self.shapley_allocate(v12)
        return all(
            abs(r12["allocations"][p] - (r1["allocations"][p] + r2["allocations"][p])) < 1e-6
            for p in self._profiles
        )

    def _verify_properties(
        self,
        allocations: Dict[str, float],
        v: Callable[[FrozenSet[str]], float],
        total_value: float,
    ) -> Dict[str, bool]:
        """Shapley 四性质验证（KB-ECON-001 §4）。"""
        players = list(allocations.keys())
        # 效率性: Σφ_i = v(N)
        efficiency = abs(sum(allocations.values()) - total_value) < 1e-6
        # 对称性: 若 i,j 同构（对任意 S⊆N\{i,j}，v(S∪{i})=v(S∪{j})），则 φ_i=φ_j
        # 遍历全子集（含第三方的子集）——修复漏检窗口
        symmetry = True
        for i, j in itertools.combinations(players, 2):
            symmetric = True
            others = [p for p in players if p not in (i, j)]
            for r in range(len(players) - 1):  # 0..n-2：空集 + 含第三方子集（n=3 → 空集+单元素）
                for subset in itertools.combinations(others, r):
                    s = frozenset(subset)
                    if abs(v(s | {i}) - v(s | {j})) > 1e-6:
                        symmetric = False
                        break
                if not symmetric:
                    break
            if symmetric and abs(allocations[i] - allocations[j]) > 1e-6:
                symmetry = False
        # Dummy 性: 若 i 对任何 S 无边际贡献，则 φ_i=0
        dummy = True
        for i in players:
            others = [p for p in players if p != i]
            is_dummy = True
            for r in range(len(players)):
                for subset in itertools.combinations(others, r):
                    s = frozenset(subset)
                    if abs(v(s | {i}) - v(s)) > 1e-6:
                        is_dummy = False
                        break
                if not is_dummy:
                    break
            if is_dummy and abs(allocations[i]) > 1e-6:
                dummy = False
        # 可加性: 需双价值函数独立验证（见 verify_additivity）；此处不硬编码
        return {
            "efficiency": efficiency,
            "symmetry": symmetry,
            "dummy": dummy,
            "additivity": "verify_via_verify_additivity",
        }
