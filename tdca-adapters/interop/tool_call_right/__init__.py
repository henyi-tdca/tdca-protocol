# -*- coding: utf-8 -*-
"""TDCA 场景配置权调用网关（S-Right，M2/V1.2）——GB/Z 185.7 工具调用 → 配置权调用。

- 主体：`sright.py`（网关 / PCR-Token / CCV 五层 / Shapley / 边界联动 / 步 3·6 结构化 / 跨主体通知）
- MCP 桥接：`mcp_bridge_adapter.py`（四工具语义映射 + 通道就绪探测 + 实执/dry-run 分流）
- M2 待细化 #1：`pcr_carrier.py`（PCR-Token 交换载体：进程内 / 文件 / 网络占位）
- M2 待细化 #2：`settlement_bridge.py`（Shapley 分配落地结算 → CLS，可选依赖）
"""
from .mcp_bridge_adapter import MCP_TOOLS, McpToolCall, McpToolFaceAdapter  # noqa: F401
from .cli_transport import (CLI_TOOL_MAP, CliCallResult, CliTransport,  # noqa: F401
                            CliTransportError)
from .sright import (PCRToken, CallOutcome, CallRequest, CallerNotification,  # noqa: F401
                     CommitmentDeclaration, GrantRecord, SRightGateway, ToolDescriptor)
from .pcr_carrier import (CARRIER_MODES, CarrierUnavailableError, ExchangeRecord,  # noqa: F401
                          FileExchangeCarrier, InProcessCarrier, NetworkCarrierStub,
                          RoundTripResult, TokenExchangeCarrier, exchange_roundtrip)

try:  # 可选依赖（CLS 闭环结算管线；缺失不影响 S-Right 主体功能）
    from .settlement_bridge import (DEFAULT_TOLERANCE, SettlementBridgeError,  # noqa: F401
                                    ShareSettlement, settle_shares)
    _HAS_SETTLEMENT = True
except Exception:  # noqa: BLE001
    _HAS_SETTLEMENT = False

__all__ = ["SRightGateway", "ToolDescriptor", "CallRequest", "CallOutcome",
           "PCRToken", "GrantRecord", "McpToolFaceAdapter", "McpToolCall", "MCP_TOOLS",
           "CommitmentDeclaration", "CallerNotification",
           "CliTransport", "CliCallResult", "CliTransportError", "CLI_TOOL_MAP",
           "TokenExchangeCarrier", "InProcessCarrier", "FileExchangeCarrier",
           "NetworkCarrierStub", "ExchangeRecord", "RoundTripResult",
           "CarrierUnavailableError", "CARRIER_MODES", "exchange_roundtrip"]
if _HAS_SETTLEMENT:
    __all__ += ["settle_shares", "ShareSettlement", "SettlementBridgeError", "DEFAULT_TOLERANCE"]
