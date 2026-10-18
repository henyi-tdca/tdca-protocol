# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，GE-IF 功能组）
# 目标函数:     M3-4 效用精灵深度对接 API——GE-IF-001/001b 端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0（ID82）+ 效用精灵只读
# 先验分布:     genie_callback.py（GE-IF 契约）+ tdca-utility-genie（ID24）
# 配置权边界:   L2 层；效用精灵只读对接
# 预期分配:     REST 端点；失败=404/422/503（效用精灵不可用）
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-4 效用精灵深度对接 API（GE-IF-001/001b）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.3 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import genie_callback, store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/genie", tags=["效用精灵深度对接（M3-4/GE-IF）"])

_core = SandboxCore()


def _require_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒存在性 + ID 合法性校验（404/422 语义统一，WARN-2 公开 API）。"""
    if not store.is_valid_sandbox_id(sandbox_id):
        raise HTTPException(status_code=422, detail=f"非法沙盒 ID: {sandbox_id!r}")
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


class EvaluateRequest(BaseModel):
    """GE-IF-001 实时回调请求（正和完整求解；objective_functions 为可序列化公式描述）。"""

    participants: List[Dict[str, Any]] = Field(min_length=1, description="参与者列表（agent_id/capability）")
    # T1 修复：REST/JSON 无法承载 callable——objective_functions 改为公式描述
    # （[{"type": "linear", "factor": 1.2}]），适配层解析为 callable
    objective_functions: List[Dict[str, Any]] = Field(
        min_length=1, description="目标函数公式描述列表（长度=参与者数，如 [{'type':'linear','factor':1.2}]）")
    reservation_utilities: List[float] = Field(min_length=1, description="保留效用列表（长度=参与者数）")
    nsfl_boundaries: List[str] = Field(default_factory=list, description="负空间边界（可空）")
    time_budget: float = Field(default=5.0, gt=0, le=30.0, description="求解时间预算（秒）")


class CheckRequest(BaseModel):
    """GE-IF-001b 快路径校验请求。"""

    coalition_utility: float = Field(gt=0, allow_inf_nan=False, description="协作总效用（有限正数）")
    independent_utilities: List[float] = Field(min_length=1)


@router.post("/{sandbox_id}/evaluate", summary="GE-IF-001 正和评估实时回调")
def genie_evaluate(sandbox_id: str, req: EvaluateRequest) -> Dict[str, Any]:
    """沙盒实验迭代实时正和评估（效用精灵 solve_positive_sum，任务书 §6.3）。

    六要素声明:
    目标函数: GE-IF-001 实时回调端点（效用精灵深度对接）
    约束矩阵: 输入——participants/objective_functions/reservation_utilities；输出——评估结果；
              禁止——正和判定 mock、非正和判通过（→ FUSE）
    先验分布: TDCAUtilityGenie.solve_positive_sum（ID84）
    配置权边界: L2；效用精灵只读
    预期分配: 200 + 评估结果；失败=404（沙盒不存在）/422（参数非法）/503（效用精灵不可用）
    审计轨迹: GENIE_EVALUATE NCA（fuse 时 negative_space_check=FUSE）
    """
    sb = _require_sandbox(sandbox_id)
    try:
        r = genie_callback.ADAPTER.evaluate(
            sandbox_id, req.participants, req.objective_functions,
            req.reservation_utilities, req.nsfl_boundaries, req.time_budget)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    # #3（compliance-auditor P0）: 评估结果回写沙盒 positive_sum_logs（实时记录契约核心）
    try:
        from .. import store as _st
        logs = list(getattr(sb, "positive_sum_logs", []) or [])
        logs.append({"operation": "GENIE_EVALUATE", "contract": "GE-IF-001",
                     "is_positive_sum": r["is_positive_sum"], "delta": r["delta"],
                     "total_utility": r["total_utility"], "touched_nsfl": r["touched_nsfl"],
                     "fuse": r["fuse"]})
        sb.positive_sum_logs = logs
        _st.save_sandbox(sb)
    except Exception:  # noqa: BLE001 - 回写失败不阻断（NCA 已存证，可观测优先）
        pass
    return r


@router.post("/{sandbox_id}/check", summary="GE-IF-001b 正和快路径校验")
def genie_check(sandbox_id: str, req: CheckRequest) -> Dict[str, Any]:
    """实时迭代轻量正和校验（S_synergy > 0 公式快路径，GE-IF-001b）。

    六要素声明:
    目标函数: GE-IF-001b 快路径校验端点（实时迭代轻量评估）
    约束矩阵: 输入——coalition_utility/independent_utilities；输出——判定；
              禁止——非正和判通过（→ FUSE）、inf/NaN 伪造（P1）
    先验分布: KB-ECON-001 §3（S_synergy > 0）
    配置权边界: L2；纯计算快路径
    预期分配: 200 + 判定（结果回写沙盒 positive_sum_logs，SV-3/SV-7 审计链闭合）；
              失败=404（沙盒不存在）/422（参数非法）
    审计轨迹: GENIE_CHECK NCA + 回写沙盒（fuse 时 negative_space_check=FUSE）
    """
    sb = _require_sandbox(sandbox_id)
    try:
        r = genie_callback.ADAPTER.check(sandbox_id, req.coalition_utility,
                                         req.independent_utilities)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    # P3: 结果回写沙盒 positive_sum_logs（SV-3 熔断标记 / SV-7 审计链闭合）
    try:
        from .. import store as _st
        logs = list(getattr(sb, "positive_sum_logs", []) or [])
        logs.append({"operation": "GENIE_CHECK", "contract": "GE-IF-001b",
                     "is_positive_sum": r["is_positive_sum"], "delta": r["delta"],
                     "positive_sum_index": r["positive_sum_index"], "fuse": r["fuse"]})
        sb.positive_sum_logs = logs
        _st.save_sandbox(sb)
    except Exception:  # noqa: BLE001 - 回写失败不阻断（NCA 已存证，可观测优先）
        pass
    return r
