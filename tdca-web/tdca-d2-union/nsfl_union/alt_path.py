# -*- coding: utf-8 -*-
"""
TDCA D-2 NSFLUnionEngine · Alt-Path 五元拓扑绕行（schema §九 N4）
对外契约 recommended_alt_path: Optional[List[str]]（MASTER 契约，零变更）；
AltPathCandidate 为引擎内部计算结构（详情进 nca_ref 审计轨迹）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from .schema import AltPathCandidate, SceneNSFL

if TYPE_CHECKING:
    from .engine import NSFLUnionEngine


class AltPathPlanner:
    """五元拓扑最短路径：寻找绕行场景 C 使 NS_A∪NS_C 与 NS_C∪NS_B 冲突更少（任务书 §三.4）。"""

    REGISTRY_MAX = 100   # 红队 FIN-8: 候选注册表上限

    def __init__(self, top_n: int = 3):
        self.top_n = top_n
        self.registry_max = self.REGISTRY_MAX

    def find_alt_paths(self, scene_a: SceneNSFL, scene_b: SceneNSFL,
                       registry: List[SceneNSFL], engine: "NSFLUnionEngine",
                       base_conflicts: int, base_premium: float) -> List[AltPathCandidate]:
        """遍历候选场景注册表，产出绕行候选（按总冲突数/溢价升序取前 N）。
        registry 候选数上限（红队 FIN-8）: 防超大规模注册表构成计算 DoS。
        """
        candidates: List[AltPathCandidate] = []
        for c in registry[: self.registry_max]:
            if c.scene_id in (scene_a.scene_id, scene_b.scene_id):
                continue
            u_ac = engine.compute(scene_a, c, compute_alt_path=False)
            u_cb = engine.compute(c, scene_b, compute_alt_path=False)
            total_conflicts = len(u_ac.conflict_set) + len(u_cb.conflict_set)
            total_premium = round((u_ac.risk_premium + u_cb.risk_premium) / 2.0, 4)
            if total_conflicts < base_conflicts or (
                    total_conflicts == base_conflicts and total_premium < base_premium):
                candidates.append(AltPathCandidate(
                    scene_c_id=c.scene_id,
                    union_ac_conflicts=len(u_ac.conflict_set),
                    union_cb_conflicts=len(u_cb.conflict_set),
                    total_risk_premium=total_premium,
                    rationale=(f"绕行 {c.scene_id}: 冲突 {base_conflicts}→{total_conflicts}, "
                               f"溢价 {base_premium}→{total_premium}"),
                ))
        candidates.sort(key=lambda x: (x.union_ac_conflicts + x.union_cb_conflicts,
                                       x.total_risk_premium))
        return candidates[: self.top_n]
