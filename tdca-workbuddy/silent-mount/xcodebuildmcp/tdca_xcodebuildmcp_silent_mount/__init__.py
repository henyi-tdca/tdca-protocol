"""TDCA × xcodebuildmcp 静默挂载适配器（tdca-xcodebuildmcp-silent-mount）。

独立组件；协议层对接 getsentry/XcodeBuildMCP 公开接口语义（MCP 服务器（Xcode 构建工具面）），
不复制上游代码、不修改上游源码、不真实连接上游 API（静默挂载 = 对方零感知）。
仅模拟态试点 · 未实连上游。
"""

from .adapter import TdcaXcodeSilentMount

__all__ = ["TdcaXcodeSilentMount"]
__version__ = "0.1.0"
__simulated__ = True
