"""pytest 会话级夹具：为 bridge 测试自动供给网关认证源（GSEQ-2815）。

tdcad mcp serve 缺省读取环境变量 TDCA_GATEWAY_AUTH_FILE 装配本地配置源；
这里把测试夹具（gateway-auth.test.json，仅含标识符 token_id 与绑定，无凭据本体）
注入环境，pytest 本地与 CI 均自动获得认证源。客户端（tdca_mcp_bridge.py）零改动。
"""
import os

os.environ.setdefault(
    "TDCA_GATEWAY_AUTH_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "gateway-auth.test.json"),
)
