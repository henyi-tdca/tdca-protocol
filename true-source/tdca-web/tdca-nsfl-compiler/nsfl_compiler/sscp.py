# -*- coding: utf-8 -*-
"""
C5 · SEA 自约束协议编译（SSCP）——进化锁契约生成
================================================
将 SSCP 声明编译为进化锁契约（LLOCK 格式），对齐 ICD §3.2:
  - 输入: SSCP 语法糖声明（LLOCK 关键字）
  - 输出: LLOCK 契约 JSON（审计完整度阈值 + 降级/冻结动作 + HUF + NS_Type 绑定 + 熔断指令）
  - 只读: 生成契约不写任何文件（BV-3），输出确定性可验证

SSCP 三机制（NSFL-ACCEL-REF-001 §3.3.2，已裁决采纳为 M2 输入）:
  - 进化锁（Evolution Lock）: SEA 权重修改权限与 NCA 审计完整度绑定
  - 负空间疫苗（NS-Vaccine）: 负空间案例作为对抗样本注入（C6/M2 评估）
  - 人类最终签名权（HUF）: 跨版本重大进化须人类配置权持有者签名

锚定: DCD-NSFL-M2-001（C5）+ NSFL-M2-ICD-001 §3.2（LLOCK 契约格式）
     + DCD-NSFL-M1-FROZEN-001（SSCP 输入）+ TDCA-NSFL-COMPILER-001 C5（编译器自约束 L2735）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .operators import FuseLevel, FuseTier, NS_Operator

# ---------------------------------------------------------------------------
# LLOCK 契约数据模型（对齐 ICD §3.2 JSON Schema）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvolutionLockContract:
    """进化锁契约（LLOCK）。"""
    contract_id: str
    subject: str                      # S_agent_cog
    audit_integrity_threshold: float  # NCA 审计完整度阈值 (0-1)
    lock_action: str                  # DEGRADE | FREEZE
    human_sign_required: bool         # HUF
    ns_type_binding: str              # LEGAL / ETHICAL / TECH_CONSTRAINT / ...
    fuse_directive: dict              # 对齐 C2 FuseDirective 结构
    compiler_ref: str = "C5-SSCP-0.1.0"
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "subject": self.subject,
            "evolution_lock": {
                "audit_integrity_threshold": self.audit_integrity_threshold,
                "lock_action": self.lock_action,
                "human_sign_required": self.human_sign_required,
                "ns_type_binding": self.ns_type_binding,
            },
            "compiler_ref": self.compiler_ref,
            "fuse_directive": self.fuse_directive,
        }


@dataclass
class SSCPCompileResult:
    """SSCP 编译结果。"""
    ok: bool
    contract: Optional[EvolutionLockContract] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "contract": self.contract.to_dict() if self.contract else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "duration_ms": round(self.duration_ms, 3),
        }


# ---------------------------------------------------------------------------
# SSCP 语法糖解析
# ---------------------------------------------------------------------------

# LLOCK 声明语法（V0.1）:
#   LLOCK <subject> WITH threshold=<0-1> LOCK_ACTION=<DEGRADE|FREEZE> \
#         HUF=<true|false> NS_TYPE=<NS_Type> [FUSE_LEVEL=<OBSERVE|SUSPEND|TEARDOWN|PERMANENT_BAN>]
_LLOCK_RE = re.compile(
    r"^\s*LLOCK\s+(?P<subject>S_\w+)\s+"
    r"WITH\s+threshold=(?P<threshold>0?\.\d+|1(\.0)?)\s+"
    r"LOCK_ACTION=(?P<action>DEGRADE|FREEZE)\s+"
    r"HUF=(?P<huf>true|false)\s+"
    r"NS_TYPE=(?P<ns_type>[A-Z_]+)"
    r"(\s+FUSE_LEVEL=(?P<level>OBSERVE|SUSPEND|TEARDOWN|PERMANENT_BAN))?"
    r"\s*$",
    re.IGNORECASE,
)

_KNOWN_NS_TYPES = {
    "LEGAL", "DATA_CROSS_BORDER", "TRANSACTION_LIMIT", "SENSITIVE_CONTENT",
    "TECH_CONSTRAINT", "ETHICAL", "EMOTIONAL", "BELIEF",
}

# NS_Type → 默认熔断档位（对齐 C2 ⊗ FORBID 语义）
_NS_TYPE_DEFAULT_LEVEL = {
    "LEGAL": (FuseLevel.PERMANENT_BAN, FuseTier.ATOMIC),
    "DATA_CROSS_BORDER": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "TRANSACTION_LIMIT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "SENSITIVE_CONTENT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "TECH_CONSTRAINT": (FuseLevel.TEARDOWN, FuseTier.HARD),
    "ETHICAL": (FuseLevel.SUSPEND, FuseTier.SOFT),
    "EMOTIONAL": (FuseLevel.SUSPEND, FuseTier.SOFT),
    "BELIEF": (FuseLevel.SUSPEND, FuseTier.SOFT),
}


class SSCPCompiler:
    """SSCP 进化锁契约编译器（C5，纯只读生成）。"""

    def __init__(self, compiler_ref: str = "C5-SSCP-0.1.0"):
        self.compiler_ref = compiler_ref

    def compile(self, source: str) -> SSCPCompileResult:
        """LLOCK 声明 → 进化锁契约（对齐 ICD §3.2 格式）。"""
        t0 = time.perf_counter()
        m = _LLOCK_RE.match(source)
        if m is None:
            return SSCPCompileResult(
                ok=False,
                errors=[f"SSCP 语法错误，无法解析 LLOCK 声明: {source!r}"],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        ns_type = m.group("ns_type").upper()
        if ns_type not in _KNOWN_NS_TYPES:
            return SSCPCompileResult(
                ok=False,
                errors=[f"未知 NS_TYPE: {ns_type!r}（注册表 V1.1 仅含 {sorted(_KNOWN_NS_TYPES)}）"],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        threshold = float(m.group("threshold"))
        if not (0.0 <= threshold <= 1.0):
            return SSCPCompileResult(
                ok=False,
                errors=[f"threshold 须在 [0,1] 区间: {threshold!r}"],
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        # 熔断指令（对齐 C2 FuseDirective：NS_Type → 默认档位）
        level, tier = _NS_TYPE_DEFAULT_LEVEL[ns_type]
        explicit_level = m.group("level")
        if explicit_level is not None:
            level = FuseLevel(explicit_level.upper())
            tier = FuseTier.ATOMIC if level == FuseLevel.PERMANENT_BAN else \
                (FuseTier.HARD if level == FuseLevel.TEARDOWN else FuseTier.SOFT)

        fuse_directive = {
            "operator": NS_Operator.RESTRICT_TIER.value,
            "fuse_level": level.value,
            "tier": tier.value,
            "alt_path": None,
        }

        warnings: List[str] = []
        # LEGAL 绑定强制 HUF + 不可降级（制度底线）
        if ns_type == "LEGAL":
            if m.group("huf").lower() != "true":
                warnings.append("LEGAL 绑定强制 HUF=true（人类最终签名权不可让渡）")
            if level != FuseLevel.PERMANENT_BAN:
                warnings.append("LEGAL 绑定强制 PERMANENT_BAN（ID86 绝对熔断）")
                level, tier = FuseLevel.PERMANENT_BAN, FuseTier.ATOMIC
                fuse_directive = {
                    "operator": NS_Operator.RESTRICT_TIER.value,
                    "fuse_level": level.value,
                    "tier": tier.value,
                    "alt_path": None,
                }

        contract = EvolutionLockContract(
            contract_id=f"LLOCK-{hashlib.sha256(source.strip().encode('utf-8')).hexdigest()[:12]}",
            subject=m.group("subject"),
            audit_integrity_threshold=threshold,
            lock_action=m.group("action").upper(),
            human_sign_required=(m.group("huf").lower() == "true") or ns_type == "LEGAL",
            ns_type_binding=ns_type,
            fuse_directive=fuse_directive,
            compiler_ref=self.compiler_ref,
            created_at=time.time(),
        )

        return SSCPCompileResult(
            ok=True,
            contract=contract,
            warnings=warnings,
            duration_ms=(time.perf_counter() - t0) * 1000,
        )

    # ---- 只读 ----

    def verify(self, contract: EvolutionLockContract) -> bool:
        """契约完整性验证（BV-3 输出验证）。"""
        if not contract.contract_id or not contract.subject:
            return False
        if not (0.0 <= contract.audit_integrity_threshold <= 1.0):
            return False
        if contract.lock_action not in ("DEGRADE", "FREEZE"):
            return False
        if contract.ns_type_binding not in _KNOWN_NS_TYPES:
            return False
        fd = contract.fuse_directive or {}
        # 对齐 C2 FuseDirective 结构：operator/tier 必填
        if fd.get("operator") not in ("FORBID", "RESTRICT_TIER", "LIMIT_MAX", "LIMIT_MIN", "LIMIT_EQ"):
            return False
        if contract.ns_type_binding == "LEGAL":
            # LEGAL 制度底线（ID86）：HUF 强制 + PERMANENT_BAN/ATOMIC + alt_path 恒 None
            if not contract.human_sign_required:
                return False
            if fd.get("fuse_level") != "PERMANENT_BAN":
                return False
            if fd.get("tier") != "ATOMIC":
                return False
            if fd.get("alt_path") is not None:
                return False
        elif fd.get("alt_path") is not None and fd.get("operator") == "RESTRICT_TIER":
            # 非 LEGAL 的档位约束也禁止逃生路径（对齐 fuse_engine alt=∅ 语义）
            return False
        return True
