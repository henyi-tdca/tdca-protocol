"""cypress_pool · Cypress 配置权计量 reporter 插件（DCD-CYPRESS-POOL-001 M1a，A 配置资产池）

Cypress（cypress-io/cypress，MIT，50,983 stars）是 E2E 测试框架——
工具/基础设施型，保留 MIT 生态独立性，TDCA 治理层叠加（路径 A 配置资产池）。

M1a 功能:
  - parse_test_run: 解析 Cypress 测试运行结果（specs/tests/pass-fail）
  - metering: 测试运行 → 配置权计量（计费口径）
  - build_metric_nca: 执行轨迹 → NCA 存证
  - l2_market: 计量结果 → L2 配置权市场对接（计费 + MOU 锚定）

制度锚定: PATH-001（A 配置资产池）/ CALL-001（L2 配置权市场）/ BIDIR-001 / ID92
NSFL-Declaration:
  - 不修改 Cypress 核心（reporter 插件叠加——物理叠加层，BIDIR-001 形态 ①）
  - 计量为模拟口径（SIMULATED），真实计费需接入 L2 市场结算
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# 配置权计量参数（CALL-001 L3 资产层：调度税 1-3% 默认 2%）
SCHEDULE_TAX_RATE = 0.02


@dataclass(frozen=True)
class MeteredRun:
    """测试运行配置权计量结果。"""
    run_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    metered_value: float          # 计量价值（计费口径）
    schedule_tax: float           # 调度税（1-3%，默认 2%）

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": round(self.pass_rate, 4),
            "metered_value": round(self.metered_value, 4),
            "schedule_tax": round(self.schedule_tax, 4),
        }


@dataclass(frozen=True)
class L2MarketOrder:
    """L2 配置权市场对接订单（计费 + MOU 锚定）。"""
    order_id: str
    run_id: str
    asset_id: str
    config_right_tier: str        # 四档：基础/商用/生态/协议
    billing_amount: float
    mou_anchor: str               # MOU 锚定（模拟）
    status: str

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "run_id": self.run_id,
            "asset_id": self.asset_id,
            "config_right_tier": self.config_right_tier,
            "billing_amount": round(self.billing_amount, 4),
            "mou_anchor": self.mou_anchor,
            "status": self.status,
        }


class CypressPoolAdapter:
    """Cypress 配置权计量 reporter（M1a，A 配置资产池）。"""

    def __init__(self, provenance: str = "SIMULATED",
                 schedule_tax_rate: float = SCHEDULE_TAX_RATE,
                 unit_price: float = 1.0):
        self._provenance = provenance
        self._tax_rate = schedule_tax_rate
        self._unit_price = unit_price

    # ---- 解析 ----

    def parse_test_run(self, raw: str) -> dict:
        """解析 Cypress 测试运行结果。"""
        if not raw or not raw.strip():
            raise ValueError("[NSFL-TRIGGER] 空测试运行结果")
        data = json.loads(raw)
        if "tests" not in data or not isinstance(data["tests"], list):
            raise ValueError("[NSFL-TRIGGER] 测试结果缺 tests 数组")
        return data

    # ---- 计量（A-1）----

    def metering(self, run: dict, unit_price: Optional[float] = None) -> MeteredRun:
        """测试运行 → 配置权计量。

        计费口径: metered_value = passed_tests × unit_price（配置权计量基础）
                  schedule_tax = metered_value × 税率（L3 资产层，CALL-001）
        """
        tests = run["tests"]
        total = len(tests)
        passed = sum(1 for t in tests if t.get("status") == "passed")
        failed = total - passed
        pass_rate = passed / total if total else 0.0
        price = unit_price if unit_price is not None else self._unit_price
        value = passed * price
        return MeteredRun(
            run_id=run.get("run_id", "run-1"),
            total_tests=total, passed_tests=passed, failed_tests=failed,
            pass_rate=pass_rate, metered_value=value,
            schedule_tax=value * self._tax_rate,
        )

    # ---- NCA 存证（A-2）----

    def build_metric_nca(self, meter: MeteredRun) -> dict:
        """执行轨迹 → NCA 存证。"""
        ts = datetime.now(timezone.utc)
        return {
            "NCA-ID": f"NCA-CYPRESS-{ts.strftime('%Y%m%d')}-001",
            "Operation-Type": "Test-Metering",
            "Timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Scope": f"Cypress 测试运行配置权计量存证（{meter.run_id}）",
            "Metered-Run": meter.to_dict(),
            "Provenance": self._provenance,
        }

    # ---- L2 市场对接（M1b）----

    def l2_market_order(self, meter: MeteredRun, asset_id: str = "cypress-io-cypress",
                        tier: str = "基础") -> L2MarketOrder:
        """计量结果 → L2 配置权市场订单（计费 + MOU 锚定）。

        四档（CALL-001）：基础/商用/生态/协议。
        billing_amount = metered_value + schedule_tax（L3 资产层自动扣缴模拟）。
        """
        order_id = hashlib.sha256(
            f"{meter.run_id}:{asset_id}:{datetime.now(timezone.utc).isoformat()}"
            .encode()).hexdigest()[:16]
        return L2MarketOrder(
            order_id=order_id, run_id=meter.run_id, asset_id=asset_id,
            config_right_tier=tier,
            billing_amount=meter.metered_value + meter.schedule_tax,
            mou_anchor="SIMULATED-MOU（真实计费需 L2 市场结算接入）",
            status="PENDING_SETTLEMENT",
        )
