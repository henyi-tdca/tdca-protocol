# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     三方多签门控（创新者/投资者/政府）——SV-4 终止权 + SV-6 出盒签名
# 约束矩阵:     FC-SBX-OPS-001 SV-4（任何一方可触发终止）/ SV-6（异构三角 ≥3 签名）
# 先验分布:     任务书 §五 SV-4/SV-6 + 工作规范（异构三角裁决）
# 配置权边界:    L2 层；签名校验不代行身份认证（真实 DID 留集成层）
# 预期分配:     签名收集/校验/达数判定；失败=签名不足
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""三方多签门控（SV-4 / SV-6）。

制度锚定: FC-SBX-OPS-001 SV-4（三方任何一方可触发终止）/ SV-6（异构三角 ≥3 签名）

异构三角: 创新者（技术/场景）+ 投资者（资本/资源）+ 政府（制度/PCR）——三方独立签名，
不可由单一主体代表（无单方黑箱，开发纪律 3）。
"""

from __future__ import annotations

from typing import Any, Dict, List

TRINITY_ROLES = ("innovator", "investor", "government")
ROLE_LABELS = {"innovator": "创新者", "investor": "投资者", "government": "政府"}
MIN_TRINITY_SIGNATURES = 3  # SV-6: 异构三角 ≥3 签名（三方各 1）


def collect_signature(role: str, did: str, signature: str) -> Dict[str, str]:
    """收集单方签名（校验角色合法 + 签名非空）。

    六要素声明:
    目标函数: 收集三位一体一方签名（SV-6 出盒/关闭签名门控前置）
    约束矩阵: 输入——role∈{innovator,investor,government}、did、signature 非空；
              输出——{role, did, signature}；禁止——角色越界、空签名
    先验分布: 任务书 §二 F2 三位一体
    配置权边界: L2；仅收集记录，验真由上层身份服务（M1 记录式）
    预期分配: 返回签名记录；失败=ValueError
    审计轨迹: 签名记录随沙盒操作 NCA 存证
    """
    if role not in TRINITY_ROLES:
        raise ValueError(f"role 必须为 {'/'.join(TRINITY_ROLES)}，收到 {role!r}")
    if not did or not signature:
        raise ValueError("did 与 signature 均不可为空")
    return {"role": role, "did": did, "signature": signature, "role_label": ROLE_LABELS[role]}


def verify_trinity_signatures(signatures: List[Dict[str, str]]) -> Dict[str, Any]:
    """校验三方签名达数（SV-6: 异构三角 ≥3，三方各至少 1 签）。

    六要素声明:
    目标函数: 判定异构三角签名是否达数（SV-6 出盒必要条件之一）
    约束矩阵: 输入——签名列表；输出——{complete, roles, count, missing, reasons}；
              禁止——同一角色重复计票、缺任一角色判 complete
    先验分布: 任务书 §五 SV-6（人类/智能体/审计异构三角）——M1 实现为三位一体三方
    配置权边界: L2；只判定达数，不验签真伪（验真留身份层）
    预期分配: 返回达数判定；失败=输入结构非法
    审计轨迹: 判定结果由调用方 NCA 存证
    """
    if not isinstance(signatures, list):
        raise ValueError("signatures 必须为列表")
    present: set[str] = set()
    for sig in signatures:
        if not isinstance(sig, dict) or sig.get("role") not in TRINITY_ROLES:
            raise ValueError("签名记录结构非法：须含合法 role")
        if sig.get("signature"):
            present.add(sig["role"])

    missing = [r for r in TRINITY_ROLES if r not in present]
    complete = len(present) >= MIN_TRINITY_SIGNATURES and not missing
    reasons: list[str] = []
    if missing:
        reasons.append(f"缺签名角色: {[ROLE_LABELS[r] for r in missing]}")
    return {
        "complete": complete,
        "roles": sorted(present),
        "count": len(present),
        "missing": missing,
        "required": MIN_TRINITY_SIGNATURES,
        "reasons": reasons,
    }


def can_trigger_termination(role: str) -> bool:
    """SV-4: 三位一体任何一方可触发终止（沙盒关闭）。

    六要素声明:
    目标函数: 判定角色是否具备三方终止触发权（SV-4）
    约束矩阵: 输入——role；输出——bool；禁止——非三方角色放行
    先验分布: 任务书 §五 SV-4
    配置权边界: L2
    预期分配: 返回判定；失败=无
    审计轨迹: 关闭操作 NCA 存证
    """
    return role in TRINITY_ROLES
