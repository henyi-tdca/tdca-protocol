# -*- coding: utf-8 -*-
"""E-1/E-2/E-3 主体经济生态权重 + 零和负和熔断（TDCA-TASK-ECOWEIGHT-001）。

制度语义（用户 2026-08-12，人类确认）:
  1. 主体配置权在某场景的价值 = 买卖总量（MOU_i = buy_i + sell_i），非单一买/卖指标
  2. 买卖总量 = 经济事实贡献最低可见指标 = 场景经济生态权重（w_i = MOU_i / ΣMOU_j）
  3. 主体经济行为对场景效用零和/负和 → 经济生态熔断（economic fuse，区别于 NSFL 法律熔断）
     → 回沙盒重塑（sandbox_reshape）或休眠（dormant，可恢复——区别于 SBX-BANNED 法律
       永久休眠 ID86）→ 禁止进入该场景配置（scene_config_blocked）→ 配置价值低

锚定: MOU=进项+出项（TERMS-001:147）+ TREATISE-026（U_正和）+ COGNITION-001（场景级）
     + SBX-OPS（SBX-BANNED 法律永久休眠 ID86——经济级处置须独立可恢复）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EcoDisposition(str):
    """经济熔断处置（可恢复——区别于法律永久休眠）。"""
    SANDBOX_RESHAPE = "sandbox_reshape"   # 回沙盒重塑
    DORMANT = "dormant"                   # 休眠（经济级，可恢复）
    NONE = "none"                         # 无熔断


@dataclass
class SubjectEcoAssessment:
    """主体经济生态评估（单主体，含买/卖权重与偏态——BIAS-001）。"""
    subject_id: str
    buy: float                            # 进项贡献（买）
    sell: float                           # 出项贡献（卖）
    mou_total: float                      # 买卖总量 MOU_i = buy + sell
    weight: float                         # 生态权重 w_i = MOU_i / ΣMOU
    buy_weight: float = 0.0               # 买权重 = buy / ΣMOU（B-1）
    sell_weight: float = 0.0              # 卖权重 = sell / ΣMOU（B-1）
    bias: float = 0.0                     # 偏态 bias ∈ [−1,1]（B-2：偏买>0/偏卖<0/均衡≈0）
    bias_label: str = "balanced"          # buy_biased / sell_biased / balanced
    zero_negative: bool = False           # 零和/负和（MOU_i ≤ 0）
    economic_fused: bool = False          # 经济生态熔断
    disposition: str = "none"             # sandbox_reshape / dormant / none
    scene_config_blocked: bool = False    # 禁止进入该场景配置
    config_value: str = "high"            # high / low（有害→low）

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "buy": self.buy,
            "sell": self.sell,
            "mou_total": self.mou_total,
            "weight": round(self.weight, 6),
            "buy_weight": round(self.buy_weight, 6),
            "sell_weight": round(self.sell_weight, 6),
            "bias": round(self.bias, 6),
            "bias_label": self.bias_label,
            "zero_negative": self.zero_negative,
            "economic_fused": self.economic_fused,
            "disposition": self.disposition,
            "scene_config_blocked": self.scene_config_blocked,
            "config_value": self.config_value,
        }


class SubjectEcoWeightEngine:
    """E-1/E-2/E-3 主体经济生态权重引擎 + B-1/B-2/B-3 买卖权重细分与偏态（BIAS-001）。"""

    def __init__(self, disposition: str = EcoDisposition.SANDBOX_RESHAPE,
                 balance_tolerance: float = 0.05):
        self._disposition = disposition     # 熔断后默认处置（沙盒重塑；可指定休眠）
        self._tol = balance_tolerance       # 均衡容差（|bias| < tol → balanced）

    def assess(self, subject_buy_sell: Dict[str, Dict[str, float]]) -> List[SubjectEcoAssessment]:
        """场景级主体评估:

        1. MOU_i = buy_i + sell_i（E-1 买卖总量，非单边）
        2. w_i = MOU_i / ΣMOU（E-2 生态权重，Σw_i=1；全部零和时权重均分）
        3. MOU_i ≤ 0 → 零和/负和 → 经济熔断 → 沙盒重塑/休眠 → 禁入该场景 → 价值低（E-3）
        """
        if not subject_buy_sell:
            return []

        totals = {}
        for sid, bs in subject_buy_sell.items():
            buy = float(bs.get("buy", 0.0))
            sell = float(bs.get("sell", 0.0))
            totals[sid] = buy + sell

        total_mou = sum(totals.values())
        if total_mou <= 0:
            # 场景整体零和/负和——权重均分（各主体均零和，全部熔断）
            weights = {sid: 1.0 / len(totals) for sid in totals}
        else:
            weights = {sid: t / total_mou for sid, t in totals.items()}

        assessments = []
        for sid, mou_i in totals.items():
            zero_negative = mou_i <= 0
            fused = zero_negative
            buy = float(subject_buy_sell[sid].get("buy", 0.0))
            sell = float(subject_buy_sell[sid].get("sell", 0.0))
            # B-1: 买/卖权重（各边 / ΣMOU）
            buy_weight = buy / total_mou if total_mou > 0 else 0.0
            sell_weight = sell / total_mou if total_mou > 0 else 0.0
            # B-2: 偏态 bias ∈ [−1,1]（归一化加权：偏买>0/偏卖<0/均衡≈0）
            side_sum = abs(buy) + abs(sell)
            if side_sum > 0:
                bias = (buy - sell) / side_sum
            else:
                bias = 0.0
            bias_label = ("buy_biased" if bias > self._tol
                          else "sell_biased" if bias < -self._tol
                          else "balanced")
            assessments.append(SubjectEcoAssessment(
                subject_id=sid,
                buy=round(buy, 2),
                sell=round(sell, 2),
                mou_total=round(mou_i, 2),
                weight=round(weights[sid], 6),
                buy_weight=round(buy_weight, 6),
                sell_weight=round(sell_weight, 6),
                bias=round(bias, 6),
                bias_label=bias_label,
                zero_negative=zero_negative,
                economic_fused=fused,
                disposition=self._disposition if fused else EcoDisposition.NONE,
                scene_config_blocked=fused,
                config_value="low" if fused else "high",
            ))
        return assessments

    def compute_weights(self, subject_mou: Dict[str, float]) -> Dict[str, float]:
        """E-2 权重纯计算（Σw=1；输入 {subject: MOU_i}）。"""
        if not subject_mou:
            return {}
        total = sum(subject_mou.values())
        if total <= 0:
            return {k: round(1.0 / len(subject_mou), 6) for k in subject_mou}
        return {k: round(v / total, 6) for k, v in subject_mou.items()}

    # ---- B-2: 偏态纯计算 ----

    def compute_bias(self, subject_buy_sell: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """B-2 偏态纯计算（bias ∈ [−1,1]：偏买>0 / 偏卖<0 / 均衡≈0）。"""
        out = {}
        for sid, bs in subject_buy_sell.items():
            buy = abs(float(bs.get("buy", 0.0)))
            sell = abs(float(bs.get("sell", 0.0)))
            side_sum = buy + sell
            out[sid] = round((buy - sell) / side_sum, 6) if side_sum > 0 else 0.0
        return out

    # ---- B-3: 跨场景配置决策（偏态互补筛选 + 正和满意解值排序）----

    def cross_scene_match(self, enterer_bias: float,
                          target_scene_subjects: Dict[str, float],
                          satisfaction_values: Optional[Dict[str, float]] = None) -> List[dict]:
        """B-3 跨场景配置决策:

        1. 偏态互补筛选（用户例子）: 互补度 = enterer_bias × subject_bias
           （负=互补；同向=推销进入者不需要的供给——降权）
        2. 最终排序（用户深化 2026-08-12）: **场景正和效用满意解值高者优先**
           ——互补候选内按 satisfaction value 降序；同向候选排后（satisfaction 亦参与排序）
        """
        sat = satisfaction_values or {}
        matches = []
        for sid, sub_bias in target_scene_subjects.items():
            complement = round(enterer_bias * sub_bias, 6)
            sat_v = round(float(sat.get(sid, 0.0)), 6)
            matches.append({
                "subject_id": sid,
                "subject_bias": round(sub_bias, 6),
                "complementarity": complement,          # 负值=互补
                "complementary": complement < 0,
                "satisfaction_value": sat_v,            # 场景正和效用满意解值
                "rank_hint": "preferred" if complement < 0
                             else "same_side" if complement > 0 else "neutral",
            })
        # 排序: ① 互补候选优先（complementary 前置）② 候选内满意解值高者优先
        matches.sort(key=lambda m: (
            m["complementary"] is False,          # True 排前
            -m["satisfaction_value"],             # 高者优先
            m["complementarity"],                 # 同向内互补度次排序
        ))
        return matches
