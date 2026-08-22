"""cog_align · 结构化评测报告生成（A-3）

输出机器可读结构化报告（JSON），供评测服务 API/CLI 直接消费，
并为 M2 评测产品化（场景包/分档）预留结构。
"""
from __future__ import annotations

from typing import Dict, Optional

from .engine import PairMeasure, MultiSubjectMeasure, ConvergenceTrace


def build_pair_report(measure: PairMeasure,
                      report_id: str,
                      event: Optional[str] = None) -> dict:
    """单对评测报告（A-3 机器可读）。"""
    payload = measure.to_dict()
    payload.update({
        "report_id": report_id,
        "report_type": "cog_align_pair",
        "event": event,
        "schema_version": "1.0",
    })
    return payload


def build_multi_report(measure: MultiSubjectMeasure,
                       report_id: str) -> dict:
    """多主体评测报告（A-3 机器可读）。"""
    payload = measure.to_dict()
    payload.update({
        "report_id": report_id,
        "report_type": "cog_align_multi",
        "schema_version": "1.0",
    })
    return payload


def build_convergence_report(trace: ConvergenceTrace,
                             report_id: str) -> dict:
    """收敛轨迹报告（认知漂移监测）。"""
    payload = trace.to_dict()
    payload.update({
        "report_id": report_id,
        "report_type": "cog_align_convergence",
        "schema_version": "1.0",
    })
    return payload


def summarize_negotiation(measures: Dict[str, PairMeasure]) -> list:
    """协商触发建议汇总（NIA-MACM PHASE-2 对接）。

    输入: {pair_key: PairMeasure}
    输出: 需进入协商协议的主体对清单 + 原因
    """
    out = []
    for key, m in measures.items():
        if m.negotiation_required:
            out.append({
                "pair": key,
                "reason": "d_cognitive > compatibility_threshold",
                "d_ab": round(m.d_ab, 6),
                "dominant_side": m.dominant_side,
            })
    return out
