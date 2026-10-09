# -*- coding: utf-8 -*-
"""
TDCA NCA 嵌套认知资产运行时生成器 — REPO-006 元层
制度锚定: ID91 自反化合原理 | ID56 双协议封印 | TypeSystem-Confirmation-001 §5.1
版本: V1.0 | 状态: M2-CODED | FC: TDCA-FC-20260804-006-M2

职责: 运行时自动生成 NCA（封印哈希 + MOU 贡献 + 追溯链），链式验证，上链钩子。
NSFL-Declaration:
  - 封印哈希必须基于内容 + 时间戳 + UUID，不可使用可预测的种子（NCA 不可伪造）
  - NCA 不可删除（SPEC-002）
SPDX-License-Identifier: TDCA-Internal
"""

import hashlib
import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class NCA:
    """嵌套认知资产"""
    nca_id: str
    type: str
    layer: int
    parent_nca: Optional[str]
    seal: str
    mou_contribution: int
    content: Dict
    timestamp: int
    chain: List[str] = field(default_factory=list)  # 追溯链


class NCAGenerator:
    """
    NCA 嵌套认知资产运行时生成器
    唯一既是输入又是输出的库（REPO-006 BIDIRECTIONAL）
    :param chain_client: 可选 TDCA 链联盟链接口（submit_nca）
    """

    def __init__(self, chain_client=None):
        self.chain = chain_client
        self.cache: Dict[str, NCA] = {}

    def generate(self, type: str, layer: int, content: Dict,
                 parent_nca: Optional[str] = None) -> NCA:
        """
        生成 NCA
        自动计算封印哈希、MOU 贡献、追溯链
        """
        nca_id = f"NCA-{uuid.uuid4().hex[:16]}"
        timestamp = int(time.time())

        # 计算封印（双协议封印 — ID56；基于内容+时间戳+UUID，不可预测）
        content_hash = hashlib.sha256(str(content).encode()).hexdigest()
        seal_payload = (
            f"{nca_id}:{type}:{layer}:{timestamp}:{content_hash}"
        )
        seal = hashlib.sha256(seal_payload.encode()).hexdigest()

        # 计算 MOU 贡献（基于内容复杂度占位；真实值须映射税收数据 ID79）
        mou_contribution = self._estimate_mou(content)

        # 构建追溯链
        chain: List[str] = []
        if parent_nca:
            chain.append(parent_nca)
            parent = self.cache.get(parent_nca)
            if parent:
                chain.extend(parent.chain)

        nca = NCA(
            nca_id=nca_id, type=type, layer=layer, parent_nca=parent_nca,
            seal=seal, mou_contribution=mou_contribution, content=content,
            timestamp=timestamp, chain=chain,
        )

        self.cache[nca_id] = nca

        # 上链钩子（TDCA 链联盟链）
        if self.chain is not None and hasattr(self.chain, "submit_nca"):
            self.chain.submit_nca(nca)

        return nca

    def verify_chain(self, nca_trace: List[str]) -> bool:
        """验证 NCA 追溯链完整性 — ID91"""
        if not nca_trace:
            return False
        return all(nca_id in self.cache for nca_id in nca_trace)

    def verify_seal(self, nca: NCA) -> bool:
        """重新计算封印并验证（防篡改校验）"""
        content_hash = hashlib.sha256(str(nca.content).encode()).hexdigest()
        seal_payload = (
            f"{nca.nca_id}:{nca.type}:{nca.layer}:{nca.timestamp}:{content_hash}"
        )
        recomputed = hashlib.sha256(seal_payload.encode()).hexdigest()
        return recomputed == nca.seal

    def get(self, nca_id: str) -> Optional[NCA]:
        return self.cache.get(nca_id)

    def count(self) -> int:
        return len(self.cache)

    def _estimate_mou(self, content: Dict) -> int:
        """估算 MOU 贡献（占位算法；生产须基于真实税收数据 ID92）"""
        return len(str(content)) * 10
