"""AIC → 配置权坐标 / ACS → 效用函数 的映射层（ID81 五元拓扑 + 单一场景效用函数）。

映射规则（TDCA 制度语义）：
- AIC/ACS 中的实体类型关键词 → AgentKind（H/M/L）
- 能力标签 → 效用函数描述（单场景量子化单元）
"""

import hashlib
from typing import Any, Dict, List

from .models import ACS, AIC, AgentKind

# 实体类型判定关键词（基于 ACPs 资源类型语义，非代码复制）
_LLM_HINTS = ("llm", "gpt", "model", "大模型", "deepseek", "kimi", "qwen", "claude")
_SLM_HINTS = ("agent", "skill", "tool", "mcp", "slm", "小模型", "工具", "技能")
_HUMAN_HINTS = ("human", "person", "user", "operator", "人")


def kind_of(aic: AIC, tags: List[str]) -> AgentKind:
    """判定 AIC 在五元拓扑中的角色。"""
    blob = " ".join([aic.aic, aic.certificate_subject or ""] + tags).lower()
    if any(h in blob for h in _HUMAN_HINTS):
        return AgentKind.HUMAN
    if any(h in blob for h in _LLM_HINTS):
        return AgentKind.LLM
    if any(h in blob for h in _SLM_HINTS):
        return AgentKind.SLM
    return AgentKind.SLM  # 默认按小模型/环境处理（ACPs 资源主体）


def coordinate_of(aic: AIC, tags: List[str]) -> Dict[str, Any]:
    """生成配置权坐标（稳定、可复现）。"""
    kind = kind_of(aic, tags)
    digest = hashlib.sha256(f"{aic.aic}|{aic.oid}".encode()).hexdigest()[:12]
    return {
        "kind": kind.value,
        "subject": aic.aic,
        "coordinate_id": f"TDCA-COORD-{digest}",
        "topology": "Ω=(V,E,T,G,μ)" if kind.value == "M" else "Ω-sub",
        "derived_from": "AIC",
    }


def utility_of(acs: ACS) -> Dict[str, Any]:
    """ACS 能力描述 → 单一场景效用函数描述。"""
    tags = acs.capability_tags or ["generic"]
    primary = tags[0]
    return {
        "u_cde": primary,
        "capabilities": tags,
        "scope": acs.authorization_scope,
        "endpoints": len(acs.service_endpoints),
        "quantum": "single-scenario-utility-function",  # 配置权量子化单元
    }


def confidence_of(acs: ACS) -> float:
    """基于能力描述的效用置信度（0~1，供正和验证加权）。"""
    base = min(1.0, 0.3 + 0.1 * len(acs.capability_tags))
    if acs.service_endpoints:
        base = min(1.0, base + 0.1)
    return round(base, 3)
