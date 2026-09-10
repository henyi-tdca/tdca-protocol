# -*- coding: utf-8 -*-
"""ATH 令牌 → 配置权边界切片 / 会话初始化（G4 余项之二）

制度依据:
  - TDCA 内部分析（TDCA 存证）§二/§三：ATH 令牌 = **配置权边界的瞬时切片**，非等价物
  - TDCA 层间规范 §四：ATH 握手/令牌 → 配置权鉴别与边界切片

关键制度点:
  握手成功 ≠ 调用权授予。ATH 令牌只给出「边界切片」（能连、能谈什么），
  转为**调用权**必须经 TDCA 侧 **CCV 五层 + 正和评估**（复用 S-Right 网关）。

纪律:
  - 切片显式标注 `NON_EQUIVALENT`（非配置权等价物）
  - 令牌须含 id/subject/boundary/expires_at；过期/缺字段即拒（fail-closed）
  - 数据性质: 模拟态
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

X_PREFIX = "x-tdca-"


class AthTokenError(Exception):
    """ATH 令牌映射纪律违例。"""


def token_to_boundary_slice(token: Dict[str, Any]) -> Dict[str, Any]:
    """ATH 握手令牌 → 配置权边界切片（瞬时）。"""
    for f in ("token_id", "subject", "boundary", "expires_at"):
        if not token.get(f):
            raise AthTokenError(f"令牌缺必填字段: {f}")
    try:
        expired = datetime.fromisoformat(str(token["expires_at"])) <= datetime.now().astimezone()
    except Exception as exc:
        raise AthTokenError(f"expires_at 非法: {exc}") from exc
    if expired:
        raise AthTokenError("令牌已过期（fail-closed）")

    return {
        "slice_id": f"BS-{token['token_id']}",
        "holder": token["subject"],
        "boundary": token["boundary"],
        "scope_capabilities": list(token.get("capabilities") or []),
        "expires_at": token["expires_at"],
        # 制度点：切片非配置权等价物；转调用权须经 CCV + 正和
        "equivalence": "NON_EQUIVALENT",
        "requires_ccv": True,
        "security_baseline": token.get("security_baseline", "standard"),
        f"{X_PREFIX}source": "ath-token",
        f"{X_PREFIX}note": "握手/令牌 = 边界瞬时切片；调用权须经 CCV 五层 + 正和评估",
        f"{X_PREFIX}simulated": True,
    }


def handshake_to_session(ath_result: Dict[str, Any]) -> Dict[str, Any]:
    """ATH 握手结果 → 配置权会话初始化（会话 ≠ 调用权）。"""
    if not ath_result.get("handshake_ok"):
        raise AthTokenError("握手未成功（handshake_ok=false）")
    token = ath_result.get("token") or {}
    slice_ = token_to_boundary_slice(token)
    return {
        "session": {"session_id": f"PCS-{token['token_id']}",
                    "holder": slice_["holder"], "boundary": slice_["boundary"],
                    "state": "INITIALIZED"},
        "boundary_slice": slice_,
        "call_right_granted": False,      # 会话初始化不授予调用权
        "next": "S-Right CCV 五层 + 正和评估 → 授予调用权",
        f"{X_PREFIX}simulated": True,
    }


def slice_to_call_request(slice_: Dict[str, Any], *, tool_id: str, scene: str,
                          coalition_utility: float,
                          independent_utilities: Optional[List[float]] = None,
                          budget_cost: float = 0.0, oid: Optional[str] = None):
    """边界切片 → S-Right 调用请求（经 CCV 五层后方可授予——复用 M2 网关）。"""
    from sright import CallRequest  # type: ignore  # 同仓模块（延迟导入）
    return CallRequest(
        caller_tdid=slice_["holder"], tool_id=tool_id, scene=scene,
        coalition_utility=coalition_utility,
        independent_utilities=list(independent_utilities or []),
        budget_cost=budget_cost, oid=oid, payload={})
