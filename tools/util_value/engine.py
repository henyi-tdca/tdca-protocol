"""util_value · 数字版权资产效用价值评估引擎（DCD-UTIL-VALUE-001 M1 评估引擎）

核心依据（复用已建立基座）:
  - TDCA-UTILITY-OBSERVABLE-001: U_observed = Σ(销项票 + 进项票) = 真实交易总额
    = 总效用的可观测下限（显示性偏好，萨缪尔森 1938）
  - MOU 本体论正解（MEMO-006-Audit）: MOU 是地板不是天花板——只输出可观测下限，
    禁止输出主观估值（天花板语义）
  - NS-007 函数七要素: 版权资产函数化度量分解框架（ID68）
  - 五阶效用理论: IP / 知识 / 交换 / 场景权重 / 认知 NCA 分层评估（权重可配）

数据纪律（ID92）: 真实交易数据按来源标注；合成数据 SIMULATED，绝不冒充。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 五阶效用分层（DCD-UTIL-VALUE-001 §三）
TIER_ORDER = ("ip", "knowledge", "exchange", "scenario", "cognitive_nca")

TIER_LABELS: Dict[str, str] = {
    "ip": "IP 层（知识产权授权/版税/许可费）",
    "knowledge": "知识层（知识资产/数据产品/技术服务）",
    "exchange": "交换层（交易/渠道/佣金流水）",
    "scenario": "场景权重层（场景化部署/场景适配价值）",
    "cognitive_nca": "认知 NCA 层（认知资产/负空间合规价值）",
}

# 默认分层权重（可配，仅用于分层构成展示——不构成主观估值）
DEFAULT_TIER_WEIGHTS: Dict[str, float] = {
    "ip": 0.30, "knowledge": 0.20, "exchange": 0.20,
    "scenario": 0.15, "cognitive_nca": 0.15,
}

# 负空间熔断阈值（文献 §3.3 智能体底线思维）:
#   proposed > 3 × U_observed → 强制锚定 U_observed × 1.5（CRITICAL）
#   proposed > 2.7 × U_observed → 过度溢价警告
FUSE_RATIO_CRITICAL = 3.0
FUSE_RATIO_WARN = 2.7
FALLBACK_RATIO = 1.5

# 交易方向
DIR_OUTPUT = "output"   # 销项（价值实现）
DIR_INPUT = "input"     # 进项（价值投入）


@dataclass(frozen=True)
class ObservableFloor:
    """效用可观测下限（U_observed 地板值，A-1）。"""
    asset_id: str
    u_observed: float               # U_observed = Σ销项 + Σ进项
    output_total: float             # Σ销项票
    input_total: float              # Σ进项票
    tx_count: int
    provenance: str                 # ID92

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "u_observed": round(self.u_observed, 4),
            "output_total": round(self.output_total, 4),
            "input_total": round(self.input_total, 4),
            "tx_count": self.tx_count,
            "provenance": self.provenance,
            "interpretation": "效用可观测下限（地板）：真实交易总额——总效用的充分统计量下限，非主观估值",
        }


@dataclass
class TierAssessment:
    """五阶效用分层评估（A-2）。"""
    asset_id: str
    tiers: Dict[str, dict]          # {tier: {amount, share, label}}
    weights: Dict[str, float]
    weighted_total: float           # Σ amount（= U_observed，分层汇总不新增估值）
    provenance: str

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "tiers": self.tiers,
            "weights": self.weights,
            "weighted_total": round(self.weighted_total, 4),
            "provenance": self.provenance,
            "note": "分层汇总=可观测下限（地板）按构成分解，权重仅描述构成比例，不构成主观估值",
        }


@dataclass(frozen=True)
class ValuationSafety:
    """估值安全熔断检查（文献 §3.3 底线思维，A-4 口径约束配套）。"""
    proposed: float
    u_observed: float
    ratio: float
    status: str                     # SAFE / WARNING / CIRCUIT_BREAKER
    action: str

    def to_dict(self) -> dict:
        return {
            "proposed": round(self.proposed, 4),
            "u_observed": round(self.u_observed, 4),
            "ratio": round(self.ratio, 4),
            "status": self.status,
            "action": self.action,
        }


class UtilValueService:
    """效用价值评估引擎（DCD-UTIL-VALUE-001 M1）。"""

    def __init__(self, tier_weights: Optional[Dict[str, float]] = None,
                 default_provenance: str = "SIMULATED"):
        self._weights = dict(DEFAULT_TIER_WEIGHTS if tier_weights is None else tier_weights)
        self._provenance = default_provenance
        # 权重规范化（和为 1）
        total = sum(self._weights.values())
        if total <= 0:
            raise ValueError("分层权重之和必须 > 0")
        self._weights = {k: v / total for k, v in self._weights.items()}

    # ---- A-1 效用下限 ----

    def observable_floor(self, asset_id: str, transactions: List[dict],
                         provenance: Optional[str] = None) -> ObservableFloor:
        """计算效用可观测下限 U_observed = Σ销项 + Σ进项。

        交易流格式: [{"direction": "output"|"input", "amount": float, ...}, ...]
        空流 → fail-closed（U_observed = 0，合法地板——禁止无锚估值）。
        """
        if not isinstance(transactions, list):
            raise ValueError("[NSFL-TRIGGER] transactions 必须为列表")
        output_total = 0.0
        input_total = 0.0
        for tx in transactions:
            if not isinstance(tx, dict):
                raise ValueError("[NSFL-TRIGGER] 交易记录必须为 dict")
            direction = tx.get("direction")
            amount = tx.get("amount")
            if direction not in (DIR_OUTPUT, DIR_INPUT):
                raise ValueError(f"[NSFL-TRIGGER] 非法交易方向: {direction}")
            if not isinstance(amount, (int, float)) or amount < 0:
                raise ValueError(f"[NSFL-TRIGGER] 非法交易金额: {amount}")
            if direction == DIR_OUTPUT:
                output_total += float(amount)
            else:
                input_total += float(amount)
        return ObservableFloor(
            asset_id=asset_id,
            u_observed=output_total + input_total,
            output_total=output_total,
            input_total=input_total,
            tx_count=len(transactions),
            provenance=provenance or self._provenance,
        )

    # ---- A-2 五阶分层 ----

    def tier_assessment(self, asset_id: str, transactions: List[dict],
                        tier_weights: Optional[Dict[str, float]] = None,
                        provenance: Optional[str] = None) -> TierAssessment:
        """五阶效用分层评估。

        每笔交易可带 tier 标签（缺省按 direction 归类到 exchange 交换层）；
        分层金额 = 各层可观测流水，分层汇总 = U_observed（不新增估值）。
        """
        floor = self.observable_floor(asset_id, transactions, provenance=provenance)
        tier_amounts: Dict[str, float] = {t: 0.0 for t in TIER_ORDER}
        for tx in transactions:
            tier = tx.get("tier")
            if tier is None:
                tier = "exchange" if tx["direction"] == DIR_OUTPUT else "knowledge"
            if tier not in TIER_ORDER:
                raise ValueError(f"[NSFL-TRIGGER] 非法分层标签: {tier}")
            tier_amounts[tier] += float(tx["amount"])

        weights = dict(self._weights if tier_weights is None else tier_weights)
        total_w = sum(weights.values())
        if total_w <= 0:
            raise ValueError("分层权重之和必须 > 0")
        weights = {k: v / total_w for k, v in weights.items()}

        tiers: Dict[str, dict] = {}
        floor_total = max(floor.u_observed, 1e-12)
        for t in TIER_ORDER:
            tiers[t] = {
                "amount": round(tier_amounts[t], 4),
                "share": round(tier_amounts[t] / floor_total, 4),
                "label": TIER_LABELS[t],
            }
        return TierAssessment(
            asset_id=asset_id,
            tiers=tiers,
            weights=weights,
            weighted_total=floor.u_observed,
            provenance=floor.provenance,
        )

    # ---- 估值安全熔断（文献 §3.3 底线思维）----

    def safety_check(self, proposed_valuation: float,
                     u_observed: float) -> ValuationSafety:
        """估值安全熔断检查。

        proposed > 3×U_observed → CRITICAL 熔断（强制锚定 U_observed×1.5）
        proposed > 2.7×U_observed → WARNING（需补充非交易效用强证据链）
        否则 SAFE。
        """
        if not isinstance(proposed_valuation, (int, float)) or proposed_valuation < 0:
            raise ValueError(f"[NSFL-TRIGGER] 非法估值: {proposed_valuation}")
        if not isinstance(u_observed, (int, float)) or u_observed < 0:
            raise ValueError(f"[NSFL-TRIGGER] 非法地板值: {u_observed}")
        if u_observed == 0:
            # 无锚定价禁止：地板为 0 时任何正估值都触发熔断
            return ValuationSafety(
                proposed=proposed_valuation, u_observed=0.0,
                ratio=float("inf") if proposed_valuation > 0 else 0.0,
                status="CIRCUIT_BREAKER" if proposed_valuation > 0 else "SAFE",
                action="U_observed=0（无真实交易）→ 禁止无锚定价，估值必须为 0",
            )
        ratio = proposed_valuation / u_observed
        if ratio > FUSE_RATIO_CRITICAL:
            return ValuationSafety(
                proposed=proposed_valuation, u_observed=u_observed, ratio=ratio,
                status="CIRCUIT_BREAKER",
                action=f"估值 > 3×U_observed → 强制锚定至 U_observed×{FALLBACK_RATIO}（{round(u_observed * FALLBACK_RATIO, 4)}）",
            )
        if ratio > FUSE_RATIO_WARN:
            return ValuationSafety(
                proposed=proposed_valuation, u_observed=u_observed, ratio=ratio,
                status="WARNING",
                action="估值 > 2.7×U_observed → 要求补充非交易效用强证据链（文化资产评估/专利池/用户粘性）",
            )
        return ValuationSafety(
            proposed=proposed_valuation, u_observed=u_observed, ratio=ratio,
            status="SAFE", action="估值在可观测下限安全区间内",
        )

    # ---- NS-007 函数七要素分解（资产分解框架，ID68）----

    def seven_element_decomposition(self, asset_id: str,
                                    meta: Dict[str, str]) -> dict:
        """按 NS-007 函数七要素分解版权资产。

        meta 提供资产描述，输出七要素结构化分解（DCD §三 函数七要素分解）。
        """
        required = ("objective", "constraint", "prior", "config_boundary",
                    "distribution", "audit")
        missing = [k for k in required if not meta.get(k)]
        if missing:
            raise ValueError(f"[NSFL-TRIGGER] 七要素缺失: {missing}")
        return {
            "asset_id": asset_id,
            "schema": "NS-007-FUNCTION-7ELEM-001",
            "elements": {
                "1_objective": meta["objective"],
                "2_constraint": meta["constraint"],
                "3_prior": meta["prior"],
                "4_config_boundary": meta["config_boundary"],
                "5_distribution": meta["distribution"],
                "6_audit": meta["audit"],
                "7_negative_space": meta.get("negative_space", "未声明——发布即契约要求补录（NS-007）"),
            },
        }
