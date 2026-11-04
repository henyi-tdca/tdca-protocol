# -*- coding: utf-8 -*-
"""L1SI195-B1-001：二期 C-2 交付清单（只施工不部署）——/api/v1/delivery/manifest|items|confirm ＋ GET /{delivery_id}。

口径（照 TDCA-HANDOFF-EXEC-L1SI195-B1-001 V1.0 §三）：
  - 落点：新页 /delivery（前端另件）；⛔ 不改 /use/upload（「生成清单」入口属后挂令）；
  - 逐件字段：名称／版本／哈希（必填）／大小；清单字段：auth_id（必填）／接收方主体／
    分批与分卷关系／交付时点；
  - 硬约束：① 缺哈希不许提交（逐件点名缺哪件）；② ⛔「稍后补」顶替；③ 大件超限拆件
    并在清单注明分卷；④ ⛔ 无 auth_id 不许开清单（提示「上一步未完成」）；
  - 状态机：draft → uploading → delivered → received；received 须报哈希，无哈希视同未收；
  - 端点：POST /manifest ｜ /items ｜ /confirm；GET /{delivery_id} 公开读免会话；
  - 存证：每步落 nca_seq（NCA 链 artifact_path=delivery:{delivery_id}）；
  - 存储＝本地 JSON 仓（/data/delivery 卷，环境变量可覆写）——⛔ 不改库表（S-3 不触发，
    免迁移）；恢复＝编号与字段可从 NCA 链反查复建；
  - 熔断（可靠性#4 C-2）：同一 delivery_id 短时重复确认／哈希连续不符 ≥3 →
    停该链（status=suspended＋冻结件），后续全拒，⛔ 降级放行；恢复＝operator 复核解冻
    （POST /confirm {resume:true}，角色 founder/operator，⛔ 自动恢复）；
  - 单件大小阈值在册未定：不設数字，页内标「待运维核定」（S-5 不触发）；
  - 全程 SIMULATED 硬标注；⛔ 部署、⛔ 对外、⛔ 接结算。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402
from api_v1 import (_nca_append, _nca_watermark, _require_session_user,  # noqa: E402
                    _utc, rec_hash_of)


def _nca_row(nca_id: str) -> M.NcaChain | None:
    with get_session() as s:
        return s.get(M.NcaChain, nca_id)

router = APIRouter(prefix="/api/v1/delivery", tags=["delivery-c2"])

# 存储目录：容器内 /data 卷（与 uploads 同卷；宿主机经 deploy 卷映射）。
# 测试以 TDCA_DELIVERY_DIR 覆写（conftest 惰性引擎同理，本模块惰性取目录）。
_STORE_ENV = "TDCA_DELIVERY_DIR"
_DEFAULT_STORE = "/data/delivery"


def _store() -> Path:
    d = Path(os.environ.get(_STORE_ENV, _DEFAULT_STORE))
    d.mkdir(parents=True, exist_ok=True)
    return d


# 编号／熔断参数（照 C-1 同口径：观察窗 30s、连不符阈值 3）
_DELIVERY_ID_RE = re.compile(r"^DLV-[0-9a-f]{10}$")
_RECONFIRM_WINDOW_SEC = 30
_HASH_STREAK_LIMIT = 3
_HASH_LEN_MAX = 128

# ⛔「稍后补」类占位顶替（硬约束②）：哈希位不得填这类字样
_HASH_PLACEHOLDER_RE = re.compile(r"^(稍后补|待补|待定|稍后|tbd|todo|none|null|暂无)$", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _doc_path(delivery_id: str) -> Path:
    return _store() / f"{delivery_id}.json"


def _freeze_path(delivery_id: str) -> Path:
    return _store() / f"{delivery_id}.freeze.json"


def _load(delivery_id: str) -> dict | None:
    p = _doc_path(delivery_id)
    if not p.is_file():
        return None
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else None
    except (ValueError, OSError):
        return None


def _save(doc: dict) -> None:
    """原子替换写（tmp → replace）；单写者网关进程内足够。"""
    doc["updated_at"] = _utc()
    p = _doc_path(doc["delivery_id"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _freeze_active(delivery_id: str) -> dict | None:
    p = _freeze_path(delivery_id)
    if not p.is_file():
        return None
    try:
        f = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if f.get("unfrozen_at"):
        return None
    return f


def _trip_freeze(delivery_id: str, reason: str, detail: str, by: str = "system") -> None:
    doc = _load(delivery_id)
    pre = doc["status"] if doc else "draft"
    f = {"freeze_id": f"DLF-{uuid.uuid4().hex[:10]}", "delivery_id": delivery_id,
         "reason": reason, "detail": detail, "frozen_by": by,
         "frozen_at": _utc(), "unfrozen_by": None, "unfrozen_at": None,
         "unfrozen_note": f"PRE_FREEZE_STATUS={pre}"}
    _freeze_path(delivery_id).write_text(json.dumps(f, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    if doc is not None and doc["status"] != "received":
        doc["status"] = "suspended"
        _save(doc)


def _assert_not_frozen(delivery_id: str) -> None:
    fz = _freeze_active(delivery_id)
    if fz is not None:
        raise HTTPException(423, f"该交付链已熔断冻结（{fz['reason']}）——后续全拒；"
                                 f"须 operator 复核解冻（⛔ 自动恢复、⛔ 降级放行）")


def _hash_match(doc: dict) -> bool:
    """双库哈希对拍：以 nca_chain 行字段按公开口径重算 rec_hash，与清单副本比对。"""
    if not doc.get("nca_seq") or not doc.get("rec_hash"):
        return False
    row = _nca_row(doc["nca_seq"])
    if row is None:
        return False
    expect = rec_hash_of(row.nca_id, row.prev_nca, row.action, row.actor,
                         row.artifact_path, row.sha256_8, row.handshake_id,
                         row.data_provenance, row.ts)
    return expect == doc["rec_hash"]


def _verify_or_trip(delivery_id: str) -> None:
    """写路径对拍：不符即累计（连续 ≥3 → 熔断②哈希连不符）。"""
    doc = _load(delivery_id)
    if doc is None:
        raise HTTPException(404, "delivery_id 不存在")
    if not doc.get("nca_seq"):
        raise HTTPException(409, "无存证视为未发生（状态停本步）——该清单尚无 NCA 存证")
    if _hash_match(doc):
        if doc.get("hash_mismatch_streak"):
            doc["hash_mismatch_streak"] = 0
            _save(doc)
        return
    streak = int(doc.get("hash_mismatch_streak", 0)) + 1
    if streak >= _HASH_STREAK_LIMIT:
        _trip_freeze(delivery_id, "hash",
                     f"双库哈希连续不符 ≥{_HASH_STREAK_LIMIT}（nca_seq={doc['nca_seq']}）")
        raise HTTPException(423, "双库哈希连续不符——该链已熔断冻结（fail-closed，⛔ 降级放行）")
    doc["hash_mismatch_streak"] = streak
    _save(doc)
    raise HTTPException(409, f"双库哈希对拍不符（连续 {streak} 次）——本次拒，"
                             f"连续 ≥{_HASH_STREAK_LIMIT} 次即熔断停链")


def _event(doc: dict, event_type: str, actor: str, detail: str, nca_ref: str) -> None:
    doc.setdefault("events", []).append({
        "event_id": f"DLE-{uuid.uuid4().hex[:10]}", "event_type": event_type,
        "actor": actor, "nca_ref": nca_ref, "detail": detail, "created_at": _utc()})


def _auth_doc_exists(auth_id: str) -> bool:
    """auth_id 存在性核验（只读 C-1 授权面板登记；只增不改，S-1 不触发）。"""
    with get_session() as s:
        return s.get(M.AuthorizationPanelDoc, auth_id) is not None


def _check_items(items: list) -> tuple[list | None, str | None]:
    """逐件硬校验：名称／哈希必填、⛔「稍后补」顶替、哈希长度限。
    返回 (净件列表, None) 或 (None, 人话理由——缺哪件逐一点名)。"""
    if not isinstance(items, list) or not items:
        return None, "清单至少须有一件——请逐件填写名称与哈希。"
    out = []
    for i, it in enumerate(items, start=1):
        if not isinstance(it, dict):
            return None, f"第 {i} 件不是对象——请按「名称／版本／哈希／大小」填写。"
        name = str(it.get("name", "")).strip()
        if not name:
            return None, f"第 {i} 件缺名称——逐件都要填名称。"
        h = str(it.get("hash", "")).strip()
        if not h:
            return None, f"「{name}」缺哈希——缺哈希不许提交（⛔「稍后补」不能顶替）。"
        if _HASH_PLACEHOLDER_RE.match(h):
            return None, f"「{name}」的哈希不能填「{h}」——缺哈希不许提交，请先算出真实哈希。"
        if len(h) > _HASH_LEN_MAX:
            return None, f"「{name}」的哈希超过 {_HASH_LEN_MAX} 字符——请核对。"
        size = it.get("size_bytes")
        if size is not None:
            try:
                size = int(size)
            except (TypeError, ValueError):
                return None, f"「{name}」的大小须为整数（字节）。"
        out.append({"name": name,
                    "version": str(it.get("version", "")).strip(),
                    "hash": h, "size_bytes": size,
                    "volume_note": str(it.get("volume_note", "")).strip()})
    return out, None


def _public_view(doc: dict) -> dict:
    """公开读投影（免会话）：交了几件、各件哈希、状态、存证指针；⛔ 起草人账号。"""
    return _nca_watermark({
        "delivery_id": doc["delivery_id"],
        "auth_id": doc["auth_id"],
        "receiver": doc["receiver"],
        "batches": doc["batches"],
        "deliver_at": doc["deliver_at"],
        "status": doc["status"],
        "items": [{"name": it["name"], "version": it["version"], "hash": it["hash"],
                   "size_bytes": it["size_bytes"], "volume_note": it["volume_note"]}
                  for it in doc["items"]],
        "total_items": len(doc["items"]),
        "nca_seq": doc.get("nca_seq"),
        "simulated": True,
        "note": "公开面：交了几件、各件哈希与状态（C-2 交付清单）；"
                "单件大小阈值待运维核定（在册未定，未设数字）。"
    }, nature="simulated")


# ────────────────────────────── 端点 ──────────────────────────────

class ManifestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auth_id: str = ""                 # 必填（⛔ 无 auth_id 不许开清单）
    receiver: str = ""                # 接收方主体
    batches: str = ""                 # 分批与分卷关系
    deliver_at: str = ""              # 交付时点
    items: list = []                  # 逐件（名称／版本／哈希必填／大小／分卷注明）
    note: str = ""


@router.post("/manifest", status_code=201)
def delivery_manifest(req: ManifestIn, request: Request):
    """开清单（须登录；auth_id 必填且在 C-1 登记；逐件哈希必填）。
    原子序：清单先落（nca_seq 空＝对外视未发生）→ NCA 落证 → 回写指针；
    NCA 失败即清清单——失败不给编号、不落存证、⛔ 半条记录。
    """
    user = _require_session_user(request)
    aid = req.auth_id.strip()
    if not aid:
        raise HTTPException(400, "上一步未完成——无 auth_id 不许开清单："
                                 "请先在授权配置面板完成授权（拿到 auth_id 再回来）。")
    if not _AUTH_ID_RE_C1(aid):
        raise HTTPException(400, "auth_id 式样不合（AP- 开头）——请从授权配置面板复制完整编号。")
    if not _auth_doc_exists(aid):
        raise HTTPException(400, "auth_id 在授权配置面板查无此号——上一步未完成或编号抄错，"
                                 "请核对后再开清单。")
    if not req.receiver.strip():
        raise HTTPException(400, "缺接收方主体——清单必填。")
    items, items_err = _check_items(req.items)
    if items_err:
        raise HTTPException(400, items_err)

    delivery_id = f"DLV-{uuid.uuid4().hex[:10]}"
    now = _utc()
    doc = {"delivery_id": delivery_id, "auth_id": aid,
           "receiver": req.receiver.strip(), "batches": req.batches.strip(),
           "deliver_at": req.deliver_at.strip(), "items": items,
           "status": "draft", "nca_seq": None, "rec_hash": None,
           "hash_mismatch_streak": 0, "events": [],
           "note": req.note.strip() or None,
           "created_by": user["username"], "created_at": now, "updated_at": now}
    # step1：清单先落（无存证位——此时对外读「视未发生」）
    _save(doc)
    # step2：NCA 落证（失败 → 清清单：不给编号不落存证）
    try:
        nca_ref = _nca_append("DELIVERY_MANIFEST", user["username"],
                              artifact_path=f"delivery:{delivery_id}")
    except Exception:
        _doc_path(delivery_id).unlink(missing_ok=True)
        raise HTTPException(500, "存证落链失败——本次开单未发生（清单已清，"
                                 "⛔ 半条记录、⛔ 编号发放）")
    # step3：回写指针＋事件（失败 → 清清单）
    row = _nca_row(nca_ref)
    try:
        doc["nca_seq"] = nca_ref
        doc["rec_hash"] = row.rec_hash if row else None
        _event(doc, "manifest", user["username"],
               f"开清单（{len(items)} 件；auth_id={aid}）", nca_ref)
        _save(doc)
    except Exception:
        _doc_path(delivery_id).unlink(missing_ok=True)
        raise HTTPException(500, "存证回写失败——本次开单未发生（清单已清）")
    return _nca_watermark({
        "delivery_id": delivery_id, "status": "draft", "total_items": len(items),
        "nca_seq": nca_ref, "simulated": True,
        "note": "清单已立（draft）——可继续补件（/items），齐了再交付确认（/confirm）。"
    }, nature="simulated")


# C-1 面板 auth_id 式样（AP-＋10 位小十六进制；只读引用其常量式样，⛔ 改 C-1）
def _AUTH_ID_RE_C1(auth_id: str) -> bool:
    return re.match(r"^AP-[0-9a-f]{10}$", auth_id) is not None


class ItemsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: str
    items: list = []


@router.post("/items")
def delivery_items(req: ItemsIn, request: Request):
    """补件（须登录；draft/uploading 可补；逐件哈希必填；大件拆件请填分卷注明）。"""
    user = _require_session_user(request)
    did = req.delivery_id.strip()
    if not _DELIVERY_ID_RE.match(did):
        raise HTTPException(404, "delivery_id 不存在")
    doc = _load(did)
    if doc is None:
        raise HTTPException(404, "delivery_id 不存在")
    _assert_not_frozen(did)
    if doc["status"] not in ("draft", "uploading"):
        raise HTTPException(409, f"该清单状态为 {doc['status']}——已交付确认，⛔ 不可再补件")
    _verify_or_trip(did)
    items, items_err = _check_items(req.items)
    if items_err:
        raise HTTPException(400, items_err)

    prev_status = doc["status"]
    doc["items"].extend(items)
    doc["status"] = "uploading"
    try:
        nca_ref = _nca_append("DELIVERY_ITEMS", user["username"],
                              artifact_path=f"delivery:{did}")
    except Exception:
        doc["items"] = doc["items"][:-len(items)]
        doc["status"] = prev_status
        _save(doc)
        raise HTTPException(500, "存证落链失败——本次补件未发生（状态停本步）")
    row = _nca_row(nca_ref)
    doc["nca_seq"] = nca_ref
    doc["rec_hash"] = row.rec_hash if row else None
    _event(doc, "items", user["username"],
           f"补件 {len(items)} 件（累计 {len(doc['items'])} 件）", nca_ref)
    _save(doc)
    return _nca_watermark({
        "delivery_id": did, "status": doc["status"],
        "total_items": len(doc["items"]), "nca_seq": nca_ref, "simulated": True,
        "note": f"已补 {len(items)} 件（累计 {len(doc['items'])} 件，uploading）——"
                "齐了可交付确认；单件大小阈值待运维核定。"
    }, nature="simulated")


class ConfirmIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: str
    received: list = []               # 接收回执：[{name, hash}]（received 须报哈希）
    resume: bool = False              # operator 复核解冻（熔断恢复；⛔ 自动恢复）
    note: str = ""


@router.post("/confirm")
def delivery_confirm(req: ConfirmIn, request: Request):
    """交付确认（须登录）：uploading→delivered→received。
    received 须报齐全部件的哈希并与清单比对（符／不符）；无哈希视同未收。
    熔断①：同一 delivery_id 观察窗内重复确认 → 停链；熔断②：哈希连续不符 ≥3 → 停链。
    """
    user = _require_session_user(request)
    did = req.delivery_id.strip()
    if not _DELIVERY_ID_RE.match(did):
        raise HTTPException(404, "delivery_id 不存在")
    doc = _load(did)
    if doc is None:
        raise HTTPException(404, "delivery_id 不存在")

    # operator 复核解冻（熔断恢复路径）
    if req.resume:
        if user["role"] not in ("founder", "operator"):
            raise HTTPException(403, "复核解冻须 operator 及以上角色（⛔ 自动恢复、⛔ 降级放行）")
        fz = _freeze_active(did)
        if fz is None:
            raise HTTPException(409, "该链未冻结——无需解冻")
        if doc["status"] != "suspended":
            raise HTTPException(409, "该清单非停权态——解冻路径不适用于此件")
        pre = "uploading"
        m = re.search(r"PRE_FREEZE_STATUS=(\w+)", fz.get("unfrozen_note") or "")
        if m and m.group(1) != "suspended":
            pre = m.group(1)
        nca_ref = _nca_append("DELIVERY_RESUME", user["username"],
                              artifact_path=f"delivery:{did}")
        row = _nca_row(nca_ref)
        doc["status"] = pre
        doc["nca_seq"] = nca_ref
        doc["rec_hash"] = row.rec_hash if row else None
        _event(doc, "resume", user["username"],
               f"operator 复核解冻（原冻结 {fz['reason']}；回摆 {pre}）", nca_ref)
        _save(doc)
        f = fz
        f["unfrozen_by"] = user["username"]
        f["unfrozen_note"] = req.note.strip() or "operator 复核通过"
        f["unfrozen_at"] = _utc()
        _freeze_path(did).write_text(json.dumps(f, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
        return _nca_watermark({
            "delivery_id": did, "status": pre, "nca_seq": nca_ref, "simulated": True,
            "note": f"已复核解冻（原冻结 {fz['reason']}）——状态回摆 {pre}；"
                    "NCA 存证在册（⛔ 自动恢复）"}, nature="simulated")

    _assert_not_frozen(did)
    if doc["status"] == "received":
        raise HTTPException(409, "该清单已签收（received）——重复确认不受理")
    if doc["status"] == "draft":
        raise HTTPException(409, "该清单还在 draft——请先补件（/items）进入 uploading 再确认交付")
    if doc["status"] not in ("uploading", "delivered"):
        raise HTTPException(409, f"该清单状态为 {doc['status']}——⛔ 确认")
    # 非清单起草人 ⛔ 确认（访客只读；确认属写路）
    if user["username"] != doc["created_by"] and user["role"] not in ("founder", "operator"):
        raise HTTPException(403, "非本人 ⛔ 确认——确认人须与开单人同一登录主体")
    # 双库对拍（不符累计；连续 ≥3 熔断②）
    _verify_or_trip(did)
    # 熔断①：观察窗内重复确认
    last = next((e for e in reversed(doc.get("events", [])) if e["event_type"] == "confirm"), None)
    if last is not None and last["actor"] == user["username"]:
        gap = (_parse_ts(_utc()) - (_parse_ts(last["created_at"])
                                    or datetime(2000, 1, 1, tzinfo=timezone.utc)))
        if gap.total_seconds() < _RECONFIRM_WINDOW_SEC:
            _trip_freeze(did, "reconfirm",
                         f"同一 delivery_id {gap.total_seconds():.0f}s 内重复确认"
                         f"（窗 {_RECONFIRM_WINDOW_SEC}s）", by=user["username"])
            raise HTTPException(423, "同一 delivery_id 短时重复确认异常——该链已熔断冻结"
                                     "（fail-closed；须 operator 复核解冻）")

    # 回执比对：received 须报齐全部件哈希；无哈希视同未收（保持 delivered）
    received_map = {}
    for r in req.received:
        if isinstance(r, dict) and str(r.get("name", "")).strip():
            received_map[str(r["name"]).strip()] = str(r.get("hash", "")).strip()
    results = [{"name": it["name"], "expected_hash": it["hash"],
                "reported_hash": received_map.get(it["name"], ""),
                "match": received_map.get(it["name"]) == it["hash"]}
               for it in doc["items"]]
    all_reported = all(r["reported_hash"] for r in results) and bool(results)

    if all_reported and all(r["match"] for r in results):
        target = "received"
    else:
        target = "delivered"
    prev_status = doc["status"]
    doc["status"] = target
    try:
        nca_ref = _nca_append("DELIVERY_CONFIRM", user["username"],
                              artifact_path=f"delivery:{did}")
    except Exception:
        doc["status"] = prev_status
        _save(doc)
        raise HTTPException(500, "确认存证落链失败——状态已停在本步，请重试")
    row = _nca_row(nca_ref)
    doc["nca_seq"] = nca_ref
    doc["rec_hash"] = row.rec_hash if row else None
    _event(doc, "confirm", user["username"],
           f"交付确认（{prev_status}→{target}；回执 {len(received_map)} 件）", nca_ref)
    _save(doc)
    note = ("已签收（received）——全部件哈希对拍相符。" if target == "received" else
            "已交付确认（delivered）——接收方回执哈希未报齐或有不符，视同未收："
            "请接收方按各件哈希回执后再确认签收。")
    return _nca_watermark({
        "delivery_id": did, "status": target, "nca_seq": nca_ref,
        "received_checks": results, "simulated": True, "note": note,
    }, nature="simulated")


@router.get("/{delivery_id}")
def delivery_public(delivery_id: str):
    """公开读（免会话）：交了几件、各件哈希与状态；⛔ 起草人账号。无存证视未发生（404）。"""
    did = (delivery_id or "").strip()
    if not _DELIVERY_ID_RE.match(did):
        raise HTTPException(404, "该端点未上线或不存在")
    doc = _load(did)
    if doc is None or not doc.get("nca_seq"):
        raise HTTPException(404, "delivery_id 不存在（无存证视为未发生）")
    return _public_view(doc)


# GET 集合面守卫：裸 GET /delivery 本令未开（⛔ 不做列表公开面）
@router.get("")
def delivery_list_guard():
    raise HTTPException(404, "该端点未上线或不存在")
