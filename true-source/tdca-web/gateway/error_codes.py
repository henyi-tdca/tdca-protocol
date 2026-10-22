# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# TDCA 统一错误码表 v2（L1SI153-ERROR-CODE-001 段一加码 · 段二判定收口）
# 约束矩阵: TDCA-HANDOFF-EXEC-ERROR-CODE-001 §二/§四——只加 code 字段，
#           ⛔ 不改 HTTP 状态码、不改文案、不改判定分支。
# 码表来源: error-code-table-v2.yaml（码名为唯一标识；SETL-RES-001 额度不足=reserved
#           只登记；422 归 TDCA-E-INPUT-INPUT-002）
# 命名规则: TDCA-E-<env: ENTER|IDENT|ASSET|AUTHZ|SCENE|COOP|NCA|SETL|DISP|CHG|EXIT|GOV>
#           -<type: INPUT|PERM|STATE|RES|SYS|EXT>-<seq3>
"""拒绝类响应统一挂码：HTTPException 全局 handler / 鉴权中间件 / 裸 JSONResponse。

classify(status, detail) 为唯一归类入口（纯函数、零副作用）：
关键词按规则序首命中先归；均不命中按状态兜底；最终兜底 TDCA-E-SYS-SYS-001
（令 §二.3：无法归类的例外用 SYS-SYS-001 并在回报逐条列出——离线全量验证清单见回报）。
"""
from __future__ import annotations

import re
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 码表常量（唯一事实源；前端 errors.ts 为同表镜像，两处各自一处定义）
# ---------------------------------------------------------------------------
CODE_INPUT_REQUIRED = "TDCA-E-INPUT-INPUT-001"    # 缺少必填项
CODE_INPUT_FORMAT = "TDCA-E-INPUT-INPUT-002"      # 格式不符（422 归此码）
CODE_IDENT_PERM = "TDCA-E-IDENT-PERM-001"         # 请先登录
CODE_IDENT_STATE = "TDCA-E-IDENT-STATE-001"       # 凭证无效或已过期
CODE_AUTHZ_PERM = "TDCA-E-AUTHZ-PERM-001"         # 无权执行
CODE_ASSET_STATE = "TDCA-E-ASSET-STATE-001"       # 资源不存在或未登记
CODE_STATE_STATE = "TDCA-E-STATE-STATE-002"       # 状态不允许
CODE_STATE_DUP = "TDCA-E-STATE-STATE-003"         # 重复提交
CODE_RES_LIMIT = "TDCA-E-RES-RES-001"             # 限流
CODE_SETL_RES = "TDCA-E-SETL-RES-001"             # 额度不足（reserved，只登记）
CODE_EXT_EXT = "TDCA-E-EXT-EXT-001"               # 外部不可用
CODE_SYS_SYS = "TDCA-E-SYS-SYS-001"               # 系统繁忙（兜底）
CODE_GOV_PERM = "TDCA-E-GOV-PERM-002"             # 制度性拒绝（负空间合规）

ERROR_CODE_TABLE = {
    CODE_INPUT_REQUIRED: "缺少必填项：〈字段名〉",
    CODE_INPUT_FORMAT: "〈字段名〉格式不符要求",
    CODE_IDENT_PERM: "请先登录",
    CODE_IDENT_STATE: "凭证无效或已过期，请重新取得",
    CODE_AUTHZ_PERM: "当前账户无权执行此操作",
    CODE_ASSET_STATE: "该资源不存在或尚未登记",
    CODE_STATE_STATE: "当前状态不允许此操作",
    CODE_STATE_DUP: "已提交，请勿重复操作",
    CODE_RES_LIMIT: "操作过于频繁，请稍后再试",
    CODE_SETL_RES: "额度不足",
    CODE_EXT_EXT: "外部服务暂不可用，请稍后重试",
    CODE_SYS_SYS: "系统繁忙，请稍后再试",
    CODE_GOV_PERM: "本次操作被制度性拒绝（合规前置未过）",
}

# ---------------------------------------------------------------------------
# 归类规则（顺序即优先级；detail 非字符串时退化为仅按状态）
# ---------------------------------------------------------------------------
_RULES = [
    (CODE_IDENT_PERM, [r"未登录"]),
    (CODE_RES_LIMIT, [r"过于频繁", r"rate limit", r"限流", r"稍后再试"]),
    (CODE_GOV_PERM, [r"负空间", r"PUBLIC_SPACE_VIOLATION", r"NS_REVIEW", r"合规前置"]),
    (CODE_STATE_DUP, [r"幂等", r"重复提交", r"重复施加", r"重复验证", r"已裁决", r"竞态", r"CONFLICT", r"事务回滚"]),
    (CODE_IDENT_STATE, [r"会话无效", r"已吊销", r"已过期", r"会话已过期", r"凭据", r"ANCHOR_INVALID",
                        r"ADMISSION_DENIED", r"HARDWARE_SIGNATURE", r"PROTOCOL_HASH", r"PROTOCOL_VERSION",
                        r"执行令牌", r"协议未加载", r"协议包哈希", r"哈希不符", r"旧密码", r"token 无效", r"签名"]),
    (CODE_ASSET_STATE, [r"未登记", r"登记号不存在", r"主体不存在", r"主体账户不存在", r"无锚记录",
                        r"NOT_FOUND", r"未创建", r"幽灵态", r"不存在", r"规范键不存在"]),
    (CODE_INPUT_REQUIRED, [r"必填", r"不得为空", r"不可为空", r"须同传", r"同传", r"缺失", r"缺一不可",
                           r"缺一不成立", r"为必填", r"REQUIREMENT_MISSING", r"缺组", r"须全部自证", r"至少载明一项", r"必须携带",
                           r"须载明", r"须载", r"须填", r"须标", r"须写", r"须含", r"须回绑"]),
    (CODE_INPUT_FORMAT, [r"仅接受", r"仅受理", r"仅\s*[\w-]+／", r"仅\s*[\w-]+=", r"过大", r"过长", r"须为", r"长度", r"非法", r"非合法", r"强度不足", r"须 ≥",
                         r"须 1~", r"格式", r"过滤值", r"超出", r"不得为负", r"不得晚于", r"不一致", r"无效",
                         r"依赖错误", r"未知", r"V-\d", r"E\.credential", r"SCOPE_REQUIRED", r"CLAIM_TOO_LONG", r"FORMULA_DETECTED",
                         r"NUMERIC_REF", r"INTERNAL_ID_DETECTED", r"须阅读并同意"]),
    (CODE_AUTHZ_PERM, [r"非有权", r"不可绕", r"仅\s*(?:founder|operator|登记主体|本人|创建人|权属登记人)",
                       r"无权", r"GRANT_REQUIRED", r"FORBIDDEN", r"仅查询", r"不可操作", r"不得代", r"PUNISH_FORBIDDEN",
                       r"PRS_FORBIDDEN", r"RESTORE_FORBIDDEN"]),
    (CODE_STATE_STATE, [r"非.{0,6}态", r"终态", r"跳步", r"未过", r"未达", r"未重塑", r"未验证", r"未加载",
                        r"STEP_ORDER", r"STATE", r"非 active", r"无返回路径", r"状态为", r"不得正空间", r"不得进沙盒",
                        r"OUT_OF_SCOPE", r"范围外"]),
]

_STATUS_FALLBACK = {401: CODE_IDENT_PERM, 403: CODE_AUTHZ_PERM, 404: CODE_ASSET_STATE,
                    409: CODE_STATE_STATE, 429: CODE_RES_LIMIT, 500: CODE_SYS_SYS,
                    502: CODE_EXT_EXT, 503: CODE_EXT_EXT}


def classify(status: Optional[int], detail: Any) -> str:
    """拒绝响应 → 错误码。纯函数；无法归类 → SYS-SYS-001（令 §二.3）。"""
    text = detail if isinstance(detail, str) else ""
    if text:
        for code, patterns in _RULES:
            if any(re.search(p, text) for p in patterns):
                return code
    return _STATUS_FALLBACK.get(int(status), CODE_SYS_SYS) if status is not None else CODE_SYS_SYS


# ---------------------------------------------------------------------------
# FastAPI 全局异常 handler（注册见 app.py；⛔ 不改状态码与文案，仅增设 code 字段）
# ---------------------------------------------------------------------------
async def tdca_http_exception_handler(request: Any, exc: Any) -> Any:
    """HTTPException（含 Starlette）→ 原 detail ＋ code。head=原样。"""
    from fastapi.responses import JSONResponse
    code = classify(getattr(exc, "status_code", None), getattr(exc, "detail", None))
    detail = getattr(exc, "detail", None)
    # P0 处置令（SITE-WALK-001 §二.3）：仅 404 框架默认文案加区分线索，
    # code 由上方 classify 按原文判定（保持不变），只加 detail 措辞。
    if getattr(exc, "status_code", None) == 404 and isinstance(detail, str) \
            and detail == "Not Found":
        detail = "Not Found（该端点未上线或不存在）"
    return JSONResponse({"detail": detail, "code": code},
                        status_code=exc.status_code, headers=getattr(exc, "headers", None))


async def tdca_validation_exception_handler(request: Any, exc: Any) -> Any:
    """RequestValidationError（422，框架校验）→ 原 detail ＋ code=INPUT-002（码表注③）。"""
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import ResponseValidationError
    from fastapi.responses import JSONResponse
    if isinstance(exc, ResponseValidationError):
        # 出向模型校验失败：非用户输入问题，按系统错误挂码
        return JSONResponse({"detail": jsonable_encoder(exc.errors()), "code": CODE_SYS_SYS},
                            status_code=500)
    return JSONResponse({"detail": jsonable_encoder(exc.errors()), "code": CODE_INPUT_FORMAT},
                        status_code=422)


def with_code(deny: dict, status_code: int) -> dict:
    """鉴权中间件/裸 JSONResponse 拒绝体补 code（原字段不动，仅增设）。"""
    deny = dict(deny)
    deny["code"] = classify(status_code, deny.get("detail") or deny.get("error") or "")
    return deny
