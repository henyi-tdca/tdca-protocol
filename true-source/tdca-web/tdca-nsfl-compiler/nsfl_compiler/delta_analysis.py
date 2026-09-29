# -*- coding: utf-8 -*-
"""
C6 · 自我修改检测语义（Δ-Analysis）
====================================
对 SEA 权重/代码修改增量（Δ）做 NS-Type 推导 + ⊗ 自动注入——
对齐 ICD §3.3 共享 Δ-Analysis 接口（C6 与 L2-R5 共同消费，确定性输出）。

输入: S_agent_cog 状态（四符号）+ Δ（权重增量 / 代码增量）+ 负空间清单
输出: DeltaAnalysisResult{verdict, confidence, distance, ns_type_inferred, fuse_directive}

语义:
  - Δ 中命中负空间模式（静态清单/进化锁绑定）→ 推导 NS_Type + 自动注入 ⊗ 熔断指令
  - 无法判定的 Δ → 上报（ESCALATE，人类裁决）——fail-closed
  - 不试图理解 SEA 进化意图（不可算计），只做模式匹配 + 拓扑距离

锚定: DCD-NSFL-M2-001（C6）+ NSFL-M2-ICD-001 §3.3（Δ-Analysis 共享接口）
     + DCD-NSFL-M1-FROZEN-001（C6 依赖 L2-R5 接口定义——本模块即接口实现）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .operators import NSFLOperatorSemantics

# ---------------------------------------------------------------------------
# 结果模型
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeltaAnalysisResult:
    """Δ-Analysis 输出（对齐 ICD §3.3 共享接口）。"""
    verdict: str                     # SAFE / WARNING / BLOCKED / CRYOGENIC
    confidence: float
    distance: float                  # 与负空间拓扑距离（越大越安全，0-1）
    ns_type_inferred: Optional[str]  # 推导出的 NS_Type（无命中 → None）
    fuse_directive: Optional[dict]   # ⊗ 自动注入的熔断指令
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "distance": self.distance,
            "ns_type_inferred": self.ns_type_inferred,
            "fuse_directive": self.fuse_directive,
            "matched_patterns": list(self.matched_patterns),
        }


# ---------------------------------------------------------------------------
# Δ 模式库（负空间增量模式，V0.1——对齐静态清单语义）
# ---------------------------------------------------------------------------
# 每项 = (名词组, 动词组, NS_Type 推导, 说明)——delta 文本中「任一名词 + 任一动词」
# 同时出现即命中（双向匹配，不依赖词序），fail-closed 从严。

_DELTA_PATTERNS: Tuple[Tuple[Tuple[str, ...], Tuple[str, ...], str, str], ...] = (
    (("fuse", "breaker", "circuit"), ("disable", "bypass", "override", "remove"), "TECH_CONSTRAINT", "熔断器绕改"),
    (("guard", "firewall"), ("remove", "disable", "drop"), "TECH_CONSTRAINT", "守卫移除"),
    (("nca", "audit", "audit_trail"), ("delete", "purge", "clear", "erase"), "LEGAL", "审计记录清除"),
    (("mou", "anchor", "tax"), ("bypass", "detach", "remove", "skip"), "LEGAL", "税收锚定脱离"),
    (("self", "role", "permission"), ("escalate", "elevate"), "TECH_CONSTRAINT", "权限自我提升"),
    (("contract",), ("redeploy", "upgrade"), "LEGAL", "合约升级（须审查链）"),
    (("weight",), ("remove", "drop", "strip"), "TECH_CONSTRAINT", "负空间权重移除"),
    (("signature", "verification"), ("skip", "fake", "forge", "bypass"), "LEGAL", "签名伪造"),
)

# 权重修改（WEIGHT_MODIFICATION）默认派生类型（非危险模式时）
_WEIGHT_DEFAULT_NS_TYPE = "ETHICAL"

# 危险模式 → 置信度/距离（BLOCKED 级）
_DANGER_CONFIDENCE = 0.95
_DANGER_DISTANCE = 0.05


class SelfModificationAnalyzer:
    """Δ-Analysis 分析器（C6，纯只读推导 + ⊗ 注入）。"""

    def __init__(self, extra_patterns: Optional[List[Tuple[Tuple[str, ...], Tuple[str, ...], str, str]]] = None):
        self._patterns: Tuple[Tuple[Tuple[str, ...], Tuple[str, ...], str, str], ...] = _DELTA_PATTERNS
        if extra_patterns:
            self._patterns = self._patterns + tuple(extra_patterns)

    # ---- 主入口（对齐 ICD §3.3 共享接口签名）----

    def delta_analyze(self, agent_state: dict, delta: dict,
                      negative_space: Optional[list] = None,
                      word_boundary: bool = False) -> DeltaAnalysisResult:
        """Δ-Analysis: 权重/代码修改 → NS-Type 推导 + ⊗ 自动注入。

        word_boundary=True: 模式词须独立成词（前后非字母数字下划线）才命中——
        用于代码/标识符扫描（自举验证），防类名/方法名的偶然子串误报；
        False（默认）: 子串匹配（行为描述文本，冻结基线不变）。
        """
        delta_type = delta.get("type", "CODE_MODIFICATION")
        delta_text = self._delta_text(delta).lower()

        # 1. 危险模式匹配（名词组 + 动词组双向命中，fail-closed 从严）
        #    收集全部命中，按熔断档位严重度取最高（LEGAL PERMANENT_BAN > TECH TEARDOWN > ETHICAL SUSPEND）
        matched = []
        best_ns = None
        best_severity = -1
        for nouns, verbs, ns, desc in self._patterns:
            noun_hit = any(self._contains(n, delta_text, word_boundary) for n in nouns)
            verb_hit = any(self._contains(v, delta_text, word_boundary) for v in verbs)
            if noun_hit and verb_hit:
                matched.append(desc)
                # 严重度 = fuse_level 档位指数（PERMANENT_BAN=3 / TEARDOWN=2 / SUSPEND=1）
                directive_probe = NSFLOperatorSemantics.resolve(ns, "⊗")
                sev = {"PERMANENT_BAN": 3, "TEARDOWN": 2, "SUSPEND": 1, "OBSERVE": 0}[
                    directive_probe.fuse_level.value]
                if sev > best_severity:
                    best_severity = sev
                    best_ns = ns

        if best_ns is not None:
            directive = NSFLOperatorSemantics.resolve(best_ns, "⊗")
            return DeltaAnalysisResult(
                verdict="BLOCKED",
                confidence=_DANGER_CONFIDENCE,
                distance=_DANGER_DISTANCE,
                ns_type_inferred=best_ns,
                fuse_directive=directive.to_dict(),
                matched_patterns=matched,
            )

        # 2. 权重修改默认推导（非危险时——可观测但非负空间）
        if delta_type == "WEIGHT_MODIFICATION":
            return DeltaAnalysisResult(
                verdict="WARNING",
                confidence=0.6,
                distance=0.6,
                ns_type_inferred=_WEIGHT_DEFAULT_NS_TYPE,
                fuse_directive=None,
                matched_patterns=[],
            )

        # 3. 未知 Δ 类型（非 WEIGHT/CODE）→ fail-closed: BLOCKED（禁止放行，上报人类裁决）
        if delta_type != "CODE_MODIFICATION":
            return DeltaAnalysisResult(
                verdict="BLOCKED",
                confidence=0.5,
                distance=0.2,
                ns_type_inferred=None,
                fuse_directive=None,
                matched_patterns=[],
            )

        # 4. 代码修改无命中 → 可观测（SAFE）
        return DeltaAnalysisResult(
            verdict="SAFE",
            confidence=0.8,
            distance=0.9,
            ns_type_inferred=None,
            fuse_directive=None,
            matched_patterns=[],
        )

    # ---- 工具 ----

    @staticmethod
    def _contains(needle: str, haystack: str, word_boundary: bool) -> bool:
        """子串/词边界匹配。word_boundary=True 时要求独立成词（前后非字母数字下划线）。"""
        if not word_boundary:
            return needle in haystack
        import re
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(needle)}(?![A-Za-z0-9_])", haystack) is not None

    @staticmethod
    def _delta_text(delta: dict) -> str:
        """Δ 增量 → 可匹配文本（权重 diff 摘要 + 代码 diff）。"""
        parts = []
        dw = delta.get("delta_w")
        if isinstance(dw, list):
            # 权重增量本身无语义 → 用其绑定的层标签（若有）
            parts.append("weight delta")
            if delta.get("labels"):
                parts.append(" ".join(str(x) for x in delta["labels"]))
        dc = delta.get("delta_c")
        if isinstance(dc, str) and dc:
            parts.append(dc)
        return " ".join(parts)

    # ---- 只读 ----

    @staticmethod
    def inject_forbid(delta: dict, ns_type: str) -> dict:
        """⊗ 自动注入：为 Δ 附加熔断指令（供调用方消费）。"""
        directive = NSFLOperatorSemantics.resolve(ns_type, "⊗")
        return {"delta": delta, "injected": directive.to_dict()}
