# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M3 验收交付，M1/M2 冻结延续）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——FastAPI 入口
# 约束矩阵:     宪法十六条（可观测）+ FC-NS-OPS-001 F1-F6 + BV-1~7
# 先验分布:     NS-GOVERNANCE-SYSTEM-001 + 论丛规格 + edu-simulator 后端模式
# 配置权边界:    L2 层；CORS 限前端；OpenAPI 暴露契约（接口熵=0）
# 预期分配:     uvicorn 可运行服务；失败=端口占用/启动异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NS-OPS M1 FastAPI 入口。

制度锚定: FC-NS-OPS-001 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import adjustments, constraints, integration, views

app = FastAPI(
    title="TDCA NS-OPS 负空间管理操作空间（M1 原型）",
    description=(
        "人类操作台（慢系统人机界面）：约束管理 CRUD（F1）+ 三层负空间视图（F1）"
        "+ 调整权操作（F2，NS-011 快慢分离）+ 声明-行为校验（F3）+ 沙盒（F4）+ NCA 存证（F6）。"
        "制度锚定: FC-NS-OPS-001 BV-1~7"
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

app.include_router(constraints.router)
app.include_router(views.router)
app.include_router(adjustments.router)
app.include_router(integration.router)


@app.get("/", tags=["健康"])
def health() -> dict:
    """服务健康检查（可观测优先）。"""
    return {"service": "tdca-ns-ops", "fc": "TDCA-FC-NS-OPS-001", "stage": "M3", "status": "ok"}
