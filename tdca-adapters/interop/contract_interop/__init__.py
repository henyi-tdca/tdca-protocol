# -*- coding: utf-8 -*-
"""TDCA 合约 × 国标交互对接（M4）——185.6 交互 → 合约 → 计税/结算触发。

- 主体：`interop.py`（三模式交互 → 日志（税触发）→ 计税 → 合约意图 → 存证）
- #10 合约族对接：`contract_family.py`（只读装载 official-kb 模板 + C01~C16 条款核验）
- #11/#12 内容元素与参与方权限：`g185_6.py`（Data/Message/Task/Session + 群组/混合 + MRCR）
- #13 结算接 CLS：`interop_cls.py`（净额/定向支付 + 台账 + NCA）
"""
from .interop import MODES, ContractCall, ContractInteropGateway, InteractionEvent  # noqa: F401
from .g185_6 import (G185_6_FIELDS, G185_6_MODES, G185_6_RELATIONS, MRCR_RULE_ACTION,  # noqa: F401
                     Data, GroupMember, GroupPermissionError, GroupRegistry, InteractionGroup,
                     Message, Session, Task, field_coverage, mrcr_check, plan_hybrid,
                     project_interaction, validate_element)
from .contract_family import (ACTION_TEMPLATE_HINTS, CORE_CLAUSES, ContractBinding,  # noqa: F401
                              ContractBindingError, ContractFamily, ClauseCheck)
from .interop_cls import (DEFAULT_TREASURY, InteropSettlement, InteropSettlementError,  # noqa: F401
                          settle_interactions)

__all__ = [
    "ContractInteropGateway", "InteractionEvent", "ContractCall", "MODES",
    # #10 合约族
    "ContractFamily", "ContractBinding", "ContractBindingError", "ClauseCheck",
    "ACTION_TEMPLATE_HINTS", "CORE_CLAUSES",
    # #11 内容元素
    "Data", "Message", "Task", "Session", "G185_6_FIELDS", "G185_6_MODES", "G185_6_RELATIONS",
    "validate_element", "field_coverage", "project_interaction",
    # #12 群组/混合/MRCR
    "GroupRegistry", "InteractionGroup", "GroupMember", "GroupPermissionError",
    "mrcr_check", "plan_hybrid", "MRCR_RULE_ACTION",
    # #13 结算接 CLS
    "settle_interactions", "InteropSettlement", "InteropSettlementError", "DEFAULT_TREASURY",
]
