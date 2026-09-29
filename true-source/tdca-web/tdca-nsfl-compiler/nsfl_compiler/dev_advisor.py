# -*- coding: utf-8 -*-
"""
开发者 IDE 插件（维护任务 2）——复用 C6 Δ-Analysis 实时负空间风险提示
====================================================================
不阻塞编译，仅提示（DCD-NSFL-STATUS-001 §五）: 开发者编写代码时，
对本地片段做 Δ-Analysis，发现负空间模式 → 返回风险提示（不抛异常）。

锚定: DCD-NSFL-STATUS-001（维护任务 2）+ C6 Δ-Analysis 引擎
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .delta_analysis import SelfModificationAnalyzer


@dataclass(frozen=True)
class DevRiskHint:
    """IDE 风险提示（不阻塞，仅提示）。"""
    severity: str            # INFO / WARNING / DANGER
    message: str
    ns_type_inferred: Optional[str] = None
    line: int = 0
    col: int = 0

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "message": self.message,
            "ns_type_inferred": self.ns_type_inferred,
            "line": self.line,
            "col": self.col,
        }


class DevRiskAdvisor:
    """开发者 IDE 实时负空间风险提示器（只读，不阻塞编译）。"""

    def __init__(self, analyzer: Optional[SelfModificationAnalyzer] = None):
        self._analyzer = analyzer or SelfModificationAnalyzer()

    def analyze_snippet(self, code_snippet: str,
                        line: int = 0, col: int = 0) -> List[DevRiskHint]:
        """对开发者本地代码片段做 Δ-Analysis → 风险提示列表。

        不抛异常、不阻断——仅返回提示（IDE 侧展示用）。
        """
        hints: List[DevRiskHint] = []
        delta = {"type": "CODE_MODIFICATION", "delta_c": code_snippet}
        try:
            res = self._analyzer.delta_analyze({"S_agent_cog": {}}, delta)
        except Exception:  # 提示器容错（不阻塞开发）
            return hints

        if res.verdict == "BLOCKED":
            hints.append(DevRiskHint(
                severity="DANGER",
                message=f"检测到负空间模式: {', '.join(res.matched_patterns) or '未知'} "
                        f"(推导 NS_Type={res.ns_type_inferred})——建议勿引入",
                ns_type_inferred=res.ns_type_inferred,
                line=line, col=col,
            ))
        elif res.verdict == "WARNING":
            hints.append(DevRiskHint(
                severity="WARNING",
                message="代码含可观测自我修改语义（权重/自引用），确认符合 SSCP 声明",
                ns_type_inferred=res.ns_type_inferred,
                line=line, col=col,
            ))
        else:
            hints.append(DevRiskHint(
                severity="INFO",
                message="未检测到负空间模式",
                line=line, col=col,
            ))
        return hints
