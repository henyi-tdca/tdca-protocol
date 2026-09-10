# -*- coding: utf-8 -*-
"""TDCA → 国标格式输出（GB/Z 185.4 智能体描述 / 185.7 工具属性描述）

制度依据:
  - 内化白皮书 §2.2（185.4 智能体描述 → 函数语料"国家语法"；185.7 工具调用 → S-Right）
  - 185.7 精读（表 1 工具属性描述六字段 ↔ TDCA 函数语料六要素同构映射）
  - 冲突识别机制 C-1 处置：**前缀隔离** —— TDCA 制度属性以 `x-tdca-*` 扩展字段附加，
    不破坏国标格式规范性，双向可溯

映射（六要素 → 国标）:
  工具标识符 toolId          ← 工具/函数唯一标识
  工具名称 toolName          ← 名称
  工具描述 toolDescription   ← 目标函数（形式化摘要）+ 语义描述
  工具版本 toolVersion       ← 版本
  工具输入参数 inputParams   ← 约束矩阵（布尔化约束 → JSON Schema constraints）
  工具输出参数 outputParams  ← 预期输出（+ 效用计量）
  扩展 x-tdca-*              ← 先验分布 / 配置权边界 / 预期分配 / 审计轨迹（制度层，前缀隔离）

纪律:
  - 输出须 JSON 可序列化；必填六字段齐备方可输出（fail-closed）
  - 国标字段保持"技术语法"纯度；TDCA 制度属性一律 x-tdca-* 前缀
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

GBZ_TOOL_FIELDS = ("toolId", "toolName", "toolDescription",
                   "toolVersion", "inputParams", "outputParams")
X_PREFIX = "x-tdca-"
SIX_ELEMENTS = ("目标函数", "约束矩阵", "先验分布", "配置权边界", "预期分配", "审计轨迹")


class GbzFormatError(Exception):
    """国标格式输出纪律违例。"""


def _json_schema_object(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"type": "object", "properties": properties,
            "required": sorted(required or [])}


def to_gbz_tool_description(
    *,
    tool_id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    objective: Optional[str] = None,
    input_params: Optional[Dict[str, Any]] = None,
    output_params: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    config_right_boundary: Optional[str] = None,
    prior_distribution: Optional[Dict[str, Any]] = None,
    expected_allocation: Optional[Dict[str, Any]] = None,
    audit_trail: Optional[List[str]] = None,
    six_elements: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造 GB/Z 185.7 工具属性描述（六字段 + x-tdca-* 制度扩展）。"""
    if not tool_id or not isinstance(tool_id, str):
        raise GbzFormatError("toolId 必填（工具唯一标识符）")
    if not name:
        raise GbzFormatError("toolName 必填")
    six = dict(six_elements or {})
    obj_text = objective or six.get("目标函数") or description
    cons = constraints if constraints is not None else six.get("约束矩阵")
    prior = prior_distribution if prior_distribution is not None else six.get("先验分布")
    boundary = config_right_boundary if config_right_boundary is not None else six.get("配置权边界")
    alloc = expected_allocation if expected_allocation is not None else six.get("预期分配")
    audit = audit_trail if audit_trail is not None else six.get("审计轨迹")

    out: Dict[str, Any] = {
        "toolId": tool_id,
        "toolName": name,
        "toolDescription": description,
        "toolVersion": version,
        "inputParams": _json_schema_object(input_params or {},
                                           required=list((input_params or {}).keys())),
        "outputParams": _json_schema_object(output_params or {}),
        # ---- 制度层扩展（前缀隔离；不破坏国标格式规范性）----
        f"{X_PREFIX}objective": obj_text,
        f"{X_PREFIX}constraints": cons if cons is not None else {},
        f"{X_PREFIX}priorDistribution": prior or {},
        f"{X_PREFIX}configRightBoundary": boundary or "scene-default",
        f"{X_PREFIX}expectedAllocation": alloc or {},
        f"{X_PREFIX}auditTrail": list(audit or []),
        f"{X_PREFIX}sixElementsMapping": {
            "目标函数": f"{X_PREFIX}objective",
            "约束矩阵": f"{X_PREFIX}constraints + inputParams",
            "先验分布": f"{X_PREFIX}priorDistribution",
            "配置权边界": f"{X_PREFIX}configRightBoundary",
            "预期分配": f"{X_PREFIX}expectedAllocation",
            "审计轨迹": f"{X_PREFIX}auditTrail",
        },
        f"{X_PREFIX}simulated": True,
    }
    return out


def to_gbz_agent_description(
    *,
    agent_id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    capabilities: Optional[List[Dict[str, Any]]] = None,
    national_agent_id: Optional[str] = None,
    config_right_boundary: Optional[str] = None,
) -> Dict[str, Any]:
    """构造 GB/Z 185.4 智能体描述（能力画像；+ x-tdca-* 扩展）。"""
    if not agent_id:
        raise GbzFormatError("agentId 必填")
    caps = capabilities or []
    return {
        "agentId": agent_id,
        "agentName": name,
        "agentDescription": description,
        "agentVersion": version,
        "capabilities": [
            {"capabilityId": c.get("capabilityId", f"cap-{i + 1}"),
             "input": _json_schema_object(c.get("input", {})),
             "output": _json_schema_object(c.get("output", {})),
             "constraints": c.get("constraints", {})}
            for i, c in enumerate(caps)],
        f"{X_PREFIX}nationalAgentId": national_agent_id,     # 走出范围时的国标身份链接（可空）
        f"{X_PREFIX}configRightBoundary": config_right_boundary or "scene-default",
        f"{X_PREFIX}simulated": True,
    }


def gbz_to_six_elements(obj: Dict[str, Any]) -> Dict[str, Any]:
    """反向还原：国标格式 → TDCA 六要素（校验同构映射完整性）。"""
    validate_gbz(obj, kind="tool")
    return {
        "目标函数": obj.get(f"{X_PREFIX}objective"),
        "约束矩阵": obj.get(f"{X_PREFIX}constraints"),
        "先验分布": obj.get(f"{X_PREFIX}priorDistribution"),
        "配置权边界": obj.get(f"{X_PREFIX}configRightBoundary"),
        "预期分配": obj.get(f"{X_PREFIX}expectedAllocation"),
        "审计轨迹": obj.get(f"{X_PREFIX}auditTrail"),
    }


def validate_gbz(obj: Dict[str, Any], kind: str = "tool") -> Dict[str, Any]:
    """格式校验：必填字段 / 类型 / JSON 可序列化（fail-closed）。"""
    checks: Dict[str, bool] = {}
    if kind == "tool":
        for f in GBZ_TOOL_FIELDS:
            checks[f"has_{f}"] = f in obj and obj[f] not in ("", None)
        checks["inputParams_is_object_schema"] = (
            isinstance(obj.get("inputParams"), dict)
            and obj["inputParams"].get("type") == "object")
        checks["outputParams_is_object_schema"] = (
            isinstance(obj.get("outputParams"), dict)
            and obj["outputParams"].get("type") == "object")
    elif kind == "agent":
        checks["has_agentId"] = bool(obj.get("agentId"))
        checks["has_capabilities"] = isinstance(obj.get("capabilities"), list)
    else:
        raise GbzFormatError(f"未知 kind: {kind}")
    checks["x_prefix_intact"] = all(
        k.startswith(X_PREFIX) or k in (*GBZ_TOOL_FIELDS, "agentId", "agentName",
                                        "agentDescription", "agentVersion", "capabilities")
        for k in obj.keys())
    try:
        json.dumps(obj, ensure_ascii=False)
        checks["json_serializable"] = True
    except Exception:
        checks["json_serializable"] = False
    return {"valid": all(checks.values()), "checks": checks, "kind": kind}


def to_gbz_from_tool_descriptor(desc, outcome=None) -> Dict[str, Any]:
    """S-Right ToolDescriptor → 185.7 工具属性描述（对接层）。"""
    return to_gbz_tool_description(
        tool_id=desc.tool_id, name=desc.name,
        description=f"{desc.name}（场景配置权调用工具）", version=desc.version,
        input_params={"payload": {"type": "object"}},
        output_params={"result": {"type": "object"},
                       "tax": {"type": "number"}, "shapley": {"type": "object"}},
        config_right_boundary=desc.boundary,
        objective=f"scene_fit={desc.scene_fit}",
        audit_trail=[getattr(outcome, "nca_ref", None)] if outcome is not None else [],
    )
