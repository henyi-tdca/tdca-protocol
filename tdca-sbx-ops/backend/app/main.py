# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证，M1 冻结延续；M3-1/M3-2/M3-3 扩展）
# 目标函数:     SBX-OPS M1 FastAPI 入口——沙盒生命周期（F1）+ 激活系数（F3）+ NCA 存证（F8）
#               M3-1 扩展: F7 沙盒-负空间联动（nsops 路由，NS-IF-001~003）
#               M3-2 扩展: 联动层 FlowEngine 挂接（flow 路由，FE-IF-001/002）
#               M3-3 扩展: 联动层 PhaseMachine 阶段推进（phase 路由，PM-IF-001）
#               M3-4 扩展: 联动层 效用精灵深度对接（genie_callback 路由，GE-IF-001）
#               M3-5 扩展: 联动层 数字人民币 MOU 锚定（cbdc 路由，CB-IF-001）
#               M3-6 扩展: 联动层 DSA 状态机扩展（dsa 路由，SBX-SUSPENDED/BANNED）
# 约束矩阵:     宪法十六条（可观测）+ FC-SBX-OPS-001 SV-1~7 + 接口熵=0
# 先验分布:     任务书 FROZEN + NS-OPS main.py 模式
# 配置权边界:    L2 层；CORS 限前端；OpenAPI 暴露契约
# 预期分配:     uvicorn 可运行服务；失败=端口占用/启动异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""SBX-OPS M1 FastAPI 入口。

制度锚定: FC-SBX-OPS-001 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import activation, cbdc, chem, dsa, flow, genie, genie_callback, nca, nsops, phase, sandboxes, sandbox_feed, sright, trinity
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时幂等播种（seed 副作用收敛于 lifespan，避免 import 期写盘）。"""
    seed_if_empty()
    yield


app = FastAPI(
    title="TDCA SBX-OPS 沙盒实验操作空间（M2 三位一体与正和验证 + M3-1~M3-6 扩展）",
    description=(
        "沙盒生命周期管理 CRUD（F1）+ 激活系数引擎（F3，SV-1 >1.2 硬编码）+ "
        "NCA 全操作存证（F8，SV-7）+ 三位一体协调（F2）+ S-Right 场景配置权（F4）"
        "+ 五阶资产化合（F5，CHEM-001~004 + ENG-003）+ 正和实时验证（F6）"
        "+ M3-1 沙盒-负空间实时联动（F7，NS-IF-001~003 对接 NS-OPS）"
        "+ M3-2 全周期生命周期挂接（FE-IF-001/002 对接 FlowEngine）"
        "+ M3-3 阶段机联动（PM-IF-001 对接 PhaseMachine）"
        "+ M3-4 效用精灵深度对接（GE-IF-001）"
        "+ M3-5 数字人民币 MOU 锚定（CB-IF-001）"
        "+ M3-6 DSA 状态机扩展（SBX-SUSPENDED/BANNED）。"
        "制度锚定: FC-SBX-OPS-001 SV-1~7 + SV-8/SV-9/SV-10"
    ),
    version="0.3.0-M3",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sandboxes.router)
app.include_router(activation.router)
app.include_router(nca.router)
app.include_router(trinity.router)  # M2: F2 三位一体
app.include_router(sright.router)   # M2: F4 S-Right
app.include_router(chem.router)     # M2: F5 五阶化合
app.include_router(genie.router)    # M2: F6 正和验证
app.include_router(nsops.router)    # M3-1: F7 沙盒-负空间联动（NS-IF-001~003）
app.include_router(flow.router)      # M3-2: 联动层 FlowEngine 挂接（FE-IF-001/002）
app.include_router(phase.router)     # M3-3: 联动层 PhaseMachine 阶段推进（PM-IF-001）
app.include_router(genie_callback.router)  # M3-4: 联动层 效用精灵深度对接（GE-IF-001）
app.include_router(cbdc.router)       # M3-5: 联动层 数字人民币 MOU 锚定（CB-IF-001）
app.include_router(dsa.router)        # M3-6: 联动层 DSA 状态机扩展（SBX-SUSPENDED/BANNED）
app.include_router(sandbox_feed.router)  # M3-7: 沙盒四维取数只读接口（NCA-SANDBOX-FEED-001·审计八维 3.2~3.5 供数）


@app.get("/", tags=["健康"])
def health() -> dict:
    """服务健康检查（可观测优先）。

    六要素声明:
    目标函数: 健康探针（宪法 C01 可观测）
    约束矩阵: 输入——无；输出——服务状态；禁止——无
    先验分布: NS-OPS main 模式
    配置权边界: L2
    预期分配: 返回健康状态；失败=无
    审计轨迹: 只读探针
    """
    return {"service": "tdca-sbx-ops", "fc": "TDCA-FC-SBX-OPS-001", "stage": "M3", "status": "ok"}
