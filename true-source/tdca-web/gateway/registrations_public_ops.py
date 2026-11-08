# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: TDCA-FC-PUBLIC-REG-001 | 目标函数: 首批三族内部权属登记·公域只读面
# 约束矩阵: HANDOFF-EXEC-L1SI204-RIGHTS-GENESIS-007（步4）——新建匿名只读面，
#           ⛔ 放开既有 401 登录面充数；⛔ 任何写操作；四项可查字段；
#           三组字与双向两行（TDCA-STD-PROOF-BOUNDARY-001 应用点3）逐字必带；
#           不公开四条零命中（内部编号／凭据密钥／自然人敏感信息／负空间词面）。
# 口径: 只读（GET）；仅列登记记录号 OR-G7-* 之首批记录（⛔ 带出表内其他记录）；
#       定名「内部权属登记（建设期）」（TDCA-AMEND-L1SI204-RIGHTS-STAGING-001），
#       ⛔ 「确权登记」。
# =============================================================================
from __future__ import annotations

import re
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/public/registrations", tags=["public-registrations"])

_DB = "/data/tdca.db"

_LABELS = {
    "stamp1": "建设期内部登记",
    "stamp2": "法定确权另行申请，正式实行时由国家可信版权链办理",
    "stamp3a": "获取方式 ≠ 已获授权",
    "stamp3b": "未登记者视为不存在",
    "provable": "本登记可证：内容于登记时点之字节与哈希、时间戳、提交主体标识、链上序号与前序衔接（第三方可复算）。",
    "not_provable": "本登记不可证：权利是否成立、作品是否独创、是否不侵害第三人权利、能否对抗第三人。",
}


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB, timeout=15)
    c.row_factory = sqlite3.Row
    return c


def _fam_of(source_lineage: str) -> str:
    s = source_lineage or ""
    if "/regulations/" in s:
        return "regulation"
    if "cop-library" in s:
        return "cop-library"
    if "whitepaper" in s:
        return "whitepaper"
    return "other"


def _parse_note(note: str) -> dict:
    short = re.search(r"短值 ([0-9A-F]{16})", note or "")
    size = re.search(r"字节 (\d+)", note or "")
    return {"short": short.group(1) if short else None,
            "bytes": int(size.group(1)) if size else None}


# 内部编号式隐去（令 -007 §三「不公开四条」之内部编号式零命中）：
# 仅面侧遮蔽来源路径中的 TDCA-编号段（⛔ 动库动件；题名经核 645 条全净）。
_ID_PAT = re.compile(r"TDCA-[A-Z0-9-]*\d{3,}-?")


def _mask_lineage(lineage: str) -> str:
    return _ID_PAT.sub("〔内部编号已隐去〕", lineage or "")


def _face() -> dict:
    """三组字＋双向两行（逐字常量，令 -007 §三）。"""
    return {
        "labels": [_LABELS["stamp1"], _LABELS["stamp2"],
                   _LABELS["stamp3a"], _LABELS["stamp3b"]],
        "proof_boundary": {
            "provable": _LABELS["provable"],
            "not_provable": _LABELS["not_provable"],
        },
    }


def _four_fields(rec: sqlite3.Row, meta: dict) -> dict:
    """四项可查字段（令 -002 §四 / -007 §三）。"""
    return {
        "ownership_info": {
            "登记题名": rec["work_title"],
            "登记记录号": rec["record_id"],
            "内容哈希短值": meta["short"],
            "字节数": meta["bytes"],
            "登记时间戳": rec["created_at"],
            "链上序号": rec["nca_ref"],
            "来源路径": _mask_lineage(rec["source_lineage"]),
        },
        "authorization_info": "本登记不含对外授权信息；授权凭据只记存在（备注位丙栏）。",
        "authorization_status": "无对外授权记录（未登记者视为不存在）。",
        "access_method": "站内公开阅读（制度栏／文库对应族面）；" + _LABELS["stamp3a"],
    }


@router.get("")
def registrations_list():
    """首批三族内部权属登记·匿名只读面（列表）。⛔ 开放写操作；⛔ 登录要求。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT record_id,work_title,source_lineage,created_at,nca_ref,status,note"
            " FROM ownership_records WHERE record_id LIKE 'OR-G7-%' ORDER BY record_id").fetchall()
    items = []
    for r in rows:
        meta = _parse_note(r["note"])
        items.append({
            "record_id": r["record_id"],
            "title": r["work_title"],
            "family": _fam_of(r["source_lineage"]),
            "content_sha256_16": meta["short"],
            "registered_at": r["created_at"],
            "nca_ref": r["nca_ref"],
            "status": r["status"],
        })
    out = {"face": "内部权属登记（建设期）", "count": len(items), "items": items}
    out.update(_face())
    return out


@router.get("/{record_id}")
def registration_detail(record_id: str):
    """单条登记详页：四字段＋备注节＋三组字＋双向两行。"""
    if not re.fullmatch(r"OR-G7-[0-9A-F]{8}", record_id):
        raise HTTPException(404, "RECORD_NOT_FOUND: 登记记录不存在")
    with _conn() as c:
        r = c.execute(
            "SELECT record_id,work_title,owner_ref,expression_form,jurisdiction_branch,"
            " source_lineage,scene,status,note,nca_ref,created_at,updated_at"
            " FROM ownership_records WHERE record_id=? AND record_id LIKE 'OR-G7-%'",
            (record_id,)).fetchone()
    if r is None:
        raise HTTPException(404, "RECORD_NOT_FOUND: 登记记录不存在")
    meta = _parse_note(r["note"])
    out = {
        "face": "内部权属登记（建设期）",
        "family": _fam_of(r["source_lineage"]),
        "fields": _four_fields(r, meta),
        "note_section": r["note"],
        "record_meta": {
            "提交主体标识": r["owner_ref"],
            "表达形式": r["expression_form"],
            "法域归口": r["jurisdiction_branch"],
            "登记状态": r["status"],
            "updated_at": r["updated_at"],
        },
    }
    out.update(_face())
    return out


@router.get("/{record_id}/evidence")
def registration_evidence(record_id: str):
    """证据包导出（四栏一式·只读；令 -004 §三）。

    仅供向法定机构提交与内部留档；⛔ 公开发布。"""
    if not re.fullmatch(r"OR-G7-[0-9A-F]{8}", record_id):
        raise HTTPException(404, "RECORD_NOT_FOUND: 登记记录不存在")
    with _conn() as c:
        r = c.execute(
            "SELECT record_id,work_title,source_lineage,note,nca_ref,created_at"
            " FROM ownership_records WHERE record_id=? AND record_id LIKE 'OR-G7-%'",
            (record_id,)).fetchone()
        ch = c.execute(
            "SELECT nca_id,prev_nca,ts,rec_hash,prev_hash FROM nca_chain WHERE nca_id=?",
            (r["nca_ref"],)).fetchone() if r else None
    if r is None:
        raise HTTPException(404, "RECORD_NOT_FOUND: 登记记录不存在")
    note = r["note"] or ""
    full = re.search(r"内容哈希（sha256）：([0-9A-F]{64})", note)
    short = re.search(r"短值 ([0-9A-F]{16})", note)
    size = re.search(r"字节 (\d+)", note)
    return {
        "用途声明": "本导出仅供向法定机构提交与内部留档，⛔ 公开发布；不含签名值与姓名。",
        "栏一_件名与路径": {"件名（净名）": r["work_title"], "路径": _mask_lineage(r["source_lineage"])},
        "栏二_内容哈希与字节": {
            "sha256 全值": full.group(1) if full else None,
            "sha256 短值": short.group(1) if short else None,
            "字节数": int(size.group(1)) if size else None,
        },
        "栏三_登记时间戳与记录号": {
            "登记时间戳": r["created_at"], "登记记录号": r["record_id"],
        },
        "栏四_链段": {
            "当条链号": ch["nca_id"] if ch else None,
            "前序衔接": ch["prev_nca"] if ch else None,
            "链记录时间": ch["ts"] if ch else None,
            "当条自哈希": ch["rec_hash"] if ch else None,
            "前序哈希": ch["prev_hash"] if ch else None,
        },
    }
