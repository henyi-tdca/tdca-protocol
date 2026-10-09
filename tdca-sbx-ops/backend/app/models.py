# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     沙盒数据模型（任务书 §3.2 数据模型落地）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 宪法十六条（可观测）
# 先验分布:     任务书 §3.2 + NS-OPS models.py 模式
# 配置权边界:    L2 层
# 预期分配:     沙盒/激活记录/NCA 数据契约；失败=校验异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""SBX-OPS M1 数据模型。

制度锚定: FC-SBX-OPS-001 §3.2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Phase(str, Enum):
    """沙盒生命周期阶段（任务书 §3.2: Phase 0→P0→P1→Exit）。"""

    PHASE0 = "Phase0"  # 准入
    P0 = "P0"          # 实验
    P1 = "P1"          # 评估
    EXIT = "Exit"      # 出盒
    CLOSED = "Closed"  # 关闭（负空间熔断 / 三方终止 / 资产清算）


class ActivationStatus(str, Enum):
    """激活系数决策门三档（任务书 §二 F3）。"""

    SELF_FINANCED = "财政自给性达成"     # > 1.2
    BREAKEVEN = "基本盈亏平衡"           # (1.0, 1.2]
    UNSUSTAINABLE = "财政不可持续"       # <= 1.0 → 熔断


class NCA(BaseModel):
    """NCA 存证记录（F8，任务书 §五 SV-7 全操作存证）。"""

    nca_id: str
    fc_id: str
    operation: str
    operator: str
    timestamp: str
    pre_state: str
    post_state: str
    config_right_token: str
    audit_trail: str
    human_signature: str
    negative_space_check: str
    prev_hash: str = ""
    content_hash: str = ""


class Sandbox(BaseModel):
    """沙盒实例（任务书 §3.2 数据模型）。"""

    sandbox_id: str = Field(description="did:tdca:sandbox:{uuid}")
    name: str
    phase: Phase = Phase.PHASE0
    initiator_did: str
    initiator_role: str
    six_elements: Dict[str, str] = Field(default_factory=dict)  # 六要素声明
    trinity: Dict[str, Any] = Field(default_factory=dict)       # 三位一体配置（M1 简化字段，F2 落地）
    s_rights: List[Dict[str, Any]] = Field(default_factory=list)  # S-Right 配置权（F4 落地）
    pucr: Optional[Dict[str, Any]] = None  # PUCR 预售/质押（SV-2 记录位）
    activation_logs: List[Dict[str, Any]] = Field(default_factory=list)  # 激活系数历史
    nca_ids: List[str] = Field(default_factory=list)  # NCA 存证链引用
    negative_space_refs: List[str] = Field(default_factory=list)  # 关联负空间约束 ID
    eng003_log: List[Dict[str, Any]] = Field(default_factory=list)  # ENG-003 最小化合检查日志（M1 预埋，M2 落地）
    reactions: List[Dict[str, Any]] = Field(default_factory=list)  # F5 化合反应记录（M2）
    positive_sum_logs: List[Dict[str, Any]] = Field(default_factory=list)  # F6 正和验证记录（M2）
    mou_logs: List[Dict[str, Any]] = Field(default_factory=list)  # M3-5: 数字人民币 MOU 锚定记录（CB-IF-001）
    # M3-6: DSA 状态机扩展字段（SBX-SUSPENDED/SBX-BANNED，扩展字段先行，DCD 批准后完整落地）
    dsa_status: Optional[str] = None  # SBX-ACTIVE / SBX-SUSPENDED / SBX-BANNED
    dsa_break_level: str = ""  # MINOR / MODERATE / SEVERE（DSA-001 §3.4 回退三档）
    dsa_reason: str = ""  # 熔断触发原因
    dsa_updated_at: str = ""
    dsa_banned_at: str = ""
    # M4-3（tdca-pricer）：配置权价格（P_C 落点；BANNED/SUSPENDED 时强制归零，DSA-001 §3.4）
    config_right_price: float = 0.0
    created_at: str = ""
    updated_at: str = ""


class ExitEligibility(BaseModel):
    """出盒资格判定（SV-1 必要条件 + SV-6 异构三角签名）。

    注: 当前由 activation_engine.check_exit_eligibility 返回 dict 承载，
    本模型保留为契约文档（M2 三位一体落地时启用）。
    """

    eligible: bool
    activation_passed: bool
    signatures_passed: bool
    activation: Dict[str, Any]
    signatures: Dict[str, Any]
    reasons: List[str] = Field(default_factory=list)
