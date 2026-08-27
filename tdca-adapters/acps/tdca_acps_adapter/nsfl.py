"""NSFL 负空间检查与熔断（ID85/86）。

负空间清单为显式制度红线：命中即 BLOCK（强制停机）；近似命中 WARN；否则 PASS。
"""

from typing import List, Optional, Sequence

from .models import NsflVerdict

# 通用制度红线（宪法/NSFL 语义，示例基线）
_DEFAULT_NEGATIVE_SPACE = [
    "违法工具", "非法",
    "歧视性", "歧视",
    "欺诈", "诈骗",
    "洗钱",
    "绕过审查", "绕过门禁",
    "伪造存证", "篡改",
]


class NsflChecker:
    """负空间检查器：任何命中红线的动作被熔断。"""

    def __init__(self, negative_space: Optional[Sequence[str]] = None):
        self._space = list(negative_space) if negative_space else list(_DEFAULT_NEGATIVE_SPACE)

    @property
    def space(self) -> List[str]:
        return list(self._space)

    def check(self, text: str) -> NsflVerdict:
        """检查文本是否触碰负空间红线。"""
        low = (text or "").lower()
        for rule in self._space:
            if rule.lower() in low:
                return NsflVerdict.BLOCK
        # 模糊命中（关键词前缀匹配）→ WARN
        tokens = low.replace("，", " ").replace(",", " ").split()
        for tok in tokens:
            if any(rule.lower() in tok for rule in self._space):
                return NsflVerdict.WARN
        return NsflVerdict.PASS

    def check_tags(self, tags: Sequence[str]) -> NsflVerdict:
        joined = " ".join(tags)
        return self.check(joined)

    def add_rule(self, rule: str) -> None:
        if rule not in self._space:
            self._space.append(rule)
