"""TDCA × mcp-atlassian 静默挂载适配器（tdca-mcp-atlassian-silent-mount）。

独立组件；协议层对接 sooperset/mcp-atlassian 公开接口语义（MCP 服务器（Jira/Confluence 工具面）），
不复制上游代码、不修改上游源码、不真实连接上游 API（静默挂载 = 对方零感知）。
仅模拟态试点 · 未实连上游。
"""

from .adapter import TdcaMcpatlSilentMount

__all__ = ["TdcaMcpatlSilentMount"]
__version__ = "0.1.0"
__simulated__ = True
