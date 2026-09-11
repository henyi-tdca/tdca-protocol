# -*- coding: utf-8 -*-
"""无主权益托管——社区基金公共品口径（G3 深化 / #17）

创始人裁定（2026-09-11）:
  > 「**休眠一年无归属确认，有社区基金托管为公共品**」

口径（本模块实现）:
  1. **触发三要件**（缺一不可）：① **无继承人**（`has_heirs=False`）② 主体**休眠满一年**
     （`unclaimed_days`，默认 365，与 dormant 窗口同源）③ **无归属确认**（期内无人主张）
  2. **托管结果**：转入**社区基金**（`fund_id`）并标记 **`public_goods=True`（公共品）**——
     此后**不可再私有化**（不得回转为继承人私有权益）
  3. **归属确认优先**：一年内出现有效归属主张（`confirm_ownership`）即**阻断托管**
  4. **争议兜底（AMEND-1 + AMEND-2）**：
     - 争议致无法确认归属 → **不托管**；主体**保持休眠**（计时不中断）；
     - **争议裁决属司法部门，非 TDCA 职责**——在**无可验证的司法正式文件**前，TDCA
       **不得有任何其他动作**（不得托管、不得唤醒、不得分配），**只能让其休眠**；
     - 司法文件明确归属 → 阻断托管且可解除休眠（`judicial_ref` 必填）；
     - 争议结束但归属仍不明 → **仍不得托管**（除非司法文件明确无归属）。
  5. **法理依据（本口径正当性）**：**无归属、无争议、满一年 → 公共品**，由社区基金托管，
     符合法律上的**善意管理 / 无因管理**规定（见 `LEGAL_BASIS_UNCLAIMED`）。
     此路径**无需任何裁决引用**（无争议即无待裁事项）。

纪律:
  - 托管与归属确认各生成 NCA 存证；幂等（已托管不可重复/不可回退）
  - 金额与资产为**模拟态**，不构成真实资产处分
  - 与 `dormancy`（窗口期满）、`royalty`（挂账余额）衔接：见 `expired()` / `escheat_held()`

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union

DEFAULT_UNCLAIMED_DAYS = 365
DEFAULT_FUND_ID = "TDCA-COMMUNITY-FUND-001"
ESCHEAT_STATES = ("PENDING", "ESCHEATED")
# 无归属无争议满一年 → 公共品的法理依据（创始人法理定性 2026-09-11）
LEGAL_BASIS_UNCLAIMED = "善意管理/无因管理（无归属·无争议·休眠满一年）"


class EscheatError(Exception):
    """无主权益托管纪律违例。"""


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


def _as_dt(value: Union[str, datetime]) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


@dataclass
class EscheatRecord:
    subject_tdid: str
    state: str = "PENDING"                            # PENDING / ESCHEATED
    has_heirs: bool = False
    dormancy_entered_at: str = ""
    unclaimed_days: int = DEFAULT_UNCLAIMED_DAYS
    eligible_at: str = ""
    confirmed_at: Optional[str] = None                # 归属确认时点（阻断托管）
    escheated_at: Optional[str] = None
    fund_id: Optional[str] = None
    public_goods: bool = False                        # 托管后 = 公共品（不可私有化）
    assets: Dict[str, Any] = field(default_factory=dict)
    judicial_ref: Optional[str] = None                # 司法可验证正式文件引用（AMEND-2）
    claimants: List[Dict[str, str]] = field(default_factory=list)
    # ---- 争议路径（创始人追加裁定 2026-09-11）----
    dispute_open: bool = False                        # 争议未决 → 排除托管、保持休眠
    dispute_grounds: Optional[str] = None
    dispute_opened_at: Optional[str] = None
    dispute_closed_at: Optional[str] = None
    ownership_clarified: Optional[bool] = None        # 争议结束时的归属结论
    may_awaken: bool = False                          # 归属明确 → 可解除休眠
    nca_refs: List[str] = field(default_factory=list)


class EscheatRegistry:
    """无主权益 → 社区基金公共品 托管登记（#17）。"""

    def __init__(self, unclaimed_days: int = DEFAULT_UNCLAIMED_DAYS,
                 fund_id: str = DEFAULT_FUND_ID, nca_generator=None):
        if int(unclaimed_days) <= 0:
            raise EscheatError("托管等待期须为正天数")
        self.unclaimed_days = int(unclaimed_days)
        self.fund_id = fund_id
        self._records: Dict[str, EscheatRecord] = {}
        self._gen = _make_generator(nca_generator)

    # ---------- 登记（无继承人 + 休眠起点）----------
    def register(self, subject_tdid: str, *, has_heirs: bool,
                 dormancy_entered_at: Union[str, datetime],
                 assets: Optional[Dict[str, Any]] = None,
                 unclaimed_days: Optional[int] = None) -> EscheatRecord:
        """登记"无归属"候选（幂等：已登记返回既有；已托管即拒）。

        目标函数: 明确"无继承人 + 休眠起点"，为一年期满判定与后续托管建立锚点
        约束矩阵: subject 必填；has_heirs=True 即拒（有继承人不得走托管路径）
        先验分布: dormancy 记录的 entered_at + 继承判定结果
        配置权边界: L2 场景层
        预期分配: EscheatRecord（state=PENDING）
        审计轨迹: nca_refs（estate-escheat-register）
        """
        if not subject_tdid:
            raise EscheatError("托管登记须载明主体")
        if has_heirs:
            raise EscheatError("有继承人不适用无主托管（应走继承路径）")
        cur = self._records.get(subject_tdid)
        if cur is not None:
            if cur.state == "ESCHEATED":
                raise EscheatError(f"主体权益已托管为公共品（不可重复登记）: {subject_tdid}")
            return cur
        days = int(self.unclaimed_days if unclaimed_days is None else unclaimed_days)
        if days <= 0:
            raise EscheatError("托管等待期须为正天数")
        entered = _as_dt(dormancy_entered_at)
        rec = EscheatRecord(
            subject_tdid=subject_tdid, has_heirs=False,
            dormancy_entered_at=entered.isoformat(timespec="seconds"),
            unclaimed_days=days,
            eligible_at=(entered + timedelta(days=days)).isoformat(timespec="seconds"),
            assets=dict(assets or {}),
        )
        nca = self._gen.generate(type="estate-escheat-register", layer=2,
                                 content={"subject_tdid": subject_tdid,
                                          "dormancy_entered_at": rec.dormancy_entered_at,
                                          "unclaimed_days": days, "eligible_at": rec.eligible_at,
                                          "assets": rec.assets, "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        self._records[subject_tdid] = rec
        return rec

    # ---------- 归属确认（阻断托管）----------
    def confirm_ownership(self, subject_tdid: str, claimant: str, evidence: str) -> EscheatRecord:
        """归属确认（一年内出现有效主张）→ 阻断托管路径。

        目标函数: 保障"一年内有人主张"优先于公共品托管（归属确认先于公共化）
        约束矩阵: 须已登记且未托管；claimant 与 evidence 必填
        先验分布: 创始人裁定"**无归属确认**"为触发要件之一
        配置权边界: L2 场景层
        预期分配: 更新后的 rec（confirmed_at 置位，后续 eligibility=False）
        审计轨迹: nca_refs（estate-escheat-ownership-confirmed）
        """
        rec = self._records.get(subject_tdid)
        if rec is None:
            raise EscheatError(f"未登记无归属候选: {subject_tdid}")
        if rec.state == "ESCHEATED":
            raise EscheatError("权益已托管为公共品，不可再确认私有归属（公共品不可私有化）")
        if not claimant or not evidence:
            raise EscheatError("归属确认须载明主张人与证据（claimant / evidence）")
        rec.confirmed_at = datetime.now().astimezone().isoformat(timespec="seconds")
        rec.claimants.append({"claimant": claimant, "evidence": evidence,
                              "at": rec.confirmed_at})
        nca = self._gen.generate(type="estate-escheat-ownership-confirmed", layer=2,
                                 content={"subject_tdid": subject_tdid, "claimant": claimant,
                                          "evidence": evidence, "blocks_escheat": True,
                                          "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        return rec

    # ---------- 争议路径（创始人追加裁定：争议致无法确认归属 → 不托管，争议期内休眠）----------
    def mark_contested(self, subject_tdid: str, grounds: str,
                      claimants: Optional[List[str]] = None) -> EscheatRecord:
        """标记争议未决：**排除托管**、主体**保持休眠**（争议期不中断休眠计时）。

        目标函数: 落实创始人追加裁定——「引争议造成无法确认归属，不托管，争议期内休眠，
                  以争议结束，归属明确后，可解除休眠」
        约束矩阵: 须已登记且未托管；grounds 必填；重复标记即拒（不重复开启）
        先验分布: 创始人追加裁定（2026-09-11）+ shapley.DisputeRegistry（争议流程）
        配置权边界: L2 场景层（判定排除；不处分资产）
        预期分配: 更新后的 rec（dispute_open=True ⇒ eligibility 恒 False）
        审计轨迹: nca_refs（estate-escheat-dispute-open）
        """
        rec = self._records.get(subject_tdid)
        if rec is None:
            raise EscheatError(f"未登记无归属候选: {subject_tdid}")
        if rec.state == "ESCHEATED":
            raise EscheatError("权益已托管为公共品，不可再标记争议")
        if not grounds:
            raise EscheatError("争议须载明事由（grounds）")
        if rec.dispute_open:
            raise EscheatError("该主体争议已处未决状态（不重复开启）")
        rec.dispute_open = True
        rec.dispute_grounds = grounds
        rec.dispute_opened_at = datetime.now().astimezone().isoformat(timespec="seconds")
        for c in (claimants or []):
            rec.claimants.append({"claimant": c, "evidence": "dispute-open",
                                  "at": rec.dispute_opened_at})
        nca = self._gen.generate(type="estate-escheat-dispute-open", layer=2,
                                 content={"subject_tdid": subject_tdid, "grounds": grounds,
                                          "claimants": list(claimants or []),
                                          "escheat_excluded": True,
                                          "dormancy_continues": True, "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        return rec

    def close_dispute(self, subject_tdid: str, *, ownership_clarified: bool, evidence: str,
                      judicial_ref: Optional[str] = None) -> Dict[str, Any]:
        """争议结束登记：**须凭司法可验证的正式文件**（AMEND-2：TDCA 不裁决争议）。

        目标函数: 落实创始人法理定性——争议裁决属**司法部门**；在无可验证的司法正式文件前，
                  TDCA **不得有任何其他动作**（只能让主体休眠）
        约束矩阵: 须存在未决争议；evidence 必填；**judicial_ref 必填**（司法文书要素：编号/出具
                  机关/日期等，供外部核验）；归属明确者阻断托管且可解除休眠；不明确者仍不得托管
        先验分布: 创始人法理定性（2026-09-11，AMEND-2）
        配置权边界: L2 场景层（**仅登记**司法结论；不自行形成结论）
        预期分配: {"closed","ownership_clarified","may_awaken","escheat_allowed","judicial_ref","nca_ref"}
        审计轨迹: nca_refs（estate-escheat-dispute-close）
        """
        rec = self._records.get(subject_tdid)
        if rec is None:
            raise EscheatError(f"未登记无归属候选: {subject_tdid}")
        if not rec.dispute_open:
            raise EscheatError("无未决争议可结束")
        if not evidence:
            raise EscheatError("争议结束须给出结案证据引用（evidence）")
        if not judicial_ref:
            raise EscheatError("争议结论须凭**司法可验证的正式文件**（judicial_ref）："
                               "争议裁决非 TDCA 职责；无司法文件前 TDCA 不得有任何其他动作，只能休眠")
        rec.dispute_open = False
        rec.dispute_closed_at = datetime.now().astimezone().isoformat(timespec="seconds")
        rec.judicial_ref = judicial_ref
        rec.ownership_clarified = bool(ownership_clarified)
        rec.may_awaken = bool(ownership_clarified)
        if ownership_clarified:
            rec.confirmed_at = rec.dispute_closed_at
        nca = self._gen.generate(type="estate-escheat-dispute-close", layer=2,
                                 content={"subject_tdid": subject_tdid,
                                          "ownership_clarified": bool(ownership_clarified),
                                          "evidence": evidence, "judicial_ref": judicial_ref,
                                          "may_awaken": rec.may_awaken,
                                          "escheat_allowed": not ownership_clarified,
                                          "authority": "judicial", "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        return {"closed": True, "subject_tdid": subject_tdid,
                "ownership_clarified": rec.ownership_clarified,
                "may_awaken": rec.may_awaken,
                "escheat_allowed": not rec.ownership_clarified,
                "judicial_ref": judicial_ref,
                "nca_ref": nca.nca_id, "simulated": True}

    # ---------- 资格判定 ----------
    def eligibility(self, subject_tdid: str, now: Optional[datetime] = None) -> Dict[str, Any]:
        """托管资格判定（三要件：无继承人 + 休眠满一年 + 无归属确认）。

        目标函数: 把创始人裁定的三要件做成**可复算判定**（而非人工记忆）
        约束矩阵: 任一要件不满足即 eligible=False，并给 reasons
        先验分布: 创始人裁定（2026-09-11）
        配置权边界: L2 场景层（判定层，不处分）
        预期分配: {"eligible","reasons","days_elapsed","required_days","eligible_at"}
        审计轨迹: 调用方登记 NCA
        """
        rec = self._records.get(subject_tdid)
        if rec is None:
            return {"eligible": False, "reasons": ["未登记无归属候选"], "days_elapsed": 0,
                    "required_days": self.unclaimed_days, "eligible_at": None}
        ts = now or datetime.now().astimezone()
        days_elapsed = int((ts - _as_dt(rec.dormancy_entered_at)).days)
        reasons: List[str] = []
        if rec.has_heirs:
            reasons.append("存在继承人（应走继承路径）")
        if rec.dispute_open:
            reasons.append("争议未决：不适用托管（争议期内保持休眠，待争议结束归属明确）")
        if rec.confirmed_at:
            reasons.append("期内已有归属确认")
        if days_elapsed < rec.unclaimed_days:
            reasons.append(f"休眠未满 {rec.unclaimed_days} 天（已 {days_elapsed} 天）")
        if rec.state == "ESCHEATED":
            reasons.append("已托管为公共品")
        return {"eligible": not reasons, "reasons": reasons, "days_elapsed": days_elapsed,
                "required_days": rec.unclaimed_days, "eligible_at": rec.eligible_at}

    # ---------- 托管（转社区基金公共品）----------
    def escheat(self, subject_tdid: str, *, now: Optional[datetime] = None,
                judicial_ref: Optional[str] = None) -> Dict[str, Any]:
        """按口径执行托管：**社区基金 + 公共品**（不可逆、不可私有化）。

        目标函数: 休眠满一年仍无归属的无主权益 → 社区基金托管为公共品
                  （法理依据：**善意管理 / 无因管理**——无归属、无争议、满一年）
        约束矩阵: 须满足三要件；已托管即拒；**若存在任何争议痕迹，须凭司法可验证的正式文件
                  （judicial_ref）**——争议裁决非 TDCA 职责，无司法文件不得有任何动作
        先验分布: 创始人裁定（2026-09-11 三要件 + AMEND-2 法理定性）
        配置权边界: L2 场景层（模拟态托管；不构成真实资产处分）
        预期分配: {"escheated","subject_tdid","fund_id","public_goods","total","legal_basis","nca_ref"}
        审计轨迹: nca_refs（estate-escheat-community-fund）
        """
        elig = self.eligibility(subject_tdid, now=now)
        if not elig["eligible"]:
            raise EscheatError(f"不满足托管三要件: {'；'.join(elig['reasons'])}")
        rec = self._records[subject_tdid]
        if (rec.claimants or rec.dispute_grounds) and not judicial_ref:
            raise EscheatError("存在争议痕迹：须凭**司法可验证的正式文件**（judicial_ref）方可动作；"
                               "无司法文件前 TDCA 不得有任何其他动作，只能休眠")
        total = 0.0
        for v in (rec.assets or {}).values():
            if isinstance(v, (int, float)):
                total = round(total + float(v), 2)
        rec.state = "ESCHEATED"
        rec.escheated_at = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
        rec.fund_id = self.fund_id
        rec.public_goods = True
        rec.judicial_ref = judicial_ref
        nca = self._gen.generate(type="estate-escheat-community-fund", layer=3,
                                 content={"subject_tdid": subject_tdid, "fund_id": self.fund_id,
                                          "public_goods": True, "total": total,
                                          "assets": rec.assets, "judicial_ref": judicial_ref,
                                          "legal_basis": LEGAL_BASIS_UNCLAIMED,
                                          "eligible_at": rec.eligible_at, "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        return {"escheated": True, "subject_tdid": subject_tdid, "fund_id": self.fund_id,
                "public_goods": True, "total": total, "escheated_at": rec.escheated_at,
                "judicial_ref": judicial_ref, "legal_basis": LEGAL_BASIS_UNCLAIMED,
                "nca_ref": nca.nca_id, "simulated": True}

    # ---------- 与 dormancy 衔接 ----------
    def register_from_dormancy(self, dormancy_registry, subject_tdid: str, *,
                               has_heirs: bool, assets: Optional[Dict[str, Any]] = None,
                               unclaimed_days: Optional[int] = None) -> EscheatRecord:
        """便捷衔接：从 `DormancyRegistry` 取休眠起点登记（窗口期满者方适用）。

        目标函数: 复用休眠记录作为"一年"计时锚点，避免口径各自为政
        约束矩阵: 休眠记录须存在且非 ACTIVE 之外的空缺；has_heirs 由继承侧给出
        先验分布: dormancy.DormancyRegistry.record()
        配置权边界: L2 场景层
        预期分配: EscheatRecord
        审计轨迹: nca_refs（estate-escheat-register）
        """
        drec = dormancy_registry.record(subject_tdid)
        if drec is None or not drec.entered_at:
            raise EscheatError("休眠记录缺失：须先 enter 休眠（提供计时锚点）")
        return self.register(subject_tdid, has_heirs=has_heirs,
                             dormancy_entered_at=drec.entered_at, assets=assets,
                             unclaimed_days=unclaimed_days)

    # ---------- 观测 ----------
    def record(self, subject_tdid: str) -> Optional[EscheatRecord]:
        return self._records.get(subject_tdid)

    def state_of(self, subject_tdid: str) -> str:
        rec = self._records.get(subject_tdid)
        return rec.state if rec else "NONE"

    def is_public_goods(self, subject_tdid: str) -> bool:
        rec = self._records.get(subject_tdid)
        return bool(rec and rec.public_goods)
