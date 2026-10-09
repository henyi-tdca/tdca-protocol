# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F4 S-Right 场景配置权 API——分配/梯度/PUCR 预售（SV-2）
# 约束矩阵:     FC-SBX-OPS-001 SV-2 + 宪法 C13 + 接口熵=0
# 先验分布:     任务书 §二 F4 + sright.py
# 配置权边界:    L2 层
# 预期分配:     REST 端点；失败=400/404/422
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F4 S-Right 场景配置权 API（制度梯度 + PUCR 预售）。

制度锚定: FC-SBX-OPS-001 F4 / SV-2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/sandboxes", tags=["S-Right 场景配置权 F4（M2）"])

_core = SandboxCore()


class SRightAllocate(BaseModel):
    """S-Right 分配请求。"""

    scene: str
    holder_did: str
    gradient: str = "L0"  # L0→L1→L2→L3 制度梯度


class PucrPresale(BaseModel):
    """PUCR 预售请求（SV-2）。"""

    amount: float
    data_nature: str = "simulated"
    mou_anchor: str = ""


@router.post("/{sandbox_id}/srights", response_model=Sandbox)
def allocate_sright(sandbox_id: str, req: SRightAllocate) -> Sandbox:
    """S-Right 场景配置权分配（F4：微创新场景准入 + 制度梯度）。"""
    try:
        return _core.allocate_sright(sandbox_id, req.scene, req.holder_did, req.gradient)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/pucr", response_model=Sandbox)
def pucr_presale(sandbox_id: str, req: PucrPresale) -> Sandbox:
    """PUCR 预售/质押（SV-2：零数据企业第一笔可验证硬数据）。"""
    try:
        return _core.pucr_presale(sandbox_id, req.amount, req.data_nature, req.mou_anchor)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
