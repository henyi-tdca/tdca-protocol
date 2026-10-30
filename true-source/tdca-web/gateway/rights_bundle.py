# -*- coding: utf-8 -*-
"""权利束＋保留束 过渡承载（BUNDLE-001）：note 以 #RB 前缀＋单行 JSON 承载；
stage=transition 标过渡，日后立字段（迁移 0021：rights_granted/rights_retained
两列）时从 #RB 前缀批量回填，⛔ 手工补录。本模块 ⛔ 不改表、⛔ 不建字段。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import re

RB_PREFIX = "#RB"
RB_BASIS = "著作权法第10条(五)~(十七)"
RB_STAGE = "transition"

# 十三项法定名（⛔ 自造译名、⛔ 简称）
RB_THIRTEEN = ("复制权", "发行权", "出租权", "展览权", "表演权", "放映权",
               "广播权", "信息网络传播权", "摄制权", "改编权", "翻译权",
               "汇编权", "其他权利")

# 单行 JSON、单层对象（无嵌套花括号）
_RB_JSON = re.compile(r"\{[^{}]*\}")


def rb_parse(note: str) -> tuple[str, dict | None, str | None]:
    """解析并校验 #RB 过渡块。

    返回 (note_out, bundle, anomaly)：
      - note 不以 #RB 开头 → 原样返回 (note, None, None)（普通备注不干预）；
      - 校验失败 → ValueError（人话消息，端点转 400）；
      - 通过 → (规范化 note, bundle, anomaly)。
    多条 #RB：以最后一条为准，anomaly 报重复；用户原文 ⛔ 不删。
    """
    text = note or ""
    if not text.startswith(RB_PREFIX):
        return text, None, None
    anomaly = None
    starts = [i for i in range(len(text)) if text.startswith(RB_PREFIX + "{", i)]
    if len(starts) > 1:
        anomaly = ("note 含多条 #RB 前缀——以最后一条为准（重复前缀报异常）")
    pos = starts[-1] + len(RB_PREFIX)
    m = _RB_JSON.match(text, pos)
    if not m:
        raise ValueError("#RB 前缀后须为单行 JSON 对象（如 "
                         "#RB{\"granted\":[...],\"retained\":[...],"
                         "\"basis\":\"" + RB_BASIS + "\","
                         "\"stage\":\"" + RB_STAGE + "\"}）")
    trailing = text[m.end():]
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        raise ValueError("#RB 前缀后须为单行 JSON 对象——解析失败")
    if not isinstance(obj, dict):
        raise ValueError("#RB 前缀后须为 JSON 对象")
    for key in ("granted", "retained", "basis", "stage"):
        if key not in obj:
            raise ValueError(f"#RB 缺少必填键 {key}（granted／retained／basis／stage）")
    granted, retained = obj["granted"], obj["retained"]
    for key, val in (("granted", granted), ("retained", retained)):
        if not isinstance(val, list) or any(not isinstance(x, str) for x in val):
            raise ValueError(f"#RB 之 {key} 须为字符串数组")
        for item in val:
            if item not in RB_THIRTEEN:
                raise ValueError(f"'{item}'不是法定项名，请从清单中选"
                                 f"（{'／'.join(RB_THIRTEEN)}）")
    if obj["basis"] != RB_BASIS:
        raise ValueError(f"#RB 之 basis 为固定值，须照抄：{RB_BASIS}")
    if obj["stage"] != RB_STAGE:
        raise ValueError(f"#RB 之 stage 为固定值，须照抄：{RB_STAGE}")
    if "其他权利" in (*granted, *retained) and not trailing.strip():
        raise ValueError("选「其他权利」须附一句说明（写在 #RB JSON 之后）")
    norm = RB_PREFIX + json.dumps(
        {"granted": granted, "retained": retained,
         "basis": RB_BASIS, "stage": RB_STAGE}, ensure_ascii=False) + trailing
    return norm, {"granted": granted, "retained": retained}, anomaly
