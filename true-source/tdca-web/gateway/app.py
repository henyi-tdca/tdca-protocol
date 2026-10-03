# -*- coding: utf-8 -*-
"""
TDCA 统一 API 网关（前端可用性缺口修复）
聚合 5 个 FastAPI 子应用（D-2 / CSCP / Workbuddy / Translator / P3 Cross-Scene），
mount 到语义前缀——前端经单一 BASE 访问全部数据源（CP-1~6）。

路由映射:
  /nsfl/*            → D-2 并集引擎（preflight/check，CP-1）
  /api/*             → CSCP 网关（handshake/list·detail·status + nca/chain，CP-2/4/5）
  /workflow/*        → P5 Workbuddy（status，CP-6）
  /translator/*      → W4 翻译器市场（match）
  /cross-scene/*     → W3 跨场景沙盒
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import sys
from pathlib import Path

# 跨项目路径注入（与各子应用保持一致）
_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("tdca-d2-union", "tdca-cscp", "tdca-workbuddy",
             "tdca-translator-market", "tdca-cross-scene"):
    _p = _ROOT / _sub
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import FastAPI

from nsfl_union.api import app as d2_app
from cscp_gateway.gateway import app as cscp_app
from workbuddy.api import app as wb_app
from translator_market.api import app as tm_app
from cross_scene.p3_api import app as p3_app

# B-3: 统一后端体系——纳入 tdca-bridge（原 :8080）端点，前端统一走 gateway :8100
# bridge 端点带 /api 前缀（/api/search /api/edu/* /api/agents /api/health 等），include_router 保留原路径
_BRIDGE_DIR = _ROOT / "tdca-bridge"
if _BRIDGE_DIR.is_dir() and str(_BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRIDGE_DIR))

app = FastAPI(title="TDCA Unified API Gateway", version="V1.0",
              description="5CC 阶段 1 统一网关：聚合 D-2 / CSCP / Workbuddy / Translator / P3 + bridge")

# bridge 挂载必须在 app 创建之后（修复：原位置在 app 定义前，NameError 被 except 静默吞掉导致 bridge 全 404）
try:
    from main import app as bridge_app  # tdca-bridge（惰性引擎：RAG 缺失时端点 503 不崩溃）
    app.include_router(bridge_app.router)
except Exception:  # pragma: no cover — bridge 不可用时网关其余路由不受影响
    bridge_app = None

# B-4: 网关鉴权（默认宽松，TDCA_GATEWAY_AUTH=1 启用——写操作/治理路径须 TDCA-CRT token）
from auth import TDCAGatewayAuthMiddleware  # noqa: E402
app.add_middleware(TDCAGatewayAuthMiddleware)

# B-5: WebSocket 实时端点（前端实时观测通道：handshake/tax_mou/notifier/audit）
from ws_events import router as ws_router  # noqa: E402
app.include_router(ws_router)

# A 类: API 面包装层（/api/v1/*，纯 Python FROZEN 库薄包装——首页/税收/市场/沙盒/学院/审计/治理/通知机/集群）
from api_v1 import router as api_v1_router  # noqa: E402
app.include_router(api_v1_router)

# A-12: P1 WorkBuddy 上站（/api/v1/workbuddy/*——会话鉴权 + DB 持久化 + NCA 落链；不改 FROZEN 子应用）
from workbuddy_ops import router as workbuddy_ops_router  # noqa: E402
app.include_router(workbuddy_ops_router)

# A-13: P2 集群编排 + 准入闸门（/api/v1/cluster/*——授权件四要件机验 + 配置类调用闸门 + 谱系账本）
from cluster_ops import router as cluster_ops_router  # noqa: E402
app.include_router(cluster_ops_router)

# A-14: P3 形式化与实验线结论入站（/api/v1/formal/*——只做结论面；入站 ≠ 入主仓 ≠ 对外）
from formal_ops import router as formal_ops_router  # noqa: E402
app.include_router(formal_ops_router)

# A-15: P4 工具货架（/api/v1/toolshelf/*——工具/模板目录；配置类须过准入闸门）
from toolshelf_ops import router as toolshelf_ops_router  # noqa: E402
app.include_router(toolshelf_ops_router)

# A-16: P5 CI 手动触发入口（/api/v1/ci/*——lake build＋core-go＋网关回归；绿灯徽章入 P3 页面）
from ci_ops import router as ci_ops_router  # noqa: E402
app.include_router(ci_ops_router)

# A-17: P6 模拟外部锚与版权事件（/api/v1/anchor/*——三锚 SIMULATED 硬标注；权属登记事件落 NCA 链）
from anchor_ops import router as anchor_ops_router  # noqa: E402
app.include_router(anchor_ops_router)

# A-18: P7 站点运维端（/api/v1/ops/*——红线八项分类器；触碰升 DCD；上线 NCA 存证＋对账可回滚）
from ops_ops import router as ops_ops_router  # noqa: E402
app.include_router(ops_ops_router)

# A-19: P8a 权属登记管理（/api/v1/ownership/*——登记／变更／注销／查询；四条不公开负空间 fail-closed）
from ownership_ops import router as ownership_ops_router  # noqa: E402
app.include_router(ownership_ops_router)

# A-20: P9 规范索引区（/api/v1/regulations/*——只列名目与索引入口；版本读件内不硬编码）
from regulations_ops import router as regulations_ops_router  # noqa: E402
app.include_router(regulations_ops_router)

# A-21: P9 配置权市场沙盒最小链（/api/v1/market-sim/*——发布→准入→撮合→结算；SIMULATED＋NCA 留痕）
from market_sim_ops import router as market_sim_ops_router  # noqa: E402
app.include_router(market_sim_ops_router)

# A-22: 内容区文库（/api/v1/library/*——whitepapers/papers/cop-library 只读面；family 闭集；登录 DID）
from library_ops import router as library_ops_router  # noqa: E402
app.include_router(library_ops_router)

# include_router 保留各子应用原路径（避免 mount 前缀叠加），前端仅需切换 BASE
app.include_router(d2_app.router)        # /nsfl/preflight/check（CP-1）
app.include_router(cscp_app.router)      # /handshake/* + /nca/chain（CP-2/4/5）
app.include_router(wb_app.router)        # /workflow/*（CP-6）
app.include_router(tm_app.router)        # /translator/*
app.include_router(p3_app.router)        # /cross-scene/*


@app.get("/health")
def health() -> dict:
    routes = ["/nsfl", "/handshake", "/workflow", "/translator", "/cross-scene"]
    if bridge_app is not None:
        routes.append("/api（bridge：search/edu/agents/health）")
    return {"status": "OK", "gateway": "TDCA-Unified-API-V1.0",
            "routes": routes}


# =====================================================================
# M4 一体化部署：前端 dist 静态托管 + SPA 回退（同源，免 CORS）
# 环境变量 TDCA_STATIC_DIR 指定 dist 目录；缺省自动探测 ../tdca-frontend/dist
# 目录不存在则不挂载（纯 API 模式，向后兼容既有 46 测试）
# =====================================================================
class _SPAStaticFiles(__import__("starlette.staticfiles", fromlist=["StaticFiles"]).StaticFiles):
    """SPA 回退：未命中文件且非 API 路径 → 回退 index.html（前端 15 路由客户端分发）。"""

    async def get_response(self, path: str, scope):  # noqa: ANN001
        from starlette.exceptions import HTTPException as StarletteHTTPException
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


def _mount_frontend() -> None:
    import os as _os
    static_dir = _os.environ.get("TDCA_STATIC_DIR", "")
    if not static_dir:
        candidate = _Path(__file__).resolve().parent.parent / "tdca-frontend" / "dist"
        static_dir = str(candidate) if candidate.is_dir() else ""
    if static_dir and _Path(static_dir).is_dir():
        app.mount("/", _SPAStaticFiles(directory=static_dir, html=True), name="frontend")


try:
    from pathlib import Path as _Path
    _mount_frontend()
except Exception:
    pass  # 静态托管为可选增强，失败不阻塞 API 服务
