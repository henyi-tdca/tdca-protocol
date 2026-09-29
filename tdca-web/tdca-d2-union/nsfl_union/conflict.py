# -*- coding: utf-8 -*-
"""
TDCA D-2 NSFLUnionEngine · 冲突检测（规则级语义匹配，非字符串匹配）
锚定: D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL §五（判定表穷举 + L0 全局基底 + UNKNOWN_CONFLICT + review_queue）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Tuple

from .schema import (Conflict, FuseLevel, MAX_RULES_PER_TYPE, NSLayer,
                     NS_Operator, NS_Rule, NS_Type, Resolution, SceneNSFL,
                     Severity, _severity_rank)


# ---------------------------------------------------------------------------
# 判定表实现（schema §5.2 穷举 + 显式默认 UNKNOWN_CONFLICT）
# ---------------------------------------------------------------------------

def _compare_same_type(a: NS_Rule, b: NS_Rule, _mirrored: bool = False) -> Optional[Conflict]:
    """同 ns_type 规则两两比较，返回冲突（None=无冲突）。判定表 dt-v1.0。

    对称性（红队 FIN-1/R1-01）: 未列组合先尝试反向转调——同对规则交换 A/B 方向结果一致
    （FORBID×ALLOW ≡ ALLOW×FORBID 等），消除顺序博弈面。_mirrored 防递归死循环。
    """
    op_a, op_b = a.operator, b.operator
    sev = Severity.HIGH if (a.is_legal or b.is_legal) else (
        Severity(a.severity.value if _severity_rank(a.severity) >= _severity_rank(b.severity) else b.severity.value))

    def _mk(res: Resolution, reason: str, rv=None) -> Conflict:
        return Conflict(ns_type=a.ns_type, rule_a=a, rule_b=b, severity=sev,
                        resolution=res, reason=reason, resolution_value=rv)

    # —— ALLOW 行 ——
    if op_a == NS_Operator.ALLOW and op_b == NS_Operator.ALLOW:
        if a.parameter is not None and b.parameter is not None and a.parameter != b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN,
                       f"允许域无交集: A={a.parameter} vs B={b.parameter}（ALLOW×ALLOW 参数变体）")
        return None
    if op_a == NS_Operator.ALLOW and op_b == NS_Operator.FORBID:
        return _mk(Resolution.FORBID, f"允许 vs 禁止 → 禁止（任务书例 1 形态）")
    if op_a == NS_Operator.ALLOW and op_b in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN,
                                               NS_Operator.LIMIT_EQ, NS_Operator.RESTRICT_TIER):
        return None  # 限额/档位即允许子集
    # —— FORBID 行 ——
    if op_a == NS_Operator.FORBID and op_b == NS_Operator.FORBID:
        if a.parameter is not None and b.parameter is not None and a.parameter != b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN, f"禁止对象域互斥: A={a.parameter} vs B={b.parameter}")
        return None  # 一致禁止
    if op_a == NS_Operator.FORBID and op_b in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN,
                                               NS_Operator.LIMIT_EQ):
        return None  # 禁止涵盖限额
    if op_a == NS_Operator.FORBID and op_b == NS_Operator.RESTRICT_TIER:
        return _mk(Resolution.FORBID, "禁止 vs 档位约束 → 禁止覆盖档位")
    # —— LIMIT_MAX / LIMIT_MIN / LIMIT_EQ 数值行（取严原则；EMPTY_DOMAIN 拒绝，不取宽）——
    if op_a == NS_Operator.LIMIT_MAX and op_b == NS_Operator.LIMIT_MAX:
        if a.parameter != b.parameter:
            return _mk(Resolution.TAKE_STRICTER, f"限额取严 min({a.parameter},{b.parameter})",
                       min(a.parameter, b.parameter))
        return None
    if op_a == NS_Operator.LIMIT_MIN and op_b == NS_Operator.LIMIT_MIN:
        if a.parameter != b.parameter:
            return _mk(Resolution.TAKE_STRICTER, f"下限取严 max({a.parameter},{b.parameter})",
                       max(a.parameter, b.parameter))
        return None
    if op_a == NS_Operator.LIMIT_MAX and op_b == NS_Operator.LIMIT_MIN:
        if a.parameter < b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN,
                       f"下界 {b.parameter} 高于上界 {a.parameter} → 交集域为空")
        return None
    if op_a == NS_Operator.LIMIT_MIN and op_b == NS_Operator.LIMIT_MAX:
        if a.parameter > b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN,
                       f"下界 {a.parameter} 高于上界 {b.parameter} → 交集域为空")
        return None
    if op_a == NS_Operator.LIMIT_EQ and op_b == NS_Operator.LIMIT_EQ:
        if a.parameter != b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN, f"定值矛盾: A={a.parameter} vs B={b.parameter}")
        return None
    if op_a == NS_Operator.LIMIT_EQ and op_b == NS_Operator.LIMIT_MAX:
        if a.parameter > b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN,
                       f"定值 {a.parameter} 超上限 {b.parameter} → 空域拒绝（不取宽）")
        return None
    if op_a == NS_Operator.LIMIT_EQ and op_b == NS_Operator.LIMIT_MIN:
        if a.parameter < b.parameter:
            return _mk(Resolution.EMPTY_DOMAIN,
                       f"定值 {a.parameter} 低于下限 {b.parameter} → 空域拒绝")
        return None
    if op_a == NS_Operator.LIMIT_MAX and op_b == NS_Operator.LIMIT_EQ:
        return _compare_same_type(b, a)  # 对称
    if op_a == NS_Operator.LIMIT_MIN and op_b == NS_Operator.LIMIT_EQ:
        return _compare_same_type(b, a)
    # —— 档位行 ——
    if op_a == NS_Operator.RESTRICT_TIER and op_b == NS_Operator.RESTRICT_TIER:
        if a.parameter != b.parameter:
            hi = _higher_tier(a.parameter, b.parameter)
            return _mk(Resolution.TIER_ESCALATE,
                       f"档位取严: {a.parameter.value} vs {b.parameter.value} → {hi.value}", hi)
        return None
    if op_a == NS_Operator.RESTRICT_TIER and op_b in (NS_Operator.LIMIT_MAX, NS_Operator.LIMIT_MIN,
                                                      NS_Operator.LIMIT_EQ, NS_Operator.ALLOW):
        return None  # 档位与数值正交
    # —— 未列组合（fail-closed + 对称转调，红队 FIN-1）——
    if not _mirrored:
        swapped = _compare_same_type(b, a, _mirrored=True)
        if swapped is None:
            return None                              # 反向定义为无冲突 → 本方向同样无冲突
        if swapped.resolution != Resolution.UNKNOWN:
            # 反向组合已定义 → 对称镜像（消除 A/B 方向敏感性）
            return Conflict(ns_type=a.ns_type, rule_a=a, rule_b=b,
                            severity=swapped.severity, resolution=swapped.resolution,
                            reason=f"{swapped.reason}（对称转调 {op_b.value}×{op_a.value}）",
                            resolution_value=swapped.resolution_value)
    return _mk(Resolution.UNKNOWN,
               f"未列组合 {op_a.value}×{op_b.value} → UNKNOWN_CONFLICT 上报人工复核（不得静默通过）")


def _higher_tier(t_a: FuseLevel, t_b: FuseLevel) -> FuseLevel:
    order = [FuseLevel.OBSERVE, FuseLevel.SUSPEND, FuseLevel.TEARDOWN, FuseLevel.PERMANENT_BAN]
    return t_a if order.index(t_a) >= order.index(t_b) else t_b


# ---------------------------------------------------------------------------
# L0 全局制度基底（schema §5.1）
# ---------------------------------------------------------------------------

def _legal_global_conflicts(scene_a: SceneNSFL, scene_b: SceneNSFL,
                            conflicts: List[Conflict], review: List[str]) -> None:
    """LEGAL/L0 规则注入每个并集运算，与对侧**非 LEGAL** 规则强制冲突（类型不同不豁免，fail-closed）。

    LEGAL×LEGAL 归同类型判定表（FORBID×FORBID: 一致禁止无冲突 / 参数域互斥 → EMPTY_DOMAIN）。
    规则数硬上限（红队复审 N2）: 任一侧 LEGAL 规则或对侧规则超限 → 跳过并入复核队列（防引擎层 DoS）。
    """
    legal_a, legal_b = scene_a.legal_rules(), scene_b.legal_rules()
    if len(legal_a) > MAX_RULES_PER_TYPE or len(legal_b) > MAX_RULES_PER_TYPE \
            or len(scene_a.rules) > MAX_RULES_PER_TYPE or len(scene_b.rules) > MAX_RULES_PER_TYPE:
        review.append(f"RULE_FLOOD:L0_BASE（规则数超上限 {MAX_RULES_PER_TYPE}，跳过全局基底比较）")
        return
    for la in legal_a:
        for rb in scene_b.rules:
            if rb.is_legal:
                continue
            c = Conflict(ns_type=NS_Type.LEGAL, rule_a=la, rule_b=rb,
                         severity=Severity.HIGH, resolution=Resolution.FORBID,
                         reason=f"L0 全局基底: A LEGAL × B {rb.rule_id} → 强制冲突（ID86 绝对熔断）")
            conflicts.append(c)
    for lb in legal_b:
        for ra in scene_a.rules:
            if ra.is_legal:
                continue
            c = Conflict(ns_type=NS_Type.LEGAL, rule_a=lb, rule_b=ra,
                         severity=Severity.HIGH, resolution=Resolution.FORBID,
                         reason=f"L0 全局基底: B LEGAL × A {ra.rule_id} → 强制冲突（ID86 绝对熔断）")
            conflicts.append(c)


# ---------------------------------------------------------------------------
# 冲突检测器
# ---------------------------------------------------------------------------

@dataclass
class ConflictResult:
    conflict_set: List[Conflict] = field(default_factory=list)
    review_queue: List[str] = field(default_factory=list)


class ConflictDetector:
    """规则级冲突检测：L0 基底 + 同类型判定表 + 跨类型 review_queue + 兜底上报。"""

    def compare(self, scene_a: SceneNSFL, scene_b: SceneNSFL) -> ConflictResult:
        result = ConflictResult()

        # 1. L0 全局基底（schema §5.1）
        _legal_global_conflicts(scene_a, scene_b, result.conflict_set, result.review_queue)

        # 2. 同 ns_type 判定表（schema §5.2）——按类型分组，组内两两比较
        rules_by_type_a: dict = {}
        rules_by_type_b: dict = {}
        for r in scene_a.rules:
            rules_by_type_a.setdefault(r.ns_type, []).append(r)
        for r in scene_b.rules:
            rules_by_type_b.setdefault(r.ns_type, []).append(r)
        for ns_type, list_a in rules_by_type_a.items():
            for list_b_ in [rules_by_type_b.get(ns_type, [])]:
                # 延迟 DoS 防线（红队 #2 #1）: 同类型组规则超上限 → 跳过笛卡尔比较并入复核队列
                if len(list_a) > MAX_RULES_PER_TYPE or len(list_b_) > MAX_RULES_PER_TYPE:
                    result.review_queue.append(
                        f"RULE_FLOOD:{ns_type.value}（规则数超上限 {MAX_RULES_PER_TYPE}，跳过全量比较）")
                    continue
                for ra in list_a:
                    for rb in list_b_:
                        c = _compare_same_type(ra, rb)
                        if c is not None:
                            result.conflict_set.append(c)
                            # UNKNOWN 冲突同步入复核队列（红队 FIN-1: 不得静默 PASS/放行）
                            if c.resolution == Resolution.UNKNOWN:
                                result.review_queue.append(f"UNKNOWN_CONFLICT:{c.reason}")

        # 3. 跨 ns_type 非 L0（schema §5.3）——入 review_queue（不驱动状态机，驱动复核与审计）
        for ns_a, list_a in rules_by_type_a.items():
            for ns_b, list_b in rules_by_type_b.items():
                if ns_a == ns_b or ns_a == NS_Type.LEGAL or ns_b == NS_Type.LEGAL:
                    continue
                result.review_queue.append(
                    f"CROSS_TYPE:{ns_a.value}×{ns_b.value}（阶段 1 简化，待 KG-001 关联矩阵补落）")

        # 4. 兜底上报（schema §5.1 S-09）——含 LEGAL/档位≥TEARDOWN 且 conflict_set 空
        if not result.conflict_set and (scene_a.has_legal_or_high_tier() or scene_b.has_legal_or_high_tier()):
            result.review_queue.append(
                "UNKNOWN_PATH: 场景含 LEGAL/档位≥TEARDOWN 但 conflict_set 为空 → 人工复核（不得自动 PASS）")

        return result
