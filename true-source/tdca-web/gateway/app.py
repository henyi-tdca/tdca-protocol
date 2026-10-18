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
from contextlib import asynccontextmanager
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

@asynccontextmanager
async def _lifespan(_app):
    # NCA-ATOMIC 辅改 B：服务启动即对现有 prev_nca 计数打内存基线快照
    # （告警「只报新增」基线差口径；不入库、不建表；快照失败首写惰性回退）
    from api_v1 import init_nca_fork_baseline
    init_nca_fork_baseline()
    # T-037 任务 C：超期升档扫掠（服务内定时，⛔ 不入请求径；写口只许置永久）
    import asyncio
    from agent_channel_ops import _prs_sweep_loop
    _sweep_task = asyncio.create_task(_prs_sweep_loop())
    try:
        yield
    finally:
        _sweep_task.cancel()


app = FastAPI(title="TDCA Unified API Gateway", version="V1.0",
              description="5CC 阶段 1 统一网关：聚合 D-2 / CSCP / Workbuddy / Translator / P3 + bridge",
              lifespan=_lifespan)

# L1SI153-ERROR-CODE-001 段一：拒绝类响应统一挂码（全局 handler 仅增设 code 字段；
# ⛔ 不改状态码/文案/判定分支；归簇见 error_codes.py）
from fastapi.exceptions import RequestValidationError  # noqa: E402
from starlette.exceptions import HTTPException as _StarletteHTTPException  # noqa: E402
from error_codes import (tdca_http_exception_handler,  # noqa: E402
                         tdca_validation_exception_handler)
app.add_exception_handler(_StarletteHTTPException, tdca_http_exception_handler)
app.add_exception_handler(RequestValidationError, tdca_validation_exception_handler)

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

# 乙案 P2: 运维每日日志（/api/v1/ops/logs/*——V-1~V-8 服务端校验；红点+连续未填入 P7 工单池；CSV 导出）
from ops_logs_ops import router as ops_logs_ops_router  # noqa: E402
app.include_router(ops_logs_ops_router)

# 手册接口化（INACCOUNT-DEPLOY 块 2）: /api/v1/ops/files/*——在册七件按角色出件；
# 撤 /ops/files/ 静态门后唯一取件口（白名单防穿越；md→text/markdown；容器内只读挂载）
from ops_files_ops import router as ops_files_ops_router  # noqa: E402
app.include_router(ops_files_ops_router)

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

# A-23: 公告栏（/api/v1/announcements/*——对外公告区；公开读；发布须 operator/founder 且经创始人明示；NCA 存证）
from announcements_ops import router as announcements_ops_router  # noqa: E402
app.include_router(announcements_ops_router)

# A-24: P8b 授权登记管理（/api/v1/authorization/*——登记／变更／注销／查询／操作＋公开查四字段；
# 四要件缺一即拒；四条不公开负空间 fail-closed；签名须本人、智能体不代持代填）
from authorization_ops import router as authorization_ops_router  # noqa: E402
app.include_router(authorization_ops_router)

# A-25: 配置权市场「管理」面（/api/v1/market-admin/*——挂出／查询／状态变更／下架；
# 先有成件＋四要件合取闸门（例外仅沙盒演练）；限权属登记人本人；下架不溯及授权件；
# 公开面四字段；每操作落 NCA＋事件双留痕）
from market_admin_ops import router as market_admin_ops_router  # noqa: E402
app.include_router(market_admin_ops_router)

# A-26: 智能体通道 批1 身份与登记（/api/v1/agent-channel/*——登记即创建·未登记显幽灵态；
# 主体/执行体二分；登记号为智能体侧标识（⛔ 非 TDID）；fail-closed 六步总闸；
# 凭据只存指纹·人类会话内签发·锚无效不发令牌；草案五表只读不动）
from agent_channel_ops import router as agent_channel_ops_router  # noqa: E402
app.include_router(agent_channel_ops_router)

# A-27: 公开只读制度件取得面（丙案 · L1SI151-PUBLIC-ROUTE-001——/api/public/docs/* 匿名只读
# 已入站公开件；只读容器件单一事实源；fail-closed；旧 /api/site/docs 为同一实现之别名）
from public_docs_ops import router as public_docs_router  # noqa: E402
app.include_router(public_docs_router)
from public_docs_ops import alias_router as public_docs_alias_router  # noqa: E402
app.include_router(public_docs_alias_router)

# A-28: 存证公开自查入口 M1″（/api/v1/selfcheck/*——只读匿名白名单十字段；rec_hash 可真验；
# 031 令：⛔ 不含部署、⛔ 不出 actor 原值、⛔ 不做列表接口防枚举、限流 60/分/IP）
from selfcheck_ops import router as selfcheck_ops_router  # noqa: E402
app.include_router(selfcheck_ops_router)

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
