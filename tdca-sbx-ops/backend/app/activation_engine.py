# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     激活系数计算引擎（F3）——SV-1 硬编码 >1.2 出盒必要条件
# 约束矩阵:     FC-SBX-OPS-001 SV-1（阈值硬编码不可绕过）+ 开发纪律 1（不可 mock，须数据性质标注）
# 先验分布:     任务书 §二 F3 + KB-ECON-001 §7（α=(出盒税收+就业社保)/政府初始 PCR 投入）
# 配置权边界:    L2 层；纯计算引擎，数据来源由调用方标注
# 预期分配:     激活系数 + 决策门判定 + 出盒资格；失败=非法输入拒绝
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}（计算过程由调用方存证）
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""激活系数计算引擎（F3，SV-1）。

制度锚定: FC-SBX-OPS-001 SV-1（>1.2 硬编码）/ ID39 / KB-ECON-001 §7

激活系数 = (出盒税收贡献 + 就业社保) / 政府初始 PCR 投入
决策门:
  α > 1.2  → 财政自给性达成 → 出盒必要条件满足（非充分）
  1.0 < α ≤ 1.2 → 基本盈亏平衡 → 条件续期
  α ≤ 1.0 → 财政不可持续 → 负空间熔断 / 资产清算
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .models import ActivationStatus

# ---------------------------------------------------------------------------
# SV-1 硬编码阈值（不可配置、不可绕过）
# ---------------------------------------------------------------------------
ACTIVATION_THRESHOLD: float = 1.2  # 出盒必要条件阈值（SV-1）
BREAKEVEN_THRESHOLD: float = 1.0   # 盈亏平衡阈值（条件续期）

# 允许的数据性质标注（开发纪律 1：激活系数不可 mock，数据须显式标注来源性质）
DATA_NATURES = {"real", "simulated"}  # real=真实税收/MOU 数据；simulated=沙盒模拟合约数据（须出盒前对接真实）


def compute_activation(
    pcr_input: float,
    tax_revenue: float,
    employment_ss: float,
    data_nature: str = "simulated",
) -> Dict[str, Any]:
    """计算激活系数并给出决策门判定（F3）。

    六要素声明:
    目标函数: 计算激活系数 α=(tax+ss)/pcr 并判定财政自给性（SV-1 硬编码决策门）
    约束矩阵: 输入——pcr_input>0（政府初始 PCR 投入，除数非法拒绝）、tax/ss≥0（非负校验）；
              输出——{coefficient, status, exit_required, decision, data_nature}；
              禁止——负数输入、pcr=0 除零、阈值外部可配
    先验分布: 任务书 §二 F3 公式 + KB-ECON-001 §7
    配置权边界: L2；纯计算，无副作用；数据性质须标注（real/simulated）
    预期分配: 返回计算与判定结果；失败=ValueError（非法输入）
    审计轨迹: 输入哈希/输出哈希由调用方 NCA 存证（F8）
    """
    if data_nature not in DATA_NATURES:
        raise ValueError(f"data_nature 必须为 {'/'.join(sorted(DATA_NATURES))}，收到 {data_nature!r}（开发纪律 1：数据性质不可缺省伪造）")
    if pcr_input <= 0:
        raise ValueError("政府初始 PCR 投入必须 > 0（除数非法，拒绝计算）")
    if tax_revenue < 0 or employment_ss < 0:
        raise ValueError("税收贡献与就业社保必须 ≥ 0")

    coefficient = (tax_revenue + employment_ss) / pcr_input

    if coefficient > ACTIVATION_THRESHOLD:
        status = ActivationStatus.SELF_FINANCED
        decision = "政策可复制推广"
    elif coefficient > BREAKEVEN_THRESHOLD:
        status = ActivationStatus.BREAKEVEN
        decision = "条件续期"
    else:
        status = ActivationStatus.UNSUSTAINABLE
        decision = "负空间熔断 / 资产清算"

    return {
        "pcr_input": pcr_input,
        "tax_revenue": tax_revenue,
        "employment_ss": employment_ss,
        "coefficient": round(coefficient, 6),
        "status": status.value,
        "decision": decision,
        "exit_required": coefficient > ACTIVATION_THRESHOLD,  # SV-1: >1.2 出盒必要条件
        "data_nature": data_nature,
        "threshold": ACTIVATION_THRESHOLD,
    }


def check_exit_eligibility(
    activation: Dict[str, Any],
    signatures: Dict[str, Any],
) -> Dict[str, Any]:
    """出盒资格判定：SV-1（α>1.2 必要条件）+ SV-6（异构三角 ≥3 签名）。

    六要素声明:
    目标函数: 判定沙盒是否具备出盒资格（必要非充分——最终出盒须人类签批）
    约束矩阵: 输入——activation（compute_activation 输出）、signatures（multisig 收集结果）；
              输出——{eligible, activation_passed, signatures_passed, reasons}；
              禁止——α≤1.2 放行、三方签名不全放行
    先验分布: 任务书 §五 SV-1/SV-6
    配置权边界: L2
    预期分配: 返回资格判定；失败=输入结构非法
    审计轨迹: 判定结果由调用方 NCA 存证
    """
    reasons: list[str] = []
    activation_passed = bool(activation.get("exit_required"))
    signatures_passed = bool(signatures.get("complete"))

    if not activation_passed:
        reasons.append(f"激活系数未达出盒必要条件（SV-1: α > {ACTIVATION_THRESHOLD}）")
    if not signatures_passed:
        reasons.append("异构三角签名不足（SV-6: 创新者/投资者/政府三方签名 ≥3）")

    return {
        "eligible": activation_passed and signatures_passed,
        "activation_passed": activation_passed,
        "signatures_passed": signatures_passed,
        "reasons": reasons,
    }
