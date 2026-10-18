# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-1 沙盒-负空间实时联动 API——NS-IF-001~003 端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + SV-10 + 接口熵=0（ID82）
#               + NS-OPS BV-1（越界实时监控，触发即熔断）+ ID86
# 先验分布:     nsops_adapter.py（NS-IF 契约）+ NS-OPS M3 API（8123）
# 配置权边界:   L2 层；NS-OPS 只读对接
# 预期分配:     REST 端点；失败=404/422/503（NS-OPS 不可达）
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-1 沙盒-负空间实时联动 API（NS-IF-001~003）。

制度锚定: FC-SBX-OPS-001 F7 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import nsops_adapter

router = APIRouter(prefix="/api/v1/nsops", tags=["沙盒-负空间联动（F7/M3-1）"])

_adapter = nsops_adapter.ADAPTER

# layer/scene 枚举（NS-OPS 约束层 + 场景标识，E5 输入校验；#10 与 NS-OPS context 对齐）
_VALID_LAYERS = ("subject", "scene", "institutional")
_VALID_SCENES = ("community", "hospital")


class BoundaryCheckRequest(BaseModel):
    """NS-IF-002 边界校验请求（F3 声明-行为校验 + BV-1 熔断）。"""

    actor: str = Field(min_length=2, max_length=64, description="行为主体 DID/标识")
    action: str = Field(min_length=2, max_length=256, description="行为描述")
    scene: str = Field(default="community", description="场景标识（community/hospital，与 NS-OPS context 对齐）")
    sandbox_id: str = Field(default="", description="关联沙盒 ID（M3-6 熔断落地预留，可为空）")


class ComplianceCertRequest(BaseModel):
    """NS-IF-003 合规证明请求（出盒评估）。"""

    actor: str = Field(min_length=2, max_length=64, description="行为主体 DID/标识")
    action: str = Field(min_length=2, max_length=256, description="行为描述")


@router.get("/constraints", summary="NS-IF-001 负空间约束清单查询")
def query_constraints(layer: Optional[str] = None) -> Dict[str, Any]:
    """查询 NS-OPS 负空间约束清单（沙盒创建/运行时准入校验）。

    六要素声明:
    目标函数: NS-IF-001 约束查询端点（F7 沙盒-负空间联动）
    约束矩阵: 输入——layer（subject/scene/institutional）；输出——约束清单；
              禁止——NS-OPS 不可达/非 200 静默放行（fail-closed）
    先验分布: DSA 接口规范 IF-001 语义 + NS-OPS GET /api/v1/constraints
    配置权边界: L2；NS-OPS 只读对接
    预期分配: 200 + 约束清单；失败=422（layer 非法）/503（NS-OPS 不可达）
    审计轨迹: NSOPS_QUERY_CONSTRAINTS NCA（SV-10 双向存证）
    """
    if layer is not None and layer not in _VALID_LAYERS:
        raise HTTPException(status_code=422, detail=f"layer 必须为 {'/'.join(_VALID_LAYERS)}")
    try:
        return _adapter.query_constraints(layer=layer)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/check", summary="NS-IF-002 实时边界校验 + BV-1 熔断触发")
def check_boundary(req: BoundaryCheckRequest) -> Dict[str, Any]:
    """实验运行时实时校验负空间边界（F3），触碰 → BV-1 熔断触发。

    六要素声明:
    目标函数: NS-IF-002 熔断触发端点（F7 实时联动，SV-8 <1s）
    约束矩阵: 输入——actor/action/scene/sandbox_id；输出——decision + fuse_triggered；
              禁止——BLOCK（法律负空间）放行（ID86 绝对熔断）、非 200 默认 allow（fail-closed）
    先验分布: DSA 接口规范 IF-003 语义 + NS-OPS POST /api/v1/judgments（Decision 四值枚举）
    配置权边界: L2；熔断指令来自 NS-OPS 判定，SBX-OPS 不代行
    预期分配: 200 + 判定；失败=503（NS-OPS 不可达）/422（参数缺失）
    审计轨迹: NSOPS_BOUNDARY_CHECK NCA（fuse 时 negative_space_check=FUSE，SV-10）
    """
    if req.scene not in _VALID_SCENES:
        raise HTTPException(status_code=422, detail=f"scene 必须为 {'/'.join(_VALID_SCENES)}")
    try:
        return _adapter.check_and_fuse(
            actor=req.actor, action=req.action, scene=req.scene, sandbox_id=req.sandbox_id
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/compliance", summary="NS-IF-003 负空间合规证明（出盒评估）")
def compliance_cert(req: ComplianceCertRequest) -> Dict[str, Any]:
    """出盒评估时获取负空间合规证明（NSFL 预检 + 熔断台账）。

    六要素声明:
    目标函数: NS-IF-003 合规证明端点（F7 出盒评估，SV-3 负空间合规）
    约束矩阵: 输入——actor/action；输出——compliant + 证据；
              禁止——活跃熔断/预检 blocked 判合规（ID86/NSFL 三不可）、非 200 误判合规（fail-closed）
    先验分布: DSA 接口规范 IF-002 语义参考 + NS-OPS NSFL 预检/熔断台账
    配置权边界: L2；NS-OPS 只读对接
    预期分配: 200 + 合规证明；失败=503（NS-OPS 不可达）
    审计轨迹: NSOPS_COMPLIANCE_CERT NCA（SV-10 双向存证）
    """
    try:
        return _adapter.compliance_cert(actor=req.actor, action=req.action)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
