# SPDX-License-Identifier: Apache-2.0
"""
TDCA-FC-012 C-3 Fuse-Adapter
制度锚定: ID89（化学热力学三档熔断）+ UI-006 熔断器联动
Granted-By: TDCA-FC-012-DESIGN-002
NSFL: 熔断 Level-3 永久冻结，不可自动恢复
"""
from typing import Optional


class FuseAdapter:
    """熔断对接（UI-006 前后端联动）"""

    LEVELS = {
        'LEVEL_1': {'retryable': True, 'desc': '软熔断（WARN），可重试 ≤3次'},
        'LEVEL_2': {'retryable': False, 'desc': '硬熔断（BLOCK），需回退'},
        'LEVEL_3': {'retryable': False, 'desc': '紧急熔断（FATAL），永久冻结'},
    }

    def __init__(self, on_fuse: Optional[callable] = None):
        self._on_fuse = on_fuse  # 通知前端 UI-006

    def trigger(self, level: str, reason: str, phase: str) -> dict:
        if level not in self.LEVELS:
            raise ValueError(f"[NSFL-TRIGGER] 非法熔断级别: {level}")
        result = {
            'level': level,
            'desc': self.LEVELS[level]['desc'],
            'reason': reason,
            'phase': phase,
            'retryable': self.LEVELS[level]['retryable'],
        }
        if self._on_fuse:
            self._on_fuse(result)
        return result

    def retry_count(self, history: list) -> int:
        """统计某 Phase 的重试次数"""
        return sum(1 for h in history if h.get('level') == 'LEVEL_1')

    # OPT-C3-002: 相变检测（ID89 化学热力学）— 场景权重 Delta-w 阈值
    def phase_transition_detect(self, scene_weight_delta: float,
                                threshold_upper: float = 0.3,
                                threshold_lower: float = -0.3) -> str:
        """
        场景切换相变检测：
          Δw > threshold_upper → 激活提升（Skill 预加载信号）
          Δw < threshold_lower → 抑制归档（Dreaming 候选信号）
          否则 → 稳定
        """
        if scene_weight_delta > threshold_upper:
            return 'ACTIVATE'
        if scene_weight_delta < threshold_lower:
            return 'SUPPRESS'
        return 'STABLE'
