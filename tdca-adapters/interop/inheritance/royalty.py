# -*- coding: utf-8 -*-
"""分润权益过渡期记账（G3 深化 / #16）

问题: 继承未决期间（DECLARED/OPEN/DISPUTED），主体分润权益仍在产生——归谁？何时付？
口径（本模块）:
  - **只记不付**：未决期间一律记入 `pending` 过渡账（不得支付/不得分配）
  - **执行后结转**：继承执行完成、取得最终 `distribution` 后，一次性按份额**结转**（settle）
  - **无继承人/待托管**：可 `hold`（挂账），去向待口径（继承机制立项件 §四-4 托管去向，另项）
  - **幂等**：已结转条目不再结转；重复 settle 只处理剩余 pending

纪律:
  - 记账与结转各生成 NCA 存证（可审计）
  - 结转分配合计须 ≈ 1.0（与 estate 分配口径一致）；金额为 0 条目允许（记痕）
  - 数据性质: 模拟态（**不构成任何真实支付指令**）

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional


class RoyaltyLedgerError(Exception):
    """过渡期记账纪律违例。"""


class _LocalSeal:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def generate(self, *, type: str, layer: int, content: Dict[str, Any]):
        raw = json.dumps({"t": type, "l": layer, "c": content}, ensure_ascii=False, sort_keys=True)
        nca_id = "NCA-INH-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        self._store[nca_id] = {"nca_id": nca_id, "type": type, "layer": layer, "content": content}
        return SimpleNamespace(nca_id=nca_id)

    def get(self, nca_id: str):
        return self._store.get(nca_id)

    def verify_seal(self, rec) -> bool:
        return bool(rec)


def _make_generator(nca_generator=None):
    if nca_generator is not None:
        return nca_generator
    try:
        from tdca_nca.generator import NCAGenerator  # type: ignore
        return NCAGenerator()
    except Exception:                                  # noqa: BLE001
        return _LocalSeal()


@dataclass
class RoyaltyEntry:
    entry_id: str
    subject_tdid: str
    period: str
    amount: float
    status: str = "pending"                    # pending / settled / held
    accrued_at: str = ""
    settled_at: Optional[str] = None
    allocation: Dict[str, float] = field(default_factory=dict)   # 结转去向（按份额）
    nca_refs: List[str] = field(default_factory=list)


class RoyaltyTransitionLedger:
    """继承未决期间的分润权益过渡账（#16）。"""

    def __init__(self, nca_generator=None):
        self._entries: Dict[str, RoyaltyEntry] = {}          # entry_id -> entry
        self._seq = 0
        self._gen = _make_generator(nca_generator)

    # ---------- 记账（只记不付）----------
    def accrue(self, subject_tdid: str, amount: float, period: str,
               note: Optional[str] = None) -> RoyaltyEntry:
        """未决期间记入过渡账（**pending，不支付**）。

        目标函数: 继承未决期产生的分润权益可追溯暂记（防"未决期间流失/私分"）
        约束矩阵: subject/period 必填；amount ≥ 0；每笔生成独立 entry_id + 存证
        先验分布: estate 状态机（未决 = 非 EXECUTED）
        配置权边界: L2 记账层（不触发支付）
        预期分配: RoyaltyEntry（status=pending）
        审计轨迹: nca_refs（royalty-accrual）
        """
        if not subject_tdid or not period:
            raise RoyaltyLedgerError("记账须载明主体与期间（subject_tdid / period）")
        amt = float(amount)
        if amt < 0:
            raise RoyaltyLedgerError("记账金额不得为负")
        self._seq += 1
        eid = f"RT-{subject_tdid[-8:]}-{self._seq:04d}"
        entry = RoyaltyEntry(entry_id=eid, subject_tdid=subject_tdid, period=period, amount=amt,
                             accrued_at=datetime.now().astimezone().isoformat(timespec="seconds"))
        nca = self._gen.generate(type="royalty-accrual", layer=2,
                                 content={"entry_id": eid, "subject_tdid": subject_tdid,
                                          "period": period, "amount": amt, "note": note,
                                          "status": "pending", "simulated": True})
        entry.nca_refs.append(nca.nca_id)
        self._entries[eid] = entry
        return entry

    def hold(self, subject_tdid: str, reason: str) -> Dict[str, Any]:
        """挂账（无继承人/待托管口径）——**只标记，不改变金额**。

        目标函数: 无继承人或托管口径未定时，将 pending 标记为 held（等待 #17 托管口径）
        约束矩阵: reason 必填；仅 pending 条目可挂账
        先验分布: 继承机制立项件 §四-4（托管去向，另项）
        配置权边界: L2 记账层
        预期分配: {"held_entries":[...],"held_total":float,"nca_ref":str}
        审计轨迹: nca_refs（royalty-hold）
        """
        if not reason:
            raise RoyaltyLedgerError("挂账须给出理由（托管去向待口径）")
        held: List[str] = []
        total = 0.0
        for e in self._entries.values():
            if e.subject_tdid == subject_tdid and e.status == "pending":
                e.status = "held"
                held.append(e.entry_id)
                total = round(total + e.amount, 2)
        nca = self._gen.generate(type="royalty-hold", layer=2,
                                 content={"subject_tdid": subject_tdid, "reason": reason,
                                          "entries": held, "total": total, "simulated": True})
        for eid in held:
            self._entries[eid].nca_refs.append(nca.nca_id)
        return {"held_entries": held, "held_total": total, "nca_ref": nca.nca_id}

    # ---------- 结转（执行后）----------
    def settle(self, subject_tdid: str, distribution: Dict[str, float]) -> Dict[str, Any]:
        """继承执行后**按最终分配份额一次性结转**（幂等：只结 pending）。

        目标函数: 未决期暂记 → 按最终 distribution 归属（可核销、可复算）
        约束矩阵: distribution 非空、非负、合计 ≈ 1.0；仅 pending 条目参与；held 不自动结（须先释放）
        先验分布: estate.execute_inheritance 的 distribution
        配置权边界: L2 记账层（**模拟态结转，非真实支付**）
        预期分配: {"settled_entries","total","by_beneficiary","nca_ref","skipped_held"}
        审计轨迹: nca_refs（royalty-settlement）
        """
        if not distribution:
            raise RoyaltyLedgerError("结转须提供最终分配（distribution）")
        if any(v < 0 for v in distribution.values()):
            raise RoyaltyLedgerError("分配份额不得为负")
        total_share = round(sum(distribution.values()), 6)
        if abs(total_share - 1.0) > 1e-6:
            raise RoyaltyLedgerError(f"分配份额合计须为 1.0（当前 {total_share}）")

        pending = [e for e in self._entries.values()
                   if e.subject_tdid == subject_tdid and e.status == "pending"]
        held = [e.entry_id for e in self._entries.values()
                if e.subject_tdid == subject_tdid and e.status == "held"]
        grand = round(sum(e.amount for e in pending), 2)
        by_beneficiary: Dict[str, float] = {p: 0.0 for p in distribution}
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        for e in pending:
            alloc = {p: round(e.amount * s, 2) for p, s in distribution.items()}
            drift = round(e.amount - sum(alloc.values()), 2)
            if abs(drift) >= 0.01:                       # 尾差归入最大份额者（可复算）
                top = max(distribution, key=lambda k: distribution[k])
                alloc[top] = round(alloc[top] + drift, 2)
            e.allocation = alloc
            e.status = "settled"
            e.settled_at = now
            for p, v in alloc.items():
                by_beneficiary[p] = round(by_beneficiary.get(p, 0.0) + v, 2)
        nca = self._gen.generate(type="royalty-settlement", layer=3,
                                 content={"subject_tdid": subject_tdid,
                                          "entries": [e.entry_id for e in pending],
                                          "total": grand, "by_beneficiary": by_beneficiary,
                                          "distribution": dict(distribution),
                                          "skipped_held": held, "simulated": True})
        for e in pending:
            e.nca_refs.append(nca.nca_id)
        return {"settled_entries": [e.entry_id for e in pending], "total": grand,
                "by_beneficiary": by_beneficiary, "nca_ref": nca.nca_id,
                "skipped_held": held, "simulated": True}

    # ---------- 托管衔接（G3 #17 口径）----------
    def escheat_held(self, subject_tdid: str, fund_id: str,
                     ruling_ref: Optional[str] = None) -> Dict[str, Any]:
        """把 `held` 挂账余额转入**社区基金公共品池**（口径：休眠一年无归属 → 托管为公共品）。

        目标函数: 消除"无限挂账"终态——无主权益按裁定归入公共品，而非悬置
        约束矩阵: fund_id 必填；仅 `held` 条目参与（pending 须先 hold 或 settle，语义不混）；
                  公共品归属**不可回退**（已 escheated 不再变更）
        先验分布: 创始人裁定（2026-09-11，「休眠一年无归属确认，有社区基金托管为公共品」）+ G3 #17
        配置权边界: L2 记账层（模拟态归属，不构成真实资金划转）
        预期分配: {"escheated_entries","total","fund_id","public_goods","nca_ref"}
        审计轨迹: nca_refs（royalty-escheat-community-fund）
        """
        if not fund_id:
            raise RoyaltyLedgerError("托管须指明社区基金（fund_id）")
        held = [e for e in self._entries.values()
                if e.subject_tdid == subject_tdid and e.status == "held"]
        total = round(sum(e.amount for e in held), 2)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        for e in held:
            e.status = "escheated"
            e.allocation = {fund_id: e.amount}                 # 公共品池（非私有受益人）
            e.settled_at = now
        nca = self._gen.generate(type="royalty-escheat-community-fund", layer=3,
                                 content={"subject_tdid": subject_tdid, "fund_id": fund_id,
                                          "entries": [e.entry_id for e in held],
                                          "total": total, "public_goods": True,
                                          "ruling_ref": ruling_ref, "simulated": True})
        for e in held:
            e.nca_refs.append(nca.nca_id)
        return {"escheated_entries": [e.entry_id for e in held], "total": total,
                "fund_id": fund_id, "public_goods": True, "ruling_ref": ruling_ref,
                "nca_ref": nca.nca_id, "simulated": True}

    # ---------- 观测 ----------
    def pending_total(self, subject_tdid: str) -> float:
        return round(sum(e.amount for e in self._entries.values()
                         if e.subject_tdid == subject_tdid and e.status == "pending"), 2)

    def entries(self, subject_tdid: Optional[str] = None,
                status: Optional[str] = None) -> List[RoyaltyEntry]:
        out = list(self._entries.values())
        if subject_tdid:
            out = [e for e in out if e.subject_tdid == subject_tdid]
        if status:
            out = [e for e in out if e.status == status]
        return out
