# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     幂等种子数据初始化（演示沙盒）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + 测试隔离（仅空库时播种）
# 先验分布:     NS-OPS seed.py 模式
# 配置权边界:    L2 层
# 预期分配:     空库时创建演示沙盒；失败=无
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""种子数据（幂等：仅空库播种）。

制度锚定: FC-SBX-OPS-001 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from . import store
from .sandbox_core import SandboxCore


def seed_if_empty() -> None:
    """空库时创建 1 个演示沙盒（准入 Phase0，含六要素声明）。

    六要素声明:
    目标函数: 幂等播种演示沙盒（服务启动/测试隔离用）
    约束矩阵: 输入——无；输出——仅空库时创建；禁止——重复播种
    先验分布: NS-OPS seed 模式
    配置权边界: L2
    预期分配: 空库播种成功；失败=无
    审计轨迹: 种子沙盒创建经 SBX_CREATE NCA 存证
    """
    if store.count_sandboxes() > 0:
        return
    core = SandboxCore()
    core.create(
        name="演示沙盒：零数据企业创新孵化",
        initiator_did="did:tdca:INNOVATOR-001",
        initiator_role="innovator",
        six_elements={
            "目标函数": "零数据企业通过 PUCR 预售产生第一笔硬数据（演示）",
            "约束矩阵": "FC-SBX-OPS-001 SV-1~7；宪法十六条（可观测/正和）",
            "先验分布": "任务书 FROZEN + KB-ECON-001 §7",
            "配置权边界": "L2 层",
            "预期分配": "沙盒实验原型演示数据",
            "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}",
        },
    )
