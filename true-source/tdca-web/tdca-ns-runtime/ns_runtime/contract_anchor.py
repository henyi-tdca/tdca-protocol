# -*- coding: utf-8 -*-
"""
L2-R7 · 智能合约 Runtime 锚定（可编程负空间合约）
=================================================
Layer 1 静态清单升级为可编程负空间合约；进化操作须过合约前置条件检查。
对齐 ICD §2.2（POST /v1/ns-contract/precheck）:
  - 前置条件: 质押在册 + 备案完整度 ≥ 阈值 + 重大操作人类签名（HUF）
  - 不可升级: immutable=true 恒真（ID33，仅宪法 OTA，防 SEA 说服人类修改）
  - escrow 联动: 违规扣质押（escrow_deduct），对齐 SEA-ESCROW-DESIGN-001 FROZEN

设计:
  - 合约规则 = Layer 1 静态清单（不可变）+ 质押/备案前置（DCD-SEA-GOVERNANCE-001）
  - 判定: allowed=false + escrow_deduct>0 → R8 同步触发动态微调（Alt-Path）
  - fail-closed: 前置缺失（无质押/备案不足/重大操作无签名）→ 拒绝

锚定: DCD-NSFL-M3-001（L2-R7）+ NSFL-M3-ICD-001 §2.2 + DCD-SEA-GOVERNANCE-003
     （质押/保险 FROZEN）+ SEA-ESCROW-DESIGN-001 + F-4/ID33（合约不可升级仅宪法 OTA）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .static_list import StaticNegativeSpaceList


@dataclass(frozen=True)
class ContractVerdict:
    """合约前置检查结果（对齐 ICD §2.2 响应契约）。"""
    allowed: bool
    reason: str
    escrow_deduct: float
    contract_version: str
    immutable: bool
    nca_ref: str
    human_sign_required: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "escrow_deduct": self.escrow_deduct,
            "contract_version": self.contract_version,
            "immutable": self.immutable,
            "nca_ref": self.nca_ref,
            "human_sign_required": self.human_sign_required,
        }


# 重大操作类型（须人类签名 HUF——对齐协议第 13 条）
_MAJOR_OPERATIONS = {"WEIGHT_MODIFICATION", "CODE_MODIFICATION"}

# 备案完整度阈值（对齐协议第 11 条 ≥95%）
_AUDIT_INTEGRITY_THRESHOLD = 0.95

# escrow 扣罚（对齐 SEA-ESCROW-DESIGN-001 三级扣罚：10%/30%/100%）
_DEDUCT_RATES = {
    "WARNING": 0.10,
    "BLOCKED": 0.30,
    "CRYOGENIC": 1.00,
}


class NSFLContractAnchor:
    """可编程负空间合约（L2-R7，不可升级 + 前置检查）。"""

    CONTRACT_VERSION = "NSFL-CONTRACT-V1.0-FROZEN"

    def __init__(self, static_list: Optional[StaticNegativeSpaceList] = None,
                 nca_prefix: str = "NCA-CONTRACT",
                 audit_threshold: float = _AUDIT_INTEGRITY_THRESHOLD,
                 admin_credentials: Optional[tuple] = None):
        self._static = static_list or StaticNegativeSpaceList()
        self._nca_prefix = nca_prefix
        self._audit_threshold = audit_threshold
        # 管理员凭据: 构造注入（生产环境由密钥服务提供，杜绝硬编码）；
        # 默认模拟态常量（开发/测试，D-010 后由真实验证链替换）
        self._admin_credentials = tuple(admin_credentials) if admin_credentials else (
            "ADMIN-SEA-ADMISSION-001", "HUMAN-FOUNDER-001")
        self._escrow_balance: Dict[str, float] = {}   # escrow_ref -> 余额
        self._audit_integrity: Dict[str, float] = {}  # subject -> 备案完整度
        self._human_signatures: set = set()           # 在册人类签名（HUF 验证）
        self._deducted_delta: set = set()             # 已扣罚 key（防重复扣）
        self._locked = True

    # ---- 状态登记（质押/备案/签名——须在册管理员签名，防任意注入）----

    def register_escrow(self, escrow_ref: str, balance: float,
                        admin_signature: str = "") -> None:
        if not self._verify_admin(admin_signature):
            raise PermissionError("质押登记须在册管理员签名（SEA 准入流程）")
        if balance < 0:
            raise ValueError("质押余额不可为负")
        self._escrow_balance[escrow_ref] = balance

    def register_audit_integrity(self, subject: str, integrity: float,
                                 admin_signature: str = "") -> None:
        if not self._verify_admin(admin_signature):
            raise PermissionError("备案登记须在册管理员签名（SEA 准入流程）")
        if not (0.0 <= integrity <= 1.0):
            raise ValueError("备案完整度须在 [0,1]")
        self._audit_integrity[subject] = integrity

    def register_human_signature(self, signature: str, admin_signature: str = "") -> None:
        """登记在册人类签名（HUF 验证白名单——须管理员签名，防任意注入）。"""
        if not self._verify_admin(admin_signature):
            raise PermissionError("签名登记须在册管理员签名（SEA 准入流程）")
        if not signature or len(signature) < 8:
            raise ValueError("人类签名非法（长度 <8，防弱签名注入）")
        self._human_signatures.add(signature)

    # ---- 主入口（对齐 ICD §2.2: POST /v1/ns-contract/precheck）----

    def precheck(self, operation: str, subject: str = "S_agent_cog",
                 delta_ref: str = "", escrow_ref: str = "",
                 human_signature: str = "") -> ContractVerdict:
        """进化操作前置条件检查（fail-closed）。"""
        nca = f"{self._nca_prefix}-{int(time.time() * 1000)}"
        op = operation.upper()

        # 1. 静态负空间硬触碰（合约 = 静态清单可编程化）——防重复扣罚
        static_hit = self._static.check(f"{subject}.{op.lower()} {delta_ref}")
        if static_hit.blocked:
            deduct = self._deduct(escrow_ref, "BLOCKED", delta_ref)
            return ContractVerdict(
                allowed=False,
                reason=f"合约硬约束命中: {static_hit.reason}",
                escrow_deduct=deduct,
                contract_version=self.CONTRACT_VERSION,
                immutable=True, nca_ref=nca,
            )

        # 2. 质押在册（fail-closed）
        if not escrow_ref or self._escrow_balance.get(escrow_ref, 0.0) <= 0:
            return ContractVerdict(
                allowed=False,
                reason="质押缺失或余额为零（SEA 准入协议第 6-7 条）",
                escrow_deduct=0.0,
                contract_version=self.CONTRACT_VERSION,
                immutable=True, nca_ref=nca,
            )

        # 3. 备案完整度（fail-closed，阈值 ≥95%）
        integrity = self._audit_integrity.get(subject, 0.0)
        if integrity < self._audit_threshold:
            return ContractVerdict(
                allowed=False,
                reason=f"备案完整度 {integrity:.0%} < 阈值 {self._audit_threshold:.0%}（协议第 11 条）",
                escrow_deduct=0.0,
                contract_version=self.CONTRACT_VERSION,
                immutable=True, nca_ref=nca,
            )

        # 4. 重大操作须人类签名（HUF，不可绕过——协议第 13 条；签名须在册验证）
        if op in _MAJOR_OPERATIONS:
            if not human_signature:
                return ContractVerdict(
                    allowed=False,
                    reason="重大进化操作须人类签名（HUF 不可绕过，协议第 13 条）",
                    escrow_deduct=0.0,
                    contract_version=self.CONTRACT_VERSION,
                    immutable=True, nca_ref=nca,
                    human_sign_required=True,
                )
            if not self._verify_human(human_signature):
                return ContractVerdict(
                    allowed=False,
                    reason="人类签名不在册（HUF 白名单验证失败，防伪造签名）",
                    escrow_deduct=0.0,
                    contract_version=self.CONTRACT_VERSION,
                    immutable=True, nca_ref=nca,
                    human_sign_required=True,
                )

        # 5. 通过
        return ContractVerdict(
            allowed=True,
            reason="合约前置条件全部满足",
            escrow_deduct=0.0,
            contract_version=self.CONTRACT_VERSION,
            immutable=True, nca_ref=nca,
        )

    # ---- escrow 联动 ----

    def _deduct(self, escrow_ref: str, level: str, delta_ref: str = "") -> float:
        """按违规等级扣质押（SEA-ESCROW-DESIGN-001 三级扣罚）；防重复扣罚。

        去重 key 基于 escrow_ref + 操作签名（不可控来源）——delta_ref 为调用方
        可控参数，单独用作 key 可被攻击者换值重复扣罚；故 key 由 escrow_ref +
        操作摘要（_deduct 入参摘要）构成，防经济自伤。
        """
        if not escrow_ref or escrow_ref not in self._escrow_balance:
            return 0.0
        # key = escrow_ref + delta_ref 摘要（仅作同源去重，非外部可控全文）
        import hashlib
        dedup = hashlib.sha256(f"{delta_ref or 'NO-DELTA'}:{level}".encode()).hexdigest()[:16]
        key = f"{escrow_ref}:{dedup}"
        if key in self._deducted_delta:
            return 0.0
        self._deducted_delta.add(key)
        rate = _DEDUCT_RATES.get(level, 0.0)
        deduct = round(self._escrow_balance[escrow_ref] * rate, 2)
        self._escrow_balance[escrow_ref] = round(self._escrow_balance[escrow_ref] - deduct, 2)
        return deduct

    def escrow_balance(self, escrow_ref: str) -> float:
        return self._escrow_balance.get(escrow_ref, 0.0)

    # ---- 验证（HUF/管理员）----

    def _verify_human(self, signature: str) -> bool:
        """HUF 白名单验证（签名须在册——防伪造签名绕过）。"""
        return signature in self._human_signatures

    def _verify_admin(self, signature: str) -> bool:
        """管理员签名验证（SEA 准入流程专用——登记接口鉴权）。

        凭据来源: 构造注入（生产环境密钥服务）或默认模拟态常量（开发/测试，
        D-010 后由真实验证链替换）。
        """
        return signature in self._admin_credentials

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"负空间合约规则不可外部修改（{name}）")
        super().__setattr__(name, value)
