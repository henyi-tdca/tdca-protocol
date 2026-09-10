# -*- coding: utf-8 -*-
"""TDCA 身份桥接模块（M1）——TDID ↔ 国标身份码（OID）映射。"""
from .identity_bridge import (ACTIVE, REVOKED, IdentityBridge,  # noqa: F401
                              IdentityBridgeError, IdentityLink)

__all__ = ["IdentityBridge", "IdentityLink", "IdentityBridgeError", "ACTIVE", "REVOKED"]
