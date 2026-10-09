# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 集成：F3 接入 NSFL 熔断）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——三层负空间视图路由（F1）+ 声明-行为校验（F3）
# 约束矩阵:     FC-NS-OPS-001 F1/F3 + BV-1（越界实时监控）+ NS-009 四重底线 + NS-006 五步查询
# 先验分布:     NS-009 §6.2 安全域 / NS-006 §2.3 判定枚举 / NS-008 兼容性检测
# 配置权边界:    L2 层；视图只读
# 预期分配:     TripleLayerView + JudgmentResponse；失败=参数校验
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F1 三层视图 + F3 声明-行为校验路由。

制度锚定: FC-NS-OPS-001 F1/F3 | NS-009/NS-006 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from fastapi import APIRouter

from ..models import (
    Constraint,
    ConstraintLayer,
    Decision,
    InstitutionalView,
    JudgmentRequest,
    JudgmentResponse,
    SceneView,
    SubjectView,
    TripleLayerView,
)
from ..store import generate_nca, hash_text, load_collection

# M2-2：F3 BLOCK 触发 NSFL 熔断（LEGAL 绝对熔断）
# N5 修复：集成层为强前置依赖（S1-M2 §4.3），直接导入（无假降级）
from ..integration.nsfl_adapter import NSFL, FuseType

router = APIRouter(prefix="/api/v1", tags=["三层视图 F1 / 声明-行为校验 F3"])

# 场景主题意义样例（NS-010 六要素 + Theme）——M1 演示数据
_SCENE_THEME = {
    "community": {"theme": "开源社区协作：可信共赢、贡献可溯", "six": {
        "time": "持续", "location": "线上社区", "event": "协作开发",
        "actors": "OPC 开发者/组织", "content": "代码/知识资产", "interactions": "贡献-评审-采纳",
    }},
    "hospital": {"theme": "医疗场景：隐私优先、生命至上", "six": {
        "time": "持续", "location": "医疗机构", "event": "诊疗服务",
        "actors": "医患/医疗 AI", "content": "健康数据", "interactions": "诊断-用药-随访",
    }},
}


def _to_constraint(raw: dict) -> Constraint:
    return Constraint.model_validate(raw)


@router.get("/views/triple-layer", summary="三层负空间视图（F1）")
def triple_layer_view() -> TripleLayerView:
    """聚合三层负空间：主体/场景/制度 + 四重底线状态 + 安全域。"""
    items = [i for i in load_collection("constraints") if i.get("layer")]
    subject_entries = [_to_constraint(i) for i in items if i["layer"] == ConstraintLayer.SUBJECT.value]
    scene_entries = [_to_constraint(i) for i in items if i["layer"] == ConstraintLayer.SCENE.value]
    inst_entries = [_to_constraint(i) for i in items if i["layer"] == ConstraintLayer.INSTITUTIONAL.value]

    # 主体聚合（按 owner 分组，H4：返回全部主体而非仅 [0]）
    owners: dict[str, list[Constraint]] = {}
    for c in subject_entries:
        owners.setdefault(c.owner or "未署名", []).append(c)
    subject_items = [
        SubjectView(
            subject=owner,
            entries=[c.model_dump() for c in entries],
            nsc_credit=100,
        )
        for owner, entries in owners.items()
    ]
    if not subject_items:
        subject_items = [SubjectView(subject="暂无主体声明", entries=[], nsc_credit=100)]

    # 场景视图（H4：返回全部场景；M1 按 scene 字段分组，缺省归 community）
    scene_map: dict[str, list[Constraint]] = {}
    for c in scene_entries:
        scene_key = c.context.split(";")[0].strip() or "community"
        scene_map.setdefault(scene_key, []).append(c)
    scene_items = []
    for sk, entries in scene_map.items():
        meta = _SCENE_THEME.get(sk, {"theme": sk, "six": {}})
        scene_items.append(
            SceneView(
                scene=sk,
                six_elements=meta["six"],
                theme=meta["theme"],
                theme_health=0.95,
                entries=[c.model_dump() for c in entries],
            )
        )
    if not scene_items:
        scene_items = [SceneView(scene="community", six_elements={}, theme="", entries=[])]

    # 四重底线状态（M1 简化：制度层存在=合法通过；场景/主体存在=合规/合理/合情通过）
    bottom_lines = {
        "合法": len(inst_entries) > 0,
        "合规": len(scene_entries) > 0,
        "合理": len(subject_entries) > 0,
        "合情": len(scene_entries) > 0,
    }
    safe = all(bottom_lines.values())
    return TripleLayerView(
        subjects=subject_items,
        scenes=scene_items,
        institutional=InstitutionalView(entries=[c.model_dump() for c in inst_entries]),
        bottom_lines=bottom_lines,
        safe_domain=(
            "四重底线透明重叠，协作安全域开放" if safe
            else "四重底线未完全重叠，协作受限（缺失项见 bottom_lines）"
        ),
    )


@router.post("/judgments", summary="声明-行为校验（F3，NS-006 五步查询）")
def judge_behavior(payload: JudgmentRequest) -> JudgmentResponse:
    """校验一次行为是否触碰负空间（BV-1 越界实时监控）。

    简化实现：对全部约束做文本匹配（action 关键词 ↔ 行为描述），
    制度层 absolute 命中 → BLOCK（熔断）；场景层命中 → RESTRICT；其余 → ALLOW。
    """
    items = [i for i in load_collection("constraints") if i.get("layer")]
    matched: list[str] = []
    decision = Decision.ALLOW
    fuse = False

    # bigram 匹配（行为描述与约束 action 的连续 2 字短语交集 ≥2 视为命中）
    def bigrams(s: str) -> set[str]:
        s = s.replace(" ", "").replace("，", "").replace("。", "")
        return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else set()

    action_grams = bigrams(payload.action)
    for raw in items:
        c = _to_constraint(raw)
        if not c.action:
            continue
        overlap = action_grams & bigrams(c.action)
        if len(overlap) >= 2:
            matched.append(c.id)
            if c.layer == ConstraintLayer.INSTITUTIONAL and c.certainty.value == "absolute":
                decision = Decision.BLOCK
                fuse = True
            elif decision == Decision.ALLOW:
                decision = Decision.RESTRICT if c.layer == ConstraintLayer.SCENE else decision

    # T1 修复：NSFL 声明预检无条件前置（BV-1 越界实时监控）——
    # 命中 human_override=False 的绝对负空间声明即 BLOCK（即使约束库未收录该行为）
    precheck = NSFL.precheck(payload.action)
    nsfl_hits = [r for r in precheck["results"] if r["matched_prohibitions"]]
    if precheck["blocked"] and decision == Decision.ALLOW:
        decision = Decision.BLOCK
        matched.append("NSFL-DECLARATION")
    elif precheck["blocked"] and decision != Decision.BLOCK:
        # 已有更低级判定时，绝对负空间命中升级为 BLOCK
        decision = Decision.BLOCK
        matched.append("NSFL-DECLARATION")

    reason = {
        Decision.BLOCK: "触碰制度负空间（L0 法律底线），绝对熔断（BV-1/NSFL ⊗）",
        Decision.RESTRICT: "触碰场景负空间，受限执行（附条件）",
        Decision.ALLOW_WITH_CONDITIONS: "接近边界，附加条件执行",
        Decision.ALLOW: "未触碰负空间，允许执行",
    }[decision]
    if nsfl_hits:
        reason += f"（NSFL 声明预检命中: {[r['scope'] for r in nsfl_hits]}）"

    # M2-2 接入：BLOCK 触发 NSFL 熔断（LEGAL 绝对熔断，无替代路径）
    nsfl_fuse_id = ""
    if decision == Decision.BLOCK:
        # LEGAL 熔断：绝对阻断、自动上报慢系统（ID86/ID71）
        fuse = NSFL.trigger_fuse(
            rule_id="NS-OPS-F3-LEGAL",
            reason=reason,
            fuse_type=FuseType.LEGAL,
            severity=5,
            alt_path="",
        )
        nsfl_fuse_id = fuse["fuse_id"]
        fuse = True

    nca = generate_nca(
        "TDCA-FC-NS-OPS-001", "Judgment-Check",
        f"声明-行为校验: {payload.actor} → {payload.action} = {decision.value}"
        + (f"（NSFL 熔断 {nsfl_fuse_id}）" if nsfl_fuse_id else ""),
        hash_text(payload.model_dump_json()),
        hash_text(f"{decision.value}|{','.join(matched)}|{nsfl_fuse_id}"),
        nca_type="AUDIT",
        # M3 修复：熔断事件在 NCA 中真实存证（NSFL Triggered 不再恒 false）
        nsfl_triggered=fuse,
        nsfl_reason=reason if fuse else None,
        # T-5 修复：F3 校验为非写权操作，不应要求人类签名（防 Pending 语义矛盾）
        human_signature_required=False,
    )
    return JudgmentResponse(
        decision=decision,
        reason=reason,
        matched_constraints=matched,
        fuse_triggered=fuse,
        nca_ref=nca["NCA-ID"],
    )
