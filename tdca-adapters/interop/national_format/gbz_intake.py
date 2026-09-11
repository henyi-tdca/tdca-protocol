# -*- coding: utf-8 -*-
"""国标文档入向解析——外部 GB/Z 185.4 / 185.7 → 内部模型（M3 / #9）

用途:
  - **单件解析**：外部工具属性描述（185.7）/ 智能体描述（185.4）→ 内部模型（含六要素还原）
  - **报文解析**（185.7 §6.2~6.4）：工具请求 / 工具同步 / 工具更新 / 工具调用 / 调用结果
  - **统一入口** `intake(data)`：自动判别类型后分派
  - **报送包读回** `import_bundle(dir)`：读回 M2 报送包（含 `verify_bundle` 复核）

纪律:
  - 外部文档**不可信**：类型/必需项严格校验；JSON 解析失败即拒（fail-closed）
  - **不推测填补**：缺失的可选字段返回 `None` 并记 `warnings`；缺国标必需项（185.7 `toolId`；185.4 `agentId`+`name`）即拒
  - 允许外部件**不带** `x-tdca-*` 扩展（宽松档 `profile="national"`）；未知顶层键记 `warnings` 不静默丢弃
  - 内部制度语义只在存在时**映射**，不存在时**如实标注缺失**（不伪造制度事实）
  - 时间戳沿用国标单位为**秒**

用法:
    res = intake('{"toolId": "Aabbcc001", "toolName": "add_schedule", ...}')
    assert res["kind"] == "tool";  assert res["warnings"] == []

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:                                        # 包内导入
    from .gbz_format import (GBZ_AGENT_REQUIRED, GBZ_TOOL_FIELDS, GBZ_TOOL_REQUIRED,
                             SKILL_REQUIRED, X_PREFIX, GbzFormatError,
                             gbz_to_internal_agent, gbz_to_six_elements, normalize_gbz)
    from .gbz_bundle import verify_bundle
except ImportError:                         # 顶层导入（sys.path 指向模块目录）
    from gbz_format import (GBZ_AGENT_REQUIRED, GBZ_TOOL_FIELDS, GBZ_TOOL_REQUIRED,
                            SKILL_REQUIRED, X_PREFIX, GbzFormatError,
                            gbz_to_internal_agent, gbz_to_six_elements, normalize_gbz)
    from gbz_bundle import verify_bundle

MESSAGE_TYPES = ("tool_request", "tool_sync", "tool_update", "tool_invoke", "tool_result")
_KNOWN_TOP_KEYS = set(GBZ_TOOL_FIELDS) | {
    "agentId", "name", "alias", "version", "description", "iconAddress", "provider",
    "accessAddress", "accessMethod", "servingArea", "authentication", "capabilities",
    "defaultInputTypes", "defaultOutputTypes", "skills",
    # 报文键
    "requestType", "syncType", "timestamp", "toolRequestList", "toolSyncList",
    "toolUpdateList", "sessionId", "toolInvokeList", "toolResultList",
    # 报送包清单键
    "bundleId", "generatedAt", "format", "profile", "counts", "entries", "bundleSha256", "valid",
}


class GbzIntakeError(Exception):
    """入向解析纪律违例（外部文档不可信 → 校验不过即拒）。"""


# ---------------------------------------------------------------- 基础
def loads_document(data: Any) -> Dict[str, Any]:
    """外部文档 → dict（支持 JSON 字符串 / bytes / 已是 dict）。

    目标函数: 统一入向载荷形态，隔离 JSON 解析细节
    约束矩阵: 非 dict 顶层即拒（数组/标量不接受）；JSON 畸形即拒（fail-closed）
    先验分布: 外部报送文档（未知来源）
    配置权边界: L2 报送格式层（只读）
    预期分配: dict；失败抛 GbzIntakeError
    审计轨迹: 调用方 NCA
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    if isinstance(data, str):
        try:
            obj = json.loads(data)
        except Exception as exc:                       # noqa: BLE001
            raise GbzIntakeError(f"JSON 解析失败: {exc}") from exc
        if not isinstance(obj, dict):
            raise GbzIntakeError("顶层必须是 JSON 对象（不接受数组/标量）")
        return obj
    raise GbzIntakeError(f"不支持的载荷类型: {type(data).__name__}")


def detect_kind(obj: Dict[str, Any]) -> str:
    """判别外部文档类型：`tool` / `agent` / `message`。

    目标函数: 分派依据（报文优先于单件，避免报文被误判为单件）
    约束矩阵: 报文键优先；其次 toolId → tool；再次 agentId → agent；否则拒
    先验分布: 原文 185.4 §5 表 1 / 185.7 §6.1 表 1 / §6.2~6.4
    配置权边界: L2 报送格式层
    预期分配: 类型字符串；无法判别抛 GbzIntakeError
    审计轨迹: 调用方 NCA
    """
    if _detect_message(obj):
        return "message"
    if obj.get("toolId"):
        return "tool"
    if obj.get("agentId"):
        return "agent"
    raise GbzIntakeError("无法判别文档类型（缺 toolId / agentId / 报文标识键）")


def _detect_message(obj: Dict[str, Any]) -> Optional[str]:
    if "requestType" in obj or "toolRequestList" in obj:
        return "tool_request"
    if "toolSyncList" in obj:
        return "tool_sync"
    if "toolUpdateList" in obj:
        return "tool_update"
    if "toolInvokeList" in obj or "sessionId" in obj:
        return "tool_invoke"
    if "toolResultList" in obj:
        return "tool_result"
    return None


def _unknown_keys(obj: Dict[str, Any]) -> List[str]:
    return sorted(k for k in obj if k not in _KNOWN_TOP_KEYS and not k.startswith(X_PREFIX))


# ---------------------------------------------------------------- 单件：185.7 工具
def parse_tool_document(data: Any, *, strict: bool = False) -> Dict[str, Any]:
    """外部 185.7 工具属性描述 → 内部模型（含六要素还原）。

    目标函数: 外部工具件 → 规范化字段 + 内部六要素视图（制度语义存在则映射、缺失则如实标注）
    约束矩阵: `toolId` 必需（原文表 1 唯一必需项）；strict=True 时另按 TDCA 六字段齐备校验；
              工具参数须为对象形态；未知键记 warnings（不静默丢弃）
    先验分布: 原文 §6.1 表 1 + 附录 A.3.1 示例；TDCA 国标格式规范 V1.2
    配置权边界: L2 报送格式层（只读解析）
    预期分配: {"kind","data","sixElements","warnings","missing"}
    审计轨迹: 调用方 NCA
    """
    obj = normalize_gbz(loads_document(data))          # 兼容 V1.0 旧名入向
    warnings = [f"未知顶层键: {k}" for k in _unknown_keys(obj)]
    if not obj.get("toolId"):
        raise GbzIntakeError("185.7 工具件缺 toolId（原文表 1 必需项）")
    for f in ("toolInputParam", "toolOutputParam"):
        # 国标原文（附录 A.3.1）为**裸属性表**（无 JSON Schema 包装）——故只要求"是对象"；
        # 若外部件显式声明 type，则必须是 object（不得声明为数组/标量）。
        val = obj.get(f)
        if val is None:
            continue
        if not isinstance(val, dict):
            raise GbzIntakeError(f"{f} 须为对象（原文元素类型：对象）")
        if "type" in val and val["type"] != "object":
            raise GbzIntakeError(f"{f}.type 若声明须为 'object'（原文元素类型：对象）")
    if strict:
        missing = [f for f in GBZ_TOOL_FIELDS if not obj.get(f)]
        if missing:
            raise GbzIntakeError(f"strict 模式缺国标字段: {missing}")
    six = gbz_to_six_elements(obj)
    missing = [k for k, v in six.items() if v is None]
    if missing:
        warnings.append(f"外部件未携带制度扩展（六要素缺失: {'/'.join(missing)}）——如实标注，不推测填补")
    return {"kind": "tool", "data": obj, "sixElements": six,
            "warnings": warnings, "missing": missing}


# ---------------------------------------------------------------- 单件：185.4 智能体
def parse_agent_document(data: Any, *, strict: bool = False) -> Dict[str, Any]:
    """外部 185.4 智能体描述 → 内部模型（技能画像 + 桥接链接）。

    目标函数: 外部智能体件 → 内部视图（含 skills 结构校验）
    约束矩阵: `agentId` 与 `name` 必需（原文表 1）；`skills[]` 逐项需 `skillId`+`skillName`；
              默认输入/输出类型若存在须为数组；未知键记 warnings
    先验分布: 原文 §5 表 1/表 2
    配置权边界: L2 报送格式层（只读解析）
    预期分配: {"kind","data","internal","warnings","missing"}
    审计轨迹: 调用方 NCA
    """
    obj = normalize_gbz(loads_document(data))
    warnings = [f"未知顶层键: {k}" for k in _unknown_keys(obj)]
    for f in GBZ_AGENT_REQUIRED:
        if not obj.get(f):
            raise GbzIntakeError(f"185.4 智能体件缺 {f}（原文表 1 必需项）")
    for s in obj.get("skills", []) or []:
        if not isinstance(s, dict) or any(r not in s for r in SKILL_REQUIRED):
            raise GbzIntakeError("skills[] 每项需含 skillId 与 skillName（原文表 2）")
    for f in ("defaultInputTypes", "defaultOutputTypes"):
        if f in obj and not isinstance(obj[f], list):
            raise GbzIntakeError(f"{f} 须为字符串数组（原文表 1）")
    internal = gbz_to_internal_agent(obj)
    missing = [k for k in ("nationalAgentId", "configRightBoundary") if internal.get(k) in (None, "")]
    if missing:
        warnings.append(f"外部件未携带桥接/边界扩展: {'/'.join(missing)}")
    if strict and not obj.get("description"):
        raise GbzIntakeError("strict 模式缺 description")
    return {"kind": "agent", "data": obj, "internal": internal,
            "warnings": warnings, "missing": missing}


# ---------------------------------------------------------------- 报文（185.7 §6.2~6.4）
def parse_message(data: Any, *, timestamp_unit: str = "s") -> Dict[str, Any]:
    """外部 185.7 报文 → 内部视图（请求 / 同步 / 更新 / 调用 / 结果）。

    目标函数: 五类报文的结构校验与规范化（时间戳单位秒，原文示例 1763434894）
    约束矩阵: 按类校字段与枚举（requestType∈{1,2}；syncType∈{1,2}；列表件须为数组，工具项需 toolId）
    先验分布: 原文 §6.2（工具请求/同步）、§6.3（工具更新）、§6.4（工具调用/结果）
    配置权边界: L2 报送格式层（只读解析）
    预期分配: {"kind":"message","messageType","data","warnings","missing"}
    审计轨迹: 调用方 NCA
    """
    if timestamp_unit != "s":
        raise GbzIntakeError("仅支持秒级时间戳（国标示例单位）")
    obj = loads_document(data)
    mtype = _detect_message(obj)
    if not mtype:
        raise GbzIntakeError("无法判别报文类型（§6.2~6.4 键均缺）")
    warnings = [f"未知顶层键: {k}" for k in _unknown_keys(obj)]
    if not isinstance(obj.get("timestamp"), int):
        warnings.append("timestamp 缺失或非整数秒")
    required_by_type = {
        "tool_request": ("requestType",),
        "tool_sync": ("syncType", "toolSyncList"),
        "tool_update": ("syncType", "toolUpdateList"),
        "tool_invoke": ("sessionId", "toolInvokeList"),
        "tool_result": ("toolResultList",),
    }
    missing = [k for k in required_by_type[mtype] if k not in obj]
    if missing:
        raise GbzIntakeError(f"[{mtype}] 缺必需字段: {missing}")
    if mtype == "tool_request" and obj["requestType"] not in (1, 2):
        raise GbzIntakeError("requestType 仅允许 1（申请工具列表）或 2（更新工具列表）")
    if mtype in ("tool_sync", "tool_update") and obj["syncType"] not in (1, 2):
        raise GbzIntakeError("syncType 仅允许 1（获取完整列表）或 2（更新列表）")
    if mtype == "tool_sync":
        lst = obj["toolSyncList"]
        if not isinstance(lst, list):
            raise GbzIntakeError("toolSyncList 须为数组")
        for t in lst:
            if not isinstance(t, dict) or not t.get("toolId"):
                raise GbzIntakeError("toolSyncList 每项需含 toolId")
    if mtype in ("tool_invoke", "tool_result"):
        key = "toolInvokeList" if mtype == "tool_invoke" else "toolResultList"
        if not isinstance(obj[key], list):
            raise GbzIntakeError(f"{key} 须为数组")
    return {"kind": "message", "messageType": mtype, "data": obj,
            "warnings": warnings, "missing": missing}


# ---------------------------------------------------------------- 统一入口
def intake(data: Any, *, expect: Optional[str] = None, strict: bool = False) -> Dict[str, Any]:
    """统一入向入口：自动判别 `tool` / `agent` / `message` 后分派解析。

    目标函数: 外部载荷 → 内部模型（单入口，便于批量接入）
    约束矩阵: expect 指定时须与判别结果一致；判别失败即拒
    先验分布: 本模块各专用解析函数
    配置权边界: L2 报送格式层
    预期分配: 各解析函数结果（附 "kind"）；不一致抛 GbzIntakeError
    审计轨迹: 调用方 NCA
    """
    obj = loads_document(data)
    kind = detect_kind(obj)
    if expect and expect != kind:
        raise GbzIntakeError(f"类型不符: 判别为 {kind}，期望 {expect}")
    if kind == "tool":
        return parse_tool_document(obj, strict=strict)
    if kind == "agent":
        return parse_agent_document(obj, strict=strict)
    return parse_message(obj)


# ---------------------------------------------------------------- 报送包读回（M2 反向）
def import_bundle(directory: str) -> Dict[str, Any]:
    """读回 M2 报送包（清单 + 逐件解析 + 回验）。

    目标函数: 报送包 → 内部条目列表（可再入内部模型），并给出包级复核结论
    约束矩阵: 先跑 `verify_bundle`（哈希/计数/清单自洽）；逐件解析失败记 errors（不中断全包）
    先验分布: gbz_bundle.make_bundle 产出的目录
    配置权边界: L2 报送格式层（只读）
    预期分配: {"valid","errors","tools","agents","manifest"}
    审计轨迹: 调用方 NCA
    """
    v = verify_bundle(directory)
    errors = list(v["errors"])
    tools: List[Dict[str, Any]] = []
    agents: List[Dict[str, Any]] = []
    for e in v["manifest"].get("entries", []):
        p = os.path.join(directory, *str(e.get("file", "")).split("/"))
        try:
            with open(p, "rb") as f:
                raw = f.read()
        except OSError as exc:
            errors.append(f"读取失败: {e.get('file')} ({exc})")
            continue
        try:
            if e.get("kind") == "tool":
                tools.append(parse_tool_document(raw))
            else:
                agents.append(parse_agent_document(raw))
        except GbzIntakeError as exc:
            errors.append(f"[{e.get('file')}] 解析失败: {exc}")
    return {"valid": not errors, "errors": errors, "tools": tools,
            "agents": agents, "manifest": v["manifest"]}
