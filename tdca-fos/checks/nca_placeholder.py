# -*- coding: utf-8 -*-
"""
TDCA NCA 生成器占位实现 — REPO-003 内嵌 NCA 记录器（M1 占位，M3 桥接 TDCA-MEMO-006 附录 C）
制度锚定: TDCA-MEMO-006 附录 C | ID91 自反化合原理
版本: V1.0 | 状态: M1-PLACEHOLDER | FC: TDCA-FC-20260804-006

职责: 为图查询 / 知识单元操作 / 推理执行提供 record_query 语义的 NCA 记录。
M3 里程碑将切换为真实 YAML NCA 落盘（tdca_nca_generator.TDCANCAGenerator）。
NSFL-Declaration:
  - 占位实现不伪造存证哈希；seal 由内容真实哈希生成
  - NCA 不可删除（SPEC-002）
SPDX-License-Identifier: TDCA-Internal
"""

import hashlib
import time
from typing import Dict, Any, List, Optional


class NCAGeneratorPlaceholder:
    """
    NCA 记录占位器 — 内存记录 + 内容哈希封印
    接口对齐 TDCA-KG-001 §3.4 NCAReference：
      record_query / record_cross_call / record_inference / verify_chain
    """

    def __init__(self):
        self._records: Dict[str, Dict] = {}
        self._seq = 0

    def record_query(self, query_type: str, parameters: Dict,
                     result_summary: Any) -> str:
        """记录一次查询操作 NCA — ID91"""
        return self._record(
            type="COGNITIVE",
            layer=1,
            content={
                "query_type": query_type,
                "parameters": parameters,
                "result_summary": result_summary,
            },
        )

    def record_cross_call(self, source: str, target: str, call_type: str,
                          config_right: Any = None, result_hash: str = "") -> str:
        """记录跨库调用 NCA — ID91"""
        return self._record(
            type="COGNITIVE",
            layer=1,
            content={
                "call_type": call_type,
                "source": source,
                "target": target,
                "result_hash": result_hash,
            },
        )

    def record_inference(self, rule_name: str, principle: str,
                         trigger_params: Dict, alert: Dict) -> str:
        """记录推理规则执行 NCA — ID91"""
        return self._record(
            type="COGNITIVE",
            layer=1,
            content={
                "inference_rule": rule_name,
                "principle": principle,
                "trigger_params": trigger_params,
                "alert": alert,
            },
        )

    def verify_chain(self, nca_trace: List[str]) -> bool:
        """验证 NCA 追溯链完整性 — ID91"""
        if not nca_trace:
            return False
        return all(nca_id in self._records for nca_id in nca_trace)

    def get(self, nca_id: str) -> Optional[Dict]:
        return self._records.get(nca_id)

    def count(self) -> int:
        return len(self._records)

    # ---- 内部 ----

    def _record(self, type: str, layer: int, content: Dict) -> str:
        self._seq += 1
        nca_id = f"NCA-PLACEHOLDER-{self._seq:04d}"
        seal = hashlib.sha256(
            f"{nca_id}:{type}:{sorted(str(content).encode())}".encode()
        ).hexdigest()
        self._records[nca_id] = {
            "nca_id": nca_id,
            "type": type,
            "layer": layer,
            "seal": seal,
            "mou_contribution": 0,
            "timestamp": int(time.time()),
            "content": content,
        }
        return nca_id
