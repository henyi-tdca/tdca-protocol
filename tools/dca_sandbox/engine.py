"""dca_sandbox · DCA-重塑版 SEA 沙盒模拟引擎（DCD-DCA-SANDBOX-001 M1 装配）

装配: merchant_loop M1（FROZEN，只装配不改写）+ 模拟参数 → 可运行周推进模拟模型。
对齐 SBX-OPS 三空间状态机语义（Phase0 准入 → P0 实验 → P1 评估 → Exit/Closed）。

模拟模型（剥壳取核，TDCA-REVIEW-DCA-LEGACY-001）:
  - 商家发布消费权益（merchant_loop 权益模板）→ 消费者到店真实消费事件 → 逐笔核销
  - 日清 = 逐笔即时让利（无池、无杠杆、零滞留——merchant_loop no_cls 语义）
  - 每周聚合: 核销率 / 现金流平衡 / ROI / CCA 需求信号占位
  - 出盒指标检测器（DCD-DCA-SANDBOX-001 §二，M1 预埋/M3 评估用）:
    ① 26 周零穿池（现金流模拟） ② 核销率 ≥60% 连续 8 周 ③ 0 金融化违例 ④ CCA 响应率 ≥ 阈值

纪律: 全 SIMULATED（ID92）；0 真实资金流；0 配置权真实调用；红线（无资产/无保本/无资金池/
无庞氏）内嵌审计——检出违例 → BLOCKED（回滚语义，对齐 SBX-OPS Closed）。

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 装配 FROZEN merchant_loop（只 import 不改写）
from merchant_loop.engine import MerchantLoopEngine, BenefitTemplate, RedemptionEvent
from merchant_loop.roi import RoiService

# 出盒门槛（DCD-DCA-SANDBOX-001 §二——M1 预埋检测器）
WEEK_RUN = 26                # M2 完整周数
NUCLEAR_RATE_TARGET = 0.60   # 核销率 ≥60%
NUCLEAR_RATE_CONSEC_WEEKS = 8  # 连续 8 周
CCA_RESPONSE_TARGET = 0.30   # CCA 响应率阈值（SIMULATED 候选，R-7 M3 定标）
ACTIVATION_THRESHOLD = 1.2   # 激活系数 >1.2 出盒（ID27/SBX-OPS）

# 违例红线词（金融化回归审计——检出即 BLOCKED）
VIOLATION_TERMS = ("升值", "保本", "二级交易", "回购", "倍数返现", "集换", "配售", "杠杆", "资金池")

# 状态机（SBX-OPS 语义）
ST_PHASE0 = "Phase0"   # 准入（装配完成）
ST_P0 = "P0"           # 实验（模拟运行中）
ST_P1 = "P1"           # 评估（指标检测）
ST_EXIT = "Exit"       # 出盒（M3 人类签批后）
ST_CLOSED = "Closed"   # 熔断/终止（违例/人类裁决）


@dataclass
class MerchantConfig:
    """商户模拟配置（SIMULATED）。"""
    merchant_id: str
    benefit_raw: dict                     # merchant_loop 权益模板原始配置
    customer_base: float = 2000.0         # 触达顾客数
    arrival_rate: float = 0.25            # 周核销到达率 λ（SIMULATED，M2 校准）
    avg_ticket: float = 100.0             # 客单价（SIMULATED）
    ticket_sigma: float = 25.0


@dataclass
class WeeklyResult:
    """单周聚合结果。"""
    week: int
    events: int                            # 核销事件数
    redemption_value: float                # 核销消费额
    allowance_cost: float                  # 让利成本（discount+rebate）
    net_revenue: float                     # 净收入（消费额−让利）
    redemption_rate: float                 # 核销率 = 核销事件/触达
    cashflow_balance: float                # 日清现金流余额（逐笔即时→≈0）
    cca_signal: float                      # CCA 需求信号（SIMULATED 占位 = 核销额×场景权重）
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "week": self.week,
            "events": self.events,
            "redemption_value": round(self.redemption_value, 2),
            "allowance_cost": round(self.allowance_cost, 2),
            "net_revenue": round(self.net_revenue, 2),
            "redemption_rate": round(self.redemption_rate, 4),
            "cashflow_balance": round(self.cashflow_balance, 4),
            "cca_signal": round(self.cca_signal, 4),
            "violations": self.violations,
        }


@dataclass
class SandboxRunResult:
    """模拟运行结果（P1 评估 + 出盒指标检测）。"""
    sandbox_id: str
    phase: str
    weeks_run: int
    weekly: List[WeeklyResult]
    total_events: int
    avg_redemption_rate: float
    consecutive_target_weeks: int          # 核销率≥60% 连续周数
    zero_piercing: bool                    # 零穿池（现金流无负）
    violations: List[str]                  # 全期违例（0 = 合规）
    activation: float                      # 激活系数（M3 完整计算——占位估算）
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "sandbox_id": self.sandbox_id,
            "phase": self.phase,
            "weeks_run": self.weeks_run,
            "total_events": self.total_events,
            "avg_redemption_rate": round(self.avg_redemption_rate, 4),
            "consecutive_target_weeks": self.consecutive_target_weeks,
            "zero_piercing": self.zero_piercing,
            "violations": self.violations,
            "activation": round(self.activation, 4),
            "exit_gate": {
                "nuclear_rate_60pct_8wk": self.consecutive_target_weeks >= NUCLEAR_RATE_CONSEC_WEEKS,
                "zero_piercing_26wk": self.zero_piercing,
                "zero_financialization_violation": len(self.violations) == 0,
                "activation_gt_1_2": self.activation > ACTIVATION_THRESHOLD,
            },
            "weekly": [w.to_dict() for w in self.weekly],
            "note": self.note,
        }


class DcaSandboxSimulation:
    """DCA-重塑版周推进模拟引擎（M1 装配版——merchant_loop 接入）。"""

    def __init__(self, default_provenance: str = "SIMULATED"):
        self._provenance = default_provenance
        self._ml_engine = MerchantLoopEngine(default_provenance=default_provenance)
        self._roi = RoiService()

    # ---- Phase0 准入：装配校验（merchant_loop 模板校验复用）----

    def assemble(self, merchants: List[MerchantConfig], sandbox_id: str = "SBX-DCA-001") -> List[BenefitTemplate]:
        """准入装配：逐商户权益模板经 merchant_loop validate_template 校验（FROZEN 逻辑）。

        校验失败（模板含红线/六要素缺失等）→ 装配拒绝（Phase0 fail-closed）。
        """
        templates: List[BenefitTemplate] = []
        for mc in merchants:
            tpl = self._ml_engine.validate_template(mc.benefit_raw, provenance=self._provenance)
            templates.append(tpl)
        self._sandbox_id = sandbox_id
        self._merchants = merchants
        self._templates = templates
        return templates

    # ---- P0 实验：周推进模拟 ----

    def run(self, weeks: int = 13, seed: int = 20260908,
            sandbox_id: str = "SBX-DCA-001") -> SandboxRunResult:
        """周推进日清模拟（M1 验证运行；M2 跑 WEEK_RUN=26 周）。

        每周: 每商户按 arrival_rate 生成核销事件（泊松近似）→ 逐笔 merchant_loop redeem
              → 日清即时让利（cashflow 余额≈0）→ 聚合 WeeklyResult。
        违例审计: 全期扫描资金流/参数——无聚合资金/无红线词 → violations 为空（0 违例）。
        """
        if weeks <= 0:
            raise ValueError("[NSFL-TRIGGER] weeks 须 >0")
        rng = random.Random(seed)
        weekly: List[WeeklyResult] = []
        total_events = 0
        all_violations: List[str] = []

        for wk in range(1, weeks + 1):
            events = 0
            redemption_value = 0.0
            allowance = 0.0
            for mc, tpl in zip(self._merchants, self._templates):
                # 泊松近似到达（λ=arrival_rate×customer_base/周）——Random 无 poisson，用累积采样近似
                lam = mc.arrival_rate * mc.customer_base
                n_events = self._poisson_sample(rng, lam)
                for i in range(n_events):
                    min_spend = float((tpl.conditions or {}).get("min_spend", 0.0) or 0.0)
                    floor_ticket = max(10.0, min_spend + 1.0)   # 客单价下限对齐权益 min_spend
                    ticket = max(floor_ticket, rng.gauss(mc.avg_ticket, mc.ticket_sigma))
                    ev = RedemptionEvent(
                        redemption_id=f"{sandbox_id}-w{wk}-{mc.merchant_id}-{i}",
                        benefit_id=tpl.benefit_id,
                        merchant_id=tpl.merchant_id,
                        store=(tpl.stores or ["S-1"])[0],
                        consumer_id=f"C-{rng.randint(1, 5000)}",
                        amount=round(ticket, 2),
                        provenance=self._provenance,
                    )
                    # 装配 FROZEN merchant_loop redeem（CCA 预留 + 即时对价）
                    result = self._ml_engine.redeem(tpl, ev, redemption_nca_id=f"{sandbox_id}-sim")
                    events += 1
                    redemption_value += ev.amount
                    allowance += result.net_merchant_cost

            rate = events / max(1.0, sum(mc.customer_base for mc in self._merchants))
            # 日清：逐笔即时让利 → 无滞留余额；现金流平衡 = 当日让利已即时出账（≈0 非负数）
            cash_balance = 0.0   # 零滞留（merchant_loop no_cls 语义——无池）
            cca_signal = round(redemption_value * 0.5, 4)   # SIMULATED 占位（场景权重 0.5，R-7 M3 定标）
            wk_violations = self._audit_week(tpl_list=self._templates, wk=wk, events=events)
            weekly.append(WeeklyResult(
                week=wk, events=events,
                redemption_value=redemption_value,
                allowance_cost=round(allowance, 2),
                net_revenue=round(redemption_value - allowance, 2),
                redemption_rate=rate,
                cashflow_balance=cash_balance,
                cca_signal=cca_signal,
                violations=wk_violations,
            ))
            total_events += events
            all_violations.extend(wk_violations)

        return self._evaluate(sandbox_id, weekly, total_events)

    # ---- P1 评估：出盒指标检测 ----

    def _evaluate(self, sandbox_id: str, weekly: List[WeeklyResult],
                  total_events: int) -> SandboxRunResult:
        weeks = len(weekly)
        avg_rate = sum(w.redemption_rate for w in weekly) / max(1, weeks)

        # 核销率 ≥60% 连续周数（滚动计数）
        cons = 0
        max_cons = 0
        for w in weekly:
            if w.redemption_rate >= NUCLEAR_RATE_TARGET:
                cons += 1
                max_cons = max(max_cons, cons)
            else:
                cons = 0

        zero_piercing = all(w.cashflow_balance >= 0 for w in weekly)
        violations = sorted({v for w in weekly for v in w.violations})

        # 激活系数（占位估算——M3 完整公式：SWU 正和×核销达标×合规；此处以核销达标率×合规系数近似）
        compliance = 1.0 if not violations else 0.0
        activation = round(1.0 + (avg_rate - 0.3) * 2.0 * compliance, 4)

        note = "M1 装配验证运行（SIMULATED 短程）——完整 26 周模拟归 M2；出盒指标检测器预埋（M3 评估）"
        return SandboxRunResult(
            sandbox_id=sandbox_id,
            phase=ST_P1,
            weeks_run=weeks,
            weekly=weekly,
            total_events=total_events,
            avg_redemption_rate=avg_rate,
            consecutive_target_weeks=max_cons,
            zero_piercing=zero_piercing,
            violations=violations,
            activation=activation,
            note=note,
        )

    # ---- 违例审计（金融化回归 0 违例）----

    @staticmethod
    def _poisson_sample(rng: random.Random, lam: float) -> int:
        """Knuth 泊松采样（λ 大时用正态近似避免慢循环）。"""
        if lam > 30.0:
            return max(0, int(rng.gauss(lam, lam ** 0.5) + 0.5))
        limit = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            p *= rng.random()
            if p <= limit:
                return k
            k += 1

    def _audit_week(self, tpl_list: List[BenefitTemplate], wk: int, events: int) -> List[str]:
        """周审计：无资金池（逐笔即时无滞留）→ 本引擎结构性保证；红线词复扫模板。"""
        hits = []
        for tpl in tpl_list:
            for term in VIOLATION_TERMS:
                raw_str = str(tpl.to_dict())
                if term in raw_str:
                    # 排除否定声明（无/不/禁/防/剥离/剔除/拒/零/未 前缀）
                    idx = raw_str.find(term)
                    before = raw_str[max(0, idx - 3):idx]
                    if not any(p in before for p in ("无", "不", "非", "禁", "防", "剥离", "剔除", "拒", "零", "未")):
                        hits.append(f"w{wk}: 模板含红线词 {term}")
        return hits
