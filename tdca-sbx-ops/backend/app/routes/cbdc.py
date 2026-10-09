# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，CB-IF 功能组）
# 目标函数:     M3-5 数字人民币 MOU 锚定 API——CB-IF-001/001b 端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0（ID82）+ tdca-fos 只读
# 先验分布:     cbdc_anchor.py（CB-IF 契约）+ tdca_adapters（mou_pipeline/dcep_adapter）
# 配置权边界:   L2 层；tdca-fos 只读对接；模拟过渡（真实锚定永不）
# 预期分配:     REST 端点；失败=404/409/422/503
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-5 数字人民币 MOU 锚定 API（CB-IF-001/001b）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.1 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import cbdc_anchor, store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/cbdc", tags=["数字人民币 MOU 锚定（M3-5/CB-IF）"])

_core = SandboxCore()


def _require_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒存在性 + ID 合法性校验（404/422 语义统一）。"""
    if not store.is_valid_sandbox_id(sandbox_id):
        raise HTTPException(status_code=422, detail=f"非法沙盒 ID: {sandbox_id!r}")
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


class AnchorRequest(BaseModel):
    """CB-IF-001 MOU 锚定请求（模拟过渡，税收数据非负）。"""

    tax_in: int = Field(ge=0, description="进项税收（≥0）")
    tax_out: int = Field(ge=0, description="出项税收（≥0）")
    transaction_id: str = Field(default="", description="交易 ID（可空，自动生成）")


@router.post("/{sandbox_id}/anchor", summary="CB-IF-001 MOU 税收锚定（模拟过渡）")
def cbdc_anchor_mou(sandbox_id: str, req: AnchorRequest) -> Dict[str, Any]:
    """沙盒出盒 MOU 税收锚定（MOUPipeline 模拟过渡，SIMULATED-TAX-AUTHORITY 显式标记）。

    六要素声明:
    目标函数: CB-IF-001 MOU 锚定端点（任务书 §6.1，模拟过渡）
    约束矩阵: 输入——tax_in/tax_out（≥0）；输出——锚定结果；禁止——负税收、无数据伪造 MOU
    先验分布: MOUPipeline.run（SimulatedTaxAuthority + DCEPAdapter）
    配置权边界: L2；tdca-fos 只读；真实锚定永不（ID92）
    预期分配: 200 + 锚定结果（simulated 显式标记）；失败=404/422/503
    审计轨迹: CBDC_ANCHOR NCA + 回写沙盒 mou_logs（SV-10）
    """
    sb = _require_sandbox(sandbox_id)
    # #10 修复：MOU 锚定限评估期（任务书 §6.1 出盒评估语义，对齐 M2 delivery_confirm P1 约束）
    if sb.phase.value != "P1":
        raise HTTPException(status_code=409,
                            detail=f"MOU 锚定须在评估期（P1），当前沙盒 phase={sb.phase.value}")
    try:
        r = cbdc_anchor.ADAPTER.anchor(sandbox_id, req.tax_in, req.tax_out, req.transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    # 回写沙盒 mou_logs（CB-IF-001b 查询数据源，SV-7 审计链闭合）
    # V3 修复：回写失败显式记录（NCA 已存证但状态查询可能不可达——可观测优先）
    try:
        from .. import store as _st
        logs = list(getattr(sb, "mou_logs", []) or [])
        logs.append({"transaction_id": r["transaction_id"], "mou": r["mou"],
                     "contract_tx": r["contract_tx"], "verified": r["verified"],
                     "simulated": r["simulated"], "source": r["source"]})
        sb.mou_logs = logs
        _st.save_sandbox(sb)
    except Exception as e:  # noqa: BLE001
        try:
            from .. import nca_logger as _nl
            nca = _nl.build_nca(
                operation="CBDC_MOU_LOG_WRITEBACK_FAILED", operator="system",
                pre_state="ANCHORED", post_state="WRITEBACK_FAILED",
                audit_trail=f"CB-IF-001 回写失败: {type(e).__name__}: {e}",
            )
            _nl.save_nca(nca)
        except Exception:  # noqa: BLE001
            pass
    return r


@router.get("/{sandbox_id}/mou", summary="CB-IF-001b MOU 锚定状态查询")
def cbdc_mou_status(sandbox_id: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
    """沙盒 MOU 锚定状态查询（CB-IF-001b，出盒评估辅助）。

    六要素声明:
    目标函数: CB-IF-001b MOU 状态查询端点
    约束矩阵: 输入——sandbox_id/transaction_id（可空）；输出——锚定状态；禁止——无
    先验分布: 沙盒 mou_logs
    配置权边界: L2；只读
    预期分配: 200 + 状态；失败=404（沙盒不存在）
    审计轨迹: 只读，不生成 NCA
    """
    _require_sandbox(sandbox_id)
    return cbdc_anchor.ADAPTER.mou_status(sandbox_id, transaction_id or "")
