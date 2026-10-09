# -*- coding: utf-8 -*-
"""
TDCA 联盟链适配器 — NCA 批量上链（M3）
制度锚定: ID43 (MCT 原理) | TypeSystem-Confirmation-001 §9.2 | ID91 NCA | ID56 封印
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

NCA 存证哈希定期批量上链，制度记忆不可篡改。
NSFL-Declaration:
  - NCA 批量上链不可因性能考虑而跳过（TDCA 链是制度记忆终极保障）
  - 上链内容含封印哈希与内容哈希，保证可验证
SPDX-License-Identifier: TDCA-Internal
"""

import hashlib
from typing import Dict, List, Optional, Any


class TDCAChainAdapter:
    """
    TDCA 链联盟链接口 — NCA 批量上链
    :param chain_client: 联盟链 SDK（submit_batch / verify 接口）
    :param batch_size: 批量上链阈值（默认 100）
    """

    def __init__(self, chain_client, nca_generator=None, batch_size: int = 100):
        self.chain = chain_client
        self.nca = nca_generator
        self.batch_size = batch_size
        self.pending_batch: List[Dict] = []
        self.flush_count = 0

    def submit_nca(self, nca: Any) -> Optional[str]:
        """
        提交 NCA 到上链队列
        达到批量阈值则自动上链
        """
        if isinstance(nca, dict):
            nca_id = nca.get("nca_id", "")
            seal = nca.get("seal", "")
            timestamp = nca.get("timestamp", 0)
            content = nca.get("content", {})
        else:
            nca_id = getattr(nca, "nca_id", "")
            seal = getattr(nca, "seal", "")
            timestamp = getattr(nca, "timestamp", 0)
            content = getattr(nca, "content", {})

        self.pending_batch.append({
            "nca_id": nca_id,
            "seal": seal,
            "timestamp": timestamp,
            "content_hash": hashlib.sha256(str(content).encode()).hexdigest(),
        })

        # 达到批量阈值则上链
        if len(self.pending_batch) >= self.batch_size:
            return self._flush_batch()
        return None

    def _flush_batch(self) -> Optional[str]:
        """批量上链"""
        if not self.pending_batch:
            return None

        tx_hash = self.chain.submit_batch(self.pending_batch)

        if self.nca is not None and hasattr(self.nca, "generate"):
            self.nca.generate(
                type="INSTITUTIONAL", layer=3,
                content={
                    "adapter": "TDCA_CHAIN",
                    "action": "batch_submit",
                    "count": len(self.pending_batch),
                    "tx_hash": tx_hash,
                },
            )

        self.flush_count += 1
        self.pending_batch = []
        return tx_hash

    def verify_on_chain(self, nca_id: str) -> bool:
        """验证 NCA 是否已上链"""
        if self.chain is None or not hasattr(self.chain, "verify"):
            return False
        return self.chain.verify(nca_id)

    def pending_count(self) -> int:
        return len(self.pending_batch)
