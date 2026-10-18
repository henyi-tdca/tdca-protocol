"""merchant_loop · 商家消费权益循环增值服务引擎（DCD-MERCHANT-LOOP-001 M1）

核心定位（剥壳取核，TDCA-REVIEW-DCA-LEGACY-001）:
  商家把「广告/折扣/佣金预算（≤历史预算）」平移为**消费权益函数**——发权益非发资产：
  折扣/即时小额让利/有效期/可核销门店/核销条件（YAML 模板 + 六要素声明）。
  商家-消费者 = **双边消费交易**（非多主体闭环结算）→ 不进 CLS 核心逻辑（T-027 裁决一致）。

制度锚点:
  - T-031 调度税（商家权益发布=配置权调用场景，模拟态 1-3%——本包不代收，标注口径）
  - util_value / cog_align 增值服务并列（DCD §四）
  - R-7 CCA（核销→贡献值记账接口预留，DCD 验收 A-2）
  - ID92（provenance real/simulated 强制标注）

红线（本包内嵌 NSFL 声明，发布即拒绝）:
  - 无资产升值因子：权益模板禁止出现「升值/回报/二级转让/保本/倍数返现」字段——检出即拒
  - 无池/无杠杆：逐笔核销 NCA 存证，无聚合资金
  - 不进 CLS：双边消费交易（核销闭环不触发 CLS 逻辑）
  - 模拟态：真实资金流 e-CNY 接入前 provenance 默认 SIMULATED（15% 分润 NCA 记账口径同）

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

# ---- 红线词（负空间字段检测，出现即拒）----
FORBIDDEN_TERMS = ("升值", "回报率", "保本", "二级市场", "二级转让", "回购", "倍数返现", "集换", "配售", "杠杆")

# 六要素声明键（NS-007 对齐，DCD §二 权益函数模板）
SIX_ELEMENTS = ("objective", "constraint", "prior", "config_boundary", "distribution", "audit")

# 场景类型（核销条件维度，接 CCA D_scene 场景权重预留位）
SCENE_TYPES = ("dine", "retail", "service", "entertainment", "other")

ALLOWED_DISCOUNT_KEYS = ("rate", "amount_off", "min_spend")
ALLOWED_REBATE_KEYS = ("rate", "amount", "cap")


@dataclass(frozen=True)
class BenefitTemplate:
    """消费权益函数模板（六要素声明 + 权益参数）。"""
    benefit_id: str
    merchant_id: str
    merchant_name: str = ""
    title: str = ""
    discount: Dict[str, float] = field(default_factory=dict)        # rate 折扣率 或 amount_off 直减
    rebate: Dict[str, float] = field(default_factory=dict)          # 即时小额让利（rate/amount/cap）
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    stores: List[str] = field(default_factory=list)                 # 可核销门店
    conditions: Dict[str, Any] = field(default_factory=dict)        # 核销条件（min_spend/时段/人群）
    budget_ceiling: float = 0.0                                     # ≤历史预算（预算平移约束）
    scene_type: str = "retail"                                      # 场景维度（接 CCA D_scene）
    six_elements: Dict[str, str] = field(default_factory=dict)      # NS-007 六要素
    provenance: str = "SIMULATED"                                   # ID92

    def to_dict(self) -> dict:
        return {
            "benefit_id": self.benefit_id,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "title": self.title,
            "discount": self.discount,
            "rebate": self.rebate,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "stores": self.stores,
            "conditions": self.conditions,
            "budget_ceiling": self.budget_ceiling,
            "scene_type": self.scene_type,
            "six_elements": self.six_elements,
            "provenance": self.provenance,
            "schema": "TDCA-MERCHANT-LOOP-BENEFIT-001",
            "boundary": "双边消费交易（不进 CLS）；无资产/无杠杆/无升值承诺",
        }


@dataclass(frozen=True)
class RedemptionEvent:
    """核销事件（A-2 核销闭环输入）。"""
    redemption_id: str
    benefit_id: str
    merchant_id: str
    store: str
    consumer_id: str
    amount: float                     # 实际消费金额（核销真实性三证据之一：金额）
    discount_applied: float = 0.0
    rebate_paid: float = 0.0
    occurred_at: Optional[str] = None
    evidence: Dict[str, str] = field(default_factory=dict)   # LBS/小票/商家确认 三方证据位
    provenance: str = "SIMULATED"

    def to_dict(self) -> dict:
        return {
            "redemption_id": self.redemption_id,
            "benefit_id": self.benefit_id,
            "merchant_id": self.merchant_id,
            "store": self.store,
            "consumer_id": self.consumer_id,
            "amount": round(self.amount, 4),
            "discount_applied": round(self.discount_applied, 4),
            "rebate_paid": round(self.rebate_paid, 4),
            "occurred_at": self.occurred_at,
            "evidence": self.evidence,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class RedemptionResult:
    """核销结果（A-2：核销 NCA 落证 + CCA 贡献值记账预留）。"""
    event: RedemptionEvent
    redemption_nca_id: str
    cca_contribution: Dict[str, Any]     # CCA 预留记账（SIMULATED——贡献值 f 形式 M3 定形，不冒充定标）
    net_merchant_cost: float              # 商家让利成本 = discount_applied + rebate_paid
    no_cls: bool = True

    def to_dict(self) -> dict:
        d = self.event.to_dict()
        d.update({
            "redemption_nca_id": self.redemption_nca_id,
            "cca_contribution": self.cca_contribution,
            "net_merchant_cost": round(self.net_merchant_cost, 4),
            "no_cls": self.no_cls,
            "channel": "cca",   # 结算通道标记（M2 §三：消费侧 CCA 主通道）
        })
        return d


class MerchantLoopEngine:
    """merchant_loop 权益生命周期引擎（发布校验 + 核销闭环）。"""

    def __init__(self, default_provenance: str = "SIMULATED"):
        self._provenance = default_provenance

    # ---- 发布：权益模板校验（A-1）----

    def validate_template(self, raw: Dict[str, Any],
                          provenance: Optional[str] = None) -> BenefitTemplate:
        """校验并构建权益模板（YAML 解析后传入）。

        校验: 必填（benefit_id/merchant_id/discount 或 rebate 至少一）+ 负空间红线词检测
              + 预算平移约束（budget_ceiling 可缺省=0，允许）+ 六要素声明完整性。
        """
        if not isinstance(raw, dict):
            raise ValueError("[NSFL-TRIGGER] 权益配置必须为对象（YAML mapping）")

        # 红线词检测（否定感知：'无杠杆/不承诺升值/禁止回购' 等否定声明不触发——
        # 只有把红线机制作为正向卖点/承诺才拒绝，防误伤合规声明）
        forbidden = self._detect_forbidden(raw)
        if forbidden:
            raise ValueError(
                f"[NSFL-TRIGGER] 权益模板含红线词（无资产化）：{forbidden}——发布拒绝"
            )

        benefit_id = raw.get("benefit_id")
        merchant_id = raw.get("merchant_id")
        if not benefit_id or not merchant_id:
            raise ValueError("[NSFL-TRIGGER] 必填缺失: benefit_id / merchant_id")

        discount = raw.get("discount") or {}
        rebate = raw.get("rebate") or {}
        if not discount and not rebate:
            raise ValueError("[NSFL-TRIGGER] discount 与 rebate 至少提供一者（权益=让利结构）")
        self._check_numeric_fields(discount, ALLOWED_DISCOUNT_KEYS, "discount")
        self._check_numeric_fields(rebate, ALLOWED_REBATE_KEYS, "rebate")

        stores = raw.get("stores")
        if stores is not None and (not isinstance(stores, list) or not stores):
            raise ValueError("[NSFL-TRIGGER] stores 须为非空列表（可核销门店）")

        scene = raw.get("scene_type", "retail")
        if scene not in SCENE_TYPES:
            raise ValueError(f"[NSFL-TRIGGER] 非法场景类型: {scene}（可选 {SCENE_TYPES}）")

        # 有效期合法性
        vf, vu = raw.get("valid_from"), raw.get("valid_until")
        if vf and vu and vf > vu:
            raise ValueError("[NSFL-TRIGGER] valid_from 晚于 valid_until")

        # 六要素声明（NS-007；缺失提示补录——发布即契约要求）
        six = {k: str(raw.get(k, "")).strip() for k in SIX_ELEMENTS}
        missing = [k for k in SIX_ELEMENTS if not six[k]]
        if missing:
            raise ValueError(f"[NSFL-TRIGGER] 六要素声明缺失: {missing}——发布即契约（NS-007）")

        budget = raw.get("budget_ceiling", 0.0)
        if not isinstance(budget, (int, float)) or budget < 0:
            raise ValueError("[NSFL-TRIGGER] budget_ceiling 非法（预算平移=≤历史预算，须非负）")

        return BenefitTemplate(
            benefit_id=benefit_id,
            merchant_id=merchant_id,
            merchant_name=str(raw.get("merchant_name", "")),
            title=str(raw.get("title", "")),
            discount={k: float(v) for k, v in discount.items() if v is not None},
            rebate={k: float(v) for k, v in rebate.items() if v is not None},
            valid_from=vf, valid_until=vu,
            stores=list(stores) if stores else [],
            conditions=raw.get("conditions") or {},
            budget_ceiling=float(budget),
            scene_type=scene,
            six_elements=six,
            provenance=provenance or self._provenance,
        )

    # ---- 核销闭环（A-2）----

    def redeem(self, template: BenefitTemplate, event: RedemptionEvent,
               redemption_nca_id: str) -> RedemptionResult:
        """核销处理：校验权益有效性 → 计算让利 → CCA 贡献值预留记账。

        核销真实性证据位（evidence: lbs/receipt/merchant_confirm）由调用方填充——
        本引擎不代验（M3 沙盒/CCA 资助检测承接执行层验证，防伪造；此处仅记账）。
        """
        if event.benefit_id != template.benefit_id:
            raise ValueError("[NSFL-TRIGGER] 核销 benefit_id 与权益模板不符")
        if event.merchant_id != template.merchant_id:
            raise ValueError("[NSFL-TRIGGER] 核销 merchant_id 与权益模板不符")
        if template.stores and event.store not in template.stores:
            raise ValueError(f"[NSFL-TRIGGER] 门店不可核销: {event.store}")
        if not isinstance(event.amount, (int, float)) or event.amount <= 0:
            raise ValueError("[NSFL-TRIGGER] 非法消费金额（须 >0）")
        if template.valid_until and self._now_str() > template.valid_until:
            raise ValueError("[NSFL-TRIGGER] 权益已过期")
        min_spend = (template.conditions or {}).get("min_spend")
        if min_spend is not None and event.amount < float(min_spend):
            raise ValueError(f"[NSFL-TRIGGER] 未达最低消费: {min_spend}")

        discount = self._apply_discount(template.discount, event.amount)
        rebate = self._apply_rebate(template.rebate, event.amount)
        net_cost = round(discount + rebate, 4)

        # CCA 贡献值记账预留（SIMULATED——f 具体形式 R-7 M3 定形，本包不冒充定标）
        cca = {
            "status": "recorded_simulated",
            "consumer_id": event.consumer_id,
            "scene_type": template.scene_type,
            "amount_basis": round(event.amount, 4),
            "contribution_formula": "CCA_i += f(amount, verif, scene)——f 待 R-7 M3 定形",
            "verif_evidence_required": ("lbs", "receipt", "merchant_confirm"),
            "provenance": "SIMULATED",
            "channel": "cca",
        }

        return RedemptionResult(
            event=event,
            redemption_nca_id=redemption_nca_id,
            cca_contribution=cca,
            net_merchant_cost=net_cost,
            no_cls=True,
        )

    # ---- 内部工具 ----

    _NEGATION_PREFIXES = ("无", "不", "非", "禁", "防", "剥离", "剔除", "拒", "零", "未")

    @classmethod
    def _detect_forbidden(cls, raw: Dict[str, Any]) -> List[str]:
        """否定感知红线词检测。

        遍历模板全部字符串值，命中 FORBIDDEN_TERMS 时向前看最近 ~3 字符：
        若紧邻否定前缀（'无杠杆/不承诺升值/禁止回购'）→ 判定为合规否定声明，不触发；
        否则（红线机制作为正向卖点/承诺）→ 判违规。
        """
        hits: List[str] = []
        text_parts: List[str] = []

        def collect(v: Any) -> None:
            if isinstance(v, str):
                text_parts.append(v)
            elif isinstance(v, dict):
                for sub in v.values():
                    collect(sub)
            elif isinstance(v, list):
                for sub in v:
                    collect(sub)

        collect(raw)
        text = "\n".join(text_parts)
        for term in FORBIDDEN_TERMS:
            idx = text.find(term)
            while idx != -1:
                before = text[max(0, idx - 3):idx]
                negated = any(p in before for p in cls._NEGATION_PREFIXES)
                if not negated:
                    if term not in hits:
                        hits.append(term)
                    break  # 该词已有正向命中即可
                idx = text.find(term, idx + len(term))
        return hits

    @staticmethod
    def _check_numeric_fields(mapping: Dict[str, Any], allowed, label: str) -> None:
        for k, v in mapping.items():
            if k not in allowed:
                raise ValueError(f"[NSFL-TRIGGER] {label} 非法字段: {k}（允许 {allowed}）")
            if not isinstance(v, (int, float)) or v < 0:
                raise ValueError(f"[NSFL-TRIGGER] {label}.{k} 非法值（须非负数值）")

    @staticmethod
    def _apply_discount(discount: Dict[str, float], amount: float) -> float:
        if not discount:
            return 0.0
        if "rate" in discount:
            rate = float(discount["rate"])
            if not (0 < rate < 1):
                raise ValueError("[NSFL-TRIGGER] discount.rate 须在 (0,1)")
            return amount * rate
        if "amount_off" in discount:
            return min(float(discount["amount_off"]), amount)
        return 0.0

    @staticmethod
    def _apply_rebate(rebate: Dict[str, float], amount: float) -> float:
        if not rebate:
            return 0.0
        value = 0.0
        if "rate" in rebate:
            rate = float(rebate["rate"])
            if not (0 < rate < 1):
                raise ValueError("[NSFL-TRIGGER] rebate.rate 须在 (0,1)")
            value = amount * rate
        elif "amount" in rebate:
            value = float(rebate["amount"])
        if "cap" in rebate:
            value = min(value, float(rebate["cap"]))
        return value

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d")
