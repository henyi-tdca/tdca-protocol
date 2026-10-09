# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，FE-IF 功能组）
# 目标函数:     M3-2 沙盒-全周期生命周期挂接 API——FE-IF-001/002 端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0（ID82）+ FlowEngine 只读
# 先验分布:     flow_adapter.py（FE-IF 契约）+ tdca-flow-orchestrator api.py（8001）
# 配置权边界:   L2 层；FlowEngine 只读对接
# 预期分配:     REST 端点；失败=404/409/422/503（FlowEngine 不可达）
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-2 沙盒-全周期生命周期挂接 API（FE-IF-001/002）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.2 | SPDX-License-Identifier: TDCA-Internal

服务边界声明（ID82）: 本服务 /api/v1/flow/* 为 SBX-OPS 对外沙盒契约（sandbox_id 路径参数）；
FlowEngine 8001 /api/v1/flow/* 为内部流程服务（flow_id body/query）——两套端点独立进程部署，
外部调用者禁止直连 8001，须经 SBX-OPS 适配层（flow_adapter）转发。
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import flow_adapter, store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/flow", tags=["全周期生命周期挂接（M3-2/FE-IF）"])

_core = SandboxCore()

# 沙盒 ID 白名单（T-3 修复：复用 store 路径穿越防护正则，非法格式 422）
_SANDBOX_ID_RE = store._SANDBOX_ID_RE  # type: ignore[attr-defined]


def _require_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒存在性 + ID 合法性校验（404/422 语义统一）。"""
    if not _SANDBOX_ID_RE.match(sandbox_id or ""):
        raise HTTPException(status_code=422, detail=f"非法沙盒 ID（格式 did:tdca:sandbox:{32-hex}）: {sandbox_id!r}")
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


class HookRequest(BaseModel):
    """FE-IF-001 挂接请求（沙盒 → FlowEngine Phase 0）。"""

    sandbox_id: str = Field(min_length=10, description="沙盒 ID（did:tdca:sandbox:{32-hex}）")


class SyncRequest(BaseModel):
    """FE-IF-001 阶段同步请求（沙盒真实 Phase → FlowEngine 对应 Phase；sandbox_id 取路径参数）。"""

    sbx_phase: str = Field(description="沙盒真实 Phase（Phase0/P0/P1/Exit）")


class AdvanceRequest(BaseModel):
    """FE-IF-002 阶段推进信号请求（sandbox_id 取路径参数；α/评估记录由服务端消费）。"""
    pass


@router.post("/hook", summary="FE-IF-001 沙盒挂接 FlowEngine 生命周期")
def hook_sandbox(req: HookRequest) -> Dict[str, Any]:
    """沙盒挂接 FlowEngine 生命周期（Phase 0 启动，任务书 §6.2）。

    六要素声明:
    目标函数: FE-IF-001 挂接端点（沙盒-全周期生命周期挂接）
    约束矩阵: 输入——sandbox_id；输出——flow_id + phase；禁止——重复挂接/非法 ID
    先验分布: FlowEngine.start（P0 意图孕育）+ 任务书 §6.2
    配置权边界: L2；FlowEngine 只读
    预期分配: 200 + flow_id；失败=404（沙盒不存在）/409（重复挂接）/422（非法 ID）/503（FlowEngine 不可达）
    审计轨迹: FLOW_PHASE_P0 NCA（SV-7）
    """
    _require_sandbox(req.sandbox_id)
    intent = {"type": "sbx_lifecycle", "sandbox_id": req.sandbox_id,
              "source": "SBX-OPS-M3-2"}
    try:
        return flow_adapter.ADAPTER.hook_sandbox(req.sandbox_id, intent)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{sandbox_id}/status", summary="FE-IF-001 沙盒关联 FlowEngine 状态")
def flow_status(sandbox_id: str) -> Dict[str, Any]:
    """查询沙盒关联 FlowEngine 生命周期状态（FE-IF-001 状态同步）。

    六要素声明:
    目标函数: FE-IF-001 状态查询端点（全周期生命周期）
    约束矩阵: 输入——sandbox_id；输出——phase/phase_seq/fuse_history；
              禁止——未挂接沙盒查询放行
    先验分布: FlowEngine.status
    配置权边界: L2；只读
    预期分配: 200 + 状态；失败=404（未挂接）
    审计轨迹: 只读，不生成 NCA
    """
    _require_sandbox(sandbox_id)
    try:
        return flow_adapter.ADAPTER.status(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{sandbox_id}/sync", summary="FE-IF-001 沙盒阶段同步至 FlowEngine")
def sync_phase(sandbox_id: str, req: SyncRequest) -> Dict[str, Any]:
    """沙盒真实 Phase 同步至 FlowEngine（FE-IF-001 状态同步，服务端构造穿越 context）。

    六要素声明:
    目标函数: FE-IF-001 阶段同步端点（全周期生命周期）
    约束矩阵: 输入——sandbox_id/sbx_phase（沙盒真实 Phase）；输出——新 phase；
              禁止——客户端自报穿越字段、客户端声明与沙盒真实 phase 不一致（C03 自证）
    先验分布: flow_adapter.SBX_TO_FLOW_PHASE 映射 + FlowEngine.advance
    配置权边界: L2；FlowEngine 只读
    预期分配: 200 + phase；失败=404（未挂接/沙盒不存在）/409（phase 不一致）/422（非法 ID）/503
    审计轨迹: FLOW_PHASE_* NCA（SV-7）
    """
    sb = _require_sandbox(sandbox_id)
    try:
        # V3 修复：服务端读取沙盒真实 phase 并与客户端声明核对（C03 自证）
        return flow_adapter.ADAPTER.sync_phase(sandbox_id, req.sbx_phase,
                                               real_phase=sb.phase.value)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{sandbox_id}/advance", summary="FE-IF-002 激活系数达标阶段推进信号")
def activation_advance(sandbox_id: str, req: AdvanceRequest) -> Dict[str, Any]:
    """激活系数达标（α>1.2，SV-1 必要非充分）→ FlowEngine 阶段推进信号（FE-IF-002）。

    六要素声明:
    目标函数: FE-IF-002 阶段推进信号端点（任务书 §6.2 事件触发）
    约束矩阵: 输入——sandbox_id；输出——推进结果；禁止——α≤1.2 发信号（SV-1）、
              客户端自报 α/delta（服务端消费沙盒真实评估记录）
    先验分布: PhaseMachine P3->P4（sandbox_pass + positive_sum）+ activation_logs/positive_sum_logs
    配置权边界: L2；FlowEngine 只读
    预期分配: 200 + phase；失败=404（未挂接/沙盒不存在）/422（α≤1.2 或正和未过）/503
    审计轨迹: FLOW_PHASE_* NCA（SV-7）
    """
    sb = _require_sandbox(sandbox_id)
    try:
        return flow_adapter.ADAPTER.activation_signal(sandbox_id, sb)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/hooks", summary="FE-IF-001 已挂接沙盒台账")
def list_hooks() -> Dict[str, Any]:
    """已挂接沙盒生命周期台账（FE-IF-001）。

    六要素声明:
    目标函数: 挂接台账查询端点（FE-IF-001）
    约束矩阵: 输入——无；输出——hooks 列表；禁止——无
    先验分布: flow_adapter.ADAPTER.list_hooks（内存台账）
    配置权边界: L2；只读
    预期分配: 200 + hooks；失败=无
    审计轨迹: 只读
    """
    return {"contract": flow_adapter.FE_IF_001, "operation": "hooks", "hooks": flow_adapter.ADAPTER.list_hooks()}
