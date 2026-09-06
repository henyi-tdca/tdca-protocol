# -*- coding: utf-8 -*-
"""
W3 T-P3-001 · CrossSceneSandbox 跨场景沙盒核心
锚定: TDCA-TASKBOOK-5CC-P3-001（V0.2）T-P3-001 + P3 接口契约 + 安全约束（负空间硬约束）
     + FC-SBX-OPS-001 M2 基线（沙盒生命周期继承）+ D2-NSFL-UNION-SCHEMA-001 V0.1-REV2-FINAL
核心公式: activation_coefficient_cross_scene = (ΣMOU/ΣPCR) × (1 − externality_decay) + externality_benefit
安全约束: 数据反向泄露禁止（脱敏+负空间审查）/ 激活系数算法哈希上链 / 晋升人类签名不可绕过
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SandboxStatus(Enum):
    HIBERNATING = "HIBERNATING"   # 创建后初始态（P3 契约）
    ACTIVE = "ACTIVE"             # 激活系数 ≥ 门槛
    PROMOTING = "PROMOTING"       # 自动晋升提案生成（待人类签名）
    CLOSED = "CLOSED"             # 终止（负空间熔断/出盒完成）


@dataclass
class SceneSlot:
    """沙盒内场景位（数据隔离：场景 A 数据脱敏后可供场景 B 调用，T-P3-001）。"""
    scene_id: str
    mou_contribution: float = 0.0      # MOU 贡献（可正和）
    pcr_investment: float = 0.0        # PCR 投资（配置权请求）
    data_in: Dict[str, Any] = field(default_factory=dict)   # 本场景注入数据（原始，隔离）
    data_sanitized: Dict[str, Any] = field(default_factory=dict)  # 脱敏后共享视图


@dataclass
class CrossSceneSandbox:
    """跨场景沙盒（继承 SBX-OPS 沙盒生命周期语义，≥3 场景交互）。"""
    sandbox_id: str
    scene_ids: List[str]
    sponsor_did: str
    pcr_budget: float = 0.0
    status: SandboxStatus = SandboxStatus.HIBERNATING
    scenes: Dict[str, SceneSlot] = field(default_factory=dict)
    interactions: List[Dict[str, Any]] = field(default_factory=list)  # 交互记录（负空间冲突数来源）
    algorithm_hash: str = ""          # 激活系数算法哈希（安全约束：不可篡改）
    created_at: float = 0.0

    @classmethod
    def create(cls, scene_ids: List[str], pcr_budget: float,
               sponsor_did: str, mou_map: Optional[Dict[str, float]] = None,
               pcr_map: Optional[Dict[str, float]] = None) -> "CrossSceneSandbox":
        """创建跨场景沙盒（≥3 场景强制：T-P3-001 验收）。"""
        if len(set(scene_ids)) < 3:
            raise ValueError(f"跨场景沙盒需 ≥3 个场景，当前 {len(set(scene_ids))}（T-P3-001 验收）")
        sb = CrossSceneSandbox(
            sandbox_id=f"CSB-{uuid.uuid4().hex[:10]}",
            scene_ids=list(dict.fromkeys(scene_ids)),   # 去重保序
            sponsor_did=sponsor_did,
            pcr_budget=pcr_budget,
        )
        for sid in sb.scene_ids:
            sb.scenes[sid] = SceneSlot(
                scene_id=sid,
                mou_contribution=(mou_map or {}).get(sid, 1.0),
                pcr_investment=(pcr_map or {}).get(sid, pcr_budget / len(sb.scene_ids)),
            )
        sb.algorithm_hash = sb.compute_algorithm_hash()
        return sb

    # ---- 核心公式（T-P3-001，可解释输出至 NCA）----

    def activation_coefficient(self) -> Dict[str, float]:
        """activation_coefficient_cross_scene：
        (ΣMOU/ΣPCR) × (1 − externality_decay) + externality_benefit(network_effects)。
        输出明细（MOU/PCR/衰减/网络效应）→ 可解释（验收：明细至 NCA）。
        """
        total_mou = sum(s.mou_contribution for s in self.scenes.values())
        total_pcr = sum(s.pcr_investment for s in self.scenes.values())
        if total_pcr <= 0:
            raise ValueError("ΣPCR 必须 > 0")
        decay = self.compute_externality_decay()
        benefit = self.externality_benefit()
        alpha = (total_mou / total_pcr) * (1 - decay) + benefit
        return {
            "activation_coefficient": round(alpha, 4),
            "total_mou": round(total_mou, 4),
            "total_pcr": round(total_pcr, 4),
            "externality_decay": round(decay, 4),
            "externality_benefit": round(benefit, 4),
        }

    def compute_externality_decay(self) -> float:
        """外部性衰减：基于负空间冲突数 + 配置权映射成本（T-P3-001 公式）。
        冲突越多 → 衰减越大；无冲突 → 0。"""
        conflicts = sum(int(i.get("conflicts", 0)) for i in self.interactions)
        mapping_cost = sum(int(i.get("mapping_cost", 0)) for i in self.interactions)
        raw = 0.05 * conflicts + 0.02 * mapping_cost
        return min(0.9, raw)   # 衰减上限 0.9（保底可激活性）

    def externality_benefit(self) -> float:
        """网络效应收益：场景对数 × 0.02（正和面）。"""
        n = len(self.scene_ids)
        return round(0.02 * (n * (n - 1) / 2), 4) if n >= 2 else 0.0

    # ---- 数据隔离与共享（安全约束：脱敏 + 负空间审查）----

    def inject_data(self, scene_id: str, data: Dict[str, Any],
                    nsfl_verdict: str = "PASS") -> Dict[str, Any]:
        """注入数据（T-P3-001 跨场景数据隔离）：
        - 原始数据仅存本场景槽（隔离）
        - 经负空间审查（nsfl_verdict）与脱敏后写入共享视图供其他场景调用
        - nsfl_verdict != PASS → REJECTED（负空间边界，联调 D-2）
        """
        if scene_id not in self.scenes:
            raise KeyError(f"场景 {scene_id} 不在沙盒内")
        if nsfl_verdict != "PASS":
            return {"injection_status": "REJECTED",
                    "reason": f"负空间边界拒绝: {nsfl_verdict}"}
        slot = self.scenes[scene_id]
        slot.data_in = data
        slot.data_sanitized = self._sanitize(data, scene_id)
        self.interactions.append({"type": "inject", "scene": scene_id,
                                  "conflicts": 0, "mapping_cost": 1})
        return {"injection_status": "SUCCESS", "scene_id": scene_id,
                "sanitized_keys": list(slot.data_sanitized.keys())}

    @staticmethod
    def _sanitize(data: Dict[str, Any], scene_id: str) -> Dict[str, Any]:
        """脱敏：剔除标识类键（id/name/did/address），数值保留（跨场景调用面）。"""
        BLOCKED = {"id", "did", "name", "address", "phone", "owner"}
        return {k: v for k, v in data.items() if k.lower() not in BLOCKED}

    def get_shared_view(self, scene_id: str, caller: str) -> Dict[str, Any]:
        """共享视图：其他场景经脱敏数据调用（原始数据隔离，安全约束）。"""
        if caller == scene_id:
            raise PermissionError(f"{scene_id} 只能经脱敏视图访问自身数据（隔离）")
        slot = self.scenes.get(scene_id)
        if slot is None:
            raise KeyError(scene_id)
        return dict(slot.data_sanitized)

    # ---- 算法哈希上链（安全约束）----

    def compute_algorithm_hash(self) -> str:
        """激活系数算法源码哈希（SHA-256，防内部篡改——安全约束第 2 条）。"""
        source = inspect_getsource(self.activation_coefficient)
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def verify_algorithm_hash(self) -> bool:
        return self.compute_algorithm_hash() == self.algorithm_hash


def inspect_getsource(func) -> str:
    """获取函数源码（哈希上链用）。"""
    import inspect
    return inspect.getsource(func)
