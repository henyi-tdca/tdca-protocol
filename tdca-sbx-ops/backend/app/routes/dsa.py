# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，DSA 扩展组）
# 目标函数:     M3-6 DSA 状态机扩展 API——SBX-SUSPENDED/BANNED 扩展字段端点
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-9 + 接口熵=0（ID82）+ DSA-001 只读参考
# 先验分布:     dsa_extension.py（DSA 扩展契约）+ TDCA-PRINCIPLE-DSA-001
# 配置权边界:   L2 层；DSA-001 只读（待 DCD）
# 预期分配:     REST 端点；失败=404/409/422/503
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-6 DSA 状态机扩展 API（SBX-SUSPENDED/BANNED 扩展字段先行）。

制度锚定: FC-SBX-OPS-001 / SV-9 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import dsa_extension, store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/dsa", tags=["DSA 状态机扩展（M3-6）"])

_core = SandboxCore()

_VALID_LEVELS = (dsa_extension.BREAK_LEVEL_MINOR, dsa_extension.BREAK_LEVEL_MODERATE,
                 dsa_extension.BREAK_LEVEL_SEVERE)


def _require_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒存在性 + ID 合法性校验（404/422 语义统一）。"""
    if not store.is_valid_sandbox_id(sandbox_id):
        raise HTTPException(status_code=422, detail=f"非法沙盒 ID: {sandbox_id!r}")
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


class SuspendRequest(BaseModel):
    """DSA 熔断落地请求（SV-9）。"""

    reason: str = Field(min_length=2, max_length=256, description="熔断触发原因")
    break_level: str = Field(default=dsa_extension.BREAK_LEVEL_MINOR,
                             description="回退档位 MINOR/MODERATE（SEVERE 走 ban 端点）")


class BanRequest(BaseModel):
    """DSA 永久休眠请求（I-5：L0 法律负空间最重裁决，须人类签批）。"""

    reason: str = Field(min_length=2, max_length=256, description="法律负空间触发原因")
    human_signatory: str = Field(min_length=3, description="人类裁决签名（L0 永久休眠必填）")


class ResumeRequest(BaseModel):
    """DSA 恢复请求（轻微越界限期重整；中度需人类裁决）。"""

    human_approval: str = Field(default="", description="人类裁决签名（中度越界必填）")


@router.post("/{sandbox_id}/suspend", summary="DSA 熔断落地 → SBX-SUSPENDED（SV-9）")
def dsa_suspend(sandbox_id: str, req: SuspendRequest) -> Dict[str, Any]:
    """熔断触发后沙盒 100ms 内进入 SUSPENDED（SV-9 扩展字段先行）。

    六要素声明:
    目标函数: DSA 熔断落地端点（SV-9，100ms 实时性）
    约束矩阵: 输入——reason/break_level；输出——dsa_status；禁止——终态迁移/非法档位
    先验分布: DSA-001 §3.4（回退三档）
    配置权边界: L2；DSA-001 只读
    预期分配: 200 + dsa_status；失败=404/409（终态/非法档位）/422
    审计轨迹: DSA_SUSPEND NCA（SV-7）+ 回写扩展字段
    """
    _require_sandbox(sandbox_id)
    if req.break_level not in _VALID_LEVELS:
        raise HTTPException(status_code=409, detail=f"break_level 非法: {req.break_level}")
    try:
        return dsa_extension.ADAPTER.suspend(sandbox_id, req.reason, req.break_level)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{sandbox_id}/ban", summary="DSA 永久休眠 → SBX-BANNED（法律负空间）")
def dsa_ban(sandbox_id: str, req: BanRequest) -> Dict[str, Any]:
    """严重越界（法律负空间，ID86）→ SBX-BANNED 永久休眠（不可逆，I-5 须人类签批）。

    六要素声明:
    目标函数: DSA 永久休眠端点（DSA-001 §3.4 严重档）
    约束矩阵: 输入——reason/human_signatory（L0 必填）；输出——dsa_status=BANNED；
              禁止——BANNED 恢复（不可逆）、无人类签批执行（I-5）
    先验分布: DSA-001 §3.4 + ID86
    配置权边界: L2；DSA-001 只读
    预期分配: 200 + dsa_status；失败=404/409（终态/已 BANNED）/422（无签批）
    审计轨迹: DSA_BAN NCA（含 human_signature，SV-7）
    """
    _require_sandbox(sandbox_id)
    try:
        return dsa_extension.ADAPTER.ban(sandbox_id, req.reason, req.human_signatory)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{sandbox_id}/resume", summary="DSA 恢复 → SBX-ACTIVE（轻微重整后）")
def dsa_resume(sandbox_id: str, req: ResumeRequest) -> Dict[str, Any]:
    """轻微越界限期重整后恢复（中度需人类裁决，DSA-001 §3.4）。

    六要素声明:
    目标函数: DSA 恢复端点（DSA-001 §3.4）
    约束矩阵: 输入——human_approval；输出——dsa_status=ACTIVE；
              禁止——BANNED 恢复（不可逆）、中度越界无人类裁决
    先验分布: DSA-001 §3.4
    配置权边界: L2；DSA-001 只读
    预期分配: 200 + dsa_status；失败=404/409（BANNED/中度无裁决）
    审计轨迹: DSA_RESUME NCA（SV-7）
    """
    _require_sandbox(sandbox_id)
    try:
        return dsa_extension.ADAPTER.resume(sandbox_id, req.human_approval)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{sandbox_id}/status", summary="DSA 状态查询")
def dsa_status(sandbox_id: str) -> Dict[str, Any]:
    """DSA 状态扩展查询（dsa_status 扩展字段）。

    六要素声明:
    目标函数: DSA 状态查询端点
    约束矩阵: 输入——sandbox_id；输出——dsa_status/break_level/phase；禁止——无
    先验分布: 沙盒扩展字段
    配置权边界: L2；只读
    预期分配: 200 + 状态；失败=404
    审计轨迹: 只读，不生成 NCA
    """
    _require_sandbox(sandbox_id)
    try:
        return dsa_extension.ADAPTER.status(sandbox_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
