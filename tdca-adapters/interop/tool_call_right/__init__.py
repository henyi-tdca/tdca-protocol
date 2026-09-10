# -*- coding: utf-8 -*-
"""TDCA 场景配置权调用网关（S-Right，M2/V1.1）——185.7 工具调用 → 配置权调用。"""
from .mcp_bridge_adapter import MCP_TOOLS, McpToolCall, McpToolFaceAdapter  # noqa: F401
from .sright import (PCRToken, CallOutcome, CallRequest, GrantRecord,  # noqa: F401
                     SRightGateway, ToolDescriptor)

__all__ = ["SRightGateway", "ToolDescriptor", "CallRequest", "CallOutcome",
           "PCRToken", "GrantRecord", "McpToolFaceAdapter", "McpToolCall", "MCP_TOOLS"]
