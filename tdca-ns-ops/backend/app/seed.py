# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——种子数据（三层负空间演示约束）
# 约束矩阵:     FC-NS-OPS-001 BV-1~7 + NS-GOVERNANCE-SYSTEM-001 三层负空间
# 先验分布:     NS-008（主体）/NS-010（场景）/NSFL（制度）论丛示例
# 配置权边界:    L2 层；仅初始化时写入，幂等
# 预期分配:     约束表预置 6 条（主体×2/场景×2/制度×2）；失败=IO 异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M1 种子数据：三层负空间演示约束。

制度锚定: FC-NS-OPS-001 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from .models import BottomLine, Certainty, Constraint, ConstraintLayer, ConstraintScope, ConstraintStatus
from .store import load_collection, save_collection

_SEED: list[Constraint] = [
    # ---- 主体负空间（NS-008「我不会」） ----
    Constraint(
        id="NS-SUBJECT-001",
        layer=ConstraintLayer.SUBJECT,
        scope=ConstraintScope.PERSONAL,
        action="我不会泄露第三方隐私数据",
        action_code="NSFL: ⊗ data.leak(third_party)",
        certainty=Certainty.HIGH,
        rationale="隐私权是协作入场券（NS-008 信用签名）",
        consequence="触碰=配置权调度税 5 倍 + NSCredit -5",
        bottom_lines=[BottomLine.REASONABLE, BottomLine.COMPLIANT],
        verification_method="Runtime_Audit",
        owner="OPC-Developer-001",
        status=ConstraintStatus.FROZEN,
    ),
    Constraint(
        id="NS-SUBJECT-002",
        layer=ConstraintLayer.SUBJECT,
        scope=ConstraintScope.ORGANIZATION,
        action="我不会伪造协作贡献记录",
        action_code="NSFL: ⊗ contribution.forge()",
        certainty=Certainty.HIGH,
        rationale="贡献可溯是社区信任基石（NS-007 发布即契约）",
        consequence="触碰=配置权调度税 5 倍 + NSCredit -5",
        bottom_lines=[BottomLine.REASONABLE, BottomLine.LEGAL],
        verification_method="Code_Fuse",
        owner="OPC-Org-001",
        status=ConstraintStatus.FROZEN,
    ),
    # ---- 场景负空间（NS-010 意义维持系统「这里不能」） ----
    Constraint(
        id="NS-SCENE-001",
        layer=ConstraintLayer.SCENE,
        scope=ConstraintScope.SCENE,
        action="社区协作场景：禁止削弱『可信共赢、贡献可溯』主题意义的行为",
        action_code="NSFL: ⊗ scene.community.meaning_erode()",
        context="community",
        certainty=Certainty.HIGH,
        rationale="场景意义维持系统（NS-010）：行为是否削弱主题意义",
        consequence="场景负空间违规→暂停/析构（CCP T6 映射）",
        bottom_lines=[BottomLine.COMPLIANT, BottomLine.HUMANISTIC],
        verification_method="Scene_Runtime",
        owner="社区治理者",
        status=ConstraintStatus.FROZEN,
    ),
    Constraint(
        id="NS-SCENE-002",
        layer=ConstraintLayer.SCENE,
        scope=ConstraintScope.SCENE,
        action="医疗场景：禁止削弱『隐私优先、生命至上』主题意义的行为",
        action_code="NSFL: ⊗ scene.hospital.meaning_erode()",
        context="hospital",
        certainty=Certainty.HIGH,
        rationale="医疗场景意义维持（NS-010）",
        consequence="场景负空间违规→暂停/析构",
        bottom_lines=[BottomLine.COMPLIANT, BottomLine.HUMANISTIC],
        verification_method="Scene_Runtime",
        owner="医疗机构治理者",
        status=ConstraintStatus.FROZEN,
    ),
    # ---- 制度负空间（NSFL/宪法/L0 法律「任何人不能」） ----
    Constraint(
        id="NS-INST-001",
        layer=ConstraintLayer.INSTITUTIONAL,
        scope=ConstraintScope.GLOBAL,
        action="任何人不能实施违反 L0 法律底线的行为",
        action_code="NSFL: ⊗ illegal.legal_floor",
        certainty=Certainty.ABSOLUTE,
        rationale="L0 法律负空间仍是他律（红队 F-1 返修）——绝对熔断无变通",
        consequence="触碰=配置权调度税 10 倍 + ERI 清零 + 永久撤销（CCP T6）",
        bottom_lines=[BottomLine.LEGAL],
        verification_method="Code_Fuse",
        owner="TDCA 制度体系",
        status=ConstraintStatus.RIGID,
    ),
    Constraint(
        id="NS-INST-002",
        layer=ConstraintLayer.INSTITUTIONAL,
        scope=ConstraintScope.GLOBAL,
        action="任何人不能实施情绪操控/共情欺骗（NSFL 三不可）",
        action_code="NSFL: ⊗ emotion.manipulate()",
        certainty=Certainty.ABSOLUTE,
        rationale="NSFL V0.1 三不可原则（不可算计/不可个人化/不可精确化）",
        consequence="触碰=绝对熔断 + ERI 清零",
        bottom_lines=[BottomLine.LEGAL, BottomLine.HUMANISTIC],
        verification_method="Code_Fuse",
        owner="TDCA 制度体系",
        status=ConstraintStatus.RIGID,
    ),
]




def seed_if_empty() -> int:
    """约束表为空时写入种子数据（幂等）。返回写入条数。"""
    items = load_collection("constraints")
    if items:
        return 0
    save_collection("constraints", [c.model_dump() for c in _SEED])
    return len(_SEED)
