# -*- coding: utf-8 -*-
"""L1SI218-OPSACCEPT-001-001 验收记录私域面（运维栏目机面）：GET /api/v1/ops/acceptance-records。

口径（TDCA-AMEND-L1SI218-OPSACCEPT-001-001「结论可公示·作业入私域」）：
  - 私域面：全量验收记录（含作业/处置/留痕内部字段），⛔ 公开列表面
    （acceptance_ops 之裸 GET 守卫不动，公开仍只可按号查 /{acceptance_id}）；
  - 访问：人类须登录（照 /ops 惯例）；机面走授权前置闸（O-1 只读放行，require_ops_caller 统一入口）；
  - 公示结论面在 /acceptance（公开读），机面为 /api/v1/acceptance/{id}，两栏对得上（R-2/H-4）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Request

from ops_auth_gate import require_ops_caller as _require_ops_caller  # noqa: E402
from api_v1 import _nca_watermark  # noqa: E402  # WATERMARK-FIX-002：前端取件闸要求 NCA 水印信封

router = APIRouter(prefix="/api/v1/ops/acceptance-records",
                   tags=["ops-acceptance-records"])

_STORE_ENV = "TDCA_ACCEPTANCE_DIR"
_DEFAULT_STORE = "/data/acceptance"
_ACC_FILE_RE = re.compile(r"^ACC-[0-9a-f]{10}\.json$")


@router.get("")
def acceptance_records_list(request: Request):
    """私域全量列表（登录或 O-1 授权）；坏件跳过不反转（写入侧 fail-closed）。"""
    _require_ops_caller(request)  # 人类会话照原路；机面 O-1 只读放行（闸内校验授权件）
    d = Path(os.environ.get(_STORE_ENV, _DEFAULT_STORE))
    docs = []
    if d.is_dir():
        for p in sorted(d.iterdir()):
            if not _ACC_FILE_RE.match(p.name):
                continue  # 冻件 *.freeze.json 与临时件 ⛔ 混入
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if isinstance(doc, dict) and doc.get("acceptance_id"):
                docs.append(doc)
    return _nca_watermark(
        {"count": len(docs), "records": docs,
         "note": "私域运维面：全量验收记录（含作业/处置/留痕）；公示结论面 /acceptance（公开读）"})
