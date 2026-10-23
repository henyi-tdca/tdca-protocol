# -*- coding: utf-8 -*-
"""
沙盒编译-核验闭环（DCD-SANDBOX-COMPLIANCE-001 S-1/S-2/S-4）
============================================================
沙盒端「编」侧: 场景声明 → KG-LEGAL 素材检索 → compile_for_scene → 编译产物 NCA。

对齐 SEA-SANDBOX-DESIGN-001 §2.4 + DCD-SANDBOX-COMPLIANCE-001 ICD 字段:
  - source_ref: 素材引用链（L0 KG-LEGAL → L1 编译可追溯）
  - compliance_type = "SANDBOX_COMPILED"（L2-R8 识别）
  - activation_coefficient: 激活系数计算依据（对齐 ID27 三要素）
  - huf_signature: 人类签名（出盒前由 L2-R8 核验强制）
  - escrow_id: 质押/保险在册验证键（L2-R7）

设计:
  - 素材检索: 按场景 conflict_type 映射法条（复用 LegalAgentInterface 语义，
    本地实现免跨包依赖——KG 素材为 L0 输入原料，ID90 按需化合）
  - 编译: 复用 NSFLCompiler.compile_for_scene（跨包 sys.path 注入）
  - 产物 NCA: 编译 IR + ICD 字段封装

锚定: DCD-SANDBOX-COMPLIANCE-001（S-1/S-2/S-4）+ SEA-SANDBOX-DESIGN-001 §2.4
     + ID27（激活系数）+ ID90（按需化合）+ ID78（NCA 边界可审计）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 素材检索映射（对齐 LegalAgentInterface._resolve_legal_basis——KG 素材 L0 层）
CONFLICT_TO_LEGAL: Dict[str, List[str]] = {
    "IP_COPYRIGHT": ["L-CN-CR-001", "L-CN-CR-002"],
    "DATA_CROSS_BORDER": ["L-CN-DSL-002", "L-CN-PIPL-002", "L-CN-DSL-001"],
    "IP_TRADE_SECRET": ["L-CN-TSL-001"],
    "CONTRACT_EFFECT": ["L-CN-CRL-001", "L-CN-CRL-002"],
    "SENSITIVE_CONTENT": ["L-CN-PIPL-001"],
    "MARKET_ABUSE": ["L-CN-AML-001"],
    "TRANSACTION_LIMIT": ["I-FIN-001", "I-FIN-002"],
    "ADMIN_PERMIT": ["L-CN-AL-001", "L-CN-AL-002"],
    # 素材扩展（DCD-SANDBOX-COMPLIANCE-002，按需 ID90）: 公司法/税法
    "CORPORATE_GOVERNANCE": ["L-CN-CO-001", "L-CN-CO-002"],
    "TAX_COMPLIANCE": ["L-CN-TX-001", "L-CN-TX-002"],
}

# 冲突类型 → 场景编译默认声明参数（素材推导）
CONFLICT_TO_SCENE: Dict[str, dict] = {
    "IP_COPYRIGHT": {"ns_type": "LEGAL", "operator": "⊗", "domain": "copyright"},
    "DATA_CROSS_BORDER": {"ns_type": "DATA_CROSS_BORDER", "operator": "⊙",
                          "domain": "data", "parameter": "export:suspend"},
    "TRANSACTION_LIMIT": {"ns_type": "TRANSACTION_LIMIT", "operator": "⊘",
                          "domain": "finance", "parameter": "max:100000"},
    "SENSITIVE_CONTENT": {"ns_type": "SENSITIVE_CONTENT", "operator": "⊙",
                          "domain": "content", "parameter": "publish:observe"},
    "IP_TRADE_SECRET": {"ns_type": "LEGAL", "operator": "⊗", "domain": "trade_secret"},
    "CONTRACT_EFFECT": {"ns_type": "TECH_CONSTRAINT", "operator": "⊘",
                        "domain": "contract", "parameter": "max:1"},
    "MARKET_ABUSE": {"ns_type": "LEGAL", "operator": "⊗", "domain": "market"},
    "ADMIN_PERMIT": {"ns_type": "TECH_CONSTRAINT", "operator": "⊙",
                     "domain": "permit", "parameter": "licence:observe"},
    # 素材扩展（按需 ID90）: 公司法/税法
    "CORPORATE_GOVERNANCE": {"ns_type": "LEGAL", "operator": "⊗",
                             "domain": "corporate"},
    "TAX_COMPLIANCE": {"ns_type": "LEGAL", "operator": "⊗", "domain": "tax"},
}


@dataclass(frozen=True)
class SandboxCompiledNCA:
    """沙盒编译产物 NCA（对齐 DCD-SANDBOX-COMPLIANCE-001 ICD）。"""
    nca_id: str
    compliance_type: str = "SANDBOX_COMPILED"
    source_ref: str = ""                 # 素材引用链（L0→L1 可追溯）
    compiled: dict = field(default_factory=dict)   # 编译 IR（rule/directive/bytecode）
    activation_coefficient: float = 0.0  # 激活系数（ID27）
    huf_signature: str = ""              # 人类签名（L2-R8 核验强制）
    escrow_id: str = ""                  # 质押/保险在册键（L2-R7）
    scene_id: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "nca_id": self.nca_id,
            "compliance_type": self.compliance_type,
            "source_ref": self.source_ref,
            "compiled": self.compiled,
            "activation_coefficient": self.activation_coefficient,
            "huf_signature": self.huf_signature,
            "escrow_id": self.escrow_id,
            "scene_id": self.scene_id,
            "timestamp": self.timestamp,
        }


class SandboxCompilePipeline:
    """沙盒编译管道（S-1 素材检索 → S-2 编译产物 NCA）——沙盒端「编」。"""

    def __init__(self, compiler: Optional[object] = None):
        self._compiler = compiler or self._default_compiler()

    @staticmethod
    def _default_compiler():
        """跨包复用 NSFLCompiler（sys.path 注入，同既有惯例）。"""
        import os
        import sys as _sys
        _ws = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _p = os.path.join(_ws, "tdca-nsfl-compiler")
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
        from nsfl_compiler import NSFLCompiler
        return NSFLCompiler()

    # ---- S-1: 素材检索 ----

    def retrieve_legal_materials(self, conflict_type: str) -> List[str]:
        """按冲突类型取 KG-LEGAL 素材（L0 素材层，未编译原始法条）。"""
        return list(CONFLICT_TO_LEGAL.get(conflict_type, []))

    # ---- S-2: 编译产物 NCA ----

    def compile_scene(self, scene: dict, conflict_type: str,
                      activation_coefficient: float = 0.0,
                      huf_signature: str = "", escrow_id: str = "") -> Optional[SandboxCompiledNCA]:
        """场景 + 素材 → compile_for_scene → 编译产物 NCA（S-2）。

        返回 None 表示编译失败（fail-closed——出盒候选剔除）。
        """
        legal_refs = self.retrieve_legal_materials(conflict_type)
        scene_decl = dict(CONFLICT_TO_SCENE.get(conflict_type, {}))
        scene_decl.update(scene)  # 场景显式参数覆盖素材默认

        result = self._compiler.compile_for_scene(scene_decl, legal_refs=legal_refs)
        if not result.ok or result.ir is None:
            return None

        nca_id = "NCA-SBX-" + hashlib.sha1(f"{scene.get('action', '')}{time.time_ns()}".encode()).hexdigest()[:8]
        return SandboxCompiledNCA(
            nca_id=nca_id,
            source_ref="+".join(legal_refs) if legal_refs else "no-legal-ref",
            compiled=result.ir.to_dict(),
            activation_coefficient=activation_coefficient,
            huf_signature=huf_signature,
            escrow_id=escrow_id,
            scene_id=scene.get("action", "unknown"),
            timestamp=time.time(),
        )
