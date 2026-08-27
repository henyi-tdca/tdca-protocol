# -*- coding: utf-8 -*-
"""候选源抽象基座
=========================================================
让"候选主体库"成为可插拔模块: 引擎只认 Candidate 结构,
不关心主体来自本地 YAML、合成器、还是 MCP/API 连接器。
换一个全网源 = 换一个 CandidateProvider 实现。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Candidate:
    """一个全网候选协作主体 (思维协议驱动比配的最小单元)"""
    id: str
    name: str
    cop: str                       # 该主体携带/偏好的思维协议标签
    res: Dict[str, float]          # 资源维度 -> 强度 0..1
    batna: float                   # 不参与联盟的保留效用 (满意判定底线)
    source: str = "unknown"        # 来源标注 (哪个连接器/本地)


class CandidateProvider(ABC):
    """候选源统一接口 —— 任何连接器都实现它即可被引擎调度"""

    @abstractmethod
    def load(self, dims: List[str], task_id: str = "") -> List[Candidate]:
        """返回候选主体列表。引擎不关心来源, 只认 Candidate 结构。"""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """来源标识 (写入报告, 便于审计来源)"""
        ...
