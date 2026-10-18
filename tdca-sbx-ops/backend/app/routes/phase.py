# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，PM-IF 功能组）
# 目标函数:     M3-3 沙盒-阶段机联动 API——PM-IF-001 端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0（ID82）+ PhaseMachine 只读
# 先验分布:     phase_adapter.py（PM-IF 契约）+ tdca-flow-orchestrator phase_machine.py
# 配置权边界:   L2 层；PhaseMachine 只读对接
# 预期分配:     REST 端点；失败=404/409/422/503
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-3 沙盒-阶段机联动 API（PM-IF-001）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import phase_adapter, store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/phase", tags=["阶段机联动（M3-3/PM-IF）"])

_core = SandboxCore()

_SANDBOX_ID_RE = store._SANDBOX_ID_RE  # type: ignore[attr-defined]

# PhaseMachine 状态白名单（9 Phase + FUSE + COMPLETED/TERMINATED）
_VALID_PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
                 "FUSE", "COMPLETED", "TERMINATED")
# 推进起点白名单（T5 修复：仅 P0~P8，终态/FUSE 起点拒绝）
_VALID_START_PHASES = phase_adapter.VALID_START_PHASES


def _require_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒存在性 + ID 合法性校验（404/422 语义统一）。"""
    if not _SANDBOX_ID_RE.match(sandbox_id or ""):
        raise HTTPException(status_code=422, detail=f"非法沙盒 ID: {sandbox_id!r}")
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


class AdvanceRequest(BaseModel):
    """PM-IF-001 阶段推进信号请求（sandbox_id 取路径参数；α/评估记录由服务端消费）。"""

    current_phase: str = Field(default="P0", description="当前 FlowEngine Phase（P0~P8）")


@router.post("/{sandbox_id}/advance", summary="PM-IF-001 激活系数达标阶段推进信号")
def phase_advance(sandbox_id: str, req: AdvanceRequest) -> Dict[str, Any]:
    """激活系数达标（α>1.2，SV-1 必要非充分）→ PhaseMachine 阶段推进信号（PM-IF-001）。

    六要素声明:
    目标函数: PM-IF-001 阶段推进端点（任务书 §6.2 事件触发）
    约束矩阵: 输入——sandbox_id/current_phase；输出——推进结果；
              禁止——α≤1.2 发信号（SV-1）、客户端自报 α/delta（服务端消费真实记录）
    先验分布: PhaseMachine.transition（P3->P4 sandbox_pass + positive_sum）
    配置权边界: L2；PhaseMachine 只读
    预期分配: 200 + 推进结果；失败=404（沙盒不存在）/422（α≤1.2 或正和未过）/409（phase 非法）
    审计轨迹: PHASE_ADVANCE NCA（SV-7）
    """
    sb = _require_sandbox(sandbox_id)
    if req.current_phase not in _VALID_START_PHASES:  # T5: 仅 P0~P8 起点
        raise HTTPException(status_code=409,
                            detail=f"current_phase 非法起点: {req.current_phase}（仅 P0~P8）")
    try:
        # T2/C03: 服务端核对沙盒真实 FlowEngine phase（若已挂接 M3-2 flow_adapter）
        from .. import flow_adapter as _fa
        real_phase = ""
        try:
            st = _fa.ADAPTER.status(sandbox_id)
            real_phase = st.get("phase", "")
        except KeyError:
            pass  # 未挂接 FlowEngine → 不核对（PM-IF-001 为出盒评估原子信号）
        return phase_adapter.ADAPTER.advance_signal(
            sandbox_id, sb, req.current_phase, real_phase=real_phase)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/conditions", summary="PM-IF-001b 穿越条件查询")
def get_conditions(from_phase: str, to_phase: str) -> Dict[str, Any]:
    """PhaseMachine 穿越条件查询（PM-IF-001b，前端/审计参考）。

    六要素声明:
    目标函数: PM-IF-001b 穿越条件查询端点
    约束矩阵: 输入——from_phase/to_phase；输出——条件名列表；禁止——非法 phase
    先验分布: PhaseMachine.get_conditions
    配置权边界: L2；只读
    预期分配: 200 + conditions；失败=409（phase 非法）
    审计轨迹: 只读
    """
    if from_phase not in _VALID_PHASES or to_phase not in _VALID_PHASES:
        raise HTTPException(status_code=409, detail="phase 非法（P0~P8/FUSE/COMPLETED/TERMINATED）")
    return phase_adapter.ADAPTER.conditions(from_phase, to_phase)


@router.get("/states", summary="PM-IF-001 状态集合查询")
def get_states() -> Dict[str, Any]:
    """PhaseMachine 状态全集查询（审计/前端参考）。

    六要素声明:
    目标函数: PhaseMachine 状态集合查询端点
    约束矩阵: 输入——无；输出——状态列表；禁止——无
    先验分布: models.ALL_STATES
    配置权边界: L2；只读
    预期分配: 200 + states；失败=无
    审计轨迹: 只读
    """
    return {"contract": phase_adapter.PM_IF_001C, "operation": "states",
            "states": phase_adapter.ADAPTER.state_table()}
