# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-20260811-003-CALL-RULES
# 目标函数:     商业调用规则引擎（日抛判定/MOU 验证/税收计算/调用记录）
# 约束矩阵:     ID77 + ID79（T(y_t)>0 归零）+ ID84 + ID90 + ID71 + NSFL-V0.2
# 先验分布:     TDCA-PRICING-001-V1.0 + TDCA-PRINCIPLE-ENG-010
# 配置权边界:    L2 配置权市场层；税收锚定模拟态（D-011）
# 预期分配:     调用判定结果 + 税收明细 + 调用记录
# 审计轨迹:      TDCA-NCA-20260811-008-CALL-RULES
# 开发者:       [人类签批人]
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# 模拟态标注（ID92）: 本引擎为规则执行工具，税收为模拟计算，不构成真实配置权执行路径
# =============================================================================
"""TDCA 商业调用规则引擎 V1.0.0

依据 TDCA-PRICING-001（四层定价）+ TDCA-PRINCIPLE-ENG-010（核心三角）执行商业调用规则：
- 日抛判定（ID90）：物理叠加优先，三条件通过才化合
- MOU 硬锚定（ID79）：T(y_t) > 0 否则价格强制归零
- 停机定理（ID84）：正和交付的充分解
- 税收计算（L3）：配置权调度税 1-3% + 知识版税 5-10% + 交易手续费 0.5-1%
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class CallType(str, Enum):
    """商业调用类型（PRINCIPLE-ENG-010 双通道）。"""
    DISPOSABLE = "disposable"   # 日抛调用：物理叠加通道
    COMPOUND = "compound"       # 化合调用：化学反应通道


class CallVerdict(str, Enum):
    """调用裁决（ID84 停机/NSFL 熔断）。"""
    APPROVED = "APPROVED"               # 通过：正和交付
    ZEROED = "ZEROED"                   # MOU 归零：T(y_t) <= 0
    FUSED = "FUSED"                     # 负空间熔断
    REJECTED = "REJECTED"               # 其他拒绝（非正和等）


@dataclass
class TaxRates:
    """L3 资产层税率（PRICING-001）。"""
    dispatch_tax: float = 0.02      # 配置权调度税 1-3%，默认 2%
    royalty: float = 0.075          # 知识永久版税 5-10%，默认 7.5%
    trade_fee: float = 0.0075       # NCA 交易手续费 0.5-1%，默认 0.75%


@dataclass
class CallRequest:
    """商业调用请求。"""
    caller: str
    scene: str
    call_value: float               # 调用经济价值（元）
    can_stack: bool = True          # 物理叠加可覆盖？
    is_disposable: Optional[bool] = None   # 日抛标记（显式指定时跳过 ID90 判定）
    tax_receipt: float = 0.0        # 可验证税收锚定 T(y_t)（模拟态，对应 cbdc_anchor 参数）
    violates_nsfl: bool = False     # 是否触碰负空间
    # ID90 三条件（化合判定闸门，PRINCIPLE-ENG-010 §2.4）
    indivisibility: bool = False    # 不可拆分性：移除任一阶资产，解决方案消失
    emergence: bool = False         # 涌现价值：化合产物效用 > 独立效用加总
    nonlinearity: bool = False      # 非线性：任意加权组合无法逼近产物性质


@dataclass
class CallRecord:
    """调用记录（NCA 存证关联）。"""
    call_id: str
    caller: str
    scene: str
    call_type: CallType
    verdict: CallVerdict
    gross_value: float
    taxes: dict = field(default_factory=dict)
    net_value: float = 0.0
    timestamp: str = ""
    # 字段同构（与 dual-nca.json / nca-template.yaml 对齐，REV-CALL-001 M2）
    mou_anchor: dict = field(default_factory=lambda: {
        "status": "Simulated",
        "inbound_tax": None,
        "outbound_tax": None,
        "note": "模拟态 D-011，真实锚定待 DCEP 接入",
    })
    nsfl_version: str = "V0.2"
    data_nature: str = "simulated"   # ID92 真实/模拟隔离（REV-CALL-001 L4）


class CallRulesEngine:
    """商业调用规则引擎。"""

    def __init__(self, rates: Optional[TaxRates] = None):
        self.rates = rates or TaxRates()
        self.records: List[CallRecord] = []
        self._seq = 0

    # ---- Step 2: 日抛判定（ID90）----

    def judge_disposable(self, req: CallRequest) -> Optional[CallType]:
        """日抛判定（ID90）：物理叠加可覆盖 → 日抛；否则三条件全过才化合。

        三条件闸门（PRINCIPLE-ENG-010 §2.4）：不可拆分性/涌现价值/非线性全过 → COMPOUND；
        任一未过 → None（拒绝化合，避免过度设计违规）。
        显式 is_disposable=False 同样须过三条件闸门（可用物理叠加却强制化合 = 过度设计违规）。
        """
        if req.is_disposable is True:
            return CallType.DISPOSABLE
        # is_disposable=False 或物理叠加不可覆盖：走 ID90 三条件闸门
        if req.is_disposable is False or not req.can_stack:
            if req.indivisibility and req.emergence and req.nonlinearity:
                return CallType.COMPOUND
            return None
        # 物理叠加可覆盖（默认日抛）
        return CallType.DISPOSABLE

    # ---- Step 4: MOU 预计算（ID79 归零规则）----

    def validate_mou(self, req: CallRequest) -> bool:
        """MOU 硬锚定：T(y_t) > 0 才有效（TDCA-PRINCIPLE-MOU-001）。"""
        return req.tax_receipt > 0

    # ---- Step 5: 正和验证（ID77）----

    @staticmethod
    def validate_positive_sum(gross_value: float, cost: float) -> bool:
        """正和验证：调用价值 > 成本（充分解，非最优解 ID84）。"""
        return gross_value > cost

    # ---- Step 7: 税收计算（L3）----

    def compute_taxes(self, call_type: CallType, value: float, royalty_base: float = 0.0) -> dict:
        """L3 税收计算（模拟态 D-011）。"""
        taxes = {
            "dispatch_tax": round(value * self.rates.dispatch_tax, 2),
        }
        if call_type == CallType.COMPOUND:
            taxes["royalty"] = round(royalty_base * self.rates.royalty, 2)
        return taxes

    # ---- 主流程 ----

    def execute_call(self, req: CallRequest, cost: float = 0.0) -> CallRecord:
        """执行商业调用全流程（8 步，模拟态）。"""
        self._seq += 1
        call_id = f"CALL-{datetime.now().strftime('%Y%m%d')}-{self._seq:04d}"
        ts = datetime.now().isoformat()

        # Step 0: 负空间熔断预检（NSFL-V0.2，文档 §四 前置分支）
        if req.violates_nsfl:
            rec = CallRecord(call_id, req.caller, req.scene, CallType.DISPOSABLE,
                             CallVerdict.FUSED, req.call_value, {}, 0.0, ts)
            self.records.append(rec)
            return rec

        # Step 2: 日抛判定（ID90，三条件闸门）
        call_type = self.judge_disposable(req)
        if call_type is None:
            # ID90 三条件未全过：拒绝化合（避免过度设计违规）
            rec = CallRecord(call_id, req.caller, req.scene, CallType.DISPOSABLE,
                             CallVerdict.REJECTED, req.call_value, {}, 0.0, ts)
            self.records.append(rec)
            return rec

        # Step 4: MOU 硬锚定（ID79 归零规则）
        if not self.validate_mou(req):
            rec = CallRecord(call_id, req.caller, req.scene, call_type,
                             CallVerdict.ZEROED, req.call_value, {}, 0.0, ts)
            self.records.append(rec)
            return rec

        # Step 5: 正和验证（ID77/ID84）
        if not self.validate_positive_sum(req.call_value, cost):
            rec = CallRecord(call_id, req.caller, req.scene, call_type,
                             CallVerdict.REJECTED, req.call_value, {}, 0.0, ts)
            self.records.append(rec)
            return rec

        # Step 7: 税收扣缴（L3）
        taxes = self.compute_taxes(call_type, req.call_value, royalty_base=req.call_value)
        net = round(req.call_value - sum(taxes.values()), 2)

        rec = CallRecord(call_id, req.caller, req.scene, call_type,
                         CallVerdict.APPROVED, req.call_value, taxes, net, ts)
        self.records.append(rec)
        return rec

    # ---- 查询 ----

    def summary(self) -> dict:
        """调用汇总（审计）。"""
        approved = [r for r in self.records if r.verdict == CallVerdict.APPROVED]
        return {
            "total_calls": len(self.records),
            "approved": len(approved),
            "zeroed": len([r for r in self.records if r.verdict == CallVerdict.ZEROED]),
            "fused": len([r for r in self.records if r.verdict == CallVerdict.FUSED]),
            "total_dispatch_tax": round(sum(r.taxes.get("dispatch_tax", 0) for r in approved), 2),
            "total_royalty": round(sum(r.taxes.get("royalty", 0) for r in approved), 2),
        }


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="TDCA 商业调用规则引擎（模拟态）")
    parser.add_argument("--caller", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--value", type=float, required=True, help="调用经济价值（元）")
    parser.add_argument("--tax", type=float, default=100.0, help="可验证税收锚定 T(y_t)（模拟）")
    parser.add_argument("--no-stack", action="store_true", help="物理叠加不可覆盖（化合判定）")
    parser.add_argument("--indivisibility", action="store_true", help="ID90 不可拆分性")
    parser.add_argument("--emergence", action="store_true", help="ID90 涌现价值")
    parser.add_argument("--nonlinearity", action="store_true", help="ID90 非线性")
    parser.add_argument("--cost", type=float, default=0.0, help="调用成本")
    parser.add_argument("--violates-nsfl", action="store_true", help="触碰负空间")
    args = parser.parse_args()

    engine = CallRulesEngine()
    req = CallRequest(
        caller=args.caller, scene=args.scene, call_value=args.value,
        can_stack=not args.no_stack, tax_receipt=args.tax, violates_nsfl=args.violates_nsfl,
        indivisibility=args.indivisibility, emergence=args.emergence, nonlinearity=args.nonlinearity,
    )
    rec = engine.execute_call(req, cost=args.cost)
    print(json.dumps({
        "call_id": rec.call_id, "scene": rec.scene, "type": rec.call_type.value,
        "verdict": rec.verdict.value, "gross": rec.gross_value,
        "taxes": rec.taxes, "net": rec.net_value,
        "mou_anchor": rec.mou_anchor, "nsfl_version": rec.nsfl_version,
        "data_nature": rec.data_nature,   # ID92 模拟态标注（REV-CALL-001 L4）
    }, ensure_ascii=False, indent=2))
    return 0 if rec.verdict == CallVerdict.APPROVED else 2


if __name__ == "__main__":
    sys.exit(main())
