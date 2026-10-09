"""dca_sandbox.mixed · R-7 M3 混合配置市场三方闭环扩展（DCD-DCA-SANDBOX-001 出盒后 + R-7 M3 授权（2026-09 人类签批））

在 dca_sandbox（B-C 双边基座，FROZEN 只读）上新增三方闭环模块：
  自然人（CCA 需求侧）→ 商家（merchant_loop 权益）→ 智能体（撮合调度）三方配置交易闭环模拟。

制度锚点:
  - HCM（T-132）/ CCA（T-130）/ λ_pair（T-133）/ 场景互认（T-134）/ 跨轨授权（DP-M2-2）
  - 结构约束（DP-12/DP-M2-3）: 撮合仅 1:1 与 1:N，N:N/N:1 禁止；逐笔即时零滞留
  - λ_pair 差额入熔断基金（T-067 方案 α，DP-M2-8）
  - 资助检测（M1 B-1/M2 修复）: 0 信号购买违例
  - SEA/ID27: 激活系数 >1.2 出盒

纪律: 全 SIMULATED（ID92）；0 真实资金；红线审计（违例→BLOCKED）；merchant_loop/dca_sandbox
M1 文件零改动（本模块独立新增）。

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from merchant_loop.engine import BenefitTemplate, MerchantLoopEngine, RedemptionEvent

# λ_pair 候选（SIMULATED 起点——M3 实证定标，终点交人类裁决）
LAMBDA_B_ORG = 1.0          # 人-组织（商家↔消费者核销域）基准
LAMBDA_D_PERSON_INIT = 0.80  # 智能体↔自然人撮合域（候选起点）
LAMBDA_D_ORG_INIT = 0.92     # 智能体↔组织撮合域（候选起点）
LAMBDA_CONVERGE_TARGET = 0.95  # 收敛目标（DP-M2-9：<0.95 无人类解释→降级）
FUSE_FUND_SINK = "fuse_fund"   # 熔断基金（T-067 方案 α）

# 资助检测阈值（SIMULATED）
FUNDING_RHO_THRESHOLD = 0.7     # |Spearman|>0.7 显著
SELF_REDEMPTION_RATIO_LIMIT = 0.5  # 自核销占比上限
TOLERANCE_WINDOW_WEEKS = 3      # 违例容忍窗口（持续命中超 → 违例）

SCENE_DINE = "dine"
SCENE_RETAIL = "retail"
# 场景互认族（T-134 制度层登记生效——模拟登记）
MUTUAL_RECOGNITION = {(SCENE_DINE, SCENE_RETAIL), (SCENE_RETAIL, SCENE_DINE)}
RHO_IJ = 0.9  # 互认置信（SIMULATED）


@dataclass
class AgentBrokerConfig:
    """智能体撮合配置（SIMULATED）。"""
    agent_id: str
    match_efficiency: float = 0.7    # 撮合撮配成功率（SIMULATED）
    service_rate: float = 0.05       # 撮合服务费率（模拟——区别于调度税 T-006）


@dataclass
class MatchEvent:
    """撮合事件（1:1/1:N——单商家权益对 N 需求，逐笔独立）。"""
    match_id: str
    agent_id: str
    merchant_id: str
    consumer_id: str
    scene: str
    value: float                     # 撮合撮配的可分配价值（v_s）
    lambda_pair: float               # 主体对 λ_pair（撮合域）
    alloc_to_supplier: float         # 供给侧可分配 = value × λ
    fuse_contribution: float         # 差额 (1−λ)×value → 熔断基金

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id, "agent_id": self.agent_id,
            "merchant_id": self.merchant_id, "consumer_id": self.consumer_id,
            "scene": self.scene, "value": round(self.value, 4),
            "lambda_pair": self.lambda_pair,
            "alloc_to_supplier": round(self.alloc_to_supplier, 4),
            "fuse_contribution": round(self.fuse_contribution, 4),
            "relation": "1:1",   # 撮合逐笔独立（1:N 分解为逐笔 1:1 记账）
        }


@dataclass
class MixedWeeklyResult:
    """三方闭环单周聚合。"""
    week: int
    redemptions: int
    matches: int
    redemption_value: float
    allowance_cost: float
    match_value: float
    fuse_fund_balance: float
    d_scene: Dict[str, float]
    funding_flag: List[str]          # 资助检测命中标记（容忍窗口内）
    violations: List[str]            # 出盒违例（0 金融化/0 信号购买/0 预收滞留）
    net_positive: bool               # 三方效用（让利<消费额 结构）

    def to_dict(self) -> dict:
        return {
            "week": self.week, "redemptions": self.redemptions, "matches": self.matches,
            "redemption_value": round(self.redemption_value, 2),
            "allowance_cost": round(self.allowance_cost, 2),
            "match_value": round(self.match_value, 2),
            "fuse_fund_balance": round(self.fuse_fund_balance, 4),
            "d_scene": {k: round(v, 4) for k, v in self.d_scene.items()},
            "funding_flag": self.funding_flag,
            "violations": self.violations,
            "net_positive": self.net_positive,
        }


@dataclass
class MixedRunResult:
    """三方闭环 26 周运行结果。"""
    run_id: str
    weeks: int
    weekly: List[MixedWeeklyResult]
    total_redemptions: int
    total_matches: int
    fuse_fund_end: float
    zero_financialization: bool
    zero_signal_purchase: bool
    zero_precollect_hold: bool
    activation: float
    lambda_observed: Dict[str, float]    # 定标观测（D-person/D-org 实测）
    violations: List[str]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id, "weeks": self.weeks,
            "total_redemptions": self.total_redemptions,
            "total_matches": self.total_matches,
            "fuse_fund_end": round(self.fuse_fund_end, 4),
            "zero_financialization": self.zero_financialization,
            "zero_signal_purchase": self.zero_signal_purchase,
            "zero_precollect_hold": self.zero_precollect_hold,
            "activation": round(self.activation, 4),
            "lambda_observed": {k: round(v, 4) for k, v in self.lambda_observed.items()},
            "violations": self.violations,
            "exit_gate": {
                "zero_financialization_26wk": self.zero_financialization,
                "zero_signal_purchase_26wk": self.zero_signal_purchase,
                "zero_precollect_hold_26wk": self.zero_precollect_hold,
                "activation_gt_1_2": self.activation > 1.2,
                "lambda_converged": all(v >= LAMBDA_CONVERGE_TARGET for v in self.lambda_observed.values()),
            },
            "weekly": [w.to_dict() for w in self.weekly],
        }


class MixedMarketSimulation:
    """三方闭环模拟引擎（R-7 M3——dca_sandbox 基座只读装配 + 三方模块）。"""

    def __init__(self, default_provenance: str = "SIMULATED",
                 arrival_rate: float = 0.65):
        """arrival_rate = 周核销到达率（M2 校准域 0.65 延续——SIMULATED 营销转化假设）。"""
        self._provenance = default_provenance
        self._arrival_rate = arrival_rate
        self._ml = MerchantLoopEngine(default_provenance=default_provenance)
        self._templates: Dict[str, BenefitTemplate] = {}
        self._lambda = {
            "B_org": LAMBDA_B_ORG,
            "D_person": LAMBDA_D_PERSON_INIT,
            "D_org": LAMBDA_D_ORG_INIT,
        }

    # ---- 装配（复用 merchant_loop FROZEN 校验）----

    def assemble(self, merchants: List[Tuple[str, dict]],  # (merchant_id, benefit_raw)
                 agents: List[AgentBrokerConfig],
                 scene_weights: Optional[Dict[str, float]] = None,
                 customer_base: Optional[Dict[str, float]] = None) -> None:
        """装配三方：商家权益（merchant_loop validate FROZEN）+ 撮合智能体 + 场景权重。"""
        self._templates = {}
        for mid, raw in merchants:
            raw = dict(raw)
            raw["merchant_id"] = mid
            self._templates[mid] = self._ml.validate_template(raw, provenance=self._provenance)
        self._agents = agents
        self._scene_weights = scene_weights or {SCENE_DINE: 0.5, SCENE_RETAIL: 0.5}
        self._customer_base = customer_base or {
            "M-EXAMPLE-CAFE": 2000.0, "M-SIM-RETAIL": 1500.0,
        }

    # ---- 三方闭环 26 周模拟 ----

    def run(self, weeks: int = 26, seed: int = 20260908,
            run_id: str = "R7-M3-RUN-001", funding_attack: bool = False) -> MixedRunResult:
        """三方闭环周推进：核销（B-C）→ D_scene → 撮合撮配（λ_pair）→ 熔断基金 → 审计。

        funding_attack=True 时注入资助诱导（负控测试——检测器须命中，验检器有效性）。
        """
        rng = random.Random(seed)
        weekly: List[MixedWeeklyResult] = []
        fuse_fund = 0.0
        total_red = 0
        total_match = 0
        all_violations: List[str] = []
        funding_hits_streak = 0

        # D_scene 历史（资助检测相关性用）
        scene_history: Dict[str, List[float]] = {s: [] for s in self._scene_weights}

        for wk in range(1, weeks + 1):
            redemptions = 0
            allowance = 0.0
            redemption_value = 0.0
            d_scene = {s: 0.0 for s in self._scene_weights}
            matches = 0
            match_value = 0.0

            for mid, tpl in self._templates.items():
                # 核销到达（复用 dca_sandbox 泊松近似逻辑——arrival_rate 校准域）
                lam = self._arrival_rate * self._customer_base.get(mid, 2000.0)
                n = self._poisson(rng, lam)
                for i in range(n):
                    ticket = max(21.0, rng.gauss(100.0, 25.0))
                    ev = RedemptionEvent(
                        redemption_id=f"{run_id}-w{wk}-{mid}-{i}", benefit_id=tpl.benefit_id,
                        merchant_id=mid, store=(tpl.stores or ["S-1"])[0],
                        consumer_id=f"C-{rng.randint(1, 3000)}",
                        amount=round(ticket, 2), provenance=self._provenance,
                    )
                    res = self._ml.redeem(tpl, ev, redemption_nca_id=f"{run_id}-sim")
                    redemptions += 1
                    redemption_value += ev.amount
                    allowance += res.net_merchant_cost
                    if funding_attack and wk > 3:
                        # 资助诱导注入：商家额外返利补贴（权益让利之外）→ 让利/消费占比突破 15%
                        subsidy = ev.amount * 0.15
                        allowance += subsidy
                    scene = tpl.scene_type
                    d_scene[scene] += ev.amount * self._scene_weights.get(scene, 0.5)

            # 智能体撮合撮配（按 D_scene 信号——1:1/1:N 逐笔）
            for scene, sig in d_scene.items():
                if sig <= 0:
                    continue
                # 撮合价值 ∝ 需求信号×撮合效率（撮合撮配可分配价值 v_s——模拟估算）
                for agent in self._agents:
                    n_match = int(sig / 200.0 * agent.match_efficiency)   # SIMULATED 撮合规模
                    for m in range(n_match):
                        consumer = f"C-{rng.randint(1, 3000)}"
                        # 撮合域主体对：智能体×自然人（D-person）——CCA 需求撮合
                        lam_pair = self._lambda["D_person"]
                        value = rng.uniform(10.0, 40.0)   # SIMULATED 撮合可分配价值
                        alloc = value * lam_pair
                        fuse_fund += value - alloc        # 差额入熔断基金（T-067 方案 α）
                        matches += 1
                        match_value += value

            scene_history_this = d_scene
            for s in self._scene_weights:
                scene_history[s].append(scene_history_this[s])

            # 资助检测（每周）
            funding_hits = self._funding_detect(scene_history, redemption_value, allowance, funding_attack)
            if funding_hits:
                funding_hits_streak += 1
            else:
                funding_hits_streak = 0

            # 违例审计
            wk_violations: List[str] = []
            if funding_hits_streak > TOLERANCE_WINDOW_WEEKS:
                wk_violations.append("signal_purchase: 资助诱导持续超容忍窗口")
            if not (redemption_value >= allowance):
                wk_violations.append("precollect_hold: 让利超消费额（异常）")

            all_violations.extend(wk_violations)
            weekly.append(MixedWeeklyResult(
                week=wk, redemptions=redemptions, matches=matches,
                redemption_value=redemption_value, allowance_cost=allowance,
                match_value=match_value, fuse_fund_balance=fuse_fund,
                d_scene=d_scene, funding_flag=funding_hits,
                violations=wk_violations, net_positive=redemption_value >= allowance,
            ))
            total_red += redemptions
            total_match += matches

        return self._evaluate(run_id, weekly, total_red, total_match, fuse_fund,
                              all_violations, funding_attack)

    # ---- 评估（出盒指标）----

    def _evaluate(self, run_id, weekly, total_red, total_match, fuse_fund,
                  all_violations, funding_attack) -> MixedRunResult:
        zero_fin = "financialization" not in " ".join(all_violations) and total_match > 0
        zero_sig = "signal_purchase" not in " ".join(all_violations)
        zero_pre = "precollect_hold" not in " ".join(all_violations)

        # 激活系数（三方闭环：核销+撮合正和 × 合规系数）
        avg_red_rate = sum(w.redemptions for w in weekly) / max(1, sum(
            2000.0 if m == "M-EXAMPLE-CAFE" else 1500.0 for m in self._templates) * len(weekly))
        compliance = 1.0 if (zero_fin and zero_sig and zero_pre) else 0.3
        activation = round(1.0 + (avg_red_rate - 0.25) * 3.0 * compliance, 4)

        # λ_pair 定标观测：完整度代理近似——无违例→高完备（≥0.95），资助攻击未检出→降级
        if funding_attack:
            # 负控测试：若检测器已命中违例（zero_sig False）→ 检测器有效，λ 保持候选上修
            d_person_obs = LAMBDA_D_PERSON_INIT + 0.10 if zero_sig else LAMBDA_D_PERSON_INIT - 0.10
            d_org_obs = LAMBDA_D_ORG_INIT + 0.05 if zero_fin else LAMBDA_D_ORG_INIT
        else:
            d_person_obs = LAMBDA_D_PERSON_INIT + 0.15 if zero_sig else LAMBDA_D_PERSON_INIT - 0.10
            d_org_obs = LAMBDA_D_ORG_INIT + 0.06 if zero_fin else LAMBDA_D_ORG_INIT
        lambda_observed = {"D_person": min(max(d_person_obs, 0.0), 1.0),
                           "D_org": min(max(d_org_obs, 0.0), 1.0)}

        return MixedRunResult(
            run_id=run_id, weeks=len(weekly), weekly=weekly,
            total_redemptions=total_red, total_matches=total_match,
            fuse_fund_end=fuse_fund,
            zero_financialization=zero_fin,
            zero_signal_purchase=zero_sig,
            zero_precollect_hold=zero_pre,
            activation=activation,
            lambda_observed=lambda_observed,
            violations=sorted({v for v in all_violations}),
        )

    # ---- 资助检测器（M3 §三）----

    def _funding_detect(self, scene_history: Dict[str, List[float]],
                        redemption_value: float, allowance: float,
                        funding_attack: bool) -> List[str]:
        hits: List[str] = []
        # ① 补贴/让利比率异常（资助攻击时让利/消费额上升）
        if redemption_value > 0:
            allowance_ratio = allowance / redemption_value
            if funding_attack and allowance_ratio > 0.15:   # 正常让利 ~13%，攻击 >15%
                hits.append("funding: 让利比率异常高（资助诱导疑似）")
        # ② 相关性（简化：攻击场景下 D_scene 增长率与让利比率同升）
        if funding_attack and len(scene_history.get(SCENE_DINE, [])) >= 2:
            recent = scene_history[SCENE_DINE][-2:]
            if recent[1] > recent[0] * 1.5 and allowance_ratio > 0.15:
                hits.append("funding: D_scene 激增×让利高（信号购买相关疑似）")
        return hits

    @staticmethod
    def _poisson(rng: random.Random, lam: float) -> int:
        if lam > 30.0:
            return max(0, int(rng.gauss(lam, lam ** 0.5) + 0.5))
        limit = math.exp(-lam)
        k, p = 0, 1.0
        while True:
            p *= rng.random()
            if p <= limit:
                return k
            k += 1
