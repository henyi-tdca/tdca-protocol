# -*- coding: utf-8 -*-
"""层间接口适配模块（G4）——A2A Agent Card ↔ CDP / ATH 令牌 → 配置权边界切片。"""
from .a2a_cdp import (A2ACardError, card_to_cdp, cdp_to_card,  # noqa: F401
                      validate_card_mapping)
from .ath_token import (AthTokenError, handshake_to_session,  # noqa: F401
                        slice_to_call_request, token_to_boundary_slice)

__all__ = ["card_to_cdp", "cdp_to_card", "validate_card_mapping", "A2ACardError",
           "token_to_boundary_slice", "handshake_to_session", "slice_to_call_request",
           "AthTokenError"]
