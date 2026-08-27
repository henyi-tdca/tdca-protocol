# -*- coding: utf-8 -*-
"""用户约束档案 (引擎偏好 = 用户根据自身条件注入, 非 AI 硬编码)
=================================================================================
设计原则 (TDCA 搜索比配 v3):
  - 引擎"偏好"不是写死的: 用户根据自己的条件 (监管强度/上线窗口/预算) 注入一份
    ConstraintProfile, 它定义"什么叫好联盟" (存活阈值/集中度容忍/目标权重/敏感维度)。
  - 智能体拿着这份约束, 把用户条件展开成若干"验证场景", 并行对 Plan A/B/C 做压力验证,
    交叉比对哪个联盟在最多场景下成立 -> 推荐。

这对应场景 COP 的"场景依存效用": 同一引擎, 不同用户条件 -> 不同最优解。
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConstraintProfile:
    """用户根据自身条件注入的约束 (引擎据此评判, 而非自带偏好)"""
    name: str                                   # 条件命名 (用户可读)
    desc: str                                   # 条件描述 (用户为何这么设)
    min_survival_rate: float = 0.9              # 红队平均存活率门槛 (低于即不达标)
    concentration_tolerance: float = 0.6        # 集中度容忍 0..1 (低=不容单点依赖)
    horizon: float = 12.0                       # 滚动再平衡时窗(月)
    objective_weights: Dict[str, float] = field(
        default_factory=lambda: {"v": 0.34, "robustness": 0.33, "cost": 0.33})
    sensitive_dims: List[str] = field(default_factory=list)  # 用户条件下格外脆弱的维


# ---------------- 预设用户条件 (用户可整份采纳或微调, 亦可 --profile-json 自建) ----------------
CONSERVATIVE = ConstraintProfile(
    name="稳健合规型",
    desc="监管严 / 长周期 / 不容单点失效: 用户自身条件要求冗余与高存活, 偏好 Plan B",
    min_survival_rate=1.0,
    concentration_tolerance=0.2,
    horizon=12.0,
    objective_weights={"v": 0.20, "robustness": 0.70, "cost": 0.10},
    sensitive_dims=["合规", "渠道"],
)

SPEED = ConstraintProfile(
    name="快速上线型",
    desc="抢占窗口 / 短周期: 用户自身条件容忍单点依赖, 偏好最大 V (Plan A)",
    min_survival_rate=0.80,
    concentration_tolerance=0.90,
    horizon=6.0,
    objective_weights={"v": 0.70, "robustness": 0.20, "cost": 0.10},
    sensitive_dims=["算力", "模型"],
)

COST = ConstraintProfile(
    name="成本敏感型",
    desc="预算紧: 用户自身条件偏好低 BATNA 和 (Plan C), 中等存活门槛",
    min_survival_rate=0.90,
    concentration_tolerance=0.60,
    horizon=12.0,
    objective_weights={"v": 0.20, "robustness": 0.20, "cost": 0.60},
    sensitive_dims=["资本"],
)

PRESETS: Dict[str, ConstraintProfile] = {
    "conservative": CONSERVATIVE,
    "speed": SPEED,
    "cost": COST,
}


def derive_scenarios(profile: ConstraintProfile, need: List[str]) -> Dict[str, List[str]]:
    """把用户约束档案展开为验证场景 (智能体据此做并行验证)。

    - 红队核心场景: 渠道断裂 / 算力故障 / 数据泄露 + 每维单维失效
    - 用户敏感维度 -> 额外单点压力场景 (用户条件使其格外脆弱)
    - 集中度容忍低 -> 追加'双维并发失效', 进一步压冗余 (验证单点兜底是否真够)
    """
    scen: Dict[str, List[str]] = {
        "渠道断裂": ["渠道"],
        "算力故障": ["算力"],
        "数据泄露": ["数据"],
    }
    for d in need:
        scen[f"单维失效·{d}"] = [d]
    for d in profile.sensitive_dims:
        if d in need:
            scen[f"用户条件敏感·{d}"] = [d]
    if profile.concentration_tolerance < 0.5:
        pair = profile.sensitive_dims[:2] if len(profile.sensitive_dims) >= 2 else need[:2]
        scen["双维并发失效"] = list(pair)
    return scen


def load_profile_json(path: str) -> ConstraintProfile:
    """用户自建约束档案 (--profile-json): 偏好完全由用户定义"""
    import json
    d = json.load(open(path, encoding="utf-8"))
    return ConstraintProfile(
        name=d.get("name", "自定义条件"),
        desc=d.get("desc", "用户自建约束"),
        min_survival_rate=d.get("min_survival_rate", 0.9),
        concentration_tolerance=d.get("concentration_tolerance", 0.6),
        horizon=d.get("horizon", 12.0),
        objective_weights=d.get("objective_weights",
                                {"v": 0.34, "robustness": 0.33, "cost": 0.33}),
        sensitive_dims=d.get("sensitive_dims", []),
    )
