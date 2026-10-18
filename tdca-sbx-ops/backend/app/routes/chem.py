# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F5 五阶资产化合 API——CHEM-001/002 + ENG-003 + 反应轨迹
# 约束矩阵:     FC-SBX-OPS-001 SV-5（最小化合）+ KB-ECON-001 §8 + 接口熵=0
# 先验分布:     任务书 §二 F5 + chem_engine.py
# 配置权边界:    L2 层
# 预期分配:     REST 端点；失败=400/404/422
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F5 五阶资产化合 API（CHEM-001 正向 / CHEM-002 反向 / ENG-003 检查）。

制度锚定: FC-SBX-OPS-001 F5 / SV-5 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/sandboxes", tags=["五阶资产化合 F5（M2）"])

_core = SandboxCore()


class ChemCombine(BaseModel):
    """正向化合请求（CHEM-001 + ENG-003 + 正和门槛——surplus 服务端取自正和验证记录）。"""

    assets: List[str]  # 五阶资产类型（IP/knowledge/exchange/scene_weight/cognitive_nca）
    conditions: Dict[str, bool]  # ENG-003 三条件（indivisible/emergent/nonlinear）
    justification: str  # ENG-003 判定依据（可审计）
    catalyst: bool = False  # CHEM-003 催化剂场


class ChemSeparate(BaseModel):
    """反向分离请求（CHEM-002：NCA 析构，治理介入）。"""

    nca_id: str
    governance_ref: str
    separation_cost: float


@router.post("/{sandbox_id}/chem/combine", response_model=Sandbox)
def chem_combine(sandbox_id: str, req: ChemCombine) -> Sandbox:
    """正向化合（F5/CHEM-001）：ENG-003 检查 + 正和门槛 + 反应记录。"""
    try:
        return _core.chem_combine(
            sandbox_id,
            req.assets,
            req.conditions,
            req.justification,
            catalyst=req.catalyst,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/chem/separate", response_model=Sandbox)
def chem_separate(sandbox_id: str, req: ChemSeparate) -> Sandbox:
    """反向分离（F5/CHEM-002）：NCA 析构，需治理介入。"""
    try:
        return _core.chem_separate(sandbox_id, req.nca_id, req.governance_ref, req.separation_cost)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{sandbox_id}/chem/reactions")
def get_reactions(sandbox_id: str) -> Dict[str, Any]:
    """化合反应轨迹（F8 追溯：五阶资产化合轨迹）。"""
    try:
        sb = _core.get(sandbox_id)
        return {"sandbox_id": sandbox_id, "reactions": sb.reactions, "eng003_log": sb.eng003_log}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
