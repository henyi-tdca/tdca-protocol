# -*- coding: utf-8 -*-
"""M-6 领域二交付结算状态机：合约形态 × 交付形态（线上/线下/混合）。

领域二（用户论述）: 智能体调用后执行的智能合约事实交付所产生的税收——
合约可能一对一/一对多/多对一/三方或多边；线上事实交付基本无延迟；
线下事实交付须线上达成后线下完成才能结算；混合交付。

制度锚定:
  - A-8 状态机矩阵: 线上/线下/混合 × 合约形态 100% 正确；未完成线下交付禁止结算
  - 预收/预缴处理: 达成（agree）时检查税收预缴已处理（快系统有效性保障）
  - 结算: 完成后才允许（税后净额 → M-3 正和结算衔接）
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .models import DeliveryForm, DisputeStatus, MicroDelivery


class ContractForm(str, Enum):
    """合约形态（领域二）。"""
    ONE_TO_ONE = "1-1"        # 一对一
    ONE_TO_MANY = "1-n"       # 一对多
    MANY_TO_ONE = "n-1"       # 多对一
    MULTILATERAL = "n-n"      # 三方或多边


class DeliveryState(str, Enum):
    """交付结算状态。"""
    AGREED = "agreed"                 # 线上达成（税收预收/预缴已处理）
    OFFLINE_PENDING = "offline_pending"     # 线下交付待完成
    OFFLINE_COMPLETED = "offline_completed"  # 线下交付完成
    SETTLED = "settled"               # 结算完成
    DISPUTED = "disputed"             # 争议中（M-7 联动）


@dataclass
class SettlementResult:
    """结算结果（审计轨迹）。"""
    delivery_id: str
    contract_form: ContractForm
    delivery_form: DeliveryForm
    state: DeliveryState
    transitions: List[str]
    settled: bool
    prepay_ok: bool
    dispute: bool = False


class DeliverySettlementStateMachine:
    """M-6 领域二交付结算状态机（模拟态 D-011）。"""

    def __init__(self, contract_form: ContractForm,
                 delivery_form: DeliveryForm):
        self.contract_form = contract_form
        self.delivery_form = delivery_form
        self.state = DeliveryState.AGREED
        self._transitions: List[str] = ["agreed"]

    # ---- 状态推进 ----

    def agree(self, delivery: MicroDelivery) -> SettlementResult:
        """线上达成: 校验税收预缴已处理（快系统有效性——预收/预缴在达成时处理）。

        :raises ValueError: 未预缴（ID79 税款不得绕过预缴）
        """
        if delivery.prepay_status not in ("PREPAID", "VERIFIED"):
            raise ValueError(
                f"[NSFL-TRIGGER] 达成时未预缴（status={delivery.prepay_status}），"
                "税收预收/预缴须在达成时处理（ID79）")
        if delivery.event_type.value == "negative_space_fuse":
            raise ValueError("[NSFL-TRIGGER] 负空间熔断交付，禁止进入结算流程")

        self.state = DeliveryState.AGREED
        self._transitions.append("agreed")
        return self._result(delivery)

    def complete_offline(self, delivery: MicroDelivery) -> SettlementResult:
        """线下事实交付完成（仅 OFFLINE/HYBRID 可调用；ONLINE 即时交付跳过）。"""
        if self.delivery_form == DeliveryForm.ONLINE:
            # 线上交付无线下环节——幂等返回当前态
            return self._result(delivery)
        if self.state in (DeliveryState.OFFLINE_COMPLETED, DeliveryState.SETTLED):
            return self._result(delivery)
        if self.state != DeliveryState.AGREED:
            raise ValueError(f"[NSFL-TRIGGER] 非法线下完成状态: {self.state.value}")

        self.state = DeliveryState.OFFLINE_COMPLETED
        self._transitions.append("offline_completed")
        return self._result(delivery)

    def settle(self, delivery: MicroDelivery) -> SettlementResult:
        """结算（A-8 核心）:

        - ONLINE: agreed → settled（即时结算）
        - OFFLINE/HYBRID: 必须线下完成（offline_completed）才可结算——
          未完成线下交付禁止结算
        - 结算后 delivery.prepay_status → VERIFIED（预缴确认）
        """
        if self.state == DeliveryState.DISPUTED:
            raise ValueError("[NSFL-TRIGGER] 争议中禁止结算（须先仲裁，M-7）")

        if self.delivery_form == DeliveryForm.ONLINE:
            # 线上即时交付: 达成即可结算（预缴已在达成时处理）
            ok = self.state == DeliveryState.AGREED
        else:
            # 线下/混合: 必须线下完成
            ok = self.state == DeliveryState.OFFLINE_COMPLETED

        if not ok:
            raise ValueError(
                f"[NSFL-TRIGGER] 未完成线下交付禁止结算（{self.delivery_form.value} "
                f"状态={self.state.value}，A-8）")

        self.state = DeliveryState.SETTLED
        self._transitions.append("settled")
        delivery.prepay_status = "VERIFIED"   # 预缴确认（M-3 正和结算衔接）
        return self._result(delivery)

    def dispute(self, delivery: MicroDelivery, reason: str) -> SettlementResult:
        """争议挂起（转 M-7 仲裁链路）。"""
        self.state = DeliveryState.DISPUTED
        delivery.dispute_status = DisputeStatus.DISPUTED
        self._transitions.append(f"disputed:{reason}")
        return self._result(delivery)

    # ---- 内部 ----

    def _result(self, delivery: MicroDelivery) -> SettlementResult:
        return SettlementResult(
            delivery_id=delivery.delivery_id,
            contract_form=self.contract_form,
            delivery_form=self.delivery_form,
            state=self.state,
            transitions=list(self._transitions),
            settled=self.state == DeliveryState.SETTLED,
            prepay_ok=delivery.prepay_status in ("PREPAID", "VERIFIED"),
            dispute=self.state == DeliveryState.DISPUTED,
        )
