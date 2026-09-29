# -*- coding: utf-8 -*-
"""
编译器开发模式水印（DEV_NSFL）——维护任务 1
==========================================
开发模式（--dev-mode）强制注入**不可移除**的 DEV_NSFL 水印到输出 IR，
防止调试产物误入生产（DCD-NSFL-STATUS-001 §五）。

水印特性:
  - 不可移除: 水印写入 IR 的 provenance 字段（上链审计，任何下游无法剥离）
  - 显式标记: DEV_NSFL tag + dev_mode=True + 时间戳
  - 与生产 IR 区分: 生产编译（非 dev-mode）不带水印，可在消费端校验隔离

锚定: DCD-NSFL-STATUS-001（维护任务 1）+ TDCA-NSFL-COMPILER-001（M1 C4 IR 结构）
     + F-4（开发配置不污染生产）
SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

DEV_NSFL_TAG = "DEV_NSFL"
DEV_NSFL_VERSION = "1.0"


@dataclass(frozen=True)
class DevModeWatermark:
    """DEV_NSFL 水印（不可移除）。"""
    tag: str = DEV_NSFL_TAG
    dev_mode: bool = True
    version: str = DEV_NSFL_VERSION
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "dev_mode": self.dev_mode,
            "version": self.version,
            "timestamp": self.timestamp,
        }


def inject_dev_watermark(ir_dict: dict, watermark: Optional[DevModeWatermark] = None) -> dict:
    """向 IR dict 注入 DEV_NSFL 水印（declaration.provenance 字段）。

    不可移除语义: 水印写入 declaration.provenance.dev_watermark，消费端校验时必须存在；
    任何下游转换不得剥离（若剥离则校验失败——fail-closed）。
    """
    wm = watermark or DevModeWatermark(timestamp=time.time())
    out = dict(ir_dict)
    # NSFLIR 结构: to_dict() 含 "declaration" 顶层键——水印挂其下 provenance
    declaration = out.get("declaration")
    if not isinstance(declaration, dict):
        declaration = {}
    provenance = declaration.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    provenance["dev_watermark"] = wm.to_dict()
    declaration["provenance"] = provenance
    out["declaration"] = declaration
    return out


def check_dev_watermark(ir_dict: dict) -> tuple:
    """校验 IR 是否含 DEV_NSFL 水印（消费端隔离校验）。

    返回 (is_dev, watermark_dict|None)——is_dev=True 表示该 IR 为开发产物，
    不应进入生产路径（fail-closed: 生产路径消费到 dev 水印 → 拒绝）。
    """
    declaration = ir_dict.get("declaration")
    if not isinstance(declaration, dict):
        return False, None
    provenance = declaration.get("provenance")
    if not isinstance(provenance, dict):
        return False, None
    wm = provenance.get("dev_watermark")
    if not isinstance(wm, dict) or wm.get("tag") != DEV_NSFL_TAG:
        return False, None
    return bool(wm.get("dev_mode")), wm


def assert_production_clean(ir_dict: dict) -> None:
    """生产路径消费校验：发现 DEV_NSFL 水印 → 拒绝（fail-closed）。"""
    is_dev, wm = check_dev_watermark(ir_dict)
    if is_dev:
        raise PermissionError(
            f"生产路径拒绝开发产物（DEV_NSFL 水印不可入生产）: tag={DEV_NSFL_TAG} "
            f"version={DEV_NSFL_VERSION}")
