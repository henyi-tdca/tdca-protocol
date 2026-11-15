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
