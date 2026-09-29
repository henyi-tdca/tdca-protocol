# -*- coding: utf-8 -*-
"""micro-delivery 微交付域实体（M-4 骨架，M1 先行落地交付/税收/净额/预缴状态）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class DeliveryCallType(str, Enum):
    """微交付调用类型（对齐 CALL-RULES CallType 语义，双通道）。"""
    DISPOSABLE = "disposable"   # 日抛交付：物理叠加通道
    COMPOUND = "compound"       # 化合交付：化学反应通道


class TaxEventType(str, Enum):
    """税收事件类型（M-1 V2 分档结构，数值统一映射 CALL-001 三档）。

    裁决（DCD-MICROTAX-003 裁决①）: 分档结构采纳；税率数值一律来自
    CALL-001 签批默认值（调度税 2%/版税 7.5%/交易费 0.75%，模拟态 D-011）。
    """
    CONFIG_RIGHT_CALL = "config_right_call"       # 配置权调用 → 调度税
    NCA_COMPOUND = "nca_compound"                 # NCA 化合 → 调度税 + 版税
    SKILL_INVOCATION = "skill_invocation"         # Skill 调用 → 调度税 + 交易费
    CROSS_DOMAIN_TRANSFER = "cross_domain_transfer"  # 跨域转让 → 调度税 + 交易费
    ESCROW_RELEASE = "escrow_release"             # 托管释放 → 交易费
    NEGATIVE_SPACE_FUSE = "negative_space_fuse"   # 负空间熔断 → 归零


class DeliveryForm(str, Enum):
    """交付形态（领域二，M-6 状态机输入）。"""
    ONLINE = "online"       # 线上事实交付（基本无延迟）
    OFFLINE = "offline"     # 线下事实交付（线上达成须线下完成才能结算）
    HYBRID = "hybrid"       # 混合交付


class DisputeStatus(str, Enum):
    """争议状态（领域二，M-7 联动输入）。"""
    NONE = "none"           # 无争议
    DISPUTED = "disputed"   # 争议中（交付后有争议）
    ARBITRATING = "arbitrating"   # 仲裁/诉讼中
    ARBITRATED = "arbitrated"     # 已裁决
    CREDIT_ADJUSTED = "credit_adjusted"   # 过错方增信/保险联动已执行


@dataclass
class MicroDelivery:
    """微交付域实体（M-4）——交付计量 → 税收 → 净额 → 预缴状态全生命周期。

    纪律: 税款账户托管隔离（F-4/BV-3）；模拟态显式标注（ID92，D-011）。
    """
    delivery_id: str
    scene: str
    value: float                                   # 交付经济价值（元，gross）
    call_type: DeliveryCallType = DeliveryCallType.DISPOSABLE
    royalty_base: float = 0.0                      # 版税基数（化合交付可用，默认 0=无版税）
    participants: Dict[str, float] = field(default_factory=dict)  # 参与方贡献（M-3 Shapley 输入）
    taxes: Optional[dict] = None                   # 计税结果 T(y_t) 分项 + total（M-1 输出）
    net_value: float = 0.0                         # 税后净额 = value − total（M-1 输出）
    prepay_status: str = "PENDING"                 # PENDING / PREPAID / VERIFIED / FAIL_CLOSED（M-2 输出）
    prepay_ref: Optional[str] = None               # 预缴记录引用（M-2）
    simulated: bool = True                         # ID92 模拟态标注（D-011）
    # ---- V2 扩展字段（TDCA-TASK-MICROTAX-002，向后兼容——默认值不影响 V1 构造）----
    event_type: TaxEventType = TaxEventType.CONFIG_RIGHT_CALL   # M-1 V2 事件分档
    tax_in: float = 0.0                            # 进项税贡献事实（买方/调用方）
    tax_out: float = 0.0                           # 出项税贡献事实（卖方/被调用方）
    delivery_form: DeliveryForm = DeliveryForm.ONLINE          # 领域二交付形态
    dispute_status: DisputeStatus = DisputeStatus.NONE         # 领域二争议状态
    tax_fact_recorded: bool = False                # 纳税事实记录（成立即记录，不随税额归零丢失）
    # ---- TAXLAW-001 扩展（法规决策依据）----
    tax_violation: Optional[str] = None            # 显式违规模式（tax_evasion/fraud_refund/bypass_mou/false_report）

    @property
    def tax_total(self) -> float:
        """计税合计 T(y_t)（未计税返回 0.0）。"""
        if not self.taxes:
            return 0.0
        return float(self.taxes.get("total", 0.0))

    @property
    def mou_value(self) -> float:
        """MOU = 进项 + 出项（双向贡献硬下限，ID79）。"""
        return round(self.tax_in + self.tax_out, 2)

    @property
    def mou_anchor_ok(self) -> bool:
        """MOU 硬锚定（ID79）：T(y_t) > 0 恒成立（A-4）。"""
        return self.tax_total > 0
