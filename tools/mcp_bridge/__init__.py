# FC-ID: DCD-MCP-BRIDGE-001 | tdca-mcp-bridge —— MCP 智能体的 TDCA 制度层挂载
# 定位: 任何 MCP 智能体的工具调用 → NCA 存证水印 + NSFL 熔断预检（正交挂载，不改写业务逻辑）
"""tdca-mcp-bridge（M1）：标准 MCP server（stdio JSON-RPC 2.0），五模块：
server（协议）/ fuse（NSFL 预检）/ watermark（NCA 自动落链）/ query（nca:get/chain）/ core（TDCA_CORE 加载）
"""
__version__ = "0.1.0"
