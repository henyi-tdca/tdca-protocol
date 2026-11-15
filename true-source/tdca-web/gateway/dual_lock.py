# -*- coding: utf-8 -*-
"""
L1SI214-TOKEN-B3-001 两把锁四分档门（GSEQ-8203 DUAL-LOCK-001 ＋ 批3令 B/C/D 项）。

四段校验（顺序 ⛔ 倒、⛔ 跳段、⛔ 短路）：
  ① 身份段：未登录 401（上游 _require_session_user fail-closed，本门不重复）
  ② 第 1 把 · 操作权限：role × 域 × 动作（perm_table 权限点表唯一真源）
     不过 → 403 NO_OPERATION_PERM「你的账号无此操作许可」（⛔ 泄露任何对象信息）
  ③ 第 2 把 · 配置权：该具体对象的权属（ownership_records.owner_ref ＋
     status != cancelled；查无登记＝无配置权——AMEND-TOKEN-B3-001-001 撤 S-1'）
     ＋ 授权件（在册 active 授权面板件，grantee=本人，标的含该资产）
     不过 → 对象公开可查：403 NO_CONFIG_RIGHT
            「你对该项资产无配置权——须由该资产的所有者授予」；
            对象未公开／他人私域：404（与「不存在」同码同文案，⛔ 区分）
  ④ 两把皆过 → 放行（调用方执行）＋ 留痕一条（D 项：放行与拒绝皆落痕）

留痕（me_audit.audit_dual_lock → 既有 nca_chain，⛔ 新表、⛔ 凭据值）：
  谁／何动作／何对象／两把锁各自结论／时点／拒绝码（若拒）。

⭐ 接线点（批3）：授权面板「本人签署」步——签署标的含权属资产引用（OR-…）的
   授权件时，签真＋人真之后、存证生效之前过此门（令 A 项第④步「两把锁」）。
   既有自由文本标的件（C-1 在册旧面）不属资产绑定委托，本门不触发——
   compat 面照实回报，⛔ 悄悄扩大范围。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import re

from fastapi import HTTPException

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402
from me_audit import audit_dual_lock  # noqa: E402
from perm_table import GRID, _ROLE_COLUMNS  # noqa: E402

# 对外拒绝码与文案（令面逐字，⛔ 合并两句——D-8）
NO_OPERATION_PERM = "NO_OPERATION_PERM"
NO_CONFIG_RIGHT = "NO_CONFIG_RIGHT"
TEXT_LOCK1 = "你的账号无此操作许可"
TEXT_LOCK2 = "你对该项资产无配置权——须由该资产的所有者授予"

# 配置动作落权属资产＝本人私域口径（表C：权属资产系权利人私域）。
_GATE_DOMAIN = "私域(本人)"
_GATE_ACTION = "授权"        # 签名门 context：签署授权件＝「授权」动作（表B/表C ✍️ 行）

# 权属资产引用（ownership_records.record_id 形态 OR-xxx；模型层直核）
_ASSET_RE = re.compile(r"OR-[A-Za-z0-9_-]+")

# 挂出件公开面态（market_admin 公开端同口径）：公开可查 ⟺ active/paused 在架
_PUBLIC_LISTING_STATUSES = ("active", "paused")

# 授权件覆盖判定：直接委托（active 面板件，grantee=本人，标的含该资产）。
# 谱系多层转授不在本批展开（在册「层数上限未裁」，防御上限另行议）。


def extract_asset_ref(subject: str) -> str | None:
    """自授权件标的提取权属资产引用；无则不触发本门（自由文本标的＝非资产绑定委托）。"""
    m = _ASSET_RE.search(subject or "")
    return m.group(0) if m else None


def lock1_operation_perm(role: str) -> tuple[bool, str]:
    """第 1 把：role × 域 × 动作（perm_table 唯一真源；两值＝(过?, 结论记痕)）。

    founder 在表C 无「治理侧」列（GSEQ-8198 按表生成不补行）——本门 fail-closed：
    无列即无此操作许可（⛔ 自建豁免）。
    """
    col = _ROLE_COLUMNS.get(role, {}).get(_GATE_DOMAIN)
    if col is None:
        return False, f"role={role} 在 {_GATE_DOMAIN} 无表列（fail-closed）"
    marks = GRID[_GATE_DOMAIN]["rows"][_GATE_ACTION][GRID[_GATE_DOMAIN]["columns"].index(col)]
    if "❌" in marks:
        return False, f"表C·{_GATE_ACTION}·{col}＝❌（{marks}）"
    if marks.strip() == "—":
        return False, f"表C·{_GATE_ACTION}·{col}＝不适用"
    if "✍️" in marks:
        return True, f"表C·{_GATE_ACTION}·{col}＝{marks}（签名步即本人签署之兑现）"
    return True, f"表C·{_GATE_ACTION}·{col}＝{marks}"


def lock2_config_right(username: str, asset_id: str) -> tuple[bool, str]:
    """第 2 把：权属（owner_ref＋非 cancelled；查无登记＝无配置权）＋ 授权件。

    两值＝(过?, 结论记痕)。授权件＝在册 active 面板件（grantee=本人，标的含该资产）。
    """
    with get_session() as s:
        ow = s.get(M.OwnershipRecord, asset_id)
        if ow is not None and ow.owner_ref == username and ow.status != "cancelled":
            return True, f"权属在册（owner_ref=本人，status={ow.status}）"
        rows = (s.query(M.AuthorizationPanelDoc)
                .filter(M.AuthorizationPanelDoc.status == "active",
                        M.AuthorizationPanelDoc.grantee == username)
                .all())
        for r in rows:
            if asset_id in (r.subject or ""):
                return True, f"授权件在册（{r.auth_id}，grantee=本人，active）"
    if ow is None:
        return False, "查无权属登记（无登记＝无配置权；AMEND 撤 S-1'）"
    return False, f"权属在册但非本人或已注销（owner_ref={ow.owner_ref}，status={ow.status}）"


def asset_is_public(asset_id: str) -> bool:
    """对象公开可查 ⟺ 挂出件公开面在架（active/paused；同公开端口径）。"""
    with get_session() as s:
        row = (s.query(M.MarketListing)
               .filter(M.MarketListing.ownership_record_id == asset_id,
                       M.MarketListing.status.in_(_PUBLIC_LISTING_STATUSES))
               .first())
    return row is not None


def dual_lock_gate(user: dict, action: str, asset_id: str,
                   authz_ref: str | None = None) -> None:
    """四段门（②③④段；①身份段上游已 fail-closed）。拒则抛＋留痕；过则留痕返回。

    action：动作记痕用（本批＝「授权」）；asset_id：权属资产引用（OR-…）；
    authz_ref：授权件编号（面板件过门时携，落痕 authz_ref 段）。
    """
    username, role = user["username"], user.get("role", "")
    ok1, why1 = lock1_operation_perm(role)
    if not ok1:
        audit_dual_lock(username, action, asset_id, ok1, why1, False, "未执行（先判先报）",
                        allowed=False, refuse_code=NO_OPERATION_PERM, authz_ref=authz_ref)
        # ⛔ 泄露任何对象信息：文案只讲账号，不提对象
        raise HTTPException(403, f"{NO_OPERATION_PERM}：{TEXT_LOCK1}")
    ok2, why2 = lock2_config_right(username, asset_id)
    if not ok2:
        if asset_is_public(asset_id):
            audit_dual_lock(username, action, asset_id, ok1, why1, ok2, why2,
                            allowed=False, refuse_code=NO_CONFIG_RIGHT, authz_ref=authz_ref)
            raise HTTPException(403, f"{NO_CONFIG_RIGHT}：{TEXT_LOCK2}")
        audit_dual_lock(username, action, asset_id, ok1, why1, ok2, why2,
                        allowed=False, refuse_code="404", authz_ref=authz_ref)
        raise HTTPException(404, "Not Found")   # 与「不存在」同码同文案（全局 handler 同形）
    audit_dual_lock(username, action, asset_id, ok1, why1, ok2, why2,
                    allowed=True, refuse_code="", authz_ref=authz_ref)
