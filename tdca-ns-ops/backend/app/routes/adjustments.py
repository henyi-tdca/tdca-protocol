# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——调整权操作路由（F2）
# 约束矩阵:     FC-NS-OPS-001 F2 + BV-3/BV-4/BV-5/BV-6（快慢分离）+ NS-011 状态机
# 先验分布:     NSAR-Registry（NS-011 §4.2）+ AdjustmentFlowEngine
# 配置权边界:    L2 层；发起/推进均须人类签名
# 预期分配:     REST 流程接口；失败=非法迁移/沙盒未过/签名缺失
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F2 调整权操作路由（NS-011 状态机暴露）。

制度锚定: FC-NS-OPS-001 F2 | NS-011 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..adjustment_flow import FLOW
from ..human_gate import GATE
from ..models import (
    Adjustment,
    AdjustmentStartRequest,
    AdjustmentStatus,
    ConstraintLayer,
    DeliberationRecord,
)
from ..store import generate_nca, get_item, hash_text, load_collection, save_collection, upsert_item

router = APIRouter(prefix="/api/v1/adjustments", tags=["调整权操作 F2"])


def _to_adjustment(raw: dict) -> Adjustment:
    return Adjustment.model_validate(raw)


def _save(adj: Adjustment) -> None:
    upsert_item("adjustments", adj.model_dump(), key="adjustment_id")


@router.get("", summary="调整记录列表（NSAR-Registry 台账）")
def list_adjustments(status: AdjustmentStatus | None = None) -> list[dict]:
    """调整台账（读操作）。"""
    items = load_collection("adjustments")
    out = []
    for raw in items:
        a = _to_adjustment(raw)
        if status is not None and a.status != status:
            continue
        out.append(a.model_dump())
    return out


@router.get("/{adjustment_id}", summary="调整详情")
def get_adjustment(adjustment_id: str) -> dict:
    """调整详情。"""
    raw = get_item("adjustments", "adjustment_id", adjustment_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="调整记录不存在")
    return raw


@router.post("", summary="发起调整（BV-3 人类发起，进入审议态）", status_code=201)
def start_adjustment(payload: AdjustmentStartRequest) -> dict:
    """发起一次负空间调整（慢系统入口，人类专属，BV-3）。

    E1 修复：制度层（institutional）约束禁止走调整流程（L0 法律底线无变通，
    仅 OTA/宪法流程可改——红队 F-1 / NS-011 §1.3 / M7）。
    """
    # M5 修复：initiator 必须等于签名者（防伪造发起人字段）
    if payload.initiator != payload.human_signature:
        raise HTTPException(
            status_code=422,
            detail="[BV-3] initiator 必须等于 human_signature（发起人=签名人，防伪造）",
        )
    gate = GATE.check(payload.human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)

    target = get_item("constraints", "id", payload.target_constraint_id)
    if target is None:
        raise HTTPException(status_code=404, detail="目标约束不存在")

    # E1 修复：制度层约束不可经调整流程改写（防 L2 层级绕过 L0 底线）
    if target.get("layer") == ConstraintLayer.INSTITUTIONAL.value:
        raise HTTPException(
            status_code=403,
            detail="[NSFL] 制度负空间约束禁止走调整流程（L0 法律底线无变通，仅 OTA/宪法流程可改）",
        )

    adj = Adjustment(
        initiator=payload.initiator,
        target_constraint_id=payload.target_constraint_id,
        status=AdjustmentStatus.DELIBERATION,
        deliberation=DeliberationRecord(
            trigger=payload.trigger,
            proposal=payload.proposal,
            participants=[payload.initiator],
        ),
    )
    # B3 修复：发起调整即生成 NCA（BV-5 全操作存证）
    nca = generate_nca(
        "TDCA-FC-NS-OPS-001", "Adjust-Start",
        f"发起调整: {adj.adjustment_id} → {adj.target_constraint_id}（审议态）",
        hash_text(payload.model_dump_json()),
        hash_text(adj.model_dump_json()),
        nca_type="AUDIT", signer=gate.signer,
    )
    adj.nca_refs.append(nca["NCA-ID"])
    if adj.deliberation:
        adj.deliberation.nca_ref = nca["NCA-ID"]
    _save(adj)
    return adj.model_dump()


@router.post("/{adjustment_id}/transition", summary="推进调整流程（每步须人类签名，BV-3）")
def transition_adjustment(
    adjustment_id: str,
    to_status: AdjustmentStatus,
    human_signature: str,
    proposal: str = "",
    final_version: int = 1,
    effective_date: str = "",
    rollback_version: int | None = None,
    extra_signatures: str = "",
) -> dict:
    """推进状态机：deliberation→sandbox→determination→encoding→deployment→feedback/closed。

    关键约束：
    - 每步必须携带人类签名（BV-3）
    - 进入 determination 前强制沙盒（BV-4，未过则 422）
    - determination 需 ≥3 人类签名（异构三角，extra_signatures 逗号分隔补充）
    - determination 步须显式指定 effective_date（生效时间）与 rollback_version（回滚版本）（H3/E3）
    - encoding 将约束置为 rigid（刚性态，快系统执行）
    """
    raw = get_item("adjustments", "adjustment_id", adjustment_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="调整记录不存在")
    adj = _to_adjustment(raw)

    extra = {
        "proposal": proposal,
        "final_version": final_version,
        "effective_date": effective_date,
        "rollback_version": rollback_version,
        "human_signatures": [s.strip() for s in (extra_signatures or "").split(",") if s.strip()],
    }
    try:
        adj = FLOW.transition(adj, to_status, human_signature, extra)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _save(adj)
    return adj.model_dump()
