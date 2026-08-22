"""maka_nca · 正和验证插件（DCD-MAKA-COMPOUND-001 M1b）

基于 Maka Event Log 的 UtilityGenie 正和验证——评估工具调用序列是否正和博弈。

正和判定（宪法第五条 C02 正和聚合 + ID84 停机制定理）:
  - 每次 tool_call 成功 + tool_result 有效 = 正向效用贡献
  - 失败/异常 tool_result = 负向（消耗无产出）
  - 会话级正和性 = (成功调用数 − 失败调用数) / 总调用数 ≥ 阈值

制度锚定: 宪法第 5 条（C02 正和聚合）/ ID84（停机制定理：正和支付的充分解）/ ID92
NSFL-Declaration:
  - 正和判定为评测输出（SIMULATED 数据），不构成真实经济结算
  - 不修改 Maka 核心（双向赋能：独立插件包）
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

# 正和阈值（会话级成功占比下限）
POSITIVE_SUM_THRESHOLD = 0.5


@dataclass(frozen=True)
class PositiveSumVerdict:
    """正和验证结果。"""
    session_id: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_ratio: float
    positive_sum: bool          # success_ratio >= 阈值 → 正和
    verdict: str                # POSITIVE_SUM / NEGATIVE_SUM
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_ratio": round(self.success_ratio, 4),
            "positive_sum": self.positive_sum,
            "verdict": self.verdict,
            "recommendation": self.recommendation,
        }


class PositiveSumValidator:
    """UtilityGenie 正和验证插件（M1b）。"""

    def __init__(self, threshold: float = POSITIVE_SUM_THRESHOLD):
        self._threshold = threshold

    def validate(self, events: List[dict],
                 session_id: str = "maka-session") -> PositiveSumVerdict:
        """基于 Event Log 做会话级正和验证。

        统计: tool_call 事件（成功调用）+ tool_result 事件（success 判定）。
        """
        if not events:
            raise ValueError("[NSFL-TRIGGER] 空事件列表——无法验证正和")
        total = 0
        successful = 0
        for ev in events:
            etype = ev.get("type")
            if etype == "tool_call":
                total += 1
                successful += 1 if ev.get("status", "success") == "success" else 0
            elif etype == "tool_result":
                total += 1
                successful += 1 if ev.get("success", True) else 0
        if total == 0:
            return PositiveSumVerdict(
                session_id=session_id, total_calls=0, successful_calls=0,
                failed_calls=0, success_ratio=0.0, positive_sum=False,
                verdict="NO_CALLS", recommendation="会话无工具调用——无正和可验证",
            )
        failed = total - successful
        ratio = successful / total
        positive = ratio >= self._threshold
        return PositiveSumVerdict(
            session_id=session_id, total_calls=total,
            successful_calls=successful, failed_calls=failed,
            success_ratio=ratio, positive_sum=positive,
            verdict="POSITIVE_SUM" if positive else "NEGATIVE_SUM",
            recommendation=(
                "正和：效用净贡献为正，符合宪法 C02 正和聚合——可继续协作"
                if positive else
                f"负和：成功占比 {ratio:.1%} < 阈值 {self._threshold:.0%}——建议停机制定（ID84）或人工复核"
            ),
        )
