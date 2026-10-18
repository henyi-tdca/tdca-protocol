# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F5 五阶资产化合引擎——CHEM-001~004 + ENG-003 最小化合检查器
# 约束矩阵:     任务书 SV-5（化合须过最小化合检查）+ KB-ECON-001 §8（化学热力学模型）
# 先验分布:     任务书 §二 F5 + KB-ECON-001 §8 + M1 eng003_log 预埋位
# 配置权边界:    L2 层；ENG-003 物理叠加优先
# 预期分配:     化合/分离/催化剂/抑制剂 + ENG-003 检查日志；失败=非正和/叠加足够拒绝
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F5 五阶资产化合引擎（CHEM-001~004 + ENG-003 最小化合检查器）。

制度锚定: 任务书 §二 F5 + SV-5 + KB-ECON-001 §8 | SPDX-License-Identifier: TDCA-Internal

CHEM-001 正向化合: 五阶资产 + 配置权调用(活化能) → NCA + 效用剩余
CHEM-002 反向分离: NCA 析构（高成本，需法律仲裁/治理介入）
CHEM-003 催化剂场: TDCA 协议网络降低正向活化能
CHEM-004 反应抑制剂: NSFL 阻止非正和方向化合

ENG-003 最小化合检查器（SV-5）: 每次化合前自动判定——物理叠加是否足够？
三条件: 不可拆分性 / 涌现价值 / 非线性 —— 任一成立 → 化合必要；否则物理叠加优先
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

# 五阶资产类型（KB-ECON-001 §8 / 任务书 §二 F5）
FIVE_ASSET_TYPES = ("IP", "knowledge", "exchange", "scene_weight", "cognitive_nca")

# ENG-003 三条件（任一成立 → 化合必要）
ENG003_CONDITIONS = ("indivisible", "emergent", "nonlinear")
ENG003_LABELS = {
    "indivisible": "不可拆分性（资产无法物理叠加复制）",
    "emergent": "涌现价值（组合产生新效用）",
    "nonlinear": "非线性（效用非简单加和）",
}

BASE_ACTIVATION_ENERGY = 100.0  # 基准活化能（制度成本单位）
CATALYST_FACTOR = 0.6  # CHEM-003 催化剂场降低活化能至 60%


def eng003_min_compound_check(
    assets: List[str],
    conditions: Dict[str, bool],
    justification: str = "",
) -> Dict[str, Any]:
    """ENG-003 最小化合检查器（SV-5：物理叠加优先，必要才化合）。

    六要素声明:
    目标函数: 判定化合必要性（ENG-003）——三条件检验，物理叠加优先
    约束矩阵: 输入——assets（五阶资产）、conditions（三条件证据）；
              输出——{required, physically_composable, conditions, justification}；
              禁止——非法条件键、缺证据（无 justification）放行
    先验分布: 任务书 §二 F5（ENG-003 检查器）+ KB-ECON-001 §8（物理叠加优先）
    配置权边界: L2；判定记录随化合 NCA 存证
    预期分配: 返回检查结果；失败=ValueError
    审计轨迹: 检查日志写入沙盒 eng003_log（M1 预埋位启用）
    """
    for a in assets:
        if a not in FIVE_ASSET_TYPES:
            raise ValueError(f"非法五阶资产类型 {a!r}，允许: {'/'.join(FIVE_ASSET_TYPES)}")
    if set(conditions.keys()) != set(ENG003_CONDITIONS):
        raise ValueError(f"conditions 必须含三条件 {'/'.join(ENG003_CONDITIONS)}")
    if not justification:
        raise ValueError("ENG-003 判定必须附 justification（可审计）")

    required = any(conditions.values())
    return {
        "required": required,  # True=化合必要；False=物理叠加足够
        "physically_composable": not required,  # 物理叠加是否可行
        "conditions": {k: {"triggered": v, "label": ENG003_LABELS[k]} for k, v in conditions.items()},
        "justification": justification,
        "decision": "化合必要（ENG-003 三条件触发）" if required else "物理叠加优先（不化合）",
    }


def chem_combine(
    sandbox_id: str,
    assets: List[str],
    config_right_token: str,
    eng003: Dict[str, Any],
    utility_surplus: float,
    catalyst: bool = False,
) -> Dict[str, Any]:
    """CHEM-001 正向化合：五阶资产 + 配置权调用 → NCA + 效用剩余。

    六要素声明:
    目标函数: 正向化合（CHEM-001）——五阶资产组合生成新效用（含 ENG-003 前置）
    约束矩阵: 输入——assets/config_right_token/eng003 检查结果/utility_surplus（正和验证产出）；
              输出——反应记录 + 产品 NCA 引用；禁止——ENG-003 required=False 化合（物理叠加优先）、
              surplus≤0 化合（非正和，CHEM-004 抑制剂）
    先验分布: 任务书 §二 F5 + KB-ECON-001 §8 + F6 正和验证（surplus 来源）
    配置权边界: L2；化合调用随 NCA 存证
    预期分配: 返回化合记录；失败=ValueError（叠加足够/非正和）
    审计轨迹: 化合记录经 SBX_CHEM_COMBINE NCA 存证（含 eng003 判定）
    """
    if not eng003.get("required"):
        raise ValueError(f"ENG-003 判定为物理叠加优先，拒绝化合（SV-5）: {eng003.get('decision')}")
    if utility_surplus <= 0:
        raise ValueError(f"效用剩余 ≤ 0（非正和），CHEM-004 抑制剂阻断化合: surplus={utility_surplus}")

    energy = BASE_ACTIVATION_ENERGY * (CATALYST_FACTOR if catalyst else 1.0)
    return {
        "reaction_id": f"rx:{uuid.uuid4().hex}",
        "chem_type": "CHEM-001",
        "sandbox_id": sandbox_id,
        "assets": list(assets),
        "config_right_token": config_right_token,
        "activation_energy": round(energy, 2),
        "catalyst_applied": catalyst,
        "utility_surplus": round(utility_surplus, 6),
        "product_nca": None,  # 由调用方生成 NCA 后回填
        "status": "combined",
    }


def chem_separate(
    sandbox_id: str,
    nca_id: str,
    governance_ref: str,
    separation_cost: float,
) -> Dict[str, Any]:
    """CHEM-002 反向分离：NCA 析构（高成本，需法律仲裁/治理介入）。

    六要素声明:
    目标函数: 反向分离（CHEM-002）——NCA 析构，需治理介入
    约束矩阵: 输入——nca_id/governance_ref 必填、separation_cost>0；输出——分离记录；
              禁止——无治理引用、非正成本
    先验分布: 任务书 §二 F5（反向分离高成本，需法律仲裁/治理介入）
    配置权边界: L2；分离为高成本操作，须治理引用
    预期分配: 返回分离记录（待治理确认）；失败=ValueError
    审计轨迹: 分离请求经 NCA 存证
    """
    if not nca_id or not governance_ref:
        raise ValueError("nca_id 与 governance_ref 必填（反向分离需治理介入）")
    if separation_cost <= 0:
        raise ValueError("separation_cost 必须 > 0")
    return {
        "reaction_id": f"sep:{uuid.uuid4().hex}",
        "chem_type": "CHEM-002",
        "sandbox_id": sandbox_id,
        "nca_id": nca_id,
        "governance_ref": governance_ref,
        "separation_cost": separation_cost,
        "status": "pending_governance",  # 待治理确认（人类裁决）
    }


def catalyst_field(effective_energy: float) -> Dict[str, Any]:
    """CHEM-003 催化剂场：协议网络降低正向活化能。

    六要素声明:
    目标函数: 催化剂场计算（CHEM-003）——协议网络降低活化能
    约束矩阵: 输入——effective_energy>0；输出——催化因子应用结果；禁止——负能量
    先验分布: 任务书 §二 F5（催化剂场）
    配置权边界: L2
    预期分配: 返回催化结果；失败=ValueError
    审计轨迹: 随化合 NCA 存证
    """
    if effective_energy <= 0:
        raise ValueError("effective_energy 必须 > 0")
    return {
        "chem_type": "CHEM-003",
        "base_energy": effective_energy,
        "catalyst_factor": CATALYST_FACTOR,
        "reduced_energy": round(effective_energy * CATALYST_FACTOR, 2),
        "status": "catalyzed",
    }


def inhibitor_check(nsfl_hit: bool, reason: str = "") -> Dict[str, Any]:
    """CHEM-004 反应抑制剂：NSFL 阻止非正和方向化合。

    六要素声明:
    目标函数: 抑制剂判定（CHEM-004）——NSFL 非正和阻断
    约束矩阵: 输入——nsfl_hit、reason；输出——{blocked, reason}；禁止——命中却放行
    先验分布: 任务书 §二 F5（NSFL 阻止非正和化合）+ KB-ECON-001 §8
    配置权边界: L2；阻断为硬约束（SV-3 方向）
    预期分配: 返回阻断判定；失败=无
    审计轨迹: 阻断记录随 NCA 存证（negative_space_check）
    """
    return {
        "chem_type": "CHEM-004",
        "blocked": nsfl_hit,
        "reason": reason if nsfl_hit else "未命中 NSFL，化合方向允许",
        "status": "BLOCKED" if nsfl_hit else "ALLOW",
    }
