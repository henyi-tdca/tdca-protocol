# -*- coding: utf-8 -*-
"""
P9 规范索引区与最小挂接（入册面配套）：/api/v1/regulations/*。

口径（组四 P9 要件 2）：
  - 站内以在册规范为唯一权威源——本区只列名目与索引入口；
    ⛔ 不复制正文、⛔ 不另存副本、⛔ 不重写条文；
  - 版本读件内真实值（机读版 version 字段），⛔ 不硬编码；
    生效状态读在仓注记件——两者分源标注（照 P4 模板区同口径）；
  - 与 P7 运维端红线第八项（登记制度）之索引入口同源一致（ops_ops 引用本区 helper）；
  - 未入册件如实报「未收录」（⛔ 不冒充、⛔ 不自拟正文）；
    以其为权威源的挂接端点缺失时 503 fail-closed。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from api_v1 import _nca_watermark, _require_session_user  # noqa: E402
# 与 P4 模板区同源一致：版本/生效读取复用 toolshelf_ops 之 helper（⛔ 不另起口径）
from toolshelf_ops import (  # noqa: E402
    _EFFECTIVE_NOTE, _TEMPLATE_DIR, _TEMPLATE_FILES,
    _effective_from_note, _version_from_machine,
)

router = APIRouter(prefix="/api/v1/regulations", tags=["regulations"])

_REGULATIONS_DIR = _TEMPLATE_DIR  # docs/regulations/（索引区唯一落点）

# 规范索引登记（只列名目与在仓状态；⛔ 不复制正文）
# 《授权件模板》已入册（件名以在册为准）；《注册登记制度》《配置权市场规范》
# 待创始人转交权威件后入册——此处仅以文件名关键词探测收录状态，缺失如实报。
_REGULATIONS = [
    {"key": "template_auth", "name": "《授权件模板》", "doc_id": "TDCA-TEMPLATE-AUTH-001"},
    {"key": "registration_registry", "name": "《TDCA 注册登记制度》",
     "doc_id": "TDCA-REG-REGISTRY（入册件号以转交件为准）"},
    {"key": "config_market", "name": "《配置权市场规范》",
     "doc_id": "TDCA-REG-MARKET（入册件号以转交件为准）"},
]

_KEYWORD_BY_KEY = {
    "template_auth": "TDCA-TEMPLATE-AUTH-001",
    "registration_registry": "注册登记制度",
    "config_market": "配置权市场",
}


def _regulation_files(key: str) -> list:
    """在仓件清单（只报文件名/sha256_8/字节数；⛔ 不回显正文）。"""
    kw = _KEYWORD_BY_KEY.get(key, key)
    out = []
    for fpath in sorted(_REGULATIONS_DIR.glob(f"*{kw}*")):
        if fpath.is_file():
            raw = fpath.read_bytes()
            out.append({"filename": fpath.name,
                        "sha256_8": hashlib.sha256(raw).hexdigest()[:8],
                        "bytes": len(raw)})
    return out


def regulation_index_entry(key: str) -> dict:
    """单件索引（P7 红线第八项同源引用本 helper——保证索引入口一致）。"""
    spec = next((s for s in _REGULATIONS if s["key"] == key), None)
    if spec is None:
        raise KeyError(key)
    files = _regulation_files(key)
    present = bool(files)
    entry = {"key": key, "name": spec["name"], "doc_id": spec["doc_id"],
             "present": present, "files": files,
             "index_dir": "docs/regulations/",
             "note": ("已入册（引用在仓、逐字一致）" if present
                      else "未入册（索引区未收录）——不另存副本、不自拟正文；"
                           "以创始人转交之权威件为准")}
    if key == "template_auth" and present:
        # 版本/生效分源读取（与 P4 模板区同一 helper，零口径分叉）
        machine = _REGULATIONS_DIR / dict(
            (lang, fname) for lang, fname in _TEMPLATE_FILES)["machine"]
        if machine.is_file():
            entry["version"] = _version_from_machine(
                machine.read_text(encoding="utf-8"))
            entry["version_source"] = "机读版件内 version 字段（逐字读取，非硬编码）"
        eff = _effective_from_note()
        entry["effective_status"] = eff["effective"]
        entry["effective_source"] = eff["source"] + "（GSEQ-3626 创始人签批）"
    elif present:
        # 通用读取：机读版 version 字段＋生效注记件（对将来入册两件同口径生效）
        machine = next((f for f in files if f["filename"].endswith(".yaml")), None)
        if machine:
            entry["version"] = _version_from_machine(
                (_REGULATIONS_DIR / machine["filename"]).read_text(encoding="utf-8"))
            entry["version_source"] = "机读版件内 version 字段（逐字读取，非硬编码）"
        note = next((f for f in files if "生效注记" in f["filename"]), None)
        if note:
            m = re.search(r"(V\d+\.\d+-FROZEN)",
                          (_REGULATIONS_DIR / note["filename"])
                          .read_text(encoding="utf-8"))
            entry["effective_status"] = m.group(1) if m else "UNKNOWN"
            entry["effective_source"] = f"docs/regulations/{note['filename']}"
    return entry


@router.get("/index")
def regulations_index(request: Request):
    """规范索引区总目（只列名目与在仓状态；版本/生效读件内，⛔ 不硬编码）。"""
    _require_session_user(request)
    return _nca_watermark({
        "simulated": True,
        "index_dir": "docs/regulations/",
        "principle": "以在册规范为唯一权威源——只列名目与索引入口；"
                     "⛔ 不复制正文、⛔ 不另存副本、⛔ 不重写条文",
        "regulations": [regulation_index_entry(s["key"]) for s in _REGULATIONS],
        "note": "《注册登记制度》《配置权市场规范》待创始人转交权威件后入册；"
                "未入册前依赖端点一律 503 fail-closed（不冒充在册）"})


@router.get("/spec/{key}")
def regulation_spec(key: str, request: Request):
    """单件索引入口（配置权市场规范等挂接端点；未入册 ⟹ 503 fail-closed）。"""
    _require_session_user(request)
    try:
        entry = regulation_index_entry(key)
    except KeyError:
        raise HTTPException(404, "规范键不存在")
    if not entry["present"]:
        raise HTTPException(
            503, f"SPEC_UNAVAILABLE: {entry['name']} 未入册（docs/regulations/ 索引区未收录）"
                 "——不另存副本、不自拟正文；以创始人转交之权威件为准")
    return _nca_watermark({"simulated": True, "spec": entry,
                           "note": "引用在仓、逐字一致；⛔ 不回显正文于公开面"})
