# -*- coding: utf-8 -*-
"""
TDCA-KB 知识单元数据模型 — 三大白皮书结构化知识单元
制度锚定: TDCA-KG-001 §4.2 / §4.3 | ID56 双协议封印
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

NSFL-Declaration:
  - 知识单元必须溯源至真实白皮书文本（认知负空间）
  - 不生成虚假制度原理 / 伪造宪法条目 / 虚构 NCA
SPDX-License-Identifier: TDCA-Internal
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from datetime import datetime
import hashlib


@dataclass
class KnowledgeUnit:
    """
    TDCA-KB 知识单元 — 制度白皮书的最小可查询单元（TDCA-KG-001 §4.2）
    """
    id: str                    # 如 "KB-INST-001"
    source: str                # "制度白皮书" / "数学基础白皮书" / "经济模型白皮书"
    chapter: str
    section: str

    # 内容层
    content_text: str
    formalization: Optional[str] = None  # 数学/逻辑形式化
    examples: List[str] = field(default_factory=list)
    counter_examples: List[str] = field(default_factory=list)  # 破例识别训练

    # 关系层
    derives: List[str] = field(default_factory=list)      # 推导出的知识单元
    contradicts: List[str] = field(default_factory=list)  # 矛盾的知识单元（破例识别）
    implements: List[str] = field(default_factory=list)   # 实现该单元的代码
    tested_by: List[str] = field(default_factory=list)    # 验证该单元的测试

    # 元数据层
    priority: int = 3          # 1-5
    stability: Literal["STABLE", "EVOLVING", "DEPRECATED"] = "STABLE"
    ota_version: str = "v1.0"
    last_reviewed: str = field(default_factory=lambda: datetime.now().isoformat())
    reviewed_by: str = ""      # 如 "智谱-GLM5.2"
    human_confirmed: bool = False

    # 应用层
    applicable_scenes: List[str] = field(default_factory=list)
    required_for_roles: List[str] = field(default_factory=list)
    mou_impact: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"

    def compute_seal(self) -> str:
        """知识单元封印 — 用于 KG 联动（ID56）"""
        payload = f"{self.id}:{self.source}:{self.content_text}:{self.ota_version}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_kg_node(self) -> Dict:
        """转换为知识图谱节点（TDCA-KG-001 §4.4 联动机制）"""
        return {
            "labels": ["KnowledgeUnit", self.source.replace("白皮书", "")],
            "properties": {
                "unit_id": self.id,
                "priority": self.priority,
                "stability": self.stability,
                "seal": self.compute_seal(),
                "mou_impact": self.mou_impact,
            },
        }
