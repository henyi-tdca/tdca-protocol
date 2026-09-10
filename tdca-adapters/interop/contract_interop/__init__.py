# -*- coding: utf-8 -*-
"""TDCA 合约 × 国标交互对接模块（M4）——GB/Z 185.6 交互 → 合约 → 计税触发。"""
from .interop import (MODES, ContractCall, ContractInteropGateway,  # noqa: F401
                      InteractionEvent)

__all__ = ["ContractInteropGateway", "InteractionEvent", "ContractCall", "MODES"]
