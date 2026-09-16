#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L1-active.json 分轨加载（V1.1-REV 过渡期规则 · SIL 模拟态）。

对应 tdca-firmware-spec-V1.1-REV.md §二（过渡期处置，三段式）：
  旧版轨（允许列表标注 hmac-only）  → 无 SE 签名不拒载；HMAC 校验失败 → 标记降级
  新版轨（允许列表标注 se-required）→ 签名缺失/形状非法 → 拒载 + [SIGNATURE-FAIL]
  未知版本                           → fail-closed 拒载（版本门禁既有口径）

模拟态标注：本模块为 SIL 模拟——签名值与 HMAC 均为模拟占位，仅验结构、不验密码学
（真实 SM2 验签在 A7100 SE 侧）；通知机硬件未投产部署，不构成真实部署。
"""
from __future__ import annotations

import json
from pathlib import Path

# 模拟允许列表（对应规范「固件版本允许列表」逐版本标注校验级别）
FIRMWARE_L1_LEVELS = {
    "1.0.0-sim": "hmac-only",     # 旧版轨：HMAC 路径，不拒载
    "1.1.0-sim": "se-required",   # 新版轨（V1.1-REV 适用版）：SE 签名强制，失败即拒载
}


class L1ActiveRejected(Exception):
    """L1-active.json 拒载（新版轨验签失败 / 未知版本 fail-closed）。"""


def _se_sign_well_formed(l1: dict) -> bool:
    """SE 签名形状校验（SIL：模拟占位，仅验结构不验密码学）。"""
    sign = l1.get("sign")
    return (isinstance(sign, dict) and sign.get("alg") == "SM2"
            and isinstance(sign.get("value"), str) and len(sign["value"]) > 0)


def load_l1_active(tdca_dir, firmware_version: str) -> dict:
    """按固件版本轨加载 session-index/L1-active.json（V1.1-REV 过渡期规则，SIL）。

    返回 {"loaded": bool, "track": str, "degraded": bool, "marker": str|None, "l1": dict}
    拒载时抛出 L1ActiveRejected（消息含 [SIGNATURE-FAIL] 或 [UNKNOWN-FIRMWARE]）。
    """
    level = FIRMWARE_L1_LEVELS.get(firmware_version)
    if level is None:
        # 未知版本 → fail-closed（不放行）
        raise L1ActiveRejected("[UNKNOWN-FIRMWARE] version={} not in allow-list".format(firmware_version))
    p = Path(tdca_dir) / "session-index" / "L1-active.json"
    l1 = json.loads(p.read_text(encoding="utf-8"))
    if level == "se-required":
        # 新版轨：验签失败即拒载（SIL 为形状校验占位）
        if not _se_sign_well_formed(l1):
            raise L1ActiveRejected("[SIGNATURE-FAIL] session-index/L1-active.json "
                                   "(track=se-required, version={})".format(firmware_version))
        return {"loaded": True, "track": level, "degraded": False, "marker": None, "l1": l1}
    # 旧版轨：无 SE 签名不拒载；HMAC 校验失败 → 标记降级（不拒载）
    hmac = l1.get("hmac")
    degraded = hmac is not None and (not isinstance(hmac, str) or not hmac.startswith("sm3:"))
    return {"loaded": True, "track": level, "degraded": degraded,
            "marker": "HMAC-DEGRADED" if degraded else None, "l1": l1}
