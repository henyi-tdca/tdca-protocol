# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——BV-3 人类写权限门（硬隔离）
# 约束矩阵:     FC-NS-OPS-001 BV-3（人类专属写权限硬隔离）+ NS-011 §1.3（写权不可智能体代行）
#               + 红队 P0 返修 #5（NS_Generator/OTA_Updater 禁 AI 写）+ #6（声明-行为映射 BV-1）
# 先验分布:     NS-011 层级归属表（L0 立法/L1 行业/L2 场景/L3 组织/L4 个人）
# 配置权边界:    L2 层；门禁只判定"是否人类签名"，不代行人类决策
# 预期分配:     返回 gate 判定（通过/拒绝+原因）；失败=签名缺失/伪造
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""BV-3 人类写权限门。

制度锚定: FC-NS-OPS-001 BV-3 | NS-011 §1.3/§2.3 | 红队 P0-5 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

# 人类签名注册表（M1 原型：模拟异构三角签批。真实环境须接入 DID 签名验证）
# 格式: {signer_id: {"role": 角色, "level": 授权层级}}
_HUMAN_REGISTRY = {
    "HUMAN-FOUNDER-001": {"role": "TDCA 制度设计师（人类）", "level": "L0"},
    "HUMAN-ENGINEER-001": {"role": "负空间工程师（人类）", "level": "L2"},
    "HUMAN-AUDITOR-001": {"role": "审计师（人类）", "level": "L2"},
}

# 确定态（冻结）所需异构三角签名数
DETERMINATION_SIGNATURES_REQUIRED = 3


@dataclass
class GateDecision:
    """写权限门判定结果。"""

    allowed: bool
    reason: str
    signer: str | None = None
    role: str | None = None


class HumanWriteGate:
    """BV-3 人类写权限门：所有约束/调整的写操作必须经此门。

    六要素声明:
    目标函数: 判定一次写操作是否由登记在册的人类签名发起
    约束矩阵: 输入——signature 必填且 ∈ 注册表；输出——GateDecision；禁止——AI 标识放行、空签放行
    先验分布: _HUMAN_REGISTRY（M1 模拟注册表）+ NS-011 层级归属
    配置权边界: L2；门禁无写权，仅判定
    预期分配: 返回 allowed/reason/signer/role；失败=ValueError（签名非法）
    审计轨迹: 判定结果由调用方写入 NCA；时间戳=判定时刻
    """

    def __init__(self) -> None:
        self.registry = _HUMAN_REGISTRY

    def check(self, signature: str, required_level: str | None = None) -> GateDecision:
        """校验人类签名（BV-3 核心判定）。

        required_level: 若指定（如 "L0"），要求签名人层级 ≥ 该层级（NS-011 §1.3 层级归属）。
        """
        ts = datetime.now(timezone.utc).isoformat()
        if not signature or not signature.strip():
            return GateDecision(
                allowed=False,
                reason="[BV-3 BLOCKED] 写操作必须携带人类签名，签名缺失",
            )
        if signature not in self.registry:
            return GateDecision(
                allowed=False,
                reason=f"[BV-3 BLOCKED] 签名 '{signature}' 不在人类注册表中，疑似 AI 代行写权",
            )
        signer = self.registry[signature]
        # B2/E5 修复：层级权限校验（NS-011 §1.3）——required_level 要求签名人层级不低于目标层级
        # 层级序: L0(立法) > L1(行业) > L2(场景) > L3(组织) > L4(个人)；L0 可执行任意层级写操作
        if required_level:
            level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
            if required_level not in level_order:
                # T-4 修复：未知授权层级显式拒绝（防未知要求默认放行）
                return GateDecision(
                    allowed=False,
                    reason=f"[BV-3 BLOCKED] 未知授权层级 '{required_level}'，拒绝执行",
                )
            signer_level = level_order.get(signer.get("level"), 99)
            required_order = level_order[required_level]
            if signer_level > required_order:
                return GateDecision(
                    allowed=False,
                    reason=(
                        f"[BV-3 BLOCKED] 层级权限不足: 本操作需 {required_level} 级（L0 法律底线/宪法流程），"
                        f"签名 '{signature}' 为 {signer.get('level')} 级"
                    ),
                )
        return GateDecision(
            allowed=True,
            reason=f"[BV-3 ALLOW] 人类签名通过（{signer['role']}，{ts}）",
            signer=signature,
            role=signer["role"],
        )

    def is_human(self, signature: str) -> bool:
        """便捷判定：签名是否在册人类。"""
        return self.check(signature).allowed


# 全局门实例
GATE = HumanWriteGate()
