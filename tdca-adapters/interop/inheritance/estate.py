# -*- coding: utf-8 -*-
"""TDCA 智能体遗产继承机制（Inheritance）——创建主体消亡的权益承接（最小实现）

制度依据:
  - TDCA 身份管理规范 V1.0 §3.2（R-1~R-8：遗嘱优先 / 无遗嘱沿创建链回退 /
    遗产标的界定 / 存证不因死亡消失 / 人类裁决兜底 / 继承计税 / 幂等防重 / 范围与链接层衔接）
  - TDCA 治理框架 §三/四（数字资产继承候选规则 + 长尾痛点）
  - 《TDCA数字资产管理与智能体管理实务攻略》V1.0 §6.3（自然退出：法务确认→启动继承/清算→按协议分配）
  - 公理 6 反函数 f⁻（创建链可审计还原）

纪律:
  - **死亡事实须外部法律文书引用**（L0 输入，TDCA 不越级判定；legal_ref 必填）
  - **遗嘱优先**（可撤回重签，NCA 存证）；无遗嘱 → 沿创建链回退 + 法定路径标记
  - **幂等防重**：每主体继承只执行一次
  - **继承计税**（MOU 锚定，模拟态）
  - **NCA 存证不因死亡消失**：仅归属标注变更，存证引用全部保留
  - **人类裁决兜底**：争议由人类裁决登记，AI 不代行
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DISPOSITIONS = ("continue", "dormant", "deregister")


class InheritanceError(Exception):
    """继承机制纪律违例。"""


@dataclass
class Beneficiary:
    tdid: str
    share: float                       # 分配份额（0~1）
    kind: str = "person"               # person / agent / community


@dataclass
class Testament:
    declarant_tdid: str
    beneficiaries: List[Beneficiary]
    agent_disposition: str = "dormant"  # continue / dormant / deregister
    at: str = ""
    nca_ref: Optional[str] = None
    revoked: bool = False
    revoked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"declarant_tdid": self.declarant_tdid,
                "beneficiaries": [b.__dict__ for b in self.beneficiaries],
                "agent_disposition": self.agent_disposition, "at": self.at,
                "nca_ref": self.nca_ref, "revoked": self.revoked,
                "revoked_reason": self.revoked_reason, "simulated": True}


@dataclass
class EstateRecord:
    subject_tdid: str
    legal_ref: str = ""
    status: str = "DECLARED"           # DECLARED / OPEN / DISPUTED / EXECUTED
    assets: Dict[str, Any] = field(default_factory=dict)
    opened_at: str = ""
    executed_at: Optional[str] = None
    distribution: Dict[str, float] = field(default_factory=dict)
    inheritance_tax: float = 0.0
    path: str = ""                     # testament / creation-chain-fallback
    creation_chain: List[str] = field(default_factory=list)
    human_ruling: Optional[str] = None
    nca_refs: List[str] = field(default_factory=list)


class InheritanceRegistry:
    """继承登记与执行（最小实现，覆盖 ID-002 R-1~R-8）。"""

    def __init__(self, tax_rate: float = 0.02, nca_generator=None):
        self.tax_rate = float(tax_rate)
        self._testaments: Dict[str, Testament] = {}
        self._estates: Dict[str, EstateRecord] = {}
        if nca_generator is None:
            from tdca_nca.generator import NCAGenerator  # type: ignore
            nca_generator = NCAGenerator()
        self._gen = nca_generator

    # ---------- R-1 遗嘱（预授权，可撤回重签）----------
    def declare_testament(self, declarant_tdid: str, beneficiaries: List[Beneficiary],
                          agent_disposition: str = "dormant") -> Testament:
        if not declarant_tdid:
            raise InheritanceError("遗嘱须载明立嘱人（declarant_tdid）")
        if agent_disposition not in DISPOSITIONS:
            raise InheritanceError(f"处置须为 {DISPOSITIONS}")
        if not beneficiaries:
            raise InheritanceError("遗嘱须载明受益人")
        total = round(sum(b.share for b in beneficiaries), 6)
        if abs(total - 1.0) > 1e-6:
            raise InheritanceError(f"受益人份额合计须为 1.0（当前 {total}）")
        t = Testament(declarant_tdid=declarant_tdid, beneficiaries=list(beneficiaries),
                      agent_disposition=agent_disposition, at=self._now())
        nca = self._gen.generate(type="estate-testament", layer=2,
                                 content={"declarant": declarant_tdid,
                                          "beneficiaries": [b.__dict__ for b in beneficiaries],
                                          "disposition": agent_disposition, "simulated": True})
        t.nca_ref = nca.nca_id
        self._testaments[declarant_tdid] = t
        return t

    def revoke_testament(self, declarant_tdid: str, reason: str) -> Testament:
        t = self._testaments.get(declarant_tdid)
        if t is None or t.revoked:
            raise InheritanceError(f"无可撤回的遗嘱: {declarant_tdid}")
        if not reason:
            raise InheritanceError("撤回须给出理由（可审计）")
        nca = self._gen.generate(type="estate-testament-revoke", layer=2,
                                 content={"declarant": declarant_tdid, "reason": reason,
                                          "simulated": True})
        t.revoked = True
        t.revoked_reason = reason
        t.nca_ref = f"{t.nca_ref};{nca.nca_id}"
        return t

    def testament(self, declarant_tdid: str) -> Optional[Testament]:
        t = self._testaments.get(declarant_tdid)
        return t if t and not t.revoked else None

    # ---------- 死亡事实登记（L0 外部法律事实）----------
    def report_death(self, subject_tdid: str, legal_ref: str) -> EstateRecord:
        if not legal_ref:
            raise InheritanceError("死亡事实须引用外部法律文书（legal_ref 必填，TDCA 不越级判定）")
        if subject_tdid in self._estates:
            return self._estates[subject_tdid]            # 幂等：重复登记返回既有
        rec = EstateRecord(subject_tdid=subject_tdid, legal_ref=legal_ref, opened_at=self._now())
        self._estates[subject_tdid] = rec
        return rec

    # ---------- 遗产清点（R-3 标的界定）----------
    def open_estate(self, subject_tdid: str, assets: Dict[str, Any]) -> EstateRecord:
        rec = self._estates.get(subject_tdid)
        if rec is None:
            raise InheritanceError("须先登记死亡事实（report_death）")
        if rec.status == "EXECUTED":
            raise InheritanceError("遗产已执行，不可再清点")
        rec.assets = dict(assets)         # 配置权 / 分润权益 / 数字资产权益 / 协作份额
        rec.status = "OPEN"
        return rec

    # ---------- R-2/R-6/R-7 执行（遗嘱优先 / 沿链回退 / 计税 / 幂等）----------
    def execute_inheritance(self, subject_tdid: str,
                            creation_chain: Optional[List[str]] = None) -> Dict[str, Any]:
        rec = self._estates.get(subject_tdid)
        if rec is None:
            raise InheritanceError("须先登记死亡事实并清点遗产")
        if rec.status == "EXECUTED":
            raise InheritanceError("继承已执行（幂等防重：每主体仅一次）")
        if rec.status == "DISPUTED" and rec.human_ruling is None:
            raise InheritanceError("争议未决：须人类裁决（resolve_dispute）后方可执行")

        total_value = float(sum(v for v in rec.assets.values() if isinstance(v, (int, float))))
        dist: Dict[str, float] = {}
        path = ""

        testament = self.testament(subject_tdid)
        if testament is not None:
            path = "testament"
            for b in testament.beneficiaries:
                dist[b.tdid] = round(total_value * b.share, 2)
        else:
            path = "creation-chain-fallback"
            chain = list(creation_chain or [])
            if not chain:
                raise InheritanceError(
                    "无有效遗嘱且未提供创建链：沿创建链回退需 creation_chain（公理 6 f⁻ 可审计还原）")
            dist[chain[0]] = round(total_value, 2)        # 回退至创建链最近主体（父体/创建者）
            rec.creation_chain = chain

        # R-6 继承计税（MOU 模拟态）
        tax = round(total_value * self.tax_rate, 2)

        # R-4 存证：NCA 不因死亡消失（新建继承事件存证；历史引用全部保留）
        nca = self._gen.generate(type="estate-inheritance", layer=3,
                                 content={"subject_tdid": subject_tdid, "legal_ref": rec.legal_ref,
                                          "path": path, "assets": rec.assets,
                                          "distribution": dist, "tax": tax,
                                          "testament_nca": testament.nca_ref if testament else None,
                                          "simulated": True})
        rec.nca_refs.append(nca.nca_id)
        rec.distribution = dist
        rec.inheritance_tax = tax
        rec.path = path
        rec.status = "EXECUTED"
        rec.executed_at = self._now()
        disposition = testament.agent_disposition if testament else "dormant"
        return {"executed": True, "subject_tdid": subject_tdid, "path": path,
                "distribution": dist, "inheritance_tax": tax,
                "agent_disposition": disposition, "nca_ref": nca.nca_id,
                "assets_retained": dict(rec.assets), "simulated": True}

    # ---------- R-5 人类裁决兜底（AI 不代行）----------
    def mark_dispute(self, subject_tdid: str, reason: str) -> EstateRecord:
        rec = self._estates.get(subject_tdid)
        if rec is None or rec.status == "EXECUTED":
            raise InheritanceError("无待处置遗产或已执行")
        rec.status = "DISPUTED"
        rec.nca_refs.append(self._gen.generate(
            type="estate-dispute", layer=2,
            content={"subject_tdid": subject_tdid, "reason": reason, "ruling_required": True,
                     "simulated": True}).nca_id)
        return rec

    def resolve_dispute(self, subject_tdid: str, ruling: str) -> EstateRecord:
        """人类裁决登记——本接口仅登记裁决结果，AI 不代行裁决。"""
        rec = self._estates.get(subject_tdid)
        if rec is None or rec.status != "DISPUTED":
            raise InheritanceError("无争议待裁决")
        if not ruling:
            raise InheritanceError("裁决内容必填")
        rec.human_ruling = ruling
        rec.nca_refs.append(self._gen.generate(
            type="estate-human-ruling", layer=2,
            content={"subject_tdid": subject_tdid, "ruling": ruling, "by": "human", "simulated": True}
        ).nca_id)
        return rec

    # ---------- 观测 ----------
    def estate(self, subject_tdid: str) -> Optional[EstateRecord]:
        return self._estates.get(subject_tdid)

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")
