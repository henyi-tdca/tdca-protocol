# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     NCA 存证查询 API（F8）——列表/详情/链式校验
# 约束矩阵:     FC-SBX-OPS-001 SV-7（存证不可篡改）+ 接口熵=0
# 先验分布:     任务书 §二 F8 + nca_logger
# 配置权边界:    L2 层；只读查询
# 预期分配:     GET 端点；失败=404
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NCA 存证查询 API（F8）。

制度锚定: FC-SBX-OPS-001 F8 / SV-7 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from .. import nca_logger

router = APIRouter(prefix="/api/v1/nca", tags=["NCA 存证（F8）"])


@router.get("")
def list_nca() -> List[Dict[str, Any]]:
    """NCA 存证列表（F8 审计查询）。

    六要素声明:
    目标函数: NCA 列表查询（F8）
    约束矩阵: 输入——无；输出——存证列表；禁止——无
    预期分配: 200 + 列表；失败=无
    审计轨迹: 只读
    """
    return nca_logger.list_nca()


@router.get("/verify")
def verify_nca_chain() -> Dict[str, Any]:
    """NCA 链式完整性校验（SV-7 不可篡改审计）。

    六要素声明:
    目标函数: NCA 链完整性校验（SV-7）
    约束矩阵: 输入——无；输出——{valid,checked,...}；禁止——篡改判有效
    预期分配: 200 + 校验结果；失败=无
    审计轨迹: 校验动作由调用方存证
    """
    return nca_logger.verify_chain()


@router.get("/{nca_id}")
def get_nca(nca_id: str) -> Dict[str, Any]:
    """NCA 存证详情（按 id）。

    六要素声明:
    目标函数: NCA 详情查询（F8）
    约束矩阵: 输入——nca_id；输出——存证 dict；禁止——不存在放行
    预期分配: 200 + 存证；失败=404
    审计轨迹: 只读
    """
    nca = nca_logger.load_nca(nca_id)
    if nca is None:
        raise HTTPException(status_code=404, detail=f"NCA 不存在: {nca_id}")
    return nca
