# -*- coding: utf-8 -*-
"""L1SI195-B1-001：二期 C-3 验收记录（只施工不部署）——/api/v1/acceptance/standard|verdict|rectify ＋ GET /{acceptance_id}。

口径（照 TDCA-HANDOFF-EXEC-L1SI195-B1-001 V1.0 §四）：
  - 落点：新页 /acceptance（前端另件）；
  - 标准字段：条目清单须事前登记（可量化优先）；结论字段：逐条 通过/不通过＋依据哪一条＋差距；
    整改字段：条目／期限；汇总字段：delivery_id＋auth_id＋验收人＋存证号；
  - 硬约束：① 标准须事前——验收时临时加，页内拒绝并提示（后端同守：结论对不上事前标准
    即 400＋熔断③）；② 不通过必须写具体条目与差距；③ ⛔ 无 delivery_id 不许开验；
  - 状态机：pending → judging → passed／rejected（附整改）→ re_judging；
  - 端点：POST /standard ｜ /verdict ｜ /rectify；GET /{acceptance_id} 公开读；
  - 存证：每步落 nca_seq（NCA 链 artifact_path=acceptance:{acceptance_id}）；
  - 存储＝本地 JSON 仓（/data/acceptance 卷，环境变量可覆写）——⛔ 不改库表（S-3 不触发）；
    恢复＝编号与字段可从 NCA 链反查复建；
  - 熔断（可靠性#4 C-3）：结论与事前标准无法对应 → 停该链（status=suspended＋冻结件），
    后续全拒，⛔ 降级放行；恢复＝operator 复核解冻（POST /rectify {resume:true}）；
  - ⛔ 接结算（S-4）：通过只显示「可结算」字样，⛔ 触发结算、⛔ 结算字段落库；
  - 全程 SIMULATED 硬标注；⛔ 部署、⛔ 对外。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _require_session_user, _utc,  # noqa: E402
                    rec_hash_of)
import delivery_ops as _dl


def _nca_row(nca_id: str) -> M.NcaChain | None:
    with get_session() as s:
        return s.get(M.NcaChain, nca_id)

router = APIRouter(prefix="/api/v1/acceptance", tags=["acceptance-c3"])

_STORE_ENV = "TDCA_ACCEPTANCE_DIR"
_DEFAULT_STORE = "/data/acceptance"

_ACC_ID_RE = re.compile(r"^ACC-[0-9a-f]{10}$")
_DELIVERY_ID_RE = re.compile(r"^DLV-[0-9a-f]{10}$")


def _store() -> Path:
    d = Path(os.environ.get(_STORE_ENV, _DEFAULT_STORE))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return _utc()


def _doc_path(acceptance_id: str) -> Path:
    return _store() / f"{acceptance_id}.json"


def _freeze_path(acceptance_id: str) -> Path:
    return _store() / f"{acceptance_id}.freeze.json"


def _load(acceptance_id: str) -> dict | None:
    p = _doc_path(acceptance_id)
    if not p.is_file():
        return None
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else None
    except (ValueError, OSError):
        return None


def _save(doc: dict) -> None:
    doc["updated_at"] = _utc()
    p = _doc_path(doc["acceptance_id"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _freeze_active(acceptance_id: str) -> dict | None:
    p = _freeze_path(acceptance_id)
    if not p.is_file():
        return None
    try:
        f = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if f.get("unfrozen_at"):
        return None
    return f


def _trip_freeze(acceptance_id: str, reason: str, detail: str, by: str = "system") -> None:
    doc = _load(acceptance_id)
    pre = doc["status"] if doc else "pending"
    f = {"freeze_id": f"ACF-{uuid.uuid4().hex[:10]}", "acceptance_id": acceptance_id,
         "reason": reason, "detail": detail, "frozen_by": by,
         "frozen_at": _utc(), "unfrozen_by": None, "unfrozen_at": None,
         "unfrozen_note": f"PRE_FREEZE_STATUS={pre}"}
    _freeze_path(acceptance_id).write_text(json.dumps(f, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    if doc is not None and doc["status"] != "passed":
        doc["status"] = "suspended"
        _save(doc)


def _assert_not_frozen(acceptance_id: str) -> None:
    fz = _freeze_active(acceptance_id)
    if fz is not None:
        raise HTTPException(423, f"该验收链已熔断冻结（{fz['reason']}）——后续全拒；"
                                 f"须 operator 复核解冻（⛔ 自动恢复、⛔ 降级放行）")


def _hash_match(doc: dict) -> bool:
    if not doc.get("nca_seq") or not doc.get("rec_hash"):
        return False
    row = _nca_row(doc["nca_seq"])
    if row is None:
        return False
    expect = rec_hash_of(row.nca_id, row.prev_nca, row.action, row.actor,
                         row.artifact_path, row.sha256_8, row.handshake_id,
                         row.data_provenance, row.ts)
    return expect == doc["rec_hash"]


def _verify_or_trip(acceptance_id: str) -> None:
    doc = _load(acceptance_id)
    if doc is None:
        raise HTTPException(404, "acceptance_id 不存在")
    if not doc.get("nca_seq"):
        raise HTTPException(409, "无存证视为未发生（状态停本步）——该验收单尚无 NCA 存证")
    if _hash_match(doc):
        if doc.get("hash_mismatch_streak"):
            doc["hash_mismatch_streak"] = 0
            _save(doc)
        return
    streak = int(doc.get("hash_mismatch_streak", 0)) + 1
    if streak >= 3:
        _trip_freeze(acceptance_id, "hash",
                     f"双库哈希连续不符 ≥3（nca_seq={doc['nca_seq']}）")
        raise HTTPException(423, "双库哈希连续不符——该链已熔断冻结（fail-closed，⛔ 降级放行）")
    doc["hash_mismatch_streak"] = streak
    _save(doc)
    raise HTTPException(409, f"双库哈希对拍不符（连续 {streak} 次）——本次拒，连续 ≥3 次即熔断停链")


def _event(doc: dict, event_type: str, actor: str, detail: str, nca_ref: str) -> None:
    doc.setdefault("events", []).append({
        "event_id": f"ACE-{uuid.uuid4().hex[:10]}", "event_type": event_type,
        "actor": actor, "nca_ref": nca_ref, "detail": detail, "created_at": _utc()})


def _delivery_ready(delivery_id: str) -> dict | None:
    """C-3 依赖 C-2：delivery 清单须存在且已落存证（只读 delivery_ops 仓）。"""
    doc = _dl._load(delivery_id)
    if doc is None or not doc.get("nca_seq"):
        return None
    return doc


def _public_view(doc: dict) -> dict:
    """公开读投影（免会话）：标准／结论／整改／状态；⛔ 验收人账号。
    结算衔接（S-4）：passed 只显示「可结算」字样，⛔ 触发结算。"""
    view = {
        "acceptance_id": doc["acceptance_id"],
        "delivery_id": doc["delivery_id"],
        "auth_id": doc["auth_id"],
        "status": doc["status"],
        "standards": doc["standards"],
        "verdicts": doc["verdicts"],
        "rectifications": doc["rectifications"],
        "nca_seq": doc.get("nca_seq"),
        "simulated": True,
    }
    if doc["status"] == "passed":
        view["settlement"] = "可结算"   # S-4：只显示，⛔ 触发结算
    return _nca_watermark(view, nature="simulated")


# ────────────────────────────── 端点 ──────────────────────────────

class StandardIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: str = ""             # 必填（⛔ 无 delivery_id 不许开验）
    auth_id: str = ""                 # 汇总字段（随清单照录）
    standards: list = []              # 事前登记条目：[{item, criterion}]（可量化优先）
    note: str = ""


@router.post("/standard", status_code=201)
def acceptance_standard(req: StandardIn, request: Request):
    """登记验收标准（须登录；delivery_id 必填且清单已落证；标准须事前、逐条带判据）。
    原子序同 C-2：验收单先落（nca_seq 空＝视未发生）→ NCA 落证 → 回写；失败清单。
    """
    user = _require_session_user(request)
    did = req.delivery_id.strip()
    if not did:
        raise HTTPException(400, "⛔ 无 delivery_id 不许开验——请先完成交付清单（/delivery）。")
    if not _DELIVERY_ID_RE.match(did):
        raise HTTPException(400, "delivery_id 式样不合（DLV- 开头）——请从交付清单复制完整编号。")
    dlv = _delivery_ready(did)
    if dlv is None:
        raise HTTPException(400, "delivery_id 查无清单或无存证——上一步未完成，先开交付清单。")
    if not req.auth_id.strip():
        req_auth = dlv.get("auth_id", "")
    else:
        req_auth = req.auth_id.strip()
    if not isinstance(req.standards, list) or not req.standards:
        raise HTTPException(400, "标准须事前登记——请逐条填写验收条目与判据（可量化优先）。")
    standards = []
    for i, st in enumerate(req.standards, start=1):
        if not isinstance(st, dict):
            raise HTTPException(400, f"第 {i} 条标准不是对象——请按「条目／判据」填写。")
        item = str(st.get("item", "")).strip()
        criterion = str(st.get("criterion", "")).strip()
        if not item or not criterion:
            raise HTTPException(400, f"第 {i} 条标准缺条目或判据——逐条都要填（事后临时加一律拒绝）。")
        standards.append({"item": item, "criterion": criterion})

    acceptance_id = f"ACC-{uuid.uuid4().hex[:10]}"
    now = _utc()
    doc = {"acceptance_id": acceptance_id, "delivery_id": did, "auth_id": req_auth,
           "standards": standards, "verdicts": [], "rectifications": [],
           "status": "pending", "nca_seq": None, "rec_hash": None,
           "hash_mismatch_streak": 0, "events": [],
           "note": req.note.strip() or None,
           "created_by": user["username"], "created_at": now, "updated_at": now}
    _save(doc)
    try:
        nca_ref = _nca_append("ACCEPTANCE_STANDARD", user["username"],
                              artifact_path=f"acceptance:{acceptance_id}")
    except Exception:
        _doc_path(acceptance_id).unlink(missing_ok=True)
        raise HTTPException(500, "存证落链失败——本次登记未发生（验收单已清，"
                                 "⛔ 半条记录、⛔ 编号发放）")
    row = _nca_row(nca_ref)
    try:
        doc["nca_seq"] = nca_ref
        doc["rec_hash"] = row.rec_hash if row else None
        _event(doc, "standard", user["username"],
               f"登记验收标准 {len(standards)} 条（delivery_id={did}）", nca_ref)
        _save(doc)
    except Exception:
        _doc_path(acceptance_id).unlink(missing_ok=True)
        raise HTTPException(500, "存证回写失败——本次登记未发生（验收单已清）")
    return _nca_watermark({
        "acceptance_id": acceptance_id, "status": "pending",
        "total_standards": len(standards), "nca_seq": nca_ref, "simulated": True,
        "note": "验收标准已事前登记（pending）——可逐条判（/verdict）；"
                "事后临时加标准一律拒绝。"
    }, nature="simulated")


class VerdictIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acceptance_id: str
    verdicts: list = []               # [{item, pass, basis, gap}]——item 须对应事前标准
    note: str = ""


@router.post("/verdict")
def acceptance_verdict(req: VerdictIn, request: Request):
    """逐条判定（须登录；pending/re_judging 可判；结论须对应事前标准）。
    全过 → passed（只显「可结算」，⛔ 接结算）；有不通过 → rejected（必填差距）。
    熔断③：结论与事前标准无法对应 → 停链（fail-closed）。
    """
    user = _require_session_user(request)
    aid = req.acceptance_id.strip()
    if not _ACC_ID_RE.match(aid):
        raise HTTPException(404, "acceptance_id 不存在")
    doc = _load(aid)
    if doc is None:
        raise HTTPException(404, "acceptance_id 不存在")
    _assert_not_frozen(aid)
    if doc["status"] not in ("pending", "re_judging"):
        raise HTTPException(409, f"该验收单状态为 {doc['status']}——⛔ 不可判定")
    if user["username"] != doc["created_by"] and user["role"] not in ("founder", "operator"):
        raise HTTPException(403, "非本人 ⛔ 判定——验收人须与登单人同一登录主体")
    _verify_or_trip(aid)
    if not isinstance(req.verdicts, list) or not req.verdicts:
        raise HTTPException(400, "请给出逐条结论——⛔ 空判。")

    std_items = {st["item"] for st in doc["standards"]}
    verdicts = []
    for i, v in enumerate(req.verdicts, start=1):
        if not isinstance(v, dict):
            raise HTTPException(400, f"第 {i} 条结论不是对象——请按「条目／通过／依据／差距」填写。")
        item = str(v.get("item", "")).strip()
        if item not in std_items:
            # 熔断③：结论与事前标准无法对应 → 停链
            _trip_freeze(aid, "standard",
                         f"结论条目「{item or '（空）'}」不在事前登记标准内"
                         f"（验收时临时加——页内拒绝并停链）", by=user["username"])
            raise HTTPException(400, "标准无法对应：该条目不在事前登记标准内——已 fail-closed "
                                     "拦截并熔断停链（须 operator 复核解冻）")
        passed = bool(v.get("pass"))
        basis = str(v.get("basis", "")).strip()
        gap = str(v.get("gap", "")).strip()
        if not basis:
            raise HTTPException(400, f"条目「{item}」缺依据——结论须写明依据哪一条标准。")
        if not passed and not gap:
            raise HTTPException(400, f"条目「{item}」不通过——必须写具体差距（⛔ 空差距）。")
        verdicts.append({"item": item, "pass": passed, "basis": basis, "gap": gap or None})

    judged = {v["item"] for v in verdicts}
    missing = [st["item"] for st in doc["standards"] if st["item"] not in judged]
    if missing:
        raise HTTPException(400, "标准须逐条判完——尚未判定：" + "、".join(missing))
    all_pass = all(v["pass"] for v in verdicts)
    target = "passed" if all_pass else "rejected"
    prev_status = doc["status"]
    doc["status"] = "judging"
    try:
        nca_ref = _nca_append("ACCEPTANCE_VERDICT", user["username"],
                              artifact_path=f"acceptance:{aid}")
    except Exception:
        doc["status"] = prev_status
        _save(doc)
        raise HTTPException(500, "判定存证落链失败——状态已停在本步，请重试")
    row = _nca_row(nca_ref)
    doc["status"] = target
    doc["verdicts"] = verdicts
    doc["nca_seq"] = nca_ref
    doc["rec_hash"] = row.rec_hash if row else None
    _event(doc, "verdict", user["username"],
           f"逐条判定（{len(verdicts)} 条；{prev_status}→{target}）", nca_ref)
    _save(doc)
    note = ("全部条目通过（passed）——结算衔接：可结算（仅显示，⛔ 未触发结算）。"
            if all_pass else
            "有不通过（rejected）——须登记整改（/rectify：条目／期限）后复判。")
    return _nca_watermark({
        "acceptance_id": aid, "status": target, "verdicts": verdicts,
        "nca_seq": nca_ref, "simulated": True, "note": note,
    }, nature="simulated")


class RectifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acceptance_id: str
    items: list = []                  # [{item, deadline}]——rejected 必填整改单
    resume: bool = False              # operator 复核解冻（熔断恢复；⛔ 自动恢复）
    note: str = ""


@router.post("/rectify")
def acceptance_rectify(req: RectifyIn, request: Request):
    """登记整改（须登录；rejected 方可登记；→ re_judging 待复判）；或 operator 解冻。"""
    user = _require_session_user(request)
    aid = req.acceptance_id.strip()
    if not _ACC_ID_RE.match(aid):
        raise HTTPException(404, "acceptance_id 不存在")
    doc = _load(aid)
    if doc is None:
        raise HTTPException(404, "acceptance_id 不存在")

    if req.resume:
        if user["role"] not in ("founder", "operator"):
            raise HTTPException(403, "复核解冻须 operator 及以上角色（⛔ 自动恢复、⛔ 降级放行）")
        fz = _freeze_active(aid)
        if fz is None:
            raise HTTPException(409, "该链未冻结——无需解冻")
        if doc["status"] != "suspended":
            raise HTTPException(409, "该验收单非停权态——解冻路径不适用于此件")
        pre = "pending"
        m = re.search(r"PRE_FREEZE_STATUS=(\w+)", fz.get("unfrozen_note") or "")
        if m and m.group(1) != "suspended":
            pre = m.group(1)
        nca_ref = _nca_append("ACCEPTANCE_RESUME", user["username"],
                              artifact_path=f"acceptance:{aid}")
        row = _nca_row(nca_ref)
        doc["status"] = pre
        doc["nca_seq"] = nca_ref
        doc["rec_hash"] = row.rec_hash if row else None
        _event(doc, "resume", user["username"],
               f"operator 复核解冻（原冻结 {fz['reason']}；回摆 {pre}）", nca_ref)
        _save(doc)
        fz["unfrozen_by"] = user["username"]
        fz["unfrozen_note"] = req.note.strip() or "operator 复核通过"
        fz["unfrozen_at"] = _utc()
        _freeze_path(aid).write_text(json.dumps(fz, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
        return _nca_watermark({
            "acceptance_id": aid, "status": pre, "nca_seq": nca_ref, "simulated": True,
            "note": f"已复核解冻（原冻结 {fz['reason']}）——状态回摆 {pre}；"
                    "NCA 存证在册（⛔ 自动恢复）"}, nature="simulated")

    _assert_not_frozen(aid)
    if doc["status"] != "rejected":
        raise HTTPException(409, f"该验收单状态为 {doc['status']}——⛔ 无需整改（仅 rejected 可登记整改）")
    if user["username"] != doc["created_by"] and user["role"] not in ("founder", "operator"):
        raise HTTPException(403, "非本人 ⛔ 登记整改——须与登单人同一登录主体")
    _verify_or_trip(aid)
    if not isinstance(req.items, list) or not req.items:
        raise HTTPException(400, "整改单必填——请逐条填写「条目／期限」。")
    rectifications = []
    std_items = {st["item"] for st in doc["standards"]}
    for i, it in enumerate(req.items, start=1):
        if not isinstance(it, dict):
            raise HTTPException(400, f"第 {i} 条整改不是对象——请按「条目／期限」填写。")
        item = str(it.get("item", "")).strip()
        deadline = str(it.get("deadline", "")).strip()
        if item not in std_items:
            raise HTTPException(400, f"整改条目「{item or '（空）'}」不在事前标准内——"
                                     "整改须对应已判条目。")
        if not deadline:
            raise HTTPException(400, f"整改条目「{item}」缺期限——逐条都要填整改期限。")
        rectifications.append({"item": item, "deadline": deadline})

    prev_status = doc["status"]
    doc["status"] = "re_judging"
    try:
        nca_ref = _nca_append("ACCEPTANCE_RECTIFY", user["username"],
                              artifact_path=f"acceptance:{aid}")
    except Exception:
        doc["status"] = prev_status
        _save(doc)
        raise HTTPException(500, "整改存证落链失败——状态已停在本步，请重试")
    row = _nca_row(nca_ref)
    doc["rectifications"] = rectifications
    doc["status"] = "re_judging"
    doc["nca_seq"] = nca_ref
    doc["rec_hash"] = row.rec_hash if row else None
    _event(doc, "rectify", user["username"],
           f"登记整改 {len(rectifications)} 条（→ re_judging）", nca_ref)
    _save(doc)
    return _nca_watermark({
        "acceptance_id": aid, "status": "re_judging",
        "rectifications": rectifications, "nca_seq": nca_ref, "simulated": True,
        "note": "整改已登记（re_judging）——整改完成后请复判（/verdict）。"
    }, nature="simulated")


@router.get("/{acceptance_id}")
def acceptance_public(acceptance_id: str):
    """公开读（免会话）：标准／结论／整改／状态；⛔ 验收人账号。无存证视未发生（404）。"""
    aid = (acceptance_id or "").strip()
    if not _ACC_ID_RE.match(aid):
        raise HTTPException(404, "该端点未上线或不存在")
    doc = _load(aid)
    if doc is None or not doc.get("nca_seq"):
        raise HTTPException(404, "acceptance_id 不存在（无存证视为未发生）")
    return _public_view(doc)


# GET 集合面守卫：裸 GET /acceptance 本令未开（⛔ 不做列表公开面）
@router.get("")
def acceptance_list_guard():
    raise HTTPException(404, "该端点未上线或不存在")
