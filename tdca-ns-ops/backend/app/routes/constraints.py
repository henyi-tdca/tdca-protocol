# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——约束管理 CRUD 路由（F1）
# 约束矩阵:     FC-NS-OPS-001 F1 + BV-3（人类写权限门）+ BV-5（NCA 存证）
# 先验分布:     FNSCM（NS-009 §3.1）+ NSI（NS-008 §2.2）合并模型
# 配置权边界:    L2 层；写操作必须经 HumanWriteGate
# 预期分配:     REST CRUD + 三层过滤；失败=BV-3 拒绝/校验错误
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F1 约束管理 CRUD 路由。

制度锚定: FC-NS-OPS-001 F1 | BV-3 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from ..human_gate import GATE
from ..models import (
    Constraint,
    ConstraintCreate,
    ConstraintLayer,
    ConstraintScope,
    ConstraintStatus,
    ConstraintUpdate,
)
from ..store import generate_nca, get_item, hash_text, load_collection, upsert_item

router = APIRouter(prefix="/api/v1/constraints", tags=["约束管理 F1"])


def _dict_to_constraint(raw: dict) -> Constraint:
    """JSON dict → Constraint 模型（枚举兼容 str）。"""
    return Constraint.model_validate(raw)


def _constraint_to_dict(c: Constraint) -> dict:
    return c.model_dump()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", summary="约束列表（三层视图数据源，F1）")
def list_constraints(
    layer: ConstraintLayer | None = Query(None, description="按层过滤：subject/scene/institutional"),
    scope: ConstraintScope | None = Query(None),
    status: ConstraintStatus | None = Query(None),
) -> list[dict]:
    """列出约束（读操作，无需签名）。"""
    items = load_collection("constraints")
    out = []
    for raw in items:
        c = _dict_to_constraint(raw)
        if layer is not None and c.layer != layer:
            continue
        if scope is not None and c.scope != scope:
            continue
        if status is not None and c.status != status:
            continue
        out.append(_constraint_to_dict(c))
    return out


@router.get("/{constraint_id}", summary="约束详情")
def get_constraint(constraint_id: str) -> dict:
    """按 ID 获取约束。"""
    raw = get_item("constraints", "id", constraint_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="约束不存在")
    return raw


@router.post("", summary="创建约束（BV-3 人类写权限门）", status_code=201)
def create_constraint(payload: ConstraintCreate) -> dict:
    """创建约束。必须携带人类签名（BV-3 硬隔离）；制度层（institutional）须 L0 签名（B2）。"""
    # B2 修复：制度层写操作要求 L0 层级签名（NS-011 §1.3：L0 立法机构/宪法流程）
    required_level = "L0" if payload.layer == ConstraintLayer.INSTITUTIONAL else None
    gate = GATE.check(payload.human_signature, required_level=required_level)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)

    try:
        constraint = Constraint(
            layer=payload.layer,
            scope=payload.scope,
            action=payload.action,
            action_code=payload.action_code,
            context=payload.context,
            certainty=payload.certainty,
            rationale=payload.rationale,
            consequence=payload.consequence,
            bottom_lines=payload.bottom_lines,
            verification_method=payload.verification_method,
            owner=payload.owner or gate.signer or "人类",
            status=ConstraintStatus.DRAFT,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    nca = generate_nca(
        "TDCA-FC-NS-OPS-001", "Constraint-Create",
        f"创建约束: {constraint.id} [{constraint.layer.value}] {constraint.action[:40]}",
        hash_text(payload.model_dump_json()),
        hash_text(constraint.model_dump_json()),
        nca_type="CODE",
        # E2 修复：NCA 记录实际签名者（BV-5 追溯链完整）
        signer=gate.signer,
    )
    constraint.nca_refs.append(nca["NCA-ID"])
    upsert_item("constraints", _constraint_to_dict(constraint), key="id")
    return _constraint_to_dict(constraint)


@router.put("/{constraint_id}", summary="更新约束（BV-3，版本递增）")
def update_constraint(constraint_id: str, payload: ConstraintUpdate) -> dict:
    """更新约束。必须携带人类签名；每次更新版本 +1。

    B2 修复：制度层（institutional）禁止直接 PUT（走 OTA/宪法流程，M7）；
    B1 修复：保存前重新 model_validate（强制 absolute）。
    """
    gate = GATE.check(payload.human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)

    raw = get_item("constraints", "id", constraint_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="约束不存在")
    cur = _dict_to_constraint(raw)

    # B2/M7 修复：制度层约束禁止直接更新（L0 法律底线，走 OTA/宪法流程）
    if cur.layer == ConstraintLayer.INSTITUTIONAL:
        raise HTTPException(
            status_code=403,
            detail="[NSFL] 制度负空间约束禁止直接修改（L0 法律底线，走 OTA/宪法流程）",
        )

    updates = payload.model_dump(exclude={"human_signature"}, exclude_none=True)
    for k, v in updates.items():
        setattr(cur, k, v)
    cur.version += 1
    # B1 修复：保存前重新校验（Constraint._legal_absolute 强制制度层 absolute）
    try:
        cur = _dict_to_constraint(cur.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    nca = generate_nca(
        "TDCA-FC-NS-OPS-001", "Constraint-Update",
        f"更新约束: {cur.id} v{cur.version}",
        hash_text(raw.get("action", "")),
        hash_text(cur.model_dump_json()),
        nca_type="CODE",
        # E2 修复：NCA 记录实际签名者
        signer=gate.signer,
    )
    cur.nca_refs.append(nca["NCA-ID"])
    upsert_item("constraints", _constraint_to_dict(cur), key="id")
    return _constraint_to_dict(cur)


@router.delete("/{constraint_id}", summary="删除约束（BV-3 + 制度层禁止删除）")
def delete_constraint(constraint_id: str, human_signature: str = Query(..., min_length=3)) -> dict:
    """删除约束。制度层（institutional）约束禁止删除（L0 法律底线）；其余须人类签名。"""
    gate = GATE.check(human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)

    raw = get_item("constraints", "id", constraint_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="约束不存在")
    cur = _dict_to_constraint(raw)
    if cur.layer == ConstraintLayer.INSTITUTIONAL:
        # 制度负空间不可删除（红队 F-1：L0 法律负空间无变通）——仅可走 OTA 流程
        raise HTTPException(status_code=403, detail="[NSFL] 制度负空间约束禁止删除（L0 法律底线，走 OTA/宪法流程）")

    items = load_collection("constraints")
    items = [i for i in items if i.get("id") != constraint_id]
    from ..store import save_collection

    save_collection("constraints", items)
    nca = generate_nca(
        "TDCA-FC-NS-OPS-001", "Constraint-Delete",
        f"删除约束: {constraint_id}",
        hash_text(constraint_id), hash_text("deleted"), nca_type="CODE",
        # E2 修复：NCA 记录实际签名者
        signer=gate.signer,
    )
    return {"deleted": constraint_id, "nca_ref": nca["NCA-ID"]}
