"""util_value · M2 入表服务化（DCD-UTIL-VALUE-001 §五 M2）

三件套:
  1. 入表报告模板（对接会计口径——无形资产科目/入账金额/依据/期间）
  2. 版权链存证上链（版权链·天平链锚定——存证接口 + 模拟上链，真实上链需外部通道）
  3. 对外服务接口（API + CLI 扩展）

复用: UtilValueService（M1 评估引擎：observable_floor/tier_assessment/safety_check）
制度锚定: TDCA-UTILITY-OBSERVABLE-001（可观测下限地板）/ 版权链·天平链（法律赋予+存证）
         / MOU 地板语义（MEMO-006-Audit）/ ID92（数据性质标注）
NSFL-Declaration:
  - 入表报告只含可观测下限（地板），不含主观估值（会计入账依据）
  - 版权链上链为模拟通道（真实上链需司法链运营方接入——不冒充已上链）
  - 真实交易数据按来源标注；合成数据 SIMULATED
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .engine import UtilValueService

# 会计科目口径（无形资产核算常见科目）
ACCOUNT_INTANGIBLE = "无形资产-版权资产"
ACCOUNT_CWIP = "在建工程-版权资产"      # 未完成形成
ACCOUNT_RD = "研发支出-版权开发"

# 入表类型
ENTRY_CAPITALIZE = "资本化入表"         # 有可观测下限支撑
ENTRY_EXPENSE = "费用化"                # 无下限支撑（U_observed=0）


@dataclass(frozen=True)
class AccountingEntry:
    """会计入表建议（地板锚定，MOU 语义）。"""
    asset_id: str
    account: str
    entry_type: str              # 资本化入表 / 费用化
    book_value: float            # 入账金额 = U_observed（地板，非估值）
    period: str                  # 会计期间（YYYY-MM）
    basis: str                   # 依据
    evidence_chain: str          # 存证链引用（NCA）

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "account": self.account,
            "entry_type": self.entry_type,
            "book_value": round(self.book_value, 4),
            "period": self.period,
            "basis": self.basis,
            "evidence_chain": self.evidence_chain,
            "note": "入账金额=可观测下限（地板），非主观估值——会计可审计可复核",
        }


@dataclass(frozen=True)
class CopyrightChainRecord:
    """版权链存证上链记录（模拟通道）。"""
    asset_id: str
    record_hash: str
    chain_status: str            # SIMULATED_ONCHAIN（真实上链待司法链接入）
    chain_id: str
    provenance: str

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "record_hash": self.record_hash,
            "chain_status": self.chain_status,
            "chain_id": self.chain_id,
            "provenance": self.provenance,
        }


class UtilValueAccounting:
    """入表服务化（M2）。"""

    def __init__(self, service: Optional[UtilValueService] = None):
        self._svc = service or UtilValueService()

    # ---- 1. 会计入表建议（对接会计口径）----

    def accounting_entry(self, asset_id: str, transactions: List[dict],
                         period: str, account: str = ACCOUNT_INTANGIBLE,
                         provenance: str = "SIMULATED") -> AccountingEntry:
        """生成会计入表建议。

        口径: 入账金额 = U_observed（可观测下限地板）——MOU 地板语义
        判定: U_observed > 0 → 资本化入表（account 指定科目）；
              U_observed = 0 → 费用化（无下限支撑，禁止资本化）
        """
        floor = self._svc.observable_floor(asset_id, transactions, provenance=provenance)
        if floor.u_observed > 0:
            entry_type = ENTRY_CAPITALIZE
        else:
            entry_type = ENTRY_EXPENSE
            account = ACCOUNT_RD if account == ACCOUNT_INTANGIBLE else account
        return AccountingEntry(
            asset_id=asset_id,
            account=account,
            entry_type=entry_type,
            book_value=floor.u_observed,
            period=period,
            basis="TDCA-UTILITY-OBSERVABLE-001（U_observed=Σ销项+进项，显示性偏好地板）",
            evidence_chain=f"NCA-UTILVALUE-{asset_id}",
        )

    # ---- 2. 版权链存证上链（模拟通道）----

    def copyright_chain_record(self, asset_id: str, transactions: List[dict],
                               chain_id: str = "SIM-COPYRIGHT-CHAIN",
                               provenance: str = "SIMULATED") -> CopyrightChainRecord:
        """版权链存证上链（模拟通道）。

        record_hash = 交易流规范化摘要（SHA-256）——真实上链需司法链运营方接入。
        """
        import hashlib
        import json

        floor = self._svc.observable_floor(asset_id, transactions, provenance=provenance)
        digest_src = json.dumps({
            "asset_id": asset_id,
            "u_observed": floor.u_observed,
            "output_total": floor.output_total,
            "input_total": floor.input_total,
            "tx_count": floor.tx_count,
        }, ensure_ascii=False, sort_keys=True)
        record_hash = hashlib.sha256(digest_src.encode("utf-8")).hexdigest()
        return CopyrightChainRecord(
            asset_id=asset_id,
            record_hash=record_hash,
            chain_status="SIMULATED_ONCHAIN",
            chain_id=chain_id,
            provenance=provenance,
        )

    # ---- 3. 入表评估报告（M2 完整版：地板+分层+安全+会计+上链）----

    def full_entry_report(self, asset_id: str, transactions: List[dict],
                          period: str, proposed_valuation: Optional[float] = None,
                          account: str = ACCOUNT_INTANGIBLE,
                          seven_elements_meta: Optional[dict] = None,
                          provenance: str = "SIMULATED") -> dict:
        """M2 完整入表报告（供会计引用 + 存证）。

        组成: M1 评估（地板+五阶分层+安全熔断）+ M2 会计入表建议 + 版权链存证记录
        """
        floor = self._svc.observable_floor(asset_id, transactions, provenance=provenance)
        tiers = self._svc.tier_assessment(asset_id, transactions, provenance=provenance)
        safety = (self._svc.safety_check(proposed_valuation, floor.u_observed)
                  if proposed_valuation is not None else None)
        seven = (self._svc.seven_element_decomposition(asset_id, seven_elements_meta)
                 if seven_elements_meta else None)
        entry = self.accounting_entry(asset_id, transactions, period, account=account,
                                      provenance=provenance)
        chain = self.copyright_chain_record(asset_id, transactions, provenance=provenance)

        report: dict = {
            "report_type": "util_value_entry_report",
            "schema_version": "2.0",
            "asset_id": asset_id,
            "period": period,
            "floor": floor.to_dict(),
            "tiers": tiers.to_dict(),
            "accounting_entry": entry.to_dict(),
            "copyright_chain": chain.to_dict(),
            "provenance": provenance,
        }
        if safety is not None:
            report["safety"] = safety.to_dict()
        if seven is not None:
            report["seven_elements"] = seven
        return report
