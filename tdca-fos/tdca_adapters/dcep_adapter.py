# -*- coding: utf-8 -*-
"""
TDCA 数字人民币智能合约适配器 — MOU 锚定（M3）
制度锚定: ID43 (MCT 原理) | ID70 (TDCA-CBDC 唯一性) | ID79/ID92 (MOU 真实性)
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

制度即货币，货币即制度。MOU = 进项 + 出项税收总和。
NSFL-Declaration（经济负空间强制）:
  - anchor_mou 必须接收真实税收数据；无真实数据必须返回错误，禁止生成虚假 MOU
  - MOU 必须是真实进项/出项税收的映射（ID79/ID92）
SPDX-License-Identifier: TDCA-Internal
"""

import time
from typing import Dict, Optional


class DCEPAdapter:
    """
    数字人民币智能合约适配器 — MOU 锚定
    :param dcep_client: 数字人民币智能合约 SDK（execute_contract / query_contract）
    """

    def __init__(self, dcep_client, nca_generator=None):
        self.dcep = dcep_client
        self.nca = nca_generator

    def anchor_mou(self, transaction_id: str, tax_in: int,
                   tax_out: int) -> Dict:
        """
        MOU 锚定：进项 + 出项税收总和
        ID79: MOU = 进项 + 出项税收总和
        NSFL: 税收数据必须真实（≥0），否则返回错误而非生成虚假锚定
        """
        # 负空间校验：禁止无真实税收数据的 MOU 模拟（ID79/ID92）
        if tax_in is None or tax_out is None:
            raise ValueError(
                "[NSFL-TRIGGER] MOU 锚定缺少税收数据，禁止伪造 MOU 值")
        if tax_in < 0 or tax_out < 0:
            raise ValueError(
                "[NSFL-TRIGGER] 税收数据为负，非法 MOU 输入")

        mou = tax_in + tax_out

        # 调用数字人民币智能合约
        contract_result = self.dcep.execute_contract(
            contract_type="MOU_ANCHOR",
            params={
                "transaction_id": transaction_id,
                "tax_in": tax_in,
                "tax_out": tax_out,
                "mou": mou,
                "timestamp": int(time.time()),
            },
        ) or {}

        # 生成 MOU 锚定 NCA
        nca = None
        if self.nca is not None and hasattr(self.nca, "generate"):
            nca = self.nca.generate(
                type="ECONOMIC", layer=3,
                content={
                    "adapter": "DCEP",
                    "action": "anchor_mou",
                    "transaction_id": transaction_id,
                    "tax_in": tax_in,
                    "tax_out": tax_out,
                    "mou": mou,
                    "contract_tx": contract_result.get("tx_hash"),
                },
            )

        return {
            "mou": mou,
            "nca": nca,
            "contract_tx": contract_result.get("tx_hash"),
        }

    def verify_mou(self, transaction_id: str) -> bool:
        """验证某笔交易的 MOU 是否已锚定"""
        if self.dcep is None or not hasattr(self.dcep, "query_contract"):
            return False
        return bool(self.dcep.query_contract(transaction_id))
