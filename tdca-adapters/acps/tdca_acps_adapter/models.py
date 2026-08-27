"""ACPs 接口契约的最小类型定义（自建，非上游代码副本）。

基于 ACPs 公开协议规范（acps-specs）的字段语义重建，仅承载适配器所需字段。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentKind(str, Enum):
    """ACPs 身份在 TDCA 五元拓扑中的角色映射。"""
    HUMAN = "H"          # 人
    LLM = "M"            # 大模型
    SLM = "L"            # 小模型/环境


class NsflVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    WARN = "WARN"


@dataclass
class AIC:
    """智能体身份码（ACPs AIC 概念的最小实现）。"""
    oid: str
    aic: str
    certificate_subject: Optional[str] = None
    issuer: Optional[str] = None
    validity: Optional[str] = None


@dataclass
class ACS:
    """智能体能力描述（ACPs ACS 概念）。"""
    capability_tags: List[str] = field(default_factory=list)
    service_endpoints: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    authorization_scope: str = "read-only"


@dataclass
class DiscoveryQuery:
    """ADP 发现查询（自然语言或结构化）。"""
    text: str = ""
    structured_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationConfig:
    """配置权调用配置（TDCA 侧）。"""
    query: DiscoveryQuery
    requester_aic: str
    max_budget: float = 0.2          # 预算上限（模拟态货币单位，低于典型效用）
    scenario: str = "default"        # 场景坐标卡
    negative_space_hint: Optional[List[str]] = None


@dataclass
class AllocationResult:
    """配置权交易结果（TDCA 侧产出）。"""
    coordinate: Dict[str, Any]       # 配置权坐标（五元拓扑）
    utility_function: Dict[str, Any] # 效用函数描述
    positive_sum: float              # 正和剩余
    positive_sum_pass: bool
    nca: Dict[str, Any]              # NCA 六要素
    nsfl_verdict: NsflVerdict
    mou: Dict[str, Any]              # MOU 记账（模拟态）
    allocation_id: str = ""
    simulated: bool = True           # ID92 模拟态标注
