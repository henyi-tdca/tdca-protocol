# -*- coding: utf-8 -*-
"""
W3-后续 T-P3-002 · ZeroDataCrossSceneEntry 零数据企业跨场景入盒通道
锚定: TDCA-TASKBOOK-5CC-P3-SBX T-P3-002（零数据企业提交跨场景 PUCR 预售 → 政府/投资者初始 PCR
     → 沙盒内与 3 个现有场景强制交互验证 → 激活系数 >1.2 出盒进入市场）
     + 验收（申请到入盒 <48h / 政府 PCR 资金数字人民币锁定按里程碑释放）
依赖: T-P3-001 CrossSceneSandbox（基线）
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .sandbox import CrossSceneSandbox, SandboxStatus

ENTRY_THRESHOLD = 1.2          # 激活系数门槛（T-P3-002: >1.2 出盒）
MAX_ENTRY_HOURS = 48           # 验收：申请到入盒 <48h
MILESTONE_RELEASE = 0.5        # 政府 PCR 资金里程碑释放比例（50% 首里程碑）


@dataclass
class ZeroDataEntry:
    """零数据企业入盒工作流。"""
    entry_id: str
    enterprise_did: str
    pucr_pre_sale: float = 0.0        # 跨场景 PUCR 预售
    gov_pcr: float = 0.0              # 政府/投资者初始 PCR
    sandbox_id: Optional[str] = None
    status: str = "SUBMITTED"         # SUBMITTED → VERIFYING → APPROVED/REJECTED
    submitted_at: float = field(default_factory=time.time)
    gov_pcr_locked: bool = False      # 政府 PCR 资金锁定（数字人民币智能合约）
    released: float = 0.0             # 已释放里程碑资金

    @property
    def entry_hours(self) -> float:
        return (time.time() - self.submitted_at) / 3600.0


class ZeroDataCrossSceneEntry:
    """零数据企业入盒通道：强制交互验证 + 激活系数门槛 + 政府 PCR 锁定释放。"""

    def __init__(self, existing_scene_ids: List[str], mou_map: Dict[str, float],
                 pcr_map: Dict[str, float]):
        self._existing = existing_scene_ids          # 沙盒内 3 个现有场景
        self._mou_map = mou_map
        self._pcr_map = pcr_map
        self._entries: Dict[str, ZeroDataEntry] = {}

    def submit(self, enterprise_did: str, pucr_pre_sale: float,
               gov_pcr: float) -> ZeroDataEntry:
        """提交入盒申请（零数据企业：仅预售 + 政府 PCR，无历史数据）。"""
        entry = ZeroDataEntry(entry_id=f"ZDE-{uuid.uuid4().hex[:10]}",
                              enterprise_did=enterprise_did,
                              pucr_pre_sale=pucr_pre_sale, gov_pcr=gov_pcr)
        # 政府 PCR 资金数字人民币锁定（模拟 escrow，里程碑释放）
        entry.gov_pcr_locked = True
        self._entries[entry.entry_id] = entry
        return entry

    def verify_and_enter(self, entry_id: str) -> Dict[str, object]:
        """强制交互验证：与 3 个现有场景构建沙盒 + 激活系数评估。>1.2 出盒进入市场。"""
        entry = self._entries[entry_id]
        entry.status = "VERIFYING"
        # 强制交互验证：零数据企业 + 现有 3 场景组沙盒（T-P3-002 核心）
        scene_ids = self._existing + [f"ENT-{entry.enterprise_did[:6]}"]
        mou_map = dict(self._mou_map)
        mou_map[scene_ids[-1]] = entry.pucr_pre_sale
        pcr_map = dict(self._pcr_map)
        pcr_map[scene_ids[-1]] = entry.gov_pcr
        sb = CrossSceneSandbox.create(scene_ids=scene_ids, pcr_budget=sum(pcr_map.values()),
                                      sponsor_did=entry.enterprise_did,
                                      mou_map=mou_map, pcr_map=pcr_map)
        entry.sandbox_id = sb.sandbox_id
        detail = sb.activation_coefficient()
        alpha = detail["activation_coefficient"]
        if alpha > ENTRY_THRESHOLD:
            entry.status = "APPROVED"
            sb.status = SandboxStatus.ACTIVE
            # 里程碑释放（首里程碑 50%）
            entry.released = round(entry.gov_pcr * MILESTONE_RELEASE, 2)
            return {"status": "APPROVED", "entry_id": entry_id,
                    "sandbox_id": sb.sandbox_id, "activation": alpha,
                    "market_entry": True,
                    "gov_pcr_released": entry.released,
                    "entry_hours": round(entry.entry_hours, 2)}
        entry.status = "REJECTED"
        return {"status": "REJECTED", "entry_id": entry_id,
                "activation": alpha, "reason": f"激活系数 {alpha} ≤ {ENTRY_THRESHOLD}",
                "entry_hours": round(entry.entry_hours, 2)}
