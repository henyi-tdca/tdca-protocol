# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 冻结 + M3 增量：DIDVerifier）
# 目标函数:     身份签名可插拔接口（M2-4）——签名注册表 → 抽象身份校验
# 约束矩阵:     FC-NS-OPS-001 BV-3（人类专属写权）+ BV-2（声明不可智能体单方修改）
# 先验分布:     M1 human_gate.py（注册表模拟）
# 配置权边界:    L2 层；接口抽象，真实 DID/多签实现留 M3
# 预期分配:     统一签名校验接口（可插拔后端）；失败=签名无效
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2-4 身份签名可插拔接口。

制度锚定: FC-NS-OPS-001 BV-3 | NS-011 §1.3 | SPDX-License-Identifier: TDCA-Internal

M1 注册表为模拟（3 人）；M2 抽象为可插拔校验器接口，真实 DID/多签 M3 接入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


class IdentityVerifier(Protocol):
    """签名校验器协议（可插拔后端）。"""

    def verify(self, signature: str) -> dict:
        """校验签名。返回 {valid, signer, role, level}。"""
        ...


class RegistryVerifier:
    """M2 默认实现：人类签名注册表（M1 human_gate 扩展）。

    六要素声明:
    目标函数: 基于注册表校验人类签名（BV-3 写权限门身份层）
    约束矩阵: 输入——signature；输出——{valid, signer, role, level}；禁止——AI 标识放行
    先验分布: M1 human_gate._HUMAN_REGISTRY
    配置权边界: L2
    预期分配: 返回校验结果；失败=签名无效
    审计轨迹: 校验结果由调用方 NCA 存证
    """

    def __init__(self, registry: dict | None = None) -> None:
        from ..human_gate import _HUMAN_REGISTRY

        self.registry = registry or _HUMAN_REGISTRY

    def verify(self, signature: str) -> dict:
        if not signature or signature not in self.registry:
            return {"valid": False, "signer": None, "role": None, "level": None}
        info = self.registry[signature]
        return {
            "valid": True,
            "signer": signature,
            "role": info["role"],
            "level": info["level"],
        }


class DIDVerifier:
    """M3-1：DID 身份校验器（可插拔后端）。

    六要素声明:
    目标函数: 校验 DID 格式身份签名（M3 边界项落地）——真 DID 服务接入前的适配层
    约束矩阵: 输入——signature（DID 格式）；输出——{valid, signer, role, level}；
              禁止——格式非法放行、DID 绕过 BV-3 人类写权
    先验分布: W3C DID 语法（did:method:idstring）+ M1 注册表回退
    配置权边界: L2；仅校验格式 + 注册表映射，不代行真实 DID 解析（M4/外部服务）
    预期分配: 返回校验结果；失败=格式非法
    审计轨迹: 校验结果由调用方 NCA 存证
    """

    # DID 语法: did:method:idstring（method 限定 tdca，防止任意 method 注入）
    _DID_RE = r"^did:tdca:[A-Za-z0-9._:-]{8,64}$"

    def __init__(self, registry: dict | None = None, strict: bool = True) -> None:
        import re

        from ..human_gate import _HUMAN_REGISTRY

        self._re = re.compile(self._DID_RE)
        self.registry = registry or _HUMAN_REGISTRY
        self.strict = strict  # True=仅 DID 格式 + 注册表映射；False=宽松（未注册 DID 仅记录）

    def verify(self, signature: str) -> dict:
        if not signature or not self._re.match(signature):
            return {"valid": False, "signer": None, "role": None, "level": None}
        # DID 主体解析: did:tdca:{subject} → 注册表键（BV-3 人类写权身份层）
        subject = signature.split(":", 2)[-1]
        if subject in self.registry:
            info = self.registry[subject]
            return {
                "valid": True,
                "signer": signature,
                "role": info["role"],
                "level": info["level"],
                "method": "did:tdca",
            }
        # 未注册 DID：strict 模式拒绝（防任意 DID 伪造写权）
        if self.strict:
            return {"valid": False, "signer": None, "role": None, "level": None}
        return {"valid": True, "signer": signature, "role": "外部DID（未注册）",
                "level": "L4", "method": "did:tdca"}


# 当前生效的身份校验后端（M3-1：默认注册表；可 set_identity_verifier 切换 DID）
_ACTIVE: IdentityVerifier = RegistryVerifier()


def set_identity_verifier(verifier: IdentityVerifier) -> None:
    """切换身份校验后端（可插拔，M3 接 DID/多签）。"""
    global _ACTIVE
    _ACTIVE = verifier


def get_identity_verifier() -> IdentityVerifier:
    """获取当前身份校验后端。"""
    return _ACTIVE


def verify_human(signature: str) -> dict:
    """统一人类签名校验入口（BV-3）。"""
    return _ACTIVE.verify(signature)
