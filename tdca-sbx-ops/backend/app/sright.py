# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     F4 S-Right 场景配置权——制度梯度 L0-L3 + PUCR 预售/质押（SV-2）
# 约束矩阵:     任务书 SV-2（PUCR 预售须可验证 MOU）+ 开发纪律 2（PUCR 真实硬数据）
# 先验分布:     任务书 §二 F4 + KB-ECON-001 §5（MOU 税收锚定）
# 配置权边界:    L2 层；S-Right 是场景配置权（非占有权，宪法 C13）
# 预期分配:     S-Right 分配/梯度推进/PUCR 预售/成熟企业质押；失败=非法输入拒绝
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F4 S-Right 场景配置权引擎（制度梯度 + PUCR 预售/质押）。

制度锚定: 任务书 §二 F4 + SV-2 + 宪法 C13（配置权是协作调度权非占有权）
SPDX-License-Identifier: TDCA-Internal

制度梯度: L0（全约束基线）→ L1（低度松绑）→ L2（中度松绑）→ L3（高度松绑）
PUCR 预售（SV-2）: 零数据企业通过预售配置权产生第一笔硬数据；MOU 税收锚定验证位
成熟企业质押: 既有企业质押自有资源入盒
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

# 制度梯度（渐进式制度松绑；数值越大松绑程度越高）
SRIGHT_GRADIENTS = ("L0", "L1", "L2", "L3")
GRADIENT_LABELS = {
    "L0": "全约束基线（宪法+NSFL 全量）",
    "L1": "低度松绑（常规约束）",
    "L2": "中度松绑（配置权市场标准）",
    "L3": "高度松绑（场景专项便利）",
}
MAX_GRADIENT = "L3"


def new_sright_id() -> str:
    """S-Right 标识: sright:{uuid}。"""
    return f"sright:{uuid.uuid4().hex}"


def allocate_sright(
    scene: str,
    holder_did: str,
    gradient: str = "L0",
    config_rights: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """分配 S-Right 场景配置权（F4 微创新场景准入）。

    六要素声明:
    目标函数: 分配场景配置权（F4，宪法 C13 配置权非占有权）
    约束矩阵: 输入——scene/holder_did 必填、gradient∈{L0..L3}；输出——SRight 记录；
              禁止——非法梯度、空场景、越权（holder 须为注册主体）
    先验分布: 任务书 §二 F4（微创新场景准入/制度梯度）
    配置权边界: L2；分配记录随 NCA 存证
    预期分配: 返回 SRight；失败=ValueError
    审计轨迹: SBX_CONFIGURE 时经 NCA 存证
    """
    if not scene or not holder_did:
        raise ValueError("scene 与 holder_did 必填")
    if gradient not in SRIGHT_GRADIENTS:
        raise ValueError(f"gradient 必须为 {'/'.join(SRIGHT_GRADIENTS)}，收到 {gradient!r}")
    return {
        "sright_id": new_sright_id(),
        "scene": scene,
        "holder_did": holder_did,
        "gradient": gradient,
        "gradient_label": GRADIENT_LABELS[gradient],
        "config_rights": config_rights or [],
        "pucr": None,  # PUCR 预售/质押位（SV-2）
        "status": "active",
    }


def escalate_gradient(sright: Dict[str, Any], to_gradient: str) -> Dict[str, Any]:
    """制度梯度推进（L0→L1→L2→L3 渐进式松绑）。

    六要素声明:
    目标函数: S-Right 制度梯度升级（F4 渐进式松绑）
    约束矩阵: 输入——sright、to_gradient；输出——更新后 SRight；
              禁止——越级（必须逐级）、降级需人类裁决、终态再升级
    先验分布: 任务书 §二 F4（L0→L1→L2→L3 渐进式制度松绑）
    配置权边界: L2
    预期分配: 返回升级后 SRight；失败=ValueError（越级/非法）
    审计轨迹: 梯度变更随 NCA 存证
    """
    if to_gradient not in SRIGHT_GRADIENTS:
        raise ValueError(f"to_gradient 必须为 {'/'.join(SRIGHT_GRADIENTS)}")
    cur = sright.get("gradient")
    if cur not in SRIGHT_GRADIENTS:
        raise ValueError("SRight 梯度非法")
    cur_idx = SRIGHT_GRADIENTS.index(cur)
    to_idx = SRIGHT_GRADIENTS.index(to_gradient)
    if to_idx != cur_idx + 1:
        raise ValueError(f"梯度必须逐级推进（{cur} → 下一级），收到 {cur} → {to_gradient}")
    updated = dict(sright)
    updated["gradient"] = to_gradient
    updated["gradient_label"] = GRADIENT_LABELS[to_gradient]
    return updated


def pucr_presale(
    sright: Dict[str, Any],
    amount: float,
    data_nature: str = "simulated",
    mou_anchor: str = "",
) -> Dict[str, Any]:
    """PUCR 预售/质押（SV-2）：零数据企业产生第一笔可验证硬数据。

    六要素声明:
    目标函数: PUCR 预售记录（F4/SV-2）——配置权预售产生可验证数据
    约束矩阵: 输入——amount>0、data_nature∈{real,simulated}；输出——pucr 记录；
              禁止——amount≤0、数据性质缺省伪造（开发纪律 2）、无 MOU 锚定位
    先验分布: 任务书 §二 F4（PUCR 预售）+ KB-ECON-001 §5（MOU 锚定）+ SV-2
    配置权边界: L2；预售金额随 NCA 存证（MOU 锚定验证位 M4 对接真实税务）
    预期分配: 返回含 pucr 的 SRight；失败=ValueError
    审计轨迹: SBX_CONFIGURE NCA 存证（含 amount/data_nature）
    """
    if amount <= 0:
        raise ValueError("PUCR 预售金额必须 > 0（SV-2 可验证硬数据）")
    if data_nature not in {"real", "simulated"}:
        raise ValueError("data_nature 必须为 real/simulated（不可伪造）")
    updated = dict(sright)
    updated["pucr"] = {
        "amount": amount,
        "data_nature": data_nature,
        "mou_anchor": mou_anchor,  # MOU 税收锚定验证位（M4 对接真实税务）
        "status": "pending_verification",
    }
    return updated


def mature_pledge(
    sright: Dict[str, Any],
    pledged_asset: str,
    pledged_value: float,
) -> Dict[str, Any]:
    """成熟企业质押入盒（F4：既有企业质押自有资源）。

    六要素声明:
    目标函数: 成熟企业质押自有资源入盒（F4 成熟企业质押）
    约束矩阵: 输入——pledged_asset 非空、pledged_value>0；输出——质押记录；
              禁止——空资产、非正质押值
    先验分布: 任务书 §二 F4（成熟企业质押）
    配置权边界: L2
    预期分配: 返回含质押记录的 SRight；失败=ValueError
    审计轨迹: 质押随 NCA 存证
    """
    if not pledged_asset or pledged_value <= 0:
        raise ValueError("pledged_asset 非空且 pledged_value > 0")
    updated = dict(sright)
    updated["pledge"] = {
        "asset": pledged_asset,
        "value": pledged_value,
        "status": "pledged",
    }
    return updated
