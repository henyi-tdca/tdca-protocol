# -*- coding: utf-8 -*-
"""
B1-001：三态可读面 —— GET /api/v1/three-state/{negative-space|sandbox|positive-space}（匿名只读）。

口径（令 TDCA-HANDOFF-EXEC-L1SI228-B1-001）：
  - 单一数据源：three_state_data.py 静态清单（NEGATIVE_SPACE／SANDBOX／POSITIVE_SPACE），
    页与接口同取一处，⛔运行时现算、⛔第二处维护（H-3）；
  - 负空间：五类×三操作符十五格逐格有交代（空格须带理由＋依据，⛔留空⛔写「无」了事）；
    条款级清单——词面级禁项属「不公开四条」边界，本接口不载词面（H-5）；
  - 沙盒：可行域两源（负空间清单引用＋场景允许域）＋功能/安全/性能/合规分项，
    无解情形如实写「本批无解」＋理由（⛔一句达标）；
  - 正空间：认读文件——人可读正文、逐项对存证一致、给复算路径、带仓端提交号＋件哈希（1-9/1-10/1-11）；
  - 人读字段零内部编号（H-4：⛔ GSEQ/NCA-编号/块号/FC 号入人读正文）；
  - 失败闭合（H-6）：数据模块缺失即 503，⛔放行后补；
  - 三态各一条可点入口（B1-4）：负空间页 /negativespace、沙盒页 /sandbox、正空间认读段在 /rules 页；
    页运行时直读本接口渲染，三态⛔互换（禁止清单⛔当执行令、沙盒解⛔直进正空间、认读文件⛔代存证）。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from three_state_data import NEGATIVE_SPACE, POSITIVE_SPACE, SANDBOX
    _LOAD_ERROR = None
except Exception as exc:  # fail-closed（H-6）：载入失败即 503，⛔放行后补
    NEGATIVE_SPACE = SANDBOX = POSITIVE_SPACE = None
    _LOAD_ERROR = repr(exc)

router = APIRouter(prefix="/api/v1/three-state", tags=["three-state"])

VERSION_META = {
    "negative_space": "B1-1",
    "sandbox": "B1-2",
    "positive_space": "B1-3",
}


def _unavailable(what: str) -> JSONResponse:
    return JSONResponse(
        {"error": "THREE_STATE_SOURCE_UNAVAILABLE", "what": what, "detail": f"数据模块载入失败：{_LOAD_ERROR}"},
        status_code=503,
    )


@router.get("/negative-space")
def three_state_negative_space():
    """负空间清单式呈现（B1-1）：五类×三操作符十五格，逐格条款或理由＋依据，匿名只读。"""
    if NEGATIVE_SPACE is None:
        return _unavailable("negative-space")
    return NEGATIVE_SPACE


@router.get("/sandbox")
def three_state_sandbox():
    """沙盒可行域＋四维分项（B1-2）：可行域两源＋功能/安全/性能/合规分项读数与证据件。"""
    if SANDBOX is None:
        return _unavailable("sandbox")
    return SANDBOX


@router.get("/positive-space")
def three_state_positive_space():
    """正空间认读文件（B1-3）：生效制度件选编，人可读＋复算路径＋仓端提交号＋件哈希。"""
    if POSITIVE_SPACE is None:
        return _unavailable("positive-space")
    return POSITIVE_SPACE
