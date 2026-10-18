# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 系统集成）
# 目标函数:     集成状态查询路由（flow 挂接 / nsfl 熔断台账 / 沙盒状态）
# 约束矩阵:     FC-NS-OPS-001 接口链 + BV-5（NCA 存证）+ 只读查询
# 先验分布:     integration/ 四适配器
# 配置权边界:    L2 层；查询只读，挂接操作经 BV-3 门
# 预期分配:     集成台账 API；失败=接口异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2 集成路由（台账查询 + 挂接触发）。

制度锚定: FC-NS-OPS-001 M2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..human_gate import GATE
from ..models import ConstraintLayer
from ..store import get_item
from ..integration.flow_adapter import FLOW
from ..integration.nsfl_adapter import NSFL

router = APIRouter(prefix="/api/v1/integration", tags=["M2 集成"])


@router.get("/flows", summary="已挂接 FlowEngine 生命周期台账")
def list_flows() -> list[dict]:
    """全周期挂接台账（Phase 0 前置记录）。"""
    return FLOW.list_hooks()


@router.post("/flows/{adjustment_id}", summary="挂接调整到 FlowEngine（Phase 0，BV-3）", status_code=201)
def hook_flow(adjustment_id: str, human_signature: str) -> dict:
    """将已确定的调整挂接为 FlowEngine 生命周期。

    前置条件: 调整处于 determination/encoding/deployment 态（已确定冻结）；
    制度层（institutional）约束不可挂接（仅 OTA/宪法流程，E1 继承）。
    """
    gate = GATE.check(human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)

    raw = get_item("adjustments", "adjustment_id", adjustment_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="调整记录不存在")

    target = get_item("constraints", "id", raw.get("target_constraint_id", ""))
    if target and target.get("layer") == ConstraintLayer.INSTITUTIONAL.value:
        raise HTTPException(
            status_code=403,
            detail="[NSFL] 制度负空间约束禁止挂接全周期流程（仅 OTA/宪法流程）",
        )

    det = raw.get("determination")
    if det is None or not det.get("effective_date"):
        raise HTTPException(
            status_code=422,
            detail="调整未确定（冻结态缺失），不可挂接——须先完成 determination",
        )

    try:
        result = FLOW.hook_adjustment(
            adjustment_id=adjustment_id,
            constraint_id=raw["target_constraint_id"],
            final_version=int(det.get("final_version", 1)),
            effective_date=str(det.get("effective_date", "")),
            trigger=(raw.get("deliberation") or {}).get("trigger", ""),
            human_signature=gate.signer,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
    return result


@router.get("/flows/{flow_id}/status", summary="FlowEngine 生命周期状态")
def flow_status(flow_id: str) -> dict:
    """查询生命周期状态（Phase + 轨迹 + 挂接信息）。"""
    try:
        return FLOW.status(flow_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/flows/{flow_id}/advance", summary="推进 FlowEngine 下一 Phase（BV-3）")
def flow_advance(flow_id: str, human_signature: str, intent_clear: bool = True) -> dict:
    """推进生命周期（P0→P1：意图孕育条件检查）。"""
    gate = GATE.check(human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)
    try:
        return FLOW.advance(flow_id, {
            "connection_weight": 0.8,
            "intent_clear": intent_clear,
            "nsfl_triggered": False,
        }, human_signature)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/nsfl/declarations", summary="NSFL 四类声明预检结果")
def nsfl_precheck(text: str = "") -> dict:
    """对文本做四类 NSFL 声明预检（防火墙 Layer-8 前置校验）。"""
    return NSFL.precheck(text)


@router.get("/nsfl/fuses", summary="活跃熔断列表")
def nsfl_fuses() -> list[dict]:
    """活跃熔断（NSFLEngine 台账）。"""
    return NSFL.active_fuses()


@router.get("/nsfl/history", summary="熔断历史")
def nsfl_history() -> list[dict]:
    """熔断历史。"""
    return NSFL.fuse_history()

# ---- M3 路由（DID / NSFL 编译 / 场景意义判定） ----


@router.get("/identity/verify", summary="M3-1 身份校验（DID 或注册表）")
def identity_verify(signature: str) -> dict:
    """统一身份校验入口（M3-1：DID 前缀自动走 DIDVerifier，否则注册表）。"""
    from ..integration.identity import get_identity_verifier, DIDVerifier

    if signature.startswith("did:"):
        result = DIDVerifier().verify(signature)
    else:
        result = get_identity_verifier().verify(signature)
    return {"verified": result.get("valid", False), **result}


@router.post("/identity/switch", summary="M3-1 切换身份校验后端（BV-3 保护）")
def identity_switch(backend: str, human_signature: str) -> dict:
    """切换身份校验后端（registry/did）。切换本身须人类签名（BV-3）。"""
    gate = GATE.check(human_signature)
    if not gate.allowed:
        raise HTTPException(status_code=403, detail=gate.reason)
    from ..integration import identity as _id

    if backend == "did":
        _id.set_identity_verifier(_id.DIDVerifier())
    elif backend == "registry":
        _id.set_identity_verifier(_id.RegistryVerifier())
    else:
        raise HTTPException(status_code=422, detail=f"未知后端: {backend}（可选 registry/did）")
    return {"backend": backend, "active": type(_id.get_identity_verifier()).__name__}


@router.get("/nsfl/compile", summary="M3-3 NSFL 语义编译（action_code 生成）")
def nsfl_compile(layer: str, action: str, certainty: str = "medium") -> dict:
    """将约束声明编译为 NSFL 语义 action_code（复用 tdca-toolchain 约束布尔化）。"""
    try:
        return NSFL.compile_action_code(layer, action, certainty)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"编译失败: {e}")


@router.get("/scenes/meaning", summary="M3-5 场景意义判定（F5，Theme_Health）")
def scene_meaning(scene: str, behavior: str = "") -> dict:
    """F5 场景意义判定：Theme_Health + 削弱维度（可观测度量，BV-2）。"""
    from ..integration.scene_meaning import MEANING

    return MEANING.evaluate(scene, behavior)


@router.get("/scenes/themes", summary="M3-5 场景意义锚点清单（BV-7 人类维护）")
def scene_themes() -> dict:
    """场景主题意义锚点清单。"""
    from ..integration.scene_meaning import MEANING

    return MEANING.list_themes()