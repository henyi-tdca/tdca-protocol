# -*- coding: utf-8 -*-
"""
TDCA MOU 税收锚定管线 — 模拟上游数据源 → DCEP 锚定 → 闭环验证（收口 MEMO-023 ⚠️）
制度锚定: ID79 (MOU=进项+出项税收总和) | ID92 (MOU 真实性) | ID43 (MCT) | skill-mou-anchor (FC-MOU-001)
版本: V1.0 | 状态: M5-CODED | FC: TDCA-FC-20260804-006-M5

NSFL-Declaration（经济负空间强制）:
  - 模拟税收数据必须显式标注 simulated=True + 来源标识 SIMULATED-TAX-AUTHORITY，
    严禁伪装为真实税务机构数据（ID92）
  - 任何下游消费必须显式承认 simulated 标记；require_real_data 下模拟记录被拒
  - 与真实数据源接口同构：真实税收数据接入时仅替换 TaxSource 实现，管线层无感知

SPDX-License-Identifier: TDCA-Internal
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Dict, Optional


# 模拟税务机构标识（与真实税务机构区分的显式标记）
SIMULATED_SOURCE = "SIMULATED-TAX-AUTHORITY"
SIMULATED_SIGNING_KEY = "TDCA-SIMULATED-KEY-0001"  # 模拟签名密钥（严禁用于真实数据）


@dataclass
class TaxSettlementRecord:
    """税收结算记录（上游税务机构数据单元）"""
    transaction_id: str
    tax_in: int
    tax_out: int
    timestamp: int
    source: str
    data_hash: str
    signature: str
    simulated: bool = True  # 显式标记：True=模拟数据，False=真实税务数据


class SimulatedTaxAuthority:
    """
    模拟上游税务机构数据源
    生成带数据哈希 + 来源签名的税收结算记录（simulated=True）
    接口同构：真实税务机构实现相同 settle() 接口即可无缝替换
    """

    def settle(self, transaction_id: str, tax_in: int, tax_out: int) -> TaxSettlementRecord:
        """生成一笔税收结算记录（模拟）"""
        if tax_in is None or tax_out is None:
            raise ValueError("[NSFL-TRIGGER] 税收数据缺失，禁止生成结算记录")
        if tax_in < 0 or tax_out < 0:
            raise ValueError("[NSFL-TRIGGER] 税收数据为负，非法结算输入")

        timestamp = int(time.time())
        payload = self._canonical_payload(
            transaction_id, tax_in, tax_out, timestamp, SIMULATED_SOURCE)
        data_hash = hashlib.sha256(payload.encode()).hexdigest()
        signature = hashlib.sha256(
            f"{data_hash}:{SIMULATED_SIGNING_KEY}".encode()).hexdigest()

        return TaxSettlementRecord(
            transaction_id=transaction_id,
            tax_in=tax_in,
            tax_out=tax_out,
            timestamp=timestamp,
            source=SIMULATED_SOURCE,
            data_hash=data_hash,
            signature=signature,
            simulated=True,
        )

    def verify(self, record: TaxSettlementRecord) -> bool:
        """校验结算记录完整性：数据哈希 + 来源签名 + 非负（ID92 真实性）"""
        if record.tax_in is None or record.tax_out is None:
            return False
        if record.tax_in < 0 or record.tax_out < 0:
            return False
        # 数据哈希校验
        payload = self._canonical_payload(
            record.transaction_id, record.tax_in, record.tax_out,
            record.timestamp, record.source)
        if hashlib.sha256(payload.encode()).hexdigest() != record.data_hash:
            return False
        # 签名校验（模拟密钥派生；真实数据源替换为 CA 验签）
        expect = hashlib.sha256(
            f"{record.data_hash}:{SIMULATED_SIGNING_KEY}".encode()).hexdigest()
        return record.signature == expect

    @staticmethod
    def _canonical_payload(transaction_id: str, tax_in: int, tax_out: int,
                           timestamp: int, source: str) -> str:
        """规范化载荷（字段序固定，防注入/歧义）"""
        return f"{transaction_id}|{tax_in}|{tax_out}|{timestamp}|{source}"


class MOUPipeline:
    """
    MOU 锚定管线编排：上游税收数据源 → 数据校验 → DCEP 锚定 → 闭环验证
    :param tax_source: 税收数据源（SimulatedTaxAuthority 或真实实现，接口同构）
    :param dcep_adapter: DCEPAdapter 实例
    """

    def __init__(self, tax_source, dcep_adapter):
        self.tax_source = tax_source
        self.dcep = dcep_adapter

    def run(self, transaction_id: str, tax_in: int, tax_out: int,
            require_real: bool = False) -> Dict:
        """
        全链路执行
        :param transaction_id: 交易 ID
        :param tax_in: 进项税收
        :param tax_out: 出项税收
        :param require_real: True=仅接受真实税务数据（模拟数据被拒）
        """
        # 1. 上游结算（模拟税务机构生成带签名记录）
        record = self.tax_source.settle(transaction_id, tax_in, tax_out)

        # 2. 真实性守卫（ID92）
        if require_real and record.simulated:
            raise ValueError(
                "[NSFL-TRIGGER] require_real_data=True 时拒绝模拟税收数据，"
                "需接入真实税务机构数据源")

        # 3. 数据完整性校验（哈希 + 签名 + 非负）
        if not self.tax_source.verify(record):
            raise ValueError("[NSFL-TRIGGER] 税收结算记录校验失败，拒绝锚定")

        # 4. DCEP MOU 锚定（内部 NSFL：None/负值拒绝）
        anchored = self.dcep.anchor_mou(
            transaction_id, tax_in=record.tax_in, tax_out=record.tax_out)

        # 5. 闭环验证
        verified = self.dcep.verify_mou(transaction_id)

        return {
            "transaction_id": transaction_id,
            "record": record,
            "mou": anchored["mou"],
            "contract_tx": anchored.get("contract_tx"),
            "nca": anchored.get("nca"),
            "verified": verified,
            "simulated": record.simulated,  # 显式标记：下游必须承认
        }

    def require_real_data_available(self) -> bool:
        """真实数据就绪检测：当前数据源是否非模拟"""
        return getattr(self.tax_source, "simulated_only", True) is False
