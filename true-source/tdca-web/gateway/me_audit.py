# -*- coding: utf-8 -*-
"""
L1SI214-TOKEN-B2-001 批 2 两类留痕（审计面，⛔ 权限面、⛔ /me/permissions 混出）。

落点＝既有 nca_chain（_nca_append，既有审计链；⛔ 新造表、⛔ 改表结构）。
三类动作（动作名封闭枚举，结果编码在 artifact_path 末段，⛔ 凭据值）：
- user_password_change / user_password_change_failed：改密（谁=actor、何时=ts、
  结果=末段 ok/failed、改的是本人=artifact_path 挂本人域）；⛔ 密码值/哈希/旧值。
- user_token_revoke / user_token_revoke_repeat：批 2 A 项吊销（谁/被吊销令牌 id
  脱敏/时点/结果=revoked 或 already_revoked）。
- user_privilege_admin_change：私域管理员任免（谁=actor、对谁=subject_ref 脱敏形
  sha256[:12]、哪个私域=artifact_path 域段、结果=末段；op=appoint/revoke）。
- dual_lock_decision（L1SI214-TOKEN-B3-001 追加，令 D 项）：两把锁判定留痕——
  放行与拒绝皆落一条；谁/何动作/何对象/两把锁各自结论/拒绝码（若拒）；
  落点同此链，⛔ 新表、⛔ 凭据值。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib

from api_v1 import _nca_append  # noqa: E402


def _masked_subject(username: str) -> str:
    """主体脱敏形（sha256[:12]，同 nca_chain.subject_ref 口径；⛔ 返全值）。"""
    return hashlib.sha256(username.encode("utf-8")).hexdigest()[:12]


def audit_password_change(me: str, success: bool) -> str:
    """改密留痕（成功与失败各一条；who/when/result/本人域，⛔ 任何密码形态）。"""
    action = "user_password_change" if success else "user_password_change_failed"
    tail = "ok" if success else "failed"
    return _nca_append(action, me,
                       artifact_path=f"auth://me/password-change/{me}/{tail}",
                       prov="real", subject_ref=_masked_subject(me))


def audit_token_revoke(me: str, masked_id: str, already: bool) -> str:
    """吊销留痕（被吊销令牌 id 用批 1 脱敏形；结果=revoked/already_revoked）。"""
    action = "user_token_revoke_repeat" if already else "user_token_revoke"
    tail = "already_revoked" if already else "revoked"
    return _nca_append(action, me,
                       artifact_path=f"auth://me/tokens/{masked_id}/{tail}",
                       prov="real", subject_ref=_masked_subject(me))


def audit_privilege_admin_change(actor: str, appointee: str, op: str,
                                 result: str) -> str:
    """私域管理员任免留痕（谁=actor、对谁=subject_ref 脱敏、哪个私域=actor 本人域、
    结果=末段；op 仅 appoint/revoke 两值封闭）。"""
    if op not in ("appoint", "revoke"):
        raise ValueError("op 值域封闭：appoint/revoke（fail-closed）")
    tail = "ok" if result == "ok" else "failed"
    return _nca_append("user_privilege_admin_change", actor,
                       artifact_path=f"auth://me/privilege-admin/{actor}/{op}/{tail}",
                       prov="real", subject_ref=_masked_subject(appointee))


def _seg(text: str, limit: int = 80) -> str:
    """记痕段清洗：⛔ 路径分隔符（防段溢出）、限长。"""
    return (text or "").replace("/", "·")[:limit]


def audit_dual_lock(actor: str, action: str, asset_id: str,
                    ok1: bool, why1: str, ok2: bool, why2: str,
                    allowed: bool, refuse_code: str,
                    authz_ref: str | None = None) -> str:
    """两把锁判定一条（B3 令 D 项：放行/拒绝皆落；拒绝码入末段；⛔ 凭据值）。

    字段映射：谁=actor、何动作=action 段、何对象=资产段、两把锁各自结论=L1/L2 段、
    时点=链 ts 字段、拒绝码=末段（allow／deny-NO_OPERATION_PERM／deny-NO_CONFIG_RIGHT／deny-404）。
    """
    l1 = ("L1-pass" if ok1 else "L1-deny") + ":" + _seg(why1)
    l2 = ("L2-pass" if ok2 else "L2-deny") + ":" + _seg(why2)
    tail = "allow" if allowed else f"deny-{refuse_code or 'unknown'}"
    return _nca_append("dual_lock_decision", actor,
                       artifact_path=(f"auth://dual-lock/{_seg(asset_id, 40)}/"
                                      f"{_seg(action, 20)}/{l1}/{l2}/{tail}"),
                       prov="real", subject_ref=_masked_subject(actor),
                       authz_ref=authz_ref)
