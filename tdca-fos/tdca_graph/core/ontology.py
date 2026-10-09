# -*- coding: utf-8 -*-
"""
TDCA-Graph Core 本体论模型 — REPO-003 五维图数据模型
制度锚定: TDCA-KG-001 §2.2 / §3.2 | TDCA-TypeSystem-Confirmation-001 §5.1 | ID56
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

NSFL-Declaration:
  - 本模块不修改任何不可升级核心锚点（TypeSystem §9.3）
  - 节点/边类型仅从 TDCA-KG-001 §2.2 枚举派生，不新增制度语义
SPDX-License-Identifier: TDCA-Internal
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum
import hashlib


class NodeType(Enum):
    """五维图节点类型 — TDCA-KG-001 §2.2"""
    # 制度层
    PRINCIPLE = "Principle"
    CONSTITUTION = "Constitution"
    NSFL_RULE = "NSFLRule"
    # 技术层
    FUNCTION_SPEC = "FunctionSpec"
    AGENT_ROLE = "AgentRole"
    CODE_MODULE = "CodeModule"
    # 经济层
    ASSET_CLASS = "AssetClass"
    MOU_ANCHOR = "MOUAnchor"
    # 拓扑层
    TOPOLOGY_NODE = "TopologyNode"
    RELATION_EDGE = "RelationEdge"
    # 认知层
    NCA = "NCA"
    COGNITIVE_STATE = "CognitiveState"

    @classmethod
    def all_labels(cls) -> List[str]:
        return [t.value for t in cls]


class EdgeType(Enum):
    """边类型 — TDCA-KG-001 §2.2"""
    DERIVES_FROM = "DERIVES_FROM"
    ENFORCES = "ENFORCES"
    IMPLEMENTS = "IMPLEMENTS"
    COMPILES_TO = "COMPILES_TO"
    PRICES = "PRICES"
    GENERATES = "GENERATES"
    CONNECTS = "CONNECTS"
    NESTS = "NESTS"
    REFINES = "REFINES"

    @classmethod
    def all_names(cls) -> List[str]:
        return [e.value for e in cls]


class PrincipleCategory(Enum):
    INSTITUTIONAL = "INSTITUTIONAL"
    TECHNICAL = "TECHNICAL"
    ECONOMIC = "ECONOMIC"
    COGNITIVE = "COGNITIVE"


class EnforcementLevel:
    """宪法强制级别 — TDCA-KG-001 §2.2 Constitution.enforcement_level"""
    HARD = "HARD"
    SOFT = "SOFT"
    GUIDANCE = "GUIDANCE"


@dataclass
class PrincipleNode:
    """制度原理节点 — TDCA-KG-001 §2.2"""
    id: str                      # 如 "ID29"
    name: str
    category: PrincipleCategory
    priority: int                # 1-5, 5为宪法级
    dependencies: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    formalization: Optional[str] = None  # 数学/逻辑形式化表达

    def seal_hash(self) -> str:
        """双协议封印哈希 — ID56"""
        content = f"{self.id}:{self.name}:{self.priority}:{self.formalization}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ConstitutionNode:
    """宪法十六条节点 — TDCA-KG-001 §2.2"""
    article: int                 # 1-16
    title: str
    text: str
    enforcement_level: Literal["HARD", "SOFT", "GUIDANCE"] = "HARD"
    applicable_scenes: List[str] = field(default_factory=list)
    ota_version: str = "v1.0"


@dataclass
class NSFLRuleNode:
    """负空间规则节点 — TDCA-KG-001 §2.2"""
    id: str
    type: Literal["ETHICAL", "LEGAL", "EMOTIONAL", "BELIEF", "TECHNICAL"]
    pattern: str                  # ⊗ 操作符匹配模式
    level: Literal["HARD", "SOFT"] = "HARD"
    alt_path: str = ""            # 替代路径函数 ID
    human_override: bool = False


@dataclass
class FunctionSpecNode:
    """函数语料六要素节点 — ID68 / TDCA-KG-001 §2.2"""
    objective: str
    constraints: List[Dict] = field(default_factory=list)
    prior: Optional[Dict] = None
    config_right: Optional[Dict] = None
    allocation: Optional[Dict] = None
    audit_trail: Optional[str] = None
    protocolizer: str = ""        # 制度极审核签名（智谱）

    def completeness(self) -> Dict[str, bool]:
        """六要素完整性检查（TDCA-KG-001 §5.3 查询 4）"""
        return {
            "objective": bool(self.objective),
            "constraints": bool(self.constraints),
            "prior": self.prior is not None,
            "config_right": self.config_right is not None,
            "allocation": self.allocation is not None,
            "audit_trail": bool(self.audit_trail),
        }

    def is_complete(self) -> bool:
        return all(self.completeness().values())


@dataclass
class AgentRoleNode:
    """智能体角色节点 — TDCA-KG-001 §2.2"""
    role_id: str
    eios_type: Literal["TRAINER", "EXECUTOR", "AUDITOR", "SERVICE", "UTILITY_GENIE"]
    cluster: Literal["GOVERNANCE", "DEV"]
    allowed_operations: List[str] = field(default_factory=list)
    disallowed_operations: List[str] = field(default_factory=list)
    model_assignment: str = ""


@dataclass
class NCANode:
    """嵌套认知资产节点 — ID91 / TDCA-KG-001 §2.2"""
    nca_id: str
    type: Literal["COGNITIVE", "INSTITUTIONAL", "TECHNICAL", "ECONOMIC"]
    layer: int
    parent_nca: Optional[str] = None
    seal: str = ""
    mou_contribution: int = 0


@dataclass
class CognitiveStateVector:
    """
    智能体状态认知向量 — DCD-20260805-003 D1 裁决（汇编 V2.0 语义）
    用于 MACM 3.0 智能体状态演化 / KG-001 CognitiveState 节点
    S_state = (A, D, L, C, SC)
      A = 认知活跃度 (Cognitive Activity)
      D = 决策距离 (Decision Distance，与最优解偏离度)
      L = 学习速率 (Learning Rate)
      C = 协作连通度 (Collaborative Connectivity)
      SC = 自我置信度 (Self-Confidence，幻觉过滤阈值)
    """
    A: float = 0.0   # 认知活跃度
    D: float = 0.0   # 决策距离
    L: float = 0.0   # 学习速率
    C: float = 0.0   # 协作连通度
    SC: float = 0.0  # 自我置信度


@dataclass
class AssetCognitiveVector:
    """
    资产认知向量 — DCD-20260805-003 D1 裁决（TERMS-001 语义）
    用于资产评估/认知语境（与智能体状态向量符号相同但语义不同，须标注语境）
    S_asset = (A, D, L, C, SC)
      A = 可用性 (Availability)
      D = 可靠性 (Dependability)
      L = 可学习性 (Learnability)
      C = 合规性 (Compliance)
      SC = 场景一致性 (Scene Consistency)
    """
    A: float = 0.0   # 可用性
    D: float = 0.0   # 可靠性
    L: float = 0.0   # 可学习性
    C: float = 0.0   # 合规性
    SC: float = 0.0  # 场景一致性


@dataclass
class AssetValueVector:
    """
    五维价值向量（资产价值评估）— DCD-20260805-003 D2 裁决 ACCEPT
    以《TDCA 名词治理汇编 V1.0》为唯一标准（取代专著四维 v,c,s,t）
    V = (U, S, F, C, R)
      U = Utility 效用可用性
      S = Scarcity 场景稀缺性
      F = Fluidity 配置流动性
      C = Compliance 合规性
      R = Resonance 主题共鸣（R < 0 一票否决 → 资产价值强制归零）
    """
    U: float = 0.0
    S: float = 0.0
    F: float = 0.0
    C: float = 0.0
    R: float = 0.0

    def asset_value(self) -> float:
        """综合价值 = U × S × F × C × sign(R)；R≤0 一票否决"""
        if self.R <= 0:
            return 0.0
        return self.U * self.S * self.F * self.C
