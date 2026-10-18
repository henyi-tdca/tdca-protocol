# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F6 正和博弈实时验证 API——positive_sum + 交付确认
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + KB-ECON-001 §3 + 接口熵=0
# 先验分布:     任务书 §二 F6 + utility_genie_adapter.py
# 配置权边界:    L2 层；效用精灵只读
# 预期分配:     REST 端点；失败=400/404/422/503（效用精灵不可用）
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F6 正和博弈实时验证 API（效用精灵只读对接）。

制度锚定: FC-SBX-OPS-001 F6 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import Sandbox
from ..sandbox_core import SandboxCore
from .. import utility_genie_adapter as genie

router = APIRouter(prefix="/api/v1/sandboxes", tags=["正和博弈验证 F6（M2）"])

_core = SandboxCore()


class PositiveSumCheck(BaseModel):
    """正和验证请求（KB-ECON-001 §3：S_synergy > 0）。"""

    coalition_utility: float
    independent_utilities: List[float]


class DeliveryConfirm(BaseModel):
    """出盒正和交付确认请求（效用精灵 ContractDeliveryValidator）。"""

    contract_id: str
    target_utility: Dict[str, float]
    actual_mou: Dict[str, float]
    token_ref: str


@router.post("/{sandbox_id}/positive-sum", response_model=Sandbox)
def positive_sum_check(sandbox_id: str, req: PositiveSumCheck) -> Sandbox:
    """正和实时验证（F6：S_synergy > 0；非正和 → FUSE 熔断标记）。"""
    try:
        return _core.verify_positive_sum(sandbox_id, req.coalition_utility, req.independent_utilities)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/delivery-confirm", response_model=Sandbox)
def delivery_confirm(sandbox_id: str, req: DeliveryConfirm) -> Sandbox:
    """出盒正和交付确认（F6/任务书 §6.3：MOU 税收锚定硬验证 + NCA 存证 SV-7）。"""
    try:
        return _core.delivery_confirm(
            sandbox_id, req.contract_id, req.target_utility, req.actual_mou, req.token_ref
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))  # 效用精灵不可用（不可 mock）
