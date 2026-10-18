# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# L1SI153-ERROR-CODE-001 段一后端验收：classify 归码纯函数（13 码代表例＋兜底＋with_code）
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from error_codes import (  # noqa: E402
    CODE_ASSET_STATE, CODE_AUTHZ_PERM, CODE_EXT_EXT, CODE_GOV_PERM,
    CODE_IDENT_PERM, CODE_IDENT_STATE, CODE_INPUT_FORMAT, CODE_INPUT_REQUIRED,
    CODE_RES_LIMIT, CODE_STATE_DUP, CODE_STATE_STATE, CODE_SYS_SYS,
    ERROR_CODE_TABLE, classify, with_code,
)


def test_table_13_codes_match_handoff():
    assert len(ERROR_CODE_TABLE) == 13
    assert ERROR_CODE_TABLE[CODE_GOV_PERM] == "本次操作被制度性拒绝（合规前置未过）"
    assert ERROR_CODE_TABLE["TDCA-E-SETL-RES-001"] == "额度不足"  # reserved 只登记


def test_code_representatives():
    # TDCA-E-IDENT-PERM-001 未登录
    assert classify(401, "") == CODE_IDENT_PERM
    assert classify(403, "未登录") == CODE_IDENT_PERM
    # TDCA-E-IDENT-STATE-001 凭证失效（会话/锚/协议/token）
    assert classify(401, "会话已过期，请重新登录") == CODE_IDENT_STATE
    assert classify(403, "ANCHOR_INVALID: 主体锚无效") == CODE_IDENT_STATE
    assert classify(403, "PROTOCOL_HASH_MISMATCH: 哈希不符") == CODE_IDENT_STATE
    # TDCA-E-AUTHZ-PERM-001 无权
    assert classify(403, "仅 founder 可执行") == CODE_AUTHZ_PERM
    assert classify(403, "GRANT_REQUIRED: 无有效授权件") == CODE_AUTHZ_PERM
    # TDCA-E-ASSET-STATE-001 不存在/未登记
    assert classify(404, "Not Found") == CODE_ASSET_STATE
    assert classify(403, "登记号不存在（未登记）") == CODE_ASSET_STATE
    # TDCA-E-STATE-STATE-002 状态不允许
    assert classify(409, "") == CODE_STATE_STATE
    assert classify(403, "STEP_ORDER: ② 无有效执行令牌") == CODE_IDENT_STATE  # 令牌优先
    assert classify(409, "CONFLICT: 已是目标态") == CODE_STATE_DUP  # STATE-003 优先于 STATE-002
    # TDCA-E-STATE-STATE-003 重复提交
    assert classify(409, "CONFLICT: 该判级事件已裁决（幂等拒重复裁决）") == CODE_STATE_DUP
    # TDCA-E-RES-RES-001 限流
    assert classify(429, "rate limit 60/min/IP") == CODE_RES_LIMIT
    assert classify(429, "登录尝试过于频繁") == CODE_RES_LIMIT
    # TDCA-E-EXT-EXT-001 外部不可用
    assert classify(503, "DOC_SOURCE_UNAVAILABLE") == CODE_EXT_EXT
    assert classify(502, "") == CODE_EXT_EXT
    # TDCA-E-GOV-PERM-002 制度性拒绝（负空间合规）
    assert classify(400, "PUBLIC_SPACE_VIOLATION: 命中四条不公开负空间") == CODE_GOV_PERM
    assert classify(400, "NS_REVIEW_REJECTED: 负空间审查不过") == CODE_GOV_PERM


def test_input_codes():
    assert classify(400, "six_elements_ref 为必填") == CODE_INPUT_REQUIRED
    assert classify(400, "REQUIREMENT_MISSING: 场景约束（要件①）") == CODE_INPUT_REQUIRED
    assert classify(400, "action 仅接受 issue|rotate|revoke") == CODE_INPUT_FORMAT
    assert classify(400, "display_name 过长（≤64 字符）") == CODE_INPUT_FORMAT


def test_fallbacks():
    # 无法归类 → TDCA-E-SYS-SYS-001 兜底（令 §二.3）
    assert classify(418, "") == CODE_SYS_SYS
    assert classify(None, "") == CODE_SYS_SYS
    assert classify(500, "") == CODE_SYS_SYS
    # 状态兜底
    assert classify(404, "") == CODE_ASSET_STATE
    assert classify(403, "") == CODE_AUTHZ_PERM


def test_with_code_only_adds_field():
    deny = {"error": "UNAUTHORIZED", "detail": "须登录会话（TDCA-SES）或 TDCA-CRT token"}
    out = with_code(deny, 401)
    assert out["code"] == CODE_IDENT_PERM
    assert out["detail"] == deny["detail"] and out["error"] == deny["error"]
    assert "code" not in deny  # 原 dict 不被就地改动
    deny2 = {"error": "FORBIDDEN", "detail": "会话无效或已吊销"}
    assert with_code(deny2, 403)["code"] == CODE_IDENT_STATE
