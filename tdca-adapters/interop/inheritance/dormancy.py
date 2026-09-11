# -*- coding: utf-8 -*-
"""智能体休眠态（dormant）状态机与唤醒条件（G3 深化 / #14）

制度依据:
  - 继承机制立项件 §四-1（休眠态状态机细则——唤醒条件）：本模块即该项实现
  - estate.py：`agent_disposition="dormant"` 处置的**状态化承接**（原仅取值，无状态机）
  -（人类签批权不代行）：`ruling-authorized` 唤醒须携人类裁决引用

状态机:
    ACTIVE ──enter──▶ DORMANT ──awaken──▶ AWAKENED
                          └──sweep（窗口期满）──▶ DEREGISTERED
    DEREGISTERED 为终态（不可唤醒）；AWAKENED 可再次 enter（循环）

唤醒条件（三选一，均须证据引用）:
  1. `heir-request`             继承人书面请求（evidence = 请求件引用）
  2. `ruling-authorized`        人类裁决授权（evidence + **ruling_ref 必填**，）
  3. `creation-chain-recovery`  创建链主体恢复（evidence = 链引用，公理 6 f⁻ 可审计还原）

纪律:
  - 每主体同时仅一个休眠记录；进入/唤醒各生成 NCA 存证；幂等（重复 enter 拒绝）
  - 窗口期满**不自动唤醒**，转 DEREGISTERED（唤醒须主动且合条件）
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

DORMANCY_STATES = ("ACTIVE", "DORMANT", "AWAKENED", "DEREGISTERED")
WAKE_TRIGGERS = ("heir-request", "ruling-authorized", "creation-chain-recovery",
                 "dispute-resolved")   # 第四项：争议结束且归属明确 → 可解除休眠（创始人追加裁定 2026-09-11）
DEFAULT_WINDOW_DAYS = 365


class DormancyError(Exception):
    """休眠态纪律违例。"""


class _LocalSeal:
    """离线可用的轻量存证桩（tdca_nca 不可用时兜底；接口与 NCAGenerator 最小面一致）。"""

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
class DormancyRecord:
    subject_tdid: str
    state: str = "DORMANT"
    reason: str = ""
    entered_at: str = ""
    window_days: int = DEFAULT_WINDOW_DAYS
    expires_at: str = ""
    wake_trigger: Optional[str] = None
    wake_evidence: Optional[str] = None
    ruling_ref: Optional[str] = None
    judicial_ref: Optional[str] = None     # 司法可验证正式文件引用（dispute-resolved 唤醒要件，AMEND-2）
    awakened_at: Optional[str] = None
    deregistered_at: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    nca_refs: List[str] = field(default_factory=list)

    def is_dormant(self) -> bool:
        return self.state == "DORMANT"


class DormancyRegistry:
    """休眠态登记与唤醒（#14）。"""

    def __init__(self, default_window_days: int = DEFAULT_WINDOW_DAYS, nca_generator=None):
        if int(default_window_days) <= 0:
            raise DormancyError("休眠窗口须为正天数")
        self.default_window_days = int(default_window_days)
        self._records: Dict[str, DormancyRecord] = {}
        self._gen = _make_generator(nca_generator)

    # ---------- 进入休眠 ----------
    def enter(self, subject_tdid: str, reason: str, window_days: Optional[int] = None,
              from_execution: bool = False) -> DormancyRecord:
        """进入休眠态（幂等：已在休眠即拒；终态不可逆）。

        目标函数: 将 disposition="dormant" 的处置状态化（进入条件 + 窗口 + 存证）
        约束矩阵: subject 必填；reason 必填；窗口为正；已 DORMANT / DEREGISTERED 拒绝
        先验分布: estate.execute_inheritance 的 agent_disposition
        配置权边界: L2 场景层
        预期分配: DormancyRecord
        审计轨迹: nca_refs（estate-dormancy-enter）
        """
        if not subject_tdid:
            raise DormancyError("休眠登记须载明主体（subject_tdid）")
        if not reason:
            raise DormancyError("休眠须给出理由（可审计）")
        win = int(self.default_window_days if window_days is None else window_days)
        if win <= 0:
            raise DormancyError("休眠窗口须为正天数")
        rec = self._records.get(subject_tdid)
        if rec is not None and rec.state == "DORMANT":
            raise DormancyError(f"主体已处于休眠态: {subject_tdid}")
        if rec is not None and rec.state == "DEREGISTERED":
            raise DormancyError(f"主体已注销（终态，不可再休眠）: {subject_tdid}")

        now = datetime.now().astimezone()
        new_rec = DormancyRecord(
            subject_tdid=subject_tdid, state="DORMANT", reason=reason,
            entered_at=now.isoformat(timespec="seconds"),
            window_days=win,
            expires_at=(now + timedelta(days=win)).isoformat(timespec="seconds"),
        )
        nca = self._gen.generate(type="estate-dormancy-enter", layer=2,
                                 content={"subject_tdid": subject_tdid, "reason": reason,
                                          "window_days": win, "from_execution": from_execution,
                                          "simulated": True})
        new_rec.nca_refs.append(nca.nca_id)
        new_rec.history.append({"at": new_rec.entered_at, "event": "enter", "reason": reason})
        self._records[subject_tdid] = new_rec
        return new_rec

    # ---------- 唤醒 ----------
    def awaken(self, subject_tdid: str, trigger: str, evidence: str,
               ruling_ref: Optional[str] = None,
               judicial_ref: Optional[str] = None) -> DormancyRecord:
        """按唤醒条件唤醒（三选一；`ruling-authorized` 须人类裁决引用，）。

        目标函数: 休眠体复归（仅合条件者；证据引用强制留痕）
        约束矩阵: 须处于 DORMANT；trigger ∈ WAKE_TRIGGERS；evidence 必填；
                  trigger="ruling-authorized" 时 ruling_ref 必填（AI 不代行裁决）
        先验分布: 本模块 WAKE_TRIGGERS 细则
        配置权边界: L2 场景层
        预期分配: 更新后的 DormancyRecord（state=AWAKENED）
        审计轨迹: nca_refs（estate-dormancy-awaken）
        """
        rec = self._records.get(subject_tdid)
        if rec is None or rec.state != "DORMANT":
            raise DormancyError(f"主体非休眠态（当前 {rec.state if rec else 'NONE'}），不可唤醒")
        if trigger not in WAKE_TRIGGERS:
            raise DormancyError(f"唤醒触发不在允许集: {WAKE_TRIGGERS}")
        if not evidence:
            raise DormancyError("唤醒须给出证据引用（evidence 必填）")
        if trigger == "ruling-authorized" and not ruling_ref:
            raise DormancyError("裁决授权唤醒须携人类裁决引用（ruling_ref， 不代行）")
        if trigger == "dispute-resolved" and not judicial_ref:
            raise DormancyError("争议结论须凭**司法可验证的正式文件**（judicial_ref）："
                                "争议裁决非 TDCA 职责；无司法文件前 TDCA 不得有任何其他动作，只能休眠")

        rec.state = "AWAKENED"
        rec.awake_trigger = trigger
        rec.wake_evidence = evidence
        rec.ruling_ref = ruling_ref
        rec.judicial_ref = judicial_ref
        rec.awakened_at = datetime.now().astimezone().isoformat(timespec="seconds")
        nca = self._gen.generate(type="estate-dormancy-awaken", layer=2,
                                 content={"subject_tdid": subject_tdid, "trigger": trigger,
                                          "evidence": evidence, "ruling_ref": ruling_ref,
                                          "judicial_ref": judicial_ref,
                                          "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        rec.history.append({"at": rec.awakened_at, "event": "awaken", "trigger": trigger,
                            "evidence": evidence, "ruling_ref": ruling_ref})
        return rec

    # ---------- 窗口期满扫描 ----------
    def sweep(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """窗口期满扫描：超期休眠体转 DEREGISTERED（**不自动唤醒**）。

        目标函数: 窗口期满的确定性处置（转注销而非唤醒——唤醒须主动且合条件）
        约束矩阵: 仅 DORMANT 且 expires_at 已过者；逐个存证；幂等（已注销不重复）
        先验分布: 窗口 = default_window_days / 自定义
        配置权边界: L2 场景层
        预期分配: [{"subject_tdid","expired_at","nca_ref"}]
        审计轨迹: nca_refs（estate-dormancy-timeout）
        """
        ts = now or datetime.now().astimezone()
        out: List[Dict[str, Any]] = []
        for tdid, rec in self._records.items():
            if rec.state != "DORMANT":
                continue
            exp = datetime.fromisoformat(rec.expires_at)
            if ts >= exp:
                rec.state = "DEREGISTERED"
                rec.deregistered_at = ts.isoformat(timespec="seconds")
                nca = self._gen.generate(type="estate-dormancy-timeout", layer=2,
                                         content={"subject_tdid": tdid, "expired_at": rec.expires_at,
                                                  "simulated": True})
                rec.nca_refs.append(nca.nca_id)
                rec.history.append({"at": rec.deregistered_at, "event": "timeout-deregister"})
                out.append({"subject_tdid": tdid, "expired_at": rec.expires_at,
                            "nca_ref": nca.nca_id})
        return out

    # ---------- 观测 ----------
    def expired(self, now: Optional[datetime] = None) -> List[DormancyRecord]:
        """窗口已期满、仍处休眠态的记录（**只读**；供无主托管判定衔接，不改变状态）。

        目标函数: 作为 G3 #17「休眠满一年」要件的计时依据（与 escheat 模块衔接）
        约束矩阵: 只读；不改状态（注销/托管处置分别由 sweep / escheat 执行）
        先验分布: 本模块 expires_at
        配置权边界: L2 场景层
        预期分配: [DormancyRecord]
        审计轨迹: 调用方登记 NCA
        """
        ts = now or datetime.now().astimezone()
        return [r for r in self._records.values()
                if r.state == "DORMANT" and ts >= datetime.fromisoformat(r.expires_at)]

    def record(self, subject_tdid: str) -> Optional[DormancyRecord]:
        return self._records.get(subject_tdid)

    def state_of(self, subject_tdid: str) -> str:
        rec = self._records.get(subject_tdid)
        return rec.state if rec else "ACTIVE"

    def is_dormant(self, subject_tdid: str) -> bool:
        rec = self._records.get(subject_tdid)
        return bool(rec and rec.is_dormant())
