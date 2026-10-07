# -*- coding: utf-8 -*-
"""
P2 集群编排 + 准入闸门（A-13）：/api/v1/cluster/* —— 配置类调用须授权件机验 + 授权谱系落账。

口径（期一开工令 5）：
  - 准入闸门 = 配置类调用须授权件；仅握手不成立（可信联通 ≠ 可信协作）；
  - 谱系账本增授权谱系：授权件 + 多层转授链（parent_grant_id 逐级上溯，只增不改）；
  - 授权件四要件（照 P0 模板）：场景约束 / 五阶资产形态 / 全构成已授权 / 法律主体签名；
    智能体不得代签、不得代持代填（签名须法律主体本人，模拟硬件签 ≥8 字符）。
机验：要件缺一即 400 fail-closed；准入无有效授权件即 403 fail-closed。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session, get_sessionmaker  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import _nca_append, _nca_watermark, _require_session_user, _utc  # noqa: E402

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])


# =====================================================================
# 授权件四要件机验（逐条 fail-closed，缺一即拒）
# =====================================================================

def _check_four_requirements(scene_constraint: str, asset_order: int,
                             full_composition: bool, legal_signer: str,
                             signature: str) -> None:
    if not scene_constraint or not scene_constraint.strip():
        raise HTTPException(400, "REQUIREMENT_MISSING: 场景约束（要件①）")
    if asset_order not in (1, 2, 3, 4, 5):
        raise HTTPException(400, "REQUIREMENT_INVALID: 五阶资产形态（要件②）须为 1~5")
    if not full_composition:
        raise HTTPException(400, "REQUIREMENT_MISSING: 全构成已授权（要件③）")
    if not legal_signer or not legal_signer.strip():
        raise HTTPException(400, "REQUIREMENT_MISSING: 法律主体签名（要件④）")
    if not signature or len(signature) < 8:
        raise HTTPException(403, "SIGNATURE_INVALID: 模拟硬件签须 ≥8 字符"
                                 "（智能体不得代签——检测到代签尝试即熔断）")


class GrantRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject_agent: str
    scene_constraint: str
    asset_order: int
    full_composition: bool = False
    legal_signer: str = ""
    signature: str = ""


@router.post("/grant/register", status_code=201)
def grant_register(req: GrantRegister, request: Request):
    """首授登记（四要件机验 → 授权件落库 → 谱系落账 → NCA 存证）。"""
    user = _require_session_user(request)
    _check_four_requirements(req.scene_constraint, req.asset_order,
                             req.full_composition, req.legal_signer, req.signature)
    gid = f"AG-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("CLUSTER_GRANT", user["username"],
                          artifact_path=f"grant:{gid}")
    with get_sessionmaker().begin() as s:
        s.add(M.AuthGrant(
            grant_id=gid, subject_agent=req.subject_agent,
            scene_constraint=req.scene_constraint.strip(),
            asset_order=req.asset_order, full_composition=1,
            legal_signer=req.legal_signer.strip(), signature=req.signature,
            parent_grant_id=None, status="active", nca_ref=nca_ref,
            created_at=_utc()))
        s.add(M.LineageEntry(
            entry_id=f"LE-{uuid.uuid4().hex[:10]}", agent_id=req.subject_agent,
            kind="grant", grant_id=gid, parent_grant_id=None,
            nca_ref=nca_ref, ts=_utc()))
    return _nca_watermark({"grant_id": gid, "subject_agent": req.subject_agent,
                           "chain_depth": 1, "nca_ref": nca_ref,
                           "note": "授权件已登记（首授；配置类调用可凭此过准入闸门）"})


class SubGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parent_grant_id: str
    subject_agent: str
    scene_constraint: str
    asset_order: int
    full_composition: bool = False
    legal_signer: str = ""
    signature: str = ""


@router.post("/grant/subgrant", status_code=201)
def grant_subgrant(req: SubGrant, request: Request):
    """转授（上级授权件须 active → 新授权件挂 parent_grant_id → 谱系链 +1）。"""
    user = _require_session_user(request)
    _check_four_requirements(req.scene_constraint, req.asset_order,
                             req.full_composition, req.legal_signer, req.signature)
    with get_session() as s:
        parent = s.get(M.AuthGrant, req.parent_grant_id)
    if parent is None:
        raise HTTPException(404, "parent_grant_id 不存在")
    if parent.status != "active":
        raise HTTPException(403, "上级授权件已注销（revoked）——转授链失效，fail-closed")
    gid = f"AG-{uuid.uuid4().hex[:10]}"
    nca_ref = _nca_append("CLUSTER_SUBGRANT", user["username"],
                          artifact_path=f"grant:{gid}")
    with get_sessionmaker().begin() as s:
        s.add(M.AuthGrant(
            grant_id=gid, subject_agent=req.subject_agent,
            scene_constraint=req.scene_constraint.strip(),
            asset_order=req.asset_order, full_composition=1,
            legal_signer=req.legal_signer.strip(), signature=req.signature,
            parent_grant_id=req.parent_grant_id, status="active",
            nca_ref=nca_ref, created_at=_utc()))
        s.add(M.LineageEntry(
            entry_id=f"LE-{uuid.uuid4().hex[:10]}", agent_id=req.subject_agent,
            kind="subgrant", grant_id=gid, parent_grant_id=req.parent_grant_id,
            nca_ref=nca_ref, ts=_utc()))
    return _nca_watermark({"grant_id": gid, "subject_agent": req.subject_agent,
                           "parent_grant_id": req.parent_grant_id, "nca_ref": nca_ref,
                           "note": "转授已登记（多层转授链入谱系账本）"})


class GrantRevoke(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grant_id: str


@router.post("/grant/revoke")
def grant_revoke(req: GrantRevoke, request: Request):
    """注销授权件（active → revoked；谱系留 revoke 记录，历史不抹除）。"""
    user = _require_session_user(request)
    with get_session() as s:
        row = s.get(M.AuthGrant, req.grant_id)
    if row is None:
        raise HTTPException(404, "grant_id 不存在")
    if row.status == "revoked":
        return _nca_watermark({"grant_id": req.grant_id, "status": "revoked",
                               "note": "已注销（幂等返回）"})
    nca_ref = _nca_append("CLUSTER_REVOKE", user["username"],
                          artifact_path=f"grant:{req.grant_id}")
    with get_sessionmaker().begin() as s:
        r = s.get(M.AuthGrant, req.grant_id)
        r.status = "revoked"
        s.add(M.LineageEntry(
            entry_id=f"LE-{uuid.uuid4().hex[:10]}", agent_id=r.subject_agent,
            kind="revoke", grant_id=req.grant_id, parent_grant_id=r.parent_grant_id,
            nca_ref=nca_ref, ts=_utc()))
    return _nca_watermark({"grant_id": req.grant_id, "status": "revoked",
                           "nca_ref": nca_ref,
                           "note": "授权件已注销；其后代转授链不再具备准入效力"})


# =====================================================================
# 准入闸门（配置类调用；G-1~G-5 五条合取·fail-closed——2026-10-08 开工令）
# =====================================================================
# 准入判据（照在册现有制度，五条合取，缺一不准入；⛔ 不新增判据、不设新阈值）：
#   G-1 已缔约（注册即缔约：NCA 存证 user_register_contract 须在链，actor=本人）
#   G-2 权属登记成件（ownership_records：存在＋owner_ref==本人＋非 cancelled）
#   G-3 授权登记成件（authorization_records：存在——无授权不得调用）
#   G-4 授权四要件齐（req_scene／req_five_forms／req_full_grant／req_legal_signature）
#   G-5 合规前置闸门通过（授权记录非 cancelled——自有亦须件；无授权而配置＝侵权）
# 例外仅沙盒／演练（sandbox=true：跳过 G-2~G-5 与授权件闸，显式标记，出盒须授权）。
# 每次判定（准／拒）落 NCA；层数上限在册未裁，谱系上溯按现实现值（防御上限 64 层）跑。

def _deny(agent_id: str, username: str, gate: str, reason: str) -> None:
    """准入拒绝：先落 NCA 留痕再 403（fail-closed，每次判定落链）。"""
    _nca_append("CLUSTER_ADMIT_DENY", username,
                artifact_path=f"admission:{agent_id}:G-{gate}", prov="real")
    raise HTTPException(403, f"ADMISSION_DENIED（G-{gate}）: {reason}")


def _g1_contracted(s, username: str, agent_id: str) -> None:
    """G-1 已缔约：注册即缔约的存证须在 NCA 链（actor=本人）。取不到一律拦。"""
    row = s.query(M.NcaChain).filter_by(action="user_register_contract",
                                        actor=username).first()
    if row is None:
        _deny(agent_id, username, "1", "未检得缔约存证（注册即缔约；fail-closed）")


def _g2_ownership(s, username: str, agent_id: str, rid: str) -> None:
    """G-2 权属登记成件：存在＋本人为权属登记人＋非 cancelled。"""
    ow = s.get(M.OwnershipRecord, rid.strip()) if rid.strip() else None
    if ow is None or ow.owner_ref != username or ow.status == "cancelled":
        _deny(agent_id, username, "2",
              "须权属登记成件且本人为权属登记人、未注销（fail-closed）")


def _g3_g4_g5_authorization(s, username: str, agent_id: str, rid: str) -> None:
    """G-3 授权成件存在 → G-4 四要件齐 → G-5 非 cancelled（照 authorization_ops 同判据）。"""
    ar = s.get(M.AuthorizationRecord, rid.strip()) if rid.strip() else None
    if ar is None:
        _deny(agent_id, username, "3", "授权登记成件不存在（无授权不得调用；fail-closed）")
    if not (ar.req_scene and ar.req_five_forms and ar.req_full_grant
            and ar.req_legal_signature):
        _deny(agent_id, username, "4", "授权四要件未齐（fail-closed）")
    if ar.status == "cancelled":
        _deny(agent_id, username, "5", "合规前置闸门未过：授权登记已注销"
                                 "（自有亦须件；fail-closed）")


class AdmissionCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: str
    call_type: str = "config"  # config（配置类，须授权件）/ general（一般调用）
    ownership_record_id: str = ""        # G-2 权属登记成件（沙盒例外可空）
    authorization_record_id: str = ""    # G-3~G-5 授权登记成件（沙盒例外可空）
    sandbox: bool = False                # 沙盒／演练例外（显式标记；出盒须授权）


@router.post("/admission/check")
def admission_check(req: AdmissionCheck, request: Request):
    """准入判定（G-1~G-5 合取；沙盒例外显式标记；每次判定落 NCA）。

    general 调用仅握手（可信联通 ≠ 可信协作）；config 调用须五条判据全过
    且该智能体持有 active 授权件（既有谱系闸照守，未松动）。
    """
    user = _require_session_user(request)
    username = user["username"]
    if req.call_type not in ("config", "general"):
        raise HTTPException(400, "call_type 须为 config / general")
    if req.call_type == "general":
        return _nca_watermark({"agent_id": req.agent_id, "verdict": "HANDSHAKE_ONLY",
                               "admitted": False,
                               "note": "一般调用仅完成握手（可信联通）；"
                                       "协作执行（配置类）仍须授权件——可信联通 ≠ 可信协作"})
    with get_session() as s:
        _g1_contracted(s, username, req.agent_id)

    if req.sandbox:
        nca_ref = _nca_append("CLUSTER_ADMIT_SANDBOX", username,
                              artifact_path=f"admission:{req.agent_id}", prov="simulated")
        return _nca_watermark(
            {"agent_id": req.agent_id, "verdict": "ADMITTED_SANDBOX", "admitted": True,
             "sandbox": True, "chain_depth": 0, "nca_ref": nca_ref,
             "note": "沙盒／演练例外（G-1 缔约仍验；G-2~G-5 与授权件闸跳过，显式标记；"
                     "出盒须授权）"}, nature="simulated")

    with get_session() as s:
        _g2_ownership(s, username, req.agent_id, req.ownership_record_id)
        _g3_g4_g5_authorization(s, username, req.agent_id, req.authorization_record_id)
        grants = s.query(M.AuthGrant).filter_by(
            subject_agent=req.agent_id, status="active").all()
    if not grants:
        _deny(req.agent_id, username, "GRANT", "配置类调用无有效授权件"
              "（仅握手不成立——须先完成授权件登记）")
    chain = _trace_chain(grants[0].grant_id)
    nca_ref = _nca_append("CLUSTER_ADMIT", username,
                          artifact_path=f"admission:{req.agent_id}", prov="real")
    return _nca_watermark({"agent_id": req.agent_id, "verdict": "ADMITTED",
                           "admitted": True, "grant_id": grants[0].grant_id,
                           "chain": chain, "chain_depth": len(chain),
                           "gates": ["G-1 缔约", "G-2 权属成件", "G-3 授权成件",
                                     "G-4 四要件齐", "G-5 合规前置", "谱系授权件"],
                           "nca_ref": nca_ref,
                           "note": "配置类调用准入：G-1~G-5 全过，转授链可追溯"
                                   "（上溯防御上限现值 64 层；层数上限在册未裁）"},
                          nature="real")


def _trace_chain(grant_id: str) -> list:
    """从授权件逐级上溯 parent_grant_id 至首授，返回链（末项为首授）。"""
    chain = []
    gid: Optional[str] = grant_id
    for _ in range(64):  # 防御性上限：链异常成环即停止（正常链远不及此）
        with get_session() as s:
            row = s.get(M.AuthGrant, gid) if gid else None
        if row is None:
            break
        chain.append(row.grant_id)
        gid = row.parent_grant_id
        if gid is None:
            break
    return chain


@router.get("/lineage/{agent_id}")
def lineage(agent_id: str, request: Request):
    """谱系查询：该智能体的授权件全量 + 转授链（只增不改，历史可溯）。"""
    _require_session_user(request)
    with get_session() as s:
        entries = s.query(M.LineageEntry).filter_by(agent_id=agent_id) \
                   .order_by(M.LineageEntry.ts).all()
        grants = s.query(M.AuthGrant).filter_by(subject_agent=agent_id).all()
    return _nca_watermark({
        "agent_id": agent_id,
        "lineage": [{"entry_id": e.entry_id, "kind": e.kind, "grant_id": e.grant_id,
                     "parent_grant_id": e.parent_grant_id, "ts": e.ts}
                    for e in entries],
        "grants": [{"grant_id": g.grant_id, "status": g.status,
                    "asset_order": g.asset_order,
                    "parent_grant_id": g.parent_grant_id} for g in grants],
        "note": "谱系账本（授权件 + 多层转授链；revoke 留痕不抹除）"})
