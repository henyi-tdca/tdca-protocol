# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F2 三位一体 API——三方注册/Shapley 分配/审计视图
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + KB-ECON-001 §4 + 接口熵=0
# 先验分布:     任务书 §二 F2 + trinity.py
# 配置权边界:    L2 层
# 预期分配:     REST 端点；失败=400/404/422 语义化
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F2 三位一体 API（三方协调 + Shapley 分配）。

制度锚定: FC-SBX-OPS-001 F2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/sandboxes", tags=["三位一体 F2（M2）"])

_core = SandboxCore()


class TrinityProfile(BaseModel):
    """三方之一注册请求。"""

    role: str = Field(description="innovator | investor | government")
    did: str
    contribution: Dict[str, Any]
    reservation_utility: float = 0.0


class TrinityConfigure(BaseModel):
    """三方注册请求（须含三方）。"""

    profiles: List[TrinityProfile]


@router.post("/{sandbox_id}/trinity", response_model=Sandbox)
def configure_trinity(sandbox_id: str, req: TrinityConfigure) -> Sandbox:
    """三方注册（F2：创新者/投资者/政府配置）。"""
    try:
        return _core.configure_trinity(sandbox_id, [p.model_dump() for p in req.profiles])
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/trinity/shapley", response_model=Sandbox)
def shapley_allocate(sandbox_id: str) -> Sandbox:
    """Shapley 分配（F2：三方收益分配，KB-ECON-001 §4）。"""
    try:
        return _core.shapley_allocate(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{sandbox_id}/trinity")
def get_trinity(sandbox_id: str) -> Dict[str, Any]:
    """三位一体视图（含 Shapley 权重 + 四性质验证）。"""
    try:
        sb = _core.get(sandbox_id)
        return {"sandbox_id": sandbox_id, "trinity": sb.trinity}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
