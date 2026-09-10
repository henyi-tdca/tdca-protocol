# -*- coding: utf-8 -*-
"""A2A Agent Card ↔ 配置权发现（CDP）适配（G4 余项之一）

制度依据:
  - TDCA 层间规范 §三/§四：A2A → 「配置权发现（CDP）主体描述」候选载体
  - TDCA 内部分析 同源口径：**Card 签名验证的是来源，不验证正和性**
    → 本适配器区分「来源可信（signature）」与「正和可信（需 TDCA 效用精灵）」

映射:
  A2A Agent Card（v1.0：supportedInterfaces / capabilities / skills / securitySchemes / JWS 签名）
    → CDP 主体描述（能力画像 + 配置权边界声明 + 效用拟合占位 + 来源可信标注）
  扩展字段一律 `x-tdca-*` 前缀（前缀隔离，不破坏 Card 规范）

纪律:
  - Card 仅提供"技术语法"；效用拟合/正和性由 TDCA 侧填充（不在 Card 内声明）
  - 来源可信 ≠ 正和可信（显式双字段）
  - 数据性质: 模拟态
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

X_PREFIX = "x-tdca-"


class A2ACardError(Exception):
    """A2A Card 映射纪律违例。"""


def _interfaces(card: Dict[str, Any]) -> List[str]:
    """v1.0: supportedInterfaces[]；兼容 v0.3: 顶层 url。"""
    if isinstance(card.get("supportedInterfaces"), list):
        return [i.get("url") if isinstance(i, dict) else str(i)
                for i in card["supportedInterfaces"]]
    if card.get("url"):
        return [card["url"]]
    return []


def card_to_cdp(card: Dict[str, Any]) -> Dict[str, Any]:
    """A2A Agent Card → CDP 主体描述（发现层登记用）。"""
    if not card.get("name"):
        raise A2ACardError("Card 须含 name")
    ifaces = _interfaces(card)
    if not ifaces:
        raise A2ACardError("Card 须含 supportedInterfaces 或 url（A2A v1.0/v0.3 兼容）")
    caps = card.get("capabilities") or card.get("skills") or []
    if not isinstance(caps, list):
        raise A2ACardError("capabilities/skills 须为数组")

    ext = {k: v for k, v in card.items() if k.startswith(X_PREFIX)}
    boundary = ext.get(f"{X_PREFIX}configRightBoundary", "scene-scoped")
    signature = card.get("signature") or card.get("signatures")

    return {
        "cdp_subject": {
            "agent_ref": card["name"],
            "interfaces": ifaces,
            "capabilities": caps,
            "description": card.get("description", ""),
        },
        "config_right_boundary": boundary,
        # —— 制度点：来源可信与正和可信分离 ——
        "source_trust": {"method": "jws" if signature else "none",
                         "verified_source": bool(signature)},
        "positive_sum_verified": False,      # Card 不证正和；须 TDCA 效用精灵
        "utility_fit": {},                   # 由 TDCA 侧（效用精灵）填充
        "national_agent_id": ext.get(f"{X_PREFIX}nationalAgentId"),
        f"{X_PREFIX}source": "a2a-card",
        f"{X_PREFIX}mapping": {"card.name": "cdp_subject.agent_ref",
                               "card.supportedInterfaces|url": "cdp_subject.interfaces",
                               "card.capabilities|skills": "cdp_subject.capabilities"},
        f"{X_PREFIX}simulated": True,
    }


def cdp_to_card(cdp: Dict[str, Any]) -> Dict[str, Any]:
    """CDP 主体描述 → A2A Agent Card（反向；用于对外暴露能力画像）。"""
    subj = cdp.get("cdp_subject") or {}
    if not subj.get("agent_ref"):
        raise A2ACardError("CDP 须含 cdp_subject.agent_ref")
    ifaces = subj.get("interfaces") or []
    if not ifaces:
        raise A2ACardError("CDP 须含 interfaces")
    return {
        "name": subj["agent_ref"],
        "description": subj.get("description", ""),
        "supportedInterfaces": [{"url": u} for u in ifaces],
        "capabilities": list(subj.get("capabilities") or []),
        f"{X_PREFIX}configRightBoundary": cdp.get("config_right_boundary", "scene-scoped"),
        f"{X_PREFIX}nationalAgentId": cdp.get("national_agent_id"),
        f"{X_PREFIX}simulated": True,
    }


def validate_card_mapping(obj: Dict[str, Any], kind: str = "cdp") -> Dict[str, Any]:
    """映射结果校验（前缀纪律 + 必填）。"""
    checks: Dict[str, bool] = {}
    if kind == "cdp":
        checks["has_subject"] = bool(obj.get("cdp_subject", {}).get("agent_ref"))
        checks["has_boundary"] = bool(obj.get("config_right_boundary"))
        checks["source_positive_separated"] = (
            "source_trust" in obj and "positive_sum_verified" in obj)
    else:  # card
        checks["has_name"] = bool(obj.get("name"))
        checks["has_interfaces"] = bool(obj.get("supportedInterfaces"))
    allowed = {"cdp_subject", "config_right_boundary", "source_trust",
               "positive_sum_verified", "utility_fit", "national_agent_id"}
    checks["x_prefix_intact"] = all(
        k.startswith(X_PREFIX) or k in allowed or kind == "card" and k in {
            "name", "description", "supportedInterfaces", "capabilities"}
        for k in obj.keys())
    return {"valid": all(checks.values()), "checks": checks}
