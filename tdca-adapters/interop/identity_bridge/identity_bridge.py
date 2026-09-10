# -*- coding: utf-8 -*-
"""TDCA 身份桥接（Identity Bridge）——TDID ↔ 国标身份码（OID）映射

制度依据:
  - TDCA 身份管理规范 V1.1 §二/§四 —— 作用域界分与外部链接层
    （TDCA 范围内身份主键 = TDID；走出范围以国标身份码建立链接；
     链接行为本身生成可审计存证；映射不回写内部身份基线）
  - TDCA 身份管理规范（身份桥接映射规范，字段级）

纪律（强制）:
  - 映射行为必须存证（fail-closed：无 NCA 生成器不建立映射）
  - 一个国标身份码同一时刻仅链接一个 TDID（对齐"一码一智能体"语义）
  - 失效同步：撤销映射即终止链接（历史记录保留可溯）
  - 数据性质: 模拟态 —— OID 仅作格式校验与链接占位，不构成真实国标注册
  - 不回写内部基线：内部主键始终为 TDID，OID 仅作外部链接字段

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# TDID: 通知机硬件根身份（SHA256(PUF‖宪法哈希‖批次号) 前 32 位大写十六进制）
_TDID_RE = re.compile(r"^TDID-[0-9A-F]{32}$")
# OID: GB/T 26231 分层标识（前缀 1.2.156 + 内容层；此处校验前 4 层前缀 + ≥2 内容层，模拟态简化）
_OID_RE = re.compile(r"^1\.2\.156\.\d+(\.\d+){2,}$")

ACTIVE = "ACTIVE"
REVOKED = "REVOKED"


class IdentityBridgeError(Exception):
    """身份桥接纪律违例（格式/冲突/存证缺失）。"""


@dataclass
class IdentityLink:
    """一条 TDID ↔ OID 链接记录（映射即存证载体）。"""

    tdid: str
    oid: str
    created_at: str
    status: str = ACTIVE
    nca_ref: Optional[str] = None
    revoked_at: Optional[str] = None
    revoke_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tdid": self.tdid, "oid": self.oid, "created_at": self.created_at,
            "status": self.status, "nca_ref": self.nca_ref,
            "revoked_at": self.revoked_at, "revoke_reason": self.revoke_reason,
        }


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class IdentityBridge:
    """TDID ↔ 国标身份码双向桥接（范围内主键制 + 范围外链接制）。"""

    def __init__(self, nca_generator=None):
        if nca_generator is None:
            try:  # 复用 fos 存证生成器（映射必存证 — fail-closed）
                from tdca_nca.generator import NCAGenerator  # type: ignore
                nca_generator = NCAGenerator()
            except Exception as exc:  # pragma: no cover
                raise IdentityBridgeError(
                    "映射须存证（fail-closed）：未提供 NCA 生成器且 fos 不可导入 —— "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
        self._gen = nca_generator
        self._links: Dict[str, IdentityLink] = {}      # tdid -> link（含历史）
        self._oid_index: Dict[str, str] = {}           # oid -> tdid（仅 ACTIVE）

    # ---------- 校验 ----------
    @staticmethod
    def validate_tdid(tdid: str) -> None:
        if not isinstance(tdid, str) or not _TDID_RE.match(tdid):
            raise IdentityBridgeError(f"TDID 格式非法（期望 TDID-[32 位大写十六进制]）: {tdid!r}")

    @staticmethod
    def validate_oid(oid: str) -> None:
        if not isinstance(oid, str) or not _OID_RE.match(oid):
            raise IdentityBridgeError(
                f"国标身份码格式非法（期望 GB/T 26231 分层，如 1.2.156.N.N.N…）: {oid!r}")

    # ---------- 链接建立 ----------
    def link(self, tdid: str, oid: str, actor: str = "identity-bridge") -> IdentityLink:
        """建立 TDID ↔ OID 链接（幂等 + 冲突检测 + 映射存证 fail-closed）。"""
        self.validate_tdid(tdid)
        self.validate_oid(oid)

        existing = self._links.get(tdid)
        if existing is not None and existing.status == ACTIVE:
            if existing.oid == oid:
                return existing  # 幂等：同对已链接
            raise IdentityBridgeError(
                f"TDID 已链接其他国标身份码（tdid={tdid} → {existing.oid}）；"
                "变更须先 revoke 失效同步")
        holder = self._oid_index.get(oid)
        if holder is not None and holder != tdid:
            raise IdentityBridgeError(f"国标身份码已被其他 TDID 链接（oid={oid} → {holder}）")

        link = IdentityLink(tdid=tdid, oid=oid, created_at=_now())
        nca = self._gen.generate(
            type="identity-link", layer=2,
            content={"tdid": tdid, "oid": oid, "actor": actor,
                     "scope": "out-of-domain-link", "simulated": True})
        link.nca_ref = nca.nca_id
        self._links[tdid] = link
        self._oid_index[oid] = tdid
        return link

    # ---------- 双向解析 ----------
    def resolve_by_tdid(self, tdid: str) -> Optional[IdentityLink]:
        link = self._links.get(tdid)
        return link if link and link.status == ACTIVE else None

    def resolve_by_oid(self, oid: str) -> Optional[IdentityLink]:
        tdid = self._oid_index.get(oid)
        return self.resolve_by_tdid(tdid) if tdid else None

    def resolve(self, tdid: Optional[str] = None, oid: Optional[str] = None) -> Optional[IdentityLink]:
        if (tdid is None) == (oid is None):
            raise IdentityBridgeError("resolve 须且仅须指定 tdid 或 oid 之一")
        return self.resolve_by_tdid(tdid) if tdid else self.resolve_by_oid(oid)  # type: ignore[arg-type]

    # ---------- 失效同步 ----------
    def revoke(self, tdid: str, reason: str, actor: str = "identity-bridge") -> IdentityLink:
        """撤销链接（失效同步）：终止外部链接，历史保留可溯，生成失效存证。"""
        self.validate_tdid(tdid)
        link = self._links.get(tdid)
        if link is None or link.status != ACTIVE:
            raise IdentityBridgeError(f"无可撤销的活跃链接: {tdid}")
        if not reason:
            raise IdentityBridgeError("撤销须给出理由（可审计）")

        nca = self._gen.generate(
            type="identity-unlink", layer=2,
            content={"tdid": tdid, "oid": link.oid, "reason": reason,
                     "actor": actor, "simulated": True})
        link.status = REVOKED
        link.revoked_at = _now()
        link.revoke_reason = reason
        link.nca_ref = f"{link.nca_ref};{nca.nca_id}" if link.nca_ref else nca.nca_id
        self._oid_index.pop(link.oid, None)
        return link

    # ---------- 主键嵌入（事件侧接入点） ----------
    def stamp_event(self, event: Dict[str, Any], tdid: str, oid: Optional[str] = None) -> Dict[str, Any]:
        """事件主键嵌入：内部主键 tdid（必填）+ 国标身份码链接字段（可选）。

        语义: TDCA 范围内一律以 TDID 为主键；OID 仅作外部可识别链接字段，
        **不改变内部身份基线**（STD-AGENT-ID-001 V1.1 §四）。
        """
        self.validate_tdid(tdid)
        if oid is not None:
            self.validate_oid(oid)
            active = self.resolve_by_tdid(tdid)
            if active is None or active.oid != oid:
                raise IdentityBridgeError("链接字段与在册映射不一致（须先 link）")
        out = dict(event)
        out["identity"] = {"primary_key": tdid, "national_agent_id": oid,
                           "primary_key_scheme": "TDID", "simulated": True}
        return out

    # ---------- 导出与统计 ----------
    def export(self) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self._links.values()]

    def stats(self) -> Dict[str, int]:
        actives = sum(1 for l in self._links.values() if l.status == ACTIVE)
        return {"total": len(self._links), "active": actives,
                "revoked": len(self._links) - actives}
