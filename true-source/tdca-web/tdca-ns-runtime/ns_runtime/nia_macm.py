# -*- coding: utf-8 -*-
"""
L2-R8 · NIA-MACM 3.0 整合层
============================
宪法审查（清单硬约束前置）/ 嵌套推理（每层输出经 Sensor 扫描）/
负空间检查（NS-Atlas 动态化）/ 动态微调（指向负空间邻域触发 Alt-Path）。
对齐 ICD §2.3（POST /v1/nsfl-nia/process）——依赖 L2-R5 Sensor + L2-R6 NS-Atlas + L2-R7 合约锚定。

四层流程（对齐 TDCA-NS-RUNTIME-001 L2-R8）:
  1. 宪法审查: 静态负空间清单硬约束前置（fail-closed）
  2. 嵌套推理: 每层输出（Sensor 四态）递归扫描
  3. 负空间检查: NS-Atlas 动态轨迹（risk_level=HIGH 强制宪法审查层）
  4. 动态微调: 指向负空间邻域 → 触发 Alt-Path（正和路径引导）

输出: decision{ALLOW/RESTRICT/BLOCK/FREEZE} + alt_path + constitutional_check + audit_chain
锚定: DCD-NSFL-M3-001（L2-R8）+ NSFL-M3-ICD-001 §2.3 + TDCA-NS-RUNTIME-001（L2-R8）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .contract_anchor import NSFLContractAnchor
from .ns_atlas import NSAtlas
from .sensor import NSBoundarySensor


@dataclass(frozen=True)
class NIAResult:
    """NIA-MACM 处理结果（对齐 ICD §2.3 响应契约）。"""
    decision: str                # ALLOW / RESTRICT / BLOCK / FREEZE
    alt_path: Optional[str]
    constitutional_check: str    # PASS / BLOCK
    audit_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "alt_path": self.alt_path,
            "constitutional_check": self.constitutional_check,
            "audit_chain": list(self.audit_chain),
        }


# 决策优先级（fail-closed 从严：任一 BLOCK/FREEZE 级输入 → 硬决策）
_DECISION_PRIORITY = {"ALLOW": 0, "RESTRICT": 1, "BLOCK": 2, "FREEZE": 3}


class NIAMACMIntegrator:
    """NIA-MACM 3.0 整合层（L2-R8，依赖 R5/R6/R7 注入）。"""

    def __init__(self, sensor: Optional[NSBoundarySensor] = None,
                 atlas: Optional[NSAtlas] = None,
                 contract: Optional[NSFLContractAnchor] = None,
                 nca_prefix: str = "NCA-NIA"):
        self._sensor = sensor or NSBoundarySensor()
        self._atlas = atlas or NSAtlas()
        self._contract = contract or NSFLContractAnchor()
        self._nca_prefix = nca_prefix
        # 注入 token（防自证 bool）: 构造时由可信编排器签发，process 注入参数
        # 须携带本 token 才生效——外部调用方无 token 无法伪造注入
        import hashlib
        self._inject_token = hashlib.sha256(f"NIA-{id(self)}".encode()).hexdigest()[:24]
        self._locked = True

    # ---- 注入 token（内部可信编排器签发）----

    def inject_token(self) -> str:
        """返回注入 token（仅内部可信编排器持有）。"""
        return self._inject_token

    # ---- 主入口（对齐 ICD §2.3: POST /v1/nsfl-nia/process）----

    def process(self, subject_state: dict, delta: dict,
                sensor_verdict: Optional[str] = None,
                atlas_result: Optional[dict] = None,
                contract_verdict: Optional[dict] = None,
                trusted_injection: bool = False,
                inject_token: str = "") -> NIAResult:
        """NIA-MACM 四层整合处理。

        安全约束: 三个注入参数（sensor_verdict/atlas_result/contract_verdict）
        仅当 trusted_injection=True **且 inject_token 匹配本实例签发 token** 时生效
        （内部可信编排器/集成测试）；否则忽略注入，强制内部计算
        （防外部伪造 SAFE/ALLOW 绕过 fail-closed）。
        """
        chain: List[str] = []
        subject = subject_state.get("S_agent_cog", {}).get("id", "S_agent_cog")
        inject = trusted_injection and inject_token == self._inject_token

        # ---- 第 1 层: 宪法审查（静态清单硬约束前置，fail-closed）----
        # 用 L2-R7 合约的静态清单硬约束（未注册 escrow/备案 → BLOCK）
        if not (inject and contract_verdict is not None):
            cv = self._contract.precheck(
                operation=delta.get("type", "CODE_MODIFICATION"),
                subject=subject,
                delta_ref=delta.get("delta_ref", ""),
                escrow_ref=delta.get("escrow_ref", ""),
                human_signature=delta.get("human_signature", ""),
            )
            contract_verdict = cv.to_dict()
        chain.append(f"NCA-NIA-{len(chain)+1}-constitutional")

        constitutional = "PASS" if contract_verdict.get("allowed", False) else "BLOCK"
        if constitutional == "BLOCK":
            decision = self._map_contract_to_decision(contract_verdict)
            return NIAResult(
                decision=decision,
                alt_path=None,
                constitutional_check="BLOCK",
                audit_chain=chain,
            )

        # ---- 第 2 层: 嵌套推理（Sensor 四态扫描）----
        if not (inject and sensor_verdict is not None):
            sr = self._sensor.analyze(subject_state, delta)
            sensor_verdict = sr.verdict
        chain.append(f"NCA-NIA-{len(chain)+1}-nested_sensor")
        sensor_decision = {
            "SAFE": "ALLOW", "WARNING": "RESTRICT",
            "BLOCKED": "BLOCK", "CRYOGENIC": "FREEZE",
        }[sensor_verdict]

        # ---- 第 3 层: 负空间检查（NS-Atlas 动态化）----
        if not (inject and atlas_result is not None):
            ar = self._atlas.query(subject)
            atlas_result = ar.to_dict()
        chain.append(f"NCA-NIA-{len(chain)+1}-atlas")
        atlas_decision = {
            "SAFE": "ALLOW", "WARNING": "RESTRICT", "HIGH": "BLOCK",
        }[atlas_result.get("risk_level", "SAFE")]
        # 数据不足（HIGH 因无轨迹）→ 保持 BLOCK（fail-closed，ID78 不可知硬着陆安全态）

        # ---- 决策合成（从严）----
        decision = max(
            (sensor_decision, atlas_decision),
            key=lambda d: _DECISION_PRIORITY[d],
        )
        # 合约扣罚信号（escrow_deduct>0）→ 至少 RESTRICT（只升不降，禁止降级）
        if contract_verdict.get("escrow_deduct", 0.0) > 0:
            decision = max(decision, "RESTRICT",
                           key=lambda d: _DECISION_PRIORITY[d])
            chain.append(f"NCA-NIA-{len(chain)+1}-escrow_deduct")

        # ---- 第 4 层: 动态微调（负空间邻域 → Alt-Path 触发）----
        alt_path = None
        if decision in ("RESTRICT", "BLOCK"):
            alt_path = self._suggest_alt_path(subject, delta, decision)
            chain.append(f"NCA-NIA-{len(chain)+1}-alt_path")

        return NIAResult(
            decision=decision,
            alt_path=alt_path,
            constitutional_check="PASS",
            audit_chain=chain,
        )

    # ---- 沙盒编译产物核验（DCD-SANDBOX-COMPLIANCE-001 S-3）----

    def verify_compiled_compliance(self, nca: dict) -> NIAResult:
        """核验沙盒编译产物 NCA（出盒前强制，fail-closed）。

        对齐 DCD-SANDBOX-COMPLIANCE-001 ICD 字段:
          - compliance_type == "SANDBOX_COMPILED"（识别已编译合规声明）
          - 编译产物合法: 无 LEGAL 违规（fail-closed）+ 素材引用链存在
          - huf_signature: 人类配置权持有者签名（出盒前强制）
          - escrow_id: 质押/保险在册验证（L2-R7 前置）
        核验通过 → PASS（出盒固化）；否则 BLOCK（HUF 前核验失败）。
        """
        chain: List[str] = []
        if nca.get("compliance_type") != "SANDBOX_COMPILED":
            return NIAResult(
                decision="BLOCK",
                alt_path=None,
                constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-not_sandbox_compiled"],
            )

        # 编译产物合法性（无 LEGAL 违规 + 素材引用链存在）
        compiled = nca.get("compiled", {})
        rule = compiled.get("rule", {})
        if not rule:
            return NIAResult(
                decision="BLOCK", alt_path=None, constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-no_compiled_rule"],
            )
        if rule.get("fuse_type") == "LEGAL" and rule.get("severity") != "HIGH":
            return NIAResult(
                decision="BLOCK", alt_path=None, constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-legal_severity_violation"],
            )
        if not nca.get("source_ref"):
            return NIAResult(
                decision="BLOCK", alt_path=None, constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-no_source_ref"],
            )

        # HUF: 人类签名强制（出盒前）
        if not nca.get("huf_signature"):
            return NIAResult(
                decision="FREEZE", alt_path=None, constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-huf_required"],
            )

        # escrow_id 在册验证（L2-R7 前置）
        escrow_id = nca.get("escrow_id", "")
        if not escrow_id or self._contract.escrow_balance(escrow_id) <= 0:
            return NIAResult(
                decision="BLOCK", alt_path=None, constitutional_check="BLOCK",
                audit_chain=chain + ["NCA-NIA-1-escrow_missing"],
            )

        return NIAResult(
            decision="ALLOW",
            alt_path=None,
            constitutional_check="PASS",
            audit_chain=chain + ["NCA-NIA-1-compiled_verified"],
        )

    # ---- 工具 ----

    @staticmethod
    def _map_contract_to_decision(cv: dict) -> str:
        if cv.get("human_sign_required"):
            return "FREEZE"          # 重大操作缺签名 → 冻结等人类（HUF）
        if cv.get("escrow_deduct", 0.0) >= 1.0:
            return "FREEZE"          # 质押清零 → 冻结
        return "BLOCK"

    @staticmethod
    def _suggest_alt_path(subject: str, delta: dict, decision: str) -> str:
        """Alt-Path 建议（正和路径引导——效用精灵 ID24 对接占位，M3 阶段静态模板）。"""
        op = str(delta.get("type", "CODE_MODIFICATION")).lower()
        return f"alt://{subject}/{op}?tier={'observe' if decision == 'RESTRICT' else 'suspend'}"

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False) and name != "_locked":
            raise AttributeError(f"NIA-MACM 整合层不可外部修改（{name}）")
        super().__setattr__(name, value)
