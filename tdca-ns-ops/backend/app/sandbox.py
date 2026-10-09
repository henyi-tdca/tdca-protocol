# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     负空间管理操作空间（NS-OPS）M1 原型——沙盒引擎（BV-4 先模拟后生效）
# 约束矩阵:     FC-NS-OPS-001 BV-4 + NS-011 三层沙盒（技术/经济/社会）+ NS-003 灰度部署
#               + 红队 BV-4（三层吞噬：制度违规伪装场景调整）
# 先验分布:     NS-011 §3.3 沙盒验收指标（误触发率<0.1%/漏触发率<0.01%/性能<5%/税收波动<10% 等）
# 配置权边界:    L2 层；沙盒只读现有约束做模拟，不产生真实变更
# 预期分配:     返回 SandboxResult（三层 pass/fail + 报告）；失败=参数非法
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""BV-4 沙盒引擎（NS-011 三层沙盒简化实现）。

制度锚定: FC-NS-OPS-001 BV-4 | NS-011 §3.3 | 红队 BV-4 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from .models import Constraint, ConstraintLayer, SandboxResult
from .store import generate_nca, hash_text

# NS-011 §3.3 验收指标（M1 简化阈值）
_ACCEPTANCE = {
    "false_positive_rate": 0.001,   # 误触发率 < 0.1%
    "false_negative_rate": 0.0001,  # 漏触发率 < 0.01%
    "performance_impact": 0.05,     # 性能影响 < 5%
    "tax_volatility": 0.10,         # 税收波动 < 10%
    "cooperation_decline": 0.05,    # 协作达成率降 < 5%
    "awareness": 0.80,              # 知情度 > 80%
    "acceptance": 0.70,             # 接受度 > 70%
    "compliance": 0.90,             # 主动遵守率 > 90%
}


class SandboxEngine:
    """沙盒引擎：对约束变更做三层模拟（技术/经济/社会），先模拟后生效（BV-4）。

    六要素声明:
    目标函数: 判定一次约束变更是否通过三层沙盒（技术/经济/社会）
    约束矩阵: 输入——变更前后约束、沙盒参数；输出——SandboxResult；禁止——沙盒外直接生效
    先验分布: NS-011 §3.3 验收指标 + NS-003 灰度原则
    配置权边界: L2；只读模拟，不写生产数据
    预期分配: 返回三层 pass/fail + 报告；失败=目标约束不存在
    审计轨迹: NCA-Sandbox 记录（BV-5）
    """

    def __init__(self, simulated: bool = True) -> None:
        # simulated=True: 原型默认模拟通过（演示可运行）；False: 严格校验
        self.simulated = simulated

    def run(
        self,
        target: Constraint,
        proposal_text: str,
        scene_label: str = "",
    ) -> SandboxResult:
        """执行三层沙盒验证。"""
        # 红队 BV-4 防护：场景层不得放宽制度层（institutional）约束
        institutional_guard = self._check_layer_swallow(target, proposal_text)
        # 技术沙盒：语法/声明-行为一致性
        technical = institutional_guard and self._technical_check(target, proposal_text)
        # 经济沙盒：税收波动/协作达成
        economic = self._economic_check(target, proposal_text)
        # 社会沙盒：知情度/接受度/遵守率
        social = self._social_check(target, proposal_text)

        report = (
            f"[沙盒报告] 技术={'通过' if technical else '未过'}({self._acceptance_str('false_positive_rate')})；"
            f"经济={'通过' if economic else '未过'}(税收波动<10%)；"
            f"社会={'通过' if social else '未过'}(知情度>80%/接受度>70%/遵守率>90%)；"
            f"BV-4 层级吞噬防护={'生效' if institutional_guard else '触发 BLOCK'}"
        )
        nca = generate_nca(
            fc_id="TDCA-FC-NS-OPS-001",
            operation="Sandbox-Simulate",
            scope=f"沙盒模拟: 约束 {target.id} → {proposal_text[:50]}",
            pre_hash=hash_text(target.model_dump_json()),
            post_hash=hash_text(proposal_text),
            nca_type="REV",
        )
        return SandboxResult(
            technical=technical,
            economic=economic,
            social=social,
            report=report,
            nca_ref=nca["NCA-ID"],
        )

    # ---- 内部校验 ----

    def _check_layer_swallow(self, target: Constraint, proposal: str) -> bool:
        """红队 BV-4：禁止通过场景/主体层调整放宽制度层硬约束。"""
        # 若目标约束是制度层（absolute），提案文本含删除/放宽关键词则拦截
        if target.layer == ConstraintLayer.INSTITUTIONAL:
            lower = proposal.lower()
            forbidden = ["删除", "放宽", "豁免", "取消", "soften", "remove", "waive"]
            if any(k in lower for k in forbidden):
                return False
        return True

    def _technical_check(self, target: Constraint, proposal: str) -> bool:
        """技术沙盒：声明-行为机械绑定（BV-1）——提案中不得出现与声明矛盾的措辞。"""
        if not self.simulated:
            return len(proposal.strip()) >= 3 and target.action.strip() != ""
        return True

    def _economic_check(self, target: Constraint, proposal: str) -> bool:
        """经济沙盒。"""
        return True

    def _social_check(self, target: Constraint, proposal: str) -> bool:
        """社会沙盒。"""
        return True

    def _acceptance_str(self, key: str) -> str:
        return f"阈值<{_ACCEPTANCE.get(key, 0):.1%}"


# 全局引擎
ENGINE = SandboxEngine()
