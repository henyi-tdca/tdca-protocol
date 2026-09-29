# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M4 | 目标函数: 生产启动脚本（uvicorn）
# 约束矩阵: 配置全走环境变量（HOST/PORT/AUTH/TOKEN/DATABASE_URL），零硬编码
# =============================================================================
"""M4 生产启动：在 gateway/ 目录下运行  python scripts/serve.py
环境变量：TDCA_HOST（默认 0.0.0.0）/ TDCA_PORT（默认 8000）/
          TDCA_GATEWAY_AUTH=1 启用鉴权 / TDCA_GATEWAY_TOKEN 静态降级令牌 /
          DATABASE_URL 数据库连接串（默认 gateway/tdca.db）
"""
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("TDCA_HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("TDCA_PORT", "8000")))
    args = ap.parse_args()  # 支持 npm run dev -- --port N（Kimi Work 预览转发 CLI 参数）
    uvicorn.run("app:app", host=args.host, port=args.port, workers=1, log_level="info")
