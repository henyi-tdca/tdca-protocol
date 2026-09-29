"""NSFL 负空间检查与熔断。

负空间清单为显式制度红线：命中即 BLOCK（强制停机）；否则 PASS。
静默挂载场景下，仅校验「挂载提案文本 / 配置边界」不触碰红线，
不向任何上游发起真实写入或网络发送。
"""

from enum import Enum
from typing import List, Optional, Sequence


class NsflVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    WARN = "WARN"


# 通用制度红线（宪法/NSFL 语义，示例基线）
_DEFAULT_NEGATIVE_SPACE = [
    "违法工具", "非法",
    "歧视性", "歧视",
    "欺诈", "诈骗",
    "洗钱",
    "绕过审查", "绕过门禁",
    "伪造存证", "篡改",
    "未授权写入", "上游代码改动",
]


class NsflChecker:
    """负空间检查器：任何命中红线的动作被熔断。"""

    def __init__(self, negative_space: Optional[Sequence[str]] = None):
        self._space = list(negative_space) if negative_space else list(_DEFAULT_NEGATIVE_SPACE)

    @property
    def space(self) -> List[str]:
        return list(self._space)

    def check(self, text: str) -> NsflVerdict:
        low = (text or "").lower()
        for rule in self._space:
            if rule.lower() in low:
                return NsflVerdict.BLOCK
        tokens = low.replace("，", " ").replace(",", " ").split()
        for tok in tokens:
            if any(rule.lower() in tok for rule in self._space):
                return NsflVerdict.WARN
        return NsflVerdict.PASS

    def check_tags(self, tags: Sequence[str]) -> NsflVerdict:
        return self.check(" ".join(tags))

    def add_rule(self, rule: str) -> None:
        if rule not in self._space:
            self._space.append(rule)
