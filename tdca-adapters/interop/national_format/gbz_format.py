# -*- coding: utf-8 -*-
"""TDCA → 国标格式输出（GB/Z 185.4 智能体描述 / GB/Z 185.7 工具属性描述）

制度依据:
  - TDCA 国标格式规范（V1.1）｜ 内化白皮书 §2.2（185.4 → 函数语料"国家语法"；185.7 → S-Right）
  - 冲突识别机制 C-1 处置：**前缀隔离** —— TDCA 制度属性以 `x-tdca-*` 扩展字段附加，
    不破坏国标格式规范性，双向可溯

⚠️ V1.1 纠偏（D1/D2，2026-09-11，内部存证 缺陷登记）:
  - 185.7 正名: `toolInputParam` / `toolOutputParam`（原文表 1，6.1；附录 A.3.1 示例同为正名）
  - 185.4 正名: `name` / `version` / `description`（原文表 1，第 5 章）
  - 旧名（`inputParams` / `outputParams` / `agentName` / `agentVersion` / `agentDescription`）
    仅作**入向别名**兼容读入（`normalize_gbz`），**输出一律国标正名**

字段对齐（原文为准）:
  185.4 表 1（15 字段）: agentId* / name* / alias / version / description / iconAddress / provider /
                         accessAddress / accessMethod / servingArea / authentication / capabilities /
                         defaultInputTypes / defaultOutputTypes / skills        （* = 必需）
  185.4 表 2（技能）:     skillId* / skillName* / skillDescription / tags / examples /
                         inputTypes / outputTypes / dependencies              （* = 必需）
  185.7 表 1（6 字段）:   toolId* / toolName / toolDescription / toolVersion /
                         toolInputParam / toolOutputParam                     （* = 必需）

纪律:
  - 输出须 JSON 可序列化；fail-closed（`profile="national"` 按国标必需项，`profile="tdca"` 更严含六要素）
  - 国标字段保持"技术语法"纯度；TDCA 制度属性一律 `x-tdca-*` 前缀
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------- 国标字段表（原文为准）
GBZ_TOOL_FIELDS = ("toolId", "toolName", "toolDescription",
                   "toolVersion", "toolInputParam", "toolOutputParam")
GBZ_TOOL_REQUIRED = ("toolId",)                      # 原文表 1：仅 toolId 为"是"

GBZ_AGENT_FIELDS = ("agentId", "name", "alias", "version", "description", "iconAddress",
                    "provider", "accessAddress", "accessMethod", "servingArea",
                    "authentication", "capabilities", "defaultInputTypes",
                    "defaultOutputTypes", "skills")
GBZ_AGENT_REQUIRED = ("agentId", "name")             # 原文表 1：agentId 与 name 为"是"

SKILL_FIELDS = ("skillId", "skillName", "skillDescription", "tags", "examples",
                "inputTypes", "outputTypes", "dependencies")
SKILL_REQUIRED = ("skillId", "skillName")            # 原文表 2

# 旧名 → 国标正名（仅入向兼容；V1.0 → V1.1 迁移桥）
LEGACY_ALIASES = {
    "inputParams": "toolInputParam",
    "outputParams": "toolOutputParam",
    "toolInputParams": "toolInputParam",
    "toolOutputParams": "toolOutputParam",
    "agentName": "name",
    "agentVersion": "version",
    "agentDescription": "description",
    "agentAlias": "alias",
}

X_PREFIX = "x-tdca-"
SIX_ELEMENTS = ("目标函数", "约束矩阵", "先验分布", "配置权边界", "预期分配", "审计轨迹")


class GbzFormatError(Exception):
    """国标格式输出纪律违例。"""


def _json_schema_object(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    """构造 JSON Schema object 形态（国标 `toolInputParam`/`toolOutputParam` 元素类型为"对象"）。"""
    return {"type": "object", "properties": properties or {},
            "required": sorted(required or [])}


def _as_param_schema(param: Optional[Dict[str, Any]], required: bool = False) -> Dict[str, Any]:
    """参数入参容错：已带 type 的 schema 原样透传；裸属性表则包装为 object schema。"""
    if not isinstance(param, dict) or not param:
        return _json_schema_object({})
    if "type" in param and "properties" in param:
        return param
    return _json_schema_object(param, list(param.keys()) if required else None)


# ---------------------------------------------------------------- 185.7 工具属性描述
def to_gbz_tool_description(
    *,
    tool_id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    objective: Optional[str] = None,
    tool_input_param: Optional[Dict[str, Any]] = None,
    tool_output_param: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    config_right_boundary: Optional[str] = None,
    prior_distribution: Optional[Dict[str, Any]] = None,
    expected_allocation: Optional[Dict[str, Any]] = None,
    audit_trail: Optional[List[str]] = None,
    six_elements: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造 GB/Z 185.7 工具属性描述（国标六字段正名 + `x-tdca-*` 制度扩展）。

    目标函数: 国标六字段齐备 + 制度六要素零损失（前缀隔离）
    约束矩阵: toolId/name 必填；input/output 须 JSON Schema object；未知顶层键禁入（前缀纪律）
    先验分布: TDCA 国标格式规范 V1.1；原文表 1（6.1）
    配置权边界: L2 格式输出层
    预期分配: 返回国标兼容 dict；失败抛 GbzFormatError（fail-closed）
    审计轨迹: 调用方 NCA（本函数不写盘）
    """
    if not tool_id or not isinstance(tool_id, str):
        raise GbzFormatError("toolId 必填（工具唯一标识符，原文表 1 唯一必需项）")
    if not name:
        raise GbzFormatError("toolName 必填（TDCA 纪律：六字段齐备方可输出）")
    six = dict(six_elements or {})
    obj_text = objective or six.get("目标函数") or description
    cons = constraints if constraints is not None else six.get("约束矩阵")
    prior = prior_distribution if prior_distribution is not None else six.get("先验分布")
    boundary = config_right_boundary if config_right_boundary is not None else six.get("配置权边界")
    alloc = expected_allocation if expected_allocation is not None else six.get("预期分配")
    audit = audit_trail if audit_trail is not None else six.get("审计轨迹")

    out: Dict[str, Any] = {
        # ---- 国标六字段（正名，原文表 1）----
        "toolId": tool_id,
        "toolName": name,
        "toolDescription": description,
        "toolVersion": version,
        "toolInputParam": _as_param_schema(tool_input_param, required=True),
        "toolOutputParam": _as_param_schema(tool_output_param),
        # ---- 制度层扩展（前缀隔离；不破坏国标格式规范性）----
        f"{X_PREFIX}objective": obj_text,
        f"{X_PREFIX}constraints": cons if cons is not None else {},
        f"{X_PREFIX}priorDistribution": prior or {},
        f"{X_PREFIX}configRightBoundary": boundary or "scene-default",
        f"{X_PREFIX}expectedAllocation": alloc or {},
        f"{X_PREFIX}auditTrail": list(audit or []),
        f"{X_PREFIX}sixElementsMapping": {
            "目标函数": f"{X_PREFIX}objective",
            "约束矩阵": f"{X_PREFIX}constraints + toolInputParam",
            "先验分布": f"{X_PREFIX}priorDistribution",
            "配置权边界": f"{X_PREFIX}configRightBoundary",
            "预期分配": f"{X_PREFIX}expectedAllocation",
            "审计轨迹": f"{X_PREFIX}auditTrail",
        },
        f"{X_PREFIX}simulated": True,
    }
    return out


# ---------------------------------------------------------------- 185.4 智能体描述（全 15 字段 + 表 2 skills）
def build_skill(
    *,
    skill_id: str,
    name: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    examples: Optional[List[Any]] = None,
    input_types: Optional[List[str]] = None,
    output_types: Optional[List[str]] = None,
    dependencies: Optional[Any] = None,
) -> Dict[str, Any]:
    """构造 GB/Z 185.4 表 2 技能属性（skillId/skillName 必需）。

    目标函数: 技能描述结构化（国标表 2 对齐）
    约束矩阵: skillId 与 name 必填；未提供的可选字段不输出（保持最小集）
    先验分布: 原文表 2（8 行结构）
    配置权边界: L2 格式输出层
    预期分配: 返回技能 dict；缺必需项抛 GbzFormatError
    审计轨迹: 调用方 NCA
    """
    if not skill_id or not name:
        raise GbzFormatError("skillId 与 skillName 均为必需（原文表 2）")
    out: Dict[str, Any] = {"skillId": skill_id, "skillName": name}
    if description is not None:
        out["skillDescription"] = description
    for key, val in (("tags", tags), ("examples", examples),
                     ("inputTypes", input_types), ("outputTypes", output_types),
                     ("dependencies", dependencies)):
        if val is not None:
            out[key] = val
    return out


def to_gbz_agent_description(
    *,
    agent_id: str,
    name: str,
    version: str = "1.0.0",
    description: Optional[str] = None,
    alias: Optional[str] = None,
    icon_address: Optional[str] = None,
    provider: Optional[Any] = None,
    access_address: Optional[str] = None,
    access_method: Optional[Any] = None,
    serving_area: Optional[Any] = None,
    authentication: Optional[Any] = None,
    capabilities: Optional[Any] = None,
    default_input_types: Optional[List[str]] = None,
    default_output_types: Optional[List[str]] = None,
    skills: Optional[List[Dict[str, Any]]] = None,
    national_agent_id: Optional[str] = None,
    config_right_boundary: Optional[str] = None,
    capability_profile: Optional[Any] = None,
) -> Dict[str, Any]:
    """构造 GB/Z 185.4 智能体描述（国标 15 字段正名 + `x-tdca-*` 扩展）。

    目标函数: 185.4 表 1 全 15 字段可按需填出（agentId/name 必需）+ 表 2 skills
    约束矩阵: agentId 与 name 必填；skills 逐项走 build_skill 校验；
              `capabilities` 语义 = 辅助功能支持程度（原文），能力画像另落 x-tdca-capabilityProfile
    先验分布: 原文第 5 章表 1/表 2
    配置权边界: L2 格式输出层
    预期分配: 返回国标兼容 dict（未提供的可选字段不输出）；失败抛 GbzFormatError
    审计轨迹: 调用方 NCA
    """
    if not agent_id:
        raise GbzFormatError("agentId 必填（原文表 1）")
    if not name:
        raise GbzFormatError("name 必填（原文表 1）")

    out: Dict[str, Any] = {"agentId": agent_id, "name": name}
    for key, val in (("alias", alias), ("version", version), ("description", description),
                     ("iconAddress", icon_address), ("provider", provider),
                     ("accessAddress", access_address), ("accessMethod", access_method),
                     ("servingArea", serving_area), ("authentication", authentication),
                     ("capabilities", capabilities),
                     ("defaultInputTypes", default_input_types),
                     ("defaultOutputTypes", default_output_types)):
        if val is not None:
            out[key] = val
    if skills is not None:
        out["skills"] = [build_skill(**_skill_kwargs(s)) if not _is_skill(s) else s for s in skills]
    # ---- 制度层扩展 ----
    out[f"{X_PREFIX}nationalAgentId"] = national_agent_id
    out[f"{X_PREFIX}configRightBoundary"] = config_right_boundary or "scene-default"
    if capability_profile is not None:
        out[f"{X_PREFIX}capabilityProfile"] = capability_profile
    out[f"{X_PREFIX}simulated"] = True
    return out


def _skill_kwargs(s: Dict[str, Any]) -> Dict[str, Any]:
    """普通 dict（skillId/skillName/... 驼峰）→ build_skill 关键字参数。"""
    src = normalize_gbz(s)
    return {
        "skill_id": src.get("skillId"), "name": src.get("skillName"),
        "description": src.get("skillDescription"), "tags": src.get("tags"),
        "examples": src.get("examples"), "input_types": src.get("inputTypes"),
        "output_types": src.get("outputTypes"), "dependencies": src.get("dependencies"),
    }


def _is_skill(obj: Dict[str, Any]) -> bool:
    return isinstance(obj, dict) and "skillId" in obj and "skillName" in obj


# ---------------------------------------------------------------- #6 IR → 185.7（编译器对接）
def from_ir(ir: Any, *, tool_id: str, name: str, version: str = "1.0.0",
            description: Optional[str] = None, audit_trail: Optional[List[str]] = None,
            tool_output_param: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """函数编译器 IR → GB/Z 185.7 工具属性描述（全字段自动填充，#6）。

    目标函数: 将 `IntermediateRepresentation` 三核心字段与元数据自动映射为国标六字段 + x-tdca-* 扩展
    约束矩阵: IR 须具备 target_function_formalized / constraints_sat / prior_distribution_params；
              缺失即抛 GbzFormatError（不推测填补）；toolId/name 由调用方给出（IR 不含标识）
    先验分布: tdca-toolchain/tdca_function_compiler.py::IntermediateRepresentation（L32–48）
    配置权边界: L2 格式输出层（编译产物 → 国标报送格式）
    预期分配: 返回国标 185.7 dict；`x-tdca-compileStatus` 记录 IR 编译状态与告警
    审计轨迹: audit_trail（NCA 引用）原样入 `x-tdca-auditTrail`
    """
    if ir is None:
        raise GbzFormatError("from_ir: IR 不得为空")
    tf = getattr(ir, "target_function_formalized", None)
    sat = getattr(ir, "constraints_sat", None)
    prior = getattr(ir, "prior_distribution_params", None)
    if tf is None or sat is None or prior is None:
        raise GbzFormatError("from_ir: IR 缺核心三要素"
                             "（target_function_formalized/constraints_sat/prior_distribution_params）")

    source = getattr(ir, "source_elements", {}) or {}
    status = getattr(ir, "status", None)
    status_val = getattr(status, "value", status)
    warnings = list(getattr(ir, "warnings", []) or [])

    obj_text = (tf.get("formalized") or tf.get("expression") or tf.get("raw")
                or json.dumps(tf, ensure_ascii=False))
    desc = description or source.get("description") or f"IR 编译产物：{name}"
    out = to_gbz_tool_description(
        tool_id=tool_id, name=name, description=desc, version=version,
        objective=str(obj_text),
        tool_input_param={"constraints": {"type": "object"},
                          "prior": {"type": "object"}},
        tool_output_param=tool_output_param or {"result": {"type": "object"}},
        constraints=sat,
        prior_distribution=prior,
        config_right_boundary=source.get("configRightBoundary"),
        expected_allocation=source.get("expectedAllocation"),
        audit_trail=audit_trail,
    )
    out[f"{X_PREFIX}compileStatus"] = status_val
    out[f"{X_PREFIX}compileWarnings"] = warnings
    return out


# ---------------------------------------------------------------- 入向兼容（旧名 → 正名）
def normalize_gbz(obj: Dict[str, Any]) -> Dict[str, Any]:
    """旧名 → 国标正名（V1.0 → V1.1 迁移桥；仅入向使用，输出侧不再产生旧名）。

    目标函数: 兼容历史件（含 V1.0 格式件）读入，不因改名破坏既有数据
    约束矩阵: 仅重命名已知别名键；同键同时存在时以国标正名为准（不覆盖）
    先验分布: LEGACY_ALIASES（D1/D2 纠偏映射）
    配置权边界: L2 格式输出层
    预期分配: 返回新 dict（不原地改）
    审计轨迹: 调用方 NCA
    """
    out: Dict[str, Any] = {}
    for k, v in (obj or {}).items():
        nk = LEGACY_ALIASES.get(k, k)
        if nk in out and nk != k:
            continue                      # 国标正名优先
        out[nk] = v
    return out


# ---------------------------------------------------------------- 校验（fail-closed）
def validate_gbz(obj: Dict[str, Any], kind: str = "tool",
                 profile: str = "tdca") -> Dict[str, Any]:
    """格式校验：必填 / 类型 / 前缀纪律 / JSON 可序列化（fail-closed）。

    profile:
      - `national`: 严格按国标必需项（185.7 仅 toolId；185.4 为 agentId+name）
      - `tdca`（默认）: TDCA 更严纪律 —— 185.7 需六字段齐备且六要素扩展在位
    """
    checks: Dict[str, bool] = {}
    if kind == "tool":
        fields = GBZ_TOOL_FIELDS if profile == "tdca" else GBZ_TOOL_REQUIRED
        for f in fields:
            checks[f"has_{f}"] = (f in obj) and (obj[f] not in ("", None))
        for f in ("toolInputParam", "toolOutputParam"):
            checks[f"{f}_is_object_schema"] = (isinstance(obj.get(f), dict)
                                               and obj[f].get("type") == "object")
        if profile == "tdca":
            checks["six_elements_present"] = all(
                f"{X_PREFIX}{k}" in obj for k in ("objective", "constraints", "priorDistribution",
                                                  "configRightBoundary", "expectedAllocation",
                                                  "auditTrail"))
    elif kind == "agent":
        if profile == "national":
            for f in GBZ_AGENT_REQUIRED:
                checks[f"has_{f}"] = bool(obj.get(f))
        else:
            for f in ("agentId", "name"):
                checks[f"has_{f}"] = bool(obj.get(f))
            checks["x_tdca_present"] = f"{X_PREFIX}configRightBoundary" in obj
        if "skills" in obj:
            checks["skills_wellformed"] = all(
                isinstance(s, dict) and all(req in s for req in SKILL_REQUIRED)
                for s in obj["skills"])
        if "defaultInputTypes" in obj:
            checks["defaultInputTypes_is_list"] = isinstance(obj["defaultInputTypes"], list)
        if "defaultOutputTypes" in obj:
            checks["defaultOutputTypes_is_list"] = isinstance(obj["defaultOutputTypes"], list)
    else:
        raise GbzFormatError(f"未知 kind: {kind}")

    allowed = set(GBZ_TOOL_FIELDS) | set(GBZ_AGENT_FIELDS) | {"skills"}
    checks["x_prefix_intact"] = all(
        k.startswith(X_PREFIX) or k in allowed for k in obj.keys())
    try:
        json.dumps(obj, ensure_ascii=False)
        checks["json_serializable"] = True
    except Exception:
        checks["json_serializable"] = False
    return {"valid": all(checks.values()), "checks": checks, "kind": kind, "profile": profile}


# ---------------------------------------------------------------- 反向还原
def gbz_to_six_elements(obj: Dict[str, Any]) -> Dict[str, Any]:
    """反向还原：国标格式 → TDCA 六要素（校验同构映射完整性）。"""
    validate_gbz(obj, kind="tool", profile="national")
    return {
        "目标函数": obj.get(f"{X_PREFIX}objective"),
        "约束矩阵": obj.get(f"{X_PREFIX}constraints"),
        "先验分布": obj.get(f"{X_PREFIX}priorDistribution"),
        "配置权边界": obj.get(f"{X_PREFIX}configRightBoundary"),
        "预期分配": obj.get(f"{X_PREFIX}expectedAllocation"),
        "审计轨迹": obj.get(f"{X_PREFIX}auditTrail"),
    }


def gbz_to_internal_agent(obj: Dict[str, Any]) -> Dict[str, Any]:
    """国标 185.4 → 内部模型视图（#9 入向解析的内部侧；与 normalize_gbz 配合）。"""
    n = normalize_gbz(obj)
    validate_gbz(n, kind="agent", profile="national")
    return {
        "agentId": n.get("agentId"), "name": n.get("name"), "alias": n.get("alias"),
        "version": n.get("version"), "description": n.get("description"),
        "skills": n.get("skills", []),
        "nationalAgentId": n.get(f"{X_PREFIX}nationalAgentId"),
        "configRightBoundary": n.get(f"{X_PREFIX}configRightBoundary"),
    }


# ---------------------------------------------------------------- S-Right 对接（保留）
def to_gbz_from_tool_descriptor(desc, outcome=None) -> Dict[str, Any]:
    """S-Right ToolDescriptor → 185.7 工具属性描述（对接层）。"""
    return to_gbz_tool_description(
        tool_id=desc.tool_id, name=desc.name,
        description=f"{desc.name}（场景配置权调用工具）", version=desc.version,
        tool_input_param={"payload": {"type": "object"}},
        tool_output_param={"result": {"type": "object"},
                           "tax": {"type": "number"}, "shapley": {"type": "object"}},
        config_right_boundary=desc.boundary,
        objective=f"scene_fit={desc.scene_fit}",
        audit_trail=[getattr(outcome, "nca_ref", None)] if outcome is not None else [],
    )
