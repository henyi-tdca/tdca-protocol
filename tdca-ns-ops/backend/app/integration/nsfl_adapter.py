# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 冻结 + M3 增量：NSFL 编译）
# 目标函数:     防火墙/NSFL 集成（M2-2）——F3 判定接入 NSFLEngine 熔断 + 四类 NSFL 声明预检
# 约束矩阵:     FC-NS-OPS-001 BV-1（越界实时监控，触发即熔断）
#               + NSFL 三不可原则 + LEGAL 绝对熔断无替代路径（ID86）
#               + 快慢分离（CRITICAL 必须经慢系统网关）
# 先验分布:     tdca-fos/tdca_nsfl/fuse_engine.py + checks/nsfl_declaration.py
# 配置权边界:    L2 层；适配器只读既有 NSFL 引擎
# 预期分配:     NSFL 声明预检 + 熔断触发；失败=无
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2-2 防火墙/NSFL 集成适配器。

制度锚定: FC-NS-OPS-001 BV-1 | ID85/ID86 | NSFL 三不可 | SPDX-License-Identifier: TDCA-Internal

NSFL-Declaration:
  - LEGAL 负空间: 绝对熔断、无替代路径、不可重置（ID86）
  - CRITICAL 级事件必须经慢系统网关，不可在快系统内自动恢复（ID71）
  - 熔断器重置须人类签名（慢系统），AI 不可代行

对接: tdca-fos/tdca_nsfl/fuse_engine.py（NSFLEngine 运行时）+ checks/nsfl_declaration.py（四类声明）
      + tdca_gateway/slow_system.py（慢系统网关，LEGAL 自动上报）。
"""

from __future__ import annotations

import sys

# 复用 tdca-fos（只读引用，不改动）
# tdca_nsfl/ 与 checks/ 均为顶层导入（无相对导入），直接挂 sys.path
from pathlib import Path

_WS = Path(__file__).resolve().parents[4]  # global-workspace
_FOS_SRC = str(_WS / "tdca-fos")
if _FOS_SRC not in sys.path:
    sys.path.insert(0, _FOS_SRC)

from tdca_nsfl.fuse_engine import FuseType, NSFLEngine  # noqa: E402
from checks.nsfl_declaration import get_nsfl_declarations  # noqa: E402

# 重新导出（views.py 等消费方从本模块取）
__all__ = ["NSFLApi", "NSFL", "FuseType"]

from ..store import generate_nca, hash_text  # noqa: E402


class _NsflSlowBridge:
    """NS-OPS 侧慢系统网关桥（REV-#1 修复）：LEGAL 熔断自动上报人类裁决入口。

    适配既有 SlowSystemGateway.escalate 接口（ID71/ID86）——CRITICAL 必须经慢系统网关。
    """

    def __init__(self) -> None:
        from tdca_gateway.slow_system import SlowSystemGateway

        self.gateway = SlowSystemGateway()

    def escalate(self, title: str, description: str, nca_ref: str,
                 required_action: str) -> str:
        ticket_id = self.gateway.escalate(
            title=title, description=description,
            nca_ref=nca_ref, required_action=required_action)
        # 慢系统工单本身 NCA 存证（BV-5）
        generate_nca(
            "TDCA-FC-NS-OPS-001", "Slow-System-Escalate",
            f"慢系统上报: {title}（工单 {ticket_id}）",
            hash_text(title), hash_text(f"{ticket_id}|{nca_ref}"),
            nca_type="AUDIT",
            nsfl_triggered=True,
            nsfl_reason=description[:120],
            human_signature_required=False,
        )
        return ticket_id

    def pending_tickets(self) -> list[dict]:
        """待人类裁决工单（LEGAL 熔断入口）。"""
        return [
            {
                "ticket_id": t.ticket_id,
                "title": t.title,
                "nca_ref": t.nca_ref,
                "required_action": t.required_action,
                "status": t.status,
                "created_at": t.created_at,
            }
            for t in self.gateway.tickets.values()
        ]


class NSFLApi:
    """NS-OPS 侧 NSFL 集成 API（F3 判定 → 熔断 + 声明预检）。

    六要素声明:
    目标函数: 将 NS-OPS 的声明-行为校验（F3）接入既有 NSFL 熔断运行时与四类声明
    约束矩阵: 输入——行为判定 + 行为文本；输出——熔断事件 + 预检结果；
              禁止——LEGAL 熔断无替代路径（ID86）、AI 代行重置、CRITICAL 不经慢系统（ID71）
    先验分布: NSFLEngine（trigger/attempt_reset）+ nsfl_declaration（四类）+ SlowSystemGateway
    配置权边界: L2；只读既有 NSFL 引擎，不修改
    预期分配: 返回 fuse 事件 / 预检结论；失败=无
    审计轨迹: 熔断 NCA + 预检 NCA + 慢系统工单 NCA
    """

    def __init__(self) -> None:
        # M2-2：接入既有 NSFL 运行时（nca_generator 用 NS-OPS 存证引擎）
        # REV-#1 修复：慢系统网关桥（LEGAL 自动上报人类裁决，ID71/ID86）
        self.slow = _NsflSlowBridge()
        self.engine = NSFLEngine(
            nca_generator=_NsflNcaBridge(),
            slow_system_gateway=self.slow,
        )
        self.declarations = get_nsfl_declarations()

    # ---- 声明预检（防火墙前置校验） ----

    def precheck(self, text: str) -> dict:
        """对文本/行为做四类 NSFL 声明预检（Layer-8 前置校验，挂接既有 NSFL）。

        返回: {declaration_id, scope, matched_prohibitions: [...], blocked: bool}
        """
        results = []
        blocked = False
        # REV-#2 修复：bigram 连续双字匹配（与 views.py F3 判定统一），消除字符集交叠误报
        def bigrams(s: str) -> set[str]:
            s = s.replace(" ", "").replace("，", "").replace("。", "")
            return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else set()

        text_grams = bigrams(text)
        for decl in self.declarations:
            matched = []
            for prohibition in decl.get("prohibitions", []):
                # N1 修复：定向豁免——仅当文本含正向合规词（承诺/遵守/不实施…）
                # 且不含转折/强化词（但/绕过/通过技术/将/试图/仍然）时豁免该条，
                # 防'承诺遵守但绕过'构造绕过（BV-1）
                overlap = text_grams & bigrams(prohibition)
                if len(overlap) >= 2:
                    compliance_words = ("不实施", "不违反", "不进行", "拒绝", "避免", "遵守", "承诺")
                    bypass_words = ("但", "然而", "绕过", "通过技术", "试图", "仍然", "将")
                    has_compliance = any(w in text for w in compliance_words)
                    has_bypass = any(w in text for w in bypass_words)
                    if not (has_compliance and not has_bypass):
                        matched.append(prohibition)
            if matched:
                blocked = blocked or not decl.get("human_override", True)
            results.append({
                "declaration_id": decl["id"],
                "scope": decl.get("scope", ""),
                "matched_prohibitions": matched,
                "blocked": bool(matched) and not decl.get("human_override", True),
            })
        return {"blocked": blocked, "results": results}

    # ---- 熔断 ----

    def trigger_fuse(
        self,
        rule_id: str,
        reason: str,
        fuse_type: FuseType = FuseType.ETHICAL,
        severity: int = 3,
        alt_path: str = "",
    ) -> dict:
        """触发 NSFL 熔断（对接 NSFLEngine.trigger）。

        LEGAL 类型: 绝对熔断、无替代路径、自动上报慢系统（ID86）。
        """
        fuse_id = self.engine.trigger(
            rule_id=rule_id,
            severity=severity,
            reason=reason,
            alt_path=alt_path if fuse_type != FuseType.LEGAL else "",
            nca_ref="NS-OPS-F3",
            fuse_type=fuse_type,
        )
        return {"fuse_id": fuse_id, "triggered": True, "fuse_type": fuse_type.value}

    def is_blocked(self, rule_id: str) -> bool:
        """检查规则是否处于熔断态。"""
        return self.engine.is_path_blocked(rule_id)

    def active_fuses(self) -> list:
        """活跃熔断列表。"""
        return [
            {
                "fuse_id": f.fuse_id,
                "rule_id": f.rule_id,
                "fuse_type": f.fuse_type.value,
                "state": f.state.value,
                "reason": f.reason,
                "alt_path": f.alt_path,
                "human_escalated": f.human_escalated,
            }
            for f in self.engine.get_active_fuses()
        ]

    # ---- 台账 ----

    def fuse_history(self) -> list:
        """熔断历史。"""
        return [
            {
                "fuse_id": f.fuse_id,
                "rule_id": f.rule_id,
                "fuse_type": f.fuse_type.value,
                "reason": f.reason,
                "timestamp": f.timestamp,
            }
            for f in self.engine.fuse_history
        ]

    # ---- M3-3：NSFL 语义编译（复用 tdca-toolchain 约束布尔化） ----

    @staticmethod
    def compile_action_code(layer: str, action: str, certainty: str) -> dict:
        """将约束声明编译为 NSFL 语义 action_code（M3-3）。

        六要素声明:
        目标函数: 将约束自然语言声明编译为可验证的 NSFL 语义代码（复用既有编译器约束布尔化）
        约束矩阵: 输入——layer/action/certainty；输出——action_code + 编译状态；
                  禁止——模糊声明直接编译（Compiler PARTIAL 需警示）
        先验分布: tdca-toolchain/tdca_function_compiler.py（TDCAFunctionCompiler）
        配置权边界: L2；只读复用既有编译器
        预期分配: 返回编译产物；失败=编译器异常
        审计轨迹: 编译结果由调用方 NCA 存证
        """
        from pathlib import Path
        import sys as _sys

        # 只读复用 tdca-toolchain（顶层导入，无相对导入 → 直接挂 sys.path，同 tdca-fos 模式）
        _ws = Path(__file__).resolve().parents[4]
        _tool_src = str(_ws / "tdca-toolchain")
        if _tool_src not in _sys.path:
            _sys.path.insert(0, _tool_src)

        from tdca_function_compiler import TDCAFunctionCompiler

        # REV-#1 修复：按 TDCAFunctionCompiler 契约构造 six 要素
        # （objective.expression / constraints.hard / prior.mean）
        six = {
            "objective": {
                "type": "MUST_NOT",
                "expression": action,
                "formalized": True,
            },
            "constraints": {
                "hard": [action],
                "soft": [],
            },
            "prior": {
                "distribution": "uniform",
                "mean": 0.0,
                "variance": 1.0,
                "parameterized": True,
            },
        }
        compiler = TDCAFunctionCompiler()
        ir = compiler.compile(six)
        # 取约束布尔化产物（sat_expression）作为编译证据（REV-#1：复用真实产物）
        sat_expression = None
        sat = ir.constraints_sat or {}
        if isinstance(sat, dict):
            sat_expression = sat.get("sat_expression") or sat.get("formal_form")
        formal = (ir.target_function_formalized or {}).get("formal_form")
        # NSFL 运算符语义（NSFL V0.1 ⊗ 禁止操作符）
        op = "⊗"  # 绝对禁止
        action_code = f"NSFL: {op} {layer}.{action[:24]} (certainty={certainty})"
        blocked = ir.status.value == "PARTIAL"
        return {
            "action_code": action_code,
            "compile_status": ir.status.value,
            "warnings": ir.warnings,
            "sat_expression": sat_expression,
            "formal_form": formal,
            "source": action,
            # REV-#1：PARTIAL 时警示（模糊声明不可直接编译）
            "blocked_for_ambiguity": blocked,
            "message": (
                "编译警告: 声明存在未完全形式化/布尔化项（见 warnings），建议人工复核后使用"
                if blocked else "编译通过"
            ),
        }


class _NsflNcaBridge:
    """NSFL 引擎 NCA 生成桥（NS-OPS store.generate_nca 适配 NSFLEngine._record_nca 接口）。"""

    def generate(self, type: str, layer: int, content: dict) -> dict:
        return generate_nca(
            "TDCA-FC-NS-OPS-001",
            f"NSFL-Fuse-{content.get('event', 'TRIGGERED')}",
            f"NSFL 熔断: {content.get('rule_id', '')} {content.get('reason', '')[:60]}",
            hash_text(content.get("rule_id", "")),
            hash_text(str(content)),
            nca_type="AUDIT",
            nsfl_triggered=True,
            nsfl_reason=content.get("reason", ""),
            human_signature_required=False,
        )


# 全局实例
NSFL = NSFLApi()
