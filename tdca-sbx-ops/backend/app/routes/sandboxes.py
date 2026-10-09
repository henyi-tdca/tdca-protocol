# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     沙盒生命周期 CRUD API（F1）——创建/查询/配置/运行/出盒/关闭
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 接口熵=0（ID82）
# 先验分布:     任务书 §二 F1 + NS-OPS routes 模式
# 配置权边界:    L2 层
# 预期分配:     REST 端点；失败=400/404 语义化
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""沙盒生命周期 API（F1）。

制度锚定: FC-SBX-OPS-001 F1 / SV-1~7 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from .. import store
from ..models import Sandbox
from ..sandbox_core import SandboxCore

router = APIRouter(prefix="/api/v1/sandboxes", tags=["沙盒生命周期（F1）"])

_core = SandboxCore()


# ------------------------------------------------------------------ 请求模型


class SandboxCreate(BaseModel):
    """沙盒创建请求（六要素声明强制）。"""

    name: str
    initiator_did: str
    initiator_role: str
    six_elements: Dict[str, str]


class ConfigureRequest(BaseModel):
    """沙盒配置请求（PUCR 预售/质押 + S-Right）。"""

    pucr: Optional[Dict[str, Any]] = None
    s_rights: Optional[List[Dict[str, Any]]] = None


class RunRequest(BaseModel):
    """实验迭代请求。"""

    iteration: Dict[str, Any]


class ExitRequest(BaseModel):
    """出盒请求（异构三角签名 + 人类签批）。"""

    signatures: List[Dict[str, str]]
    human_signatory: str = Field(min_length=1, description="人类最终签批（任务书 §七，不可为空）")


class CloseRequest(BaseModel):
    """关闭请求（三方终止触发 + 人类裁决）。"""

    trigger_role: str
    reason: str
    human_signatory: str


# ------------------------------------------------------------------ 端点


@router.post("", response_model=Sandbox, status_code=201)
def create_sandbox(req: SandboxCreate) -> Sandbox:
    """创建沙盒（F1-C，六要素声明，多签门控前置）。

    六要素声明:
    目标函数: 沙盒创建入口（F1-C）
    约束矩阵: 输入——六要素完整；输出——Sandbox；禁止——缺要素
    预期分配: 201 + 沙盒；失败=422
    审计轨迹: SBX_CREATE NCA 存证
    """
    try:
        return _core.create(req.name, req.initiator_did, req.initiator_role, req.six_elements)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=List[Sandbox])
def list_sandboxes() -> List[Sandbox]:
    """沙盒列表（F1-R）。

    六要素声明:
    目标函数: 沙盒列表入口（F1-R）
    约束矩阵: 输入——无；输出——Sandbox[]；禁止——无
    预期分配: 200 + 列表；失败=无
    审计轨迹: 只读
    """
    return store.list_sandboxes()


@router.get("/{sandbox_id}", response_model=Sandbox)
def get_sandbox(sandbox_id: str) -> Sandbox:
    """沙盒详情（F1-R，含激活系数历史/NCA 链/ENG-003 日志）。

    六要素声明:
    目标函数: 沙盒详情读取入口（F1-R）
    约束矩阵: 输入——sandbox_id；输出——Sandbox；禁止——不存在放行
    预期分配: 200 + 沙盒；失败=404（不存在）/422（数据损坏）
    审计轨迹: 只读，不生成 NCA
    """
    try:
        return _core.get(sandbox_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, json.JSONDecodeError, ValidationError) as e:  # 非法 ID/数据损坏 → 422
        raise HTTPException(status_code=422, detail=f"沙盒数据损坏或 ID 非法: {e}")


@router.post("/{sandbox_id}/configure", response_model=Sandbox)
def configure_sandbox(sandbox_id: str, req: ConfigureRequest) -> Sandbox:
    """沙盒配置（F1-配置：PUCR 预售 SV-2 + S-Right 场景配置权）。

    六要素声明:
    目标函数: 沙盒配置入口（F1-配置，SV-2）
    约束矩阵: 输入——pucr/s_rights；输出——Sandbox；禁止——amount≤0
    预期分配: 200 + 沙盒；失败=404/422
    审计轨迹: SBX_CONFIGURE NCA 存证
    """
    try:
        return _core.configure(sandbox_id, pucr=req.pucr, s_rights=req.s_rights)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/start", response_model=Sandbox)
def start_sandbox(sandbox_id: str) -> Sandbox:
    """准入完成进入实验（Phase0→P0）。

    六要素声明:
    目标函数: 开始实验入口（Phase0→P0）
    约束矩阵: 输入——sandbox_id；输出——Sandbox；禁止——非准入期
    预期分配: 200 + P0 沙盒；失败=404/422
    审计轨迹: SBX_START NCA 存证
    """
    try:
        return _core.start_experiment(sandbox_id, operator_did="system")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/run", response_model=Sandbox)
def run_sandbox(sandbox_id: str, req: RunRequest) -> Sandbox:
    """实验迭代（F1-运行：数据收集 + ENG-003 检查日志）。

    六要素声明:
    目标函数: 实验迭代入口（F1-运行 + ENG-003 预埋）
    约束矩阵: 输入——iteration；输出——Sandbox；禁止——空迭代
    预期分配: 200 + 沙盒；失败=404/422
    审计轨迹: SBX_RUN_ITERATION NCA 存证
    """
    try:
        return _core.run_iteration(sandbox_id, req.iteration)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/exit", response_model=Sandbox)
def exit_sandbox(sandbox_id: str, req: ExitRequest) -> Sandbox:
    """沙盒出盒（F1-出盒：SV-1 α>1.2 + SV-6 三方签名 + 人类签批）。

    六要素声明:
    目标函数: 沙盒出盒入口（SV-1/SV-6 门）
    约束矩阵: 输入——signatures/human_signatory；禁止——α≤1.2、签名不足、签批为空
    预期分配: 200 + Exit 沙盒；失败=404/422
    审计轨迹: SBX_EXIT NCA 存证（Human-Signature 字段）
    """
    try:
        return _core.exit(sandbox_id, req.signatures, req.human_signatory)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{sandbox_id}/close", response_model=Sandbox)
def close_sandbox(sandbox_id: str, req: CloseRequest) -> Sandbox:
    """沙盒关闭（F1-关闭：负空间熔断 SV-3 / 三方终止 SV-4，人类裁决）。

    六要素声明:
    目标函数: 沙盒关闭入口（SV-3/SV-4）
    约束矩阵: 输入——trigger_role/reason/human_signatory；禁止——非三方角色、终态再关闭
    预期分配: 200 + Closed 沙盒；失败=404/422
    审计轨迹: SBX_CLOSE NCA 存证（negative_space_check 字段）
    """
    try:
        return _core.close(sandbox_id, req.trigger_role, req.reason, req.human_signatory)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
