# -*- coding: utf-8 -*-
"""TDCA 智能体遗产继承机制（Inheritance / G3）

- 最小实现（R-1~R-8）：`estate.py`（继承机制立项件，内部存证）
- 深化（#14~#16）：`dormancy.py`（休眠态状态机）/ `shapley.py`（份额 Shapley 化 + 争议流程）
  / `royalty.py`（分润权益过渡期记账）
- 无主权益托管（#17）：`escheat.py`（社区基金公共品；AMEND-1 / AMEND-2 口径）
- 身份桥接联动（#18）：`identity_link_sync.py`（主体消亡/终态 → TDID↔OID 链接失效同步 `revoke`）
"""
from .estate import (  # noqa: F401
    DISPOSITIONS, Beneficiary, EstateRecord, InheritanceError, InheritanceRegistry, Testament)
from .dormancy import (  # noqa: F401
    DEFAULT_WINDOW_DAYS, DORMANCY_STATES, WAKE_TRIGGERS, DormancyError, DormancyRecord,
    DormancyRegistry)
from .shapley import (  # noqa: F401
    DisputeFlow, DisputeRegistry, ShapleyError, propose_distribution, shapley_shares,
    shapley_values)
from .royalty import (  # noqa: F401
    RoyaltyEntry, RoyaltyLedgerError, RoyaltyTransitionLedger)
from .escheat import (  # noqa: F401
    DEFAULT_FUND_ID, DEFAULT_UNCLAIMED_DAYS, ESCHEAT_STATES, EscheatError, EscheatRecord,
    EscheatRegistry)
from .identity_link_sync import (  # noqa: F401
    DEMISE_TRIGGERS, SYNC_ACTIONS, TERMINAL_TRIGGERS, IdentityLinkSync, IdentityLinkSyncError,
    SyncOutcome)

__all__ = [
    # 最小实现（R-1~R-8）
    "InheritanceRegistry", "InheritanceError", "Beneficiary", "Testament", "EstateRecord",
    "DISPOSITIONS",
    # #14 休眠态
    "DormancyRegistry", "DormancyRecord", "DormancyError", "DORMANCY_STATES",
    "WAKE_TRIGGERS", "DEFAULT_WINDOW_DAYS",
    # #15 份额与争议
    "shapley_values", "shapley_shares", "propose_distribution",
    "DisputeRegistry", "DisputeFlow", "ShapleyError",
    # #16 过渡期记账
    "RoyaltyTransitionLedger", "RoyaltyEntry", "RoyaltyLedgerError",
    # #17 无主权益托管（社区基金公共品）
    "EscheatRegistry", "EscheatRecord", "EscheatError", "DEFAULT_FUND_ID",
    "DEFAULT_UNCLAIMED_DAYS", "ESCHEAT_STATES",
    # #18 身份桥接联动（主体消亡 → 链接失效同步）
    "IdentityLinkSync", "SyncOutcome", "IdentityLinkSyncError",
    "DEMISE_TRIGGERS", "TERMINAL_TRIGGERS", "SYNC_ACTIONS",
]
