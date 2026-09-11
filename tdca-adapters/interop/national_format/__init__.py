# -*- coding: utf-8 -*-
"""TDCA 国标格式输出模块（M3）——GB/Z 185.4 智能体描述 / 185.7 工具属性描述。

V1.1（2026-09-11，内部存证）：字段名按国标原文正名（D1/D2 纠偏）、
185.4 补全 15 字段 + 表 2 skills、新增 IR 对接（#6）与入向兼容（#9 内部侧）。
M2（2026-09-11，内部存证）：新增报送包批量导出（gbz_bundle，含 §6.2 报文形态）。
"""
from .gbz_format import (  # noqa: F401
    GBZ_AGENT_FIELDS, GBZ_AGENT_REQUIRED, GBZ_TOOL_FIELDS, GBZ_TOOL_REQUIRED,
    LEGACY_ALIASES, SIX_ELEMENTS, SKILL_FIELDS, SKILL_REQUIRED, X_PREFIX,
    GbzFormatError, build_skill, from_ir, gbz_to_internal_agent,
    gbz_to_six_elements, normalize_gbz, to_gbz_agent_description,
    to_gbz_from_tool_descriptor, to_gbz_tool_description, validate_gbz)
from .gbz_bundle import (  # noqa: F401
    GBZ_BUNDLE_FORMAT, GbzBundleError, make_bundle, sanitize_name,
    to_tool_request, to_tool_sync_list, verify_bundle)
from .gbz_intake import (  # noqa: F401
    MESSAGE_TYPES, GbzIntakeError, detect_kind, import_bundle, intake,
    loads_document, parse_agent_document, parse_message, parse_tool_document)

__all__ = [
    # 构造
    "to_gbz_tool_description", "to_gbz_agent_description", "build_skill",
    "to_gbz_from_tool_descriptor", "from_ir",
    # 校验 / 还原 / 入向
    "validate_gbz", "gbz_to_six_elements", "gbz_to_internal_agent", "normalize_gbz",
    # 报送包（M2 / #8）
    "make_bundle", "verify_bundle", "sanitize_name", "to_tool_sync_list",
    "to_tool_request", "GBZ_BUNDLE_FORMAT", "GbzBundleError",
    # 入向解析（M3 / #9）
    "intake", "parse_tool_document", "parse_agent_document", "parse_message",
    "import_bundle", "loads_document", "detect_kind", "GbzIntakeError", "MESSAGE_TYPES",
    # 常量
    "GbzFormatError", "GBZ_TOOL_FIELDS", "GBZ_TOOL_REQUIRED", "GBZ_AGENT_FIELDS",
    "GBZ_AGENT_REQUIRED", "SKILL_FIELDS", "SKILL_REQUIRED", "LEGACY_ALIASES",
    "SIX_ELEMENTS", "X_PREFIX",
]
