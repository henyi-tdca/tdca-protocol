# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     激活系数评估 API（F3）——SV-1 硬编码 >1.2
# 约束矩阵:     FC-SBX-OPS-001 SV-1 + 开发纪律 1（不可 mock，数据性质标注）
# 先验分布:     任务书 §二 F3 + activation_engine
# 配置权边界:    L2 层
# 预期分配:     POST 评估端点；失败=400/422/404
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""激活系数评估 API（F3）。

制度锚定: FC-SBX-OPS-001 F3 / SV-1 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/sandboxes", tags=["激活系数引擎（F3）"])

_core = SandboxCore()


class EvaluateRequest(BaseModel):
    """激活系数评估请求（F3，SV-1）。"""

    pcr_input: float  # 政府初始 PCR 投入
    tax_revenue: float  # 出盒税收贡献
    employment_ss: float  # 就业社保
    data_nature: Literal["real", "simulated"] = "simulated"  # 数据性质标注（开发纪律 1）


@router.post("/{sandbox_id}/evaluate", response_model=Sandbox)
def evaluate_sandbox(sandbox_id: str, req: EvaluateRequest) -> Sandbox:
    """激活系数计算并推进评估阶段（F3：决策门三档 + F8 过程存证）。

    激活系数 = (tax_revenue + employment_ss) / pcr_input
    α > 1.2 → 财政自给性达成（出盒必要条件）；1.0 < α ≤ 1.2 → 条件续期；α ≤ 1.0 → 熔断

    六要素声明:
    目标函数: 激活系数评估入口（F3，SV-1）
    约束矩阵: 输入——pcr/tax/ss/data_nature；禁止——pcr≤0、负数、mock 数据
    预期分配: 200 + P1 沙盒；失败=404/422
    审计轨迹: SBX_EVALUATE NCA 存证（含 input_hash）
    """
    try:
        return _core.evaluate(
            sandbox_id,
            pcr_input=req.pcr_input,
            tax_revenue=req.tax_revenue,
            employment_ss=req.employment_ss,
            data_nature=req.data_nature,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
