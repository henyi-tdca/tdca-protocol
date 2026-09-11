# -*- coding: utf-8 -*-
"""多继承人份额计算（Shapley 化）与争议裁决流程化（G3 深化 / #15）

制度依据:
  - 继承机制立项件 §四-2（多继承人份额计算器 Shapley 化 + 争议裁决流程化）：本模块即该项实现
  - Shapley 联盟定价（TDCA 经济模型）：按边际贡献分摊，替代"立嘱人直觉均分"
  -（人类签批权不代行）：**裁决份额只能由人类给定**，AI 仅登记

口径:
  - `shapley_values(coalition_values, parties)`：标准 Shapley 值（含缺省 v(∅)=0；缺子集记为 missing）
  - `shapley_shares(...)`：归一化为份额（合计 1.0）；**全部为 0 时拒绝**（不可凭空均分）
  - `propose_distribution(estate_value, ...)`：份额 → 金额建议（供遗嘱/裁决参考，**不自动执行**）
  - `DisputeRegistry`：争议流程 OPEN → PROPOSED → ADJUDICATED（人类裁决登记，可携份额）

纪律:
  - AI 不代行裁决（ruling 必填，且由人类给出）；AI 可给出 **proposal**（含 Shapley 建议）
  - 裁决份额合计须 1.0；未裁决不可进入执行（与 estate 状态机一致）
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from itertools import combinations
from types import SimpleNamespace
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple


class ShapleyError(Exception):
    """份额计算/争议流程纪律违例。"""


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


def _norm_key(s: Iterable[str]) -> FrozenSet[str]:
    return frozenset(s)


# ---------------------------------------------------------------- Shapley
def shapley_values(coalition_values: Dict[Any, float], parties: List[str]
                   ) -> Tuple[Dict[str, float], List[List[str]]]:
    """标准 Shapley 值计算。

    φ_i = Σ_{S ⊆ N\\{i}} |S|!(n-|S|-1)!/n! · [v(S∪{i}) − v(S)]

    目标函数: 按边际贡献分摊（替代直觉均分），为遗嘱/裁决提供可复算建议
    约束矩阵: parties 非空且不重复；coalition_values 键须为成员集合（frozenset/tuple/set）；
              v(∅)=0；**未提供的子集按 0 计并记入 missing**（不推测填补）
    先验分布: Shapley (1953) 联盟定价；TDCA 配置权分摊口径
    配置权边界: L2 场景层（计算层）
    预期分配: (values, missing_subsets)；异常输入抛 ShapleyError
    审计轨迹: 调用方登记 NCA
    """
    plist = list(parties or [])
    if not plist:
        raise ShapleyError("parties 不得为空")
    if len(set(plist)) != len(plist):
        raise ShapleyError("parties 存在重复成员")

    table: Dict[FrozenSet[str], float] = {}
    for k, v in (coalition_values or {}).items():
        key = _norm_key(k if isinstance(k, (set, frozenset, tuple, list)) else [k])
        table[key] = float(v)

    missing: List[List[str]] = []
    seen_missing: set = set()

    def v(S: Iterable[str]) -> float:
        key = _norm_key(S)
        if not key:
            return 0.0
        if key in table:
            return table[key]
        if key not in seen_missing:
            seen_missing.add(key)
            missing.append(sorted(key))
        return 0.0

    n = len(plist)
    phi: Dict[str, float] = {p: 0.0 for p in plist}
    for p in plist:
        others = [q for q in plist if q != p]
        for k in range(len(others) + 1):
            for S in combinations(others, k):
                weight = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                phi[p] += weight * (v(set(S) | {p}) - v(set(S)))
    return {p: round(val, 10) for p, val in phi.items()}, missing


def shapley_shares(coalition_values: Dict[Any, float], parties: List[str]
                   ) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Shapley 值 → 份额（合计 1.0）。

    目标函数: 产出可直接用于遗嘱/裁决的份额
    约束矩阵: 份额总和须 > 0（**全零即拒**：不可凭空均分）；负值成员即拒（联盟定价不应为负）
    先验分布: shapley_values
    配置权边界: L2 场景层
    预期分配: (shares, meta{values, missing, total})
    审计轨迹: 调用方登记 NCA
    """
    values, missing = shapley_values(coalition_values, parties)
    total = sum(values.values())
    if any(x < -1e-12 for x in values.values()):
        raise ShapleyError(f"Shapley 值出现负值（联盟定价异常）: {values}")
    if total <= 1e-12:
        raise ShapleyError("Shapley 值合计为 0：不可分配（不得凭空均分）")
    shares = {p: round(val / total, 10) for p, val in values.items()}
    drift = 1.0 - sum(shares.values())
    if abs(drift) > 1e-9:                              # 尾差归入最大份额者（可复算口径）
        top = max(shares, key=lambda k: shares[k])
        shares[top] = round(shares[top] + drift, 10)
    return shares, {"values": values, "missing": missing, "total": total}


def propose_distribution(estate_value: float, coalition_values: Dict[Any, float],
                         parties: List[str]) -> Dict[str, Any]:
    """按 Shapley 份额给出**金额建议**（供遗嘱/裁决参考，不自动执行）。

    目标函数: 份额 → 金额（人读建议 + 可复算证据）
    约束矩阵: estate_value ≥ 0
    先验分布: shapley_shares
    配置权边界: L2 场景层（**建议层**——执行仍走 estate 遗嘱/裁决路径）
    预期分配: {"shares","amounts","meta","simulated"}
    审计轨迹: 调用方登记 NCA
    """
    val = float(estate_value)
    if val < 0:
        raise ShapleyError("遗产价值不得为负")
    shares, meta = shapley_shares(coalition_values, parties)
    amounts = {p: round(val * s, 2) for p, s in shares.items()}
    return {"shares": shares, "amounts": amounts, "meta": meta, "simulated": True}


# ---------------------------------------------------------------- 争议裁决流程化
@dataclass
class DisputeFlow:
    subject_tdid: str
    claimants: List[str]
    grounds: str
    status: str = "OPEN"                 # OPEN / PROPOSED / ADJUDICATED
    proposal: Dict[str, float] = field(default_factory=dict)
    ruling: Optional[str] = None
    ruling_shares: Dict[str, float] = field(default_factory=dict)
    opened_at: str = ""
    resolved_at: Optional[str] = None
    nca_refs: List[str] = field(default_factory=list)


class DisputeRegistry:
    """争议裁决流程登记（OPEN → PROPOSED → ADJUDICATED）——裁决权在人类。"""

    def __init__(self, nca_generator=None):
        self._flows: Dict[str, DisputeFlow] = {}
        self._gen = _make_generator(nca_generator)

    def open(self, subject_tdid: str, claimants: List[str], grounds: str) -> DisputeFlow:
        """开启争议流程（幂等：同主体已开启且未裁决即拒）。

        目标函数: 争议的显式流程化（谁争、争何、当前状态）
        约束矩阵: subject/grounds 必填；claimants 至少 2 方（否则非"多方争议"）
        先验分布: estate.mark_dispute（状态机层面）——本流程为其**结构化作证**
        配置权边界: L2 场景层
        预期分配: DisputeFlow
        审计轨迹: nca_refs（estate-dispute-flow-open）
        """
        if not subject_tdid or not grounds:
            raise ShapleyError("争议须载明主体与事由")
        if len(set(claimants or [])) < 2:
            raise ShapleyError("争议须至少两方主张人（claimants）")
        cur = self._flows.get(subject_tdid)
        if cur is not None and cur.status != "ADJUDICATED":
            raise ShapleyError(f"该主体已有未裁决争议流程: {subject_tdid}")
        from datetime import datetime
        flow = DisputeFlow(subject_tdid=subject_tdid, claimants=list(dict.fromkeys(claimants)),
                           grounds=grounds,
                           opened_at=datetime.now().astimezone().isoformat(timespec="seconds"))
        nca = self._gen.generate(type="estate-dispute-flow-open", layer=2,
                                 content={"subject_tdid": subject_tdid,
                                          "claimants": flow.claimants, "grounds": grounds,
                                          "simulated": True})
        flow.nca_refs.append(nca.nca_id)
        self._flows[subject_tdid] = flow
        return flow

    def attach_proposal(self, subject_tdid: str, shares: Dict[str, float],
                        note: str = "AI proposal (Shapley)") -> DisputeFlow:
        """附上份额建议（AI 可给建议，**无裁决效力**）。

        目标函数: 使 AI 的 Shapley 建议进入流程留痕（供人类参考）
        约束矩阵: 流程须存在且未裁决；份额须覆盖全部主张人且合计 1.0
        先验分布: shapley_shares / propose_distribution
        配置权边界: L2 场景层（建议层）
        预期分配: 更新后的 flow（status=PROPOSED）
        审计轨迹: nca_refs（estate-dispute-flow-proposal）
        """
        flow = self._require_open_flow(subject_tdid)
        self._check_shares(shares, flow.claimants, label="建议份额")
        flow.proposal = dict(shares)
        flow.status = "PROPOSED"
        nca = self._gen.generate(type="estate-dispute-flow-proposal", layer=2,
                                 content={"subject_tdid": subject_tdid, "shares": dict(shares),
                                          "note": note, "simulated": True})
        flow.nca_refs.append(nca.nca_id)
        return flow

    def adjudicate(self, subject_tdid: str, ruling: str,
                   shares: Optional[Dict[str, float]] = None) -> DisputeFlow:
        """登记**人类裁决**（：AI 不代行；可携裁决份额，覆盖建议）。

        目标函数: 裁决结果登记并固定（含或份额），使争议进入可执行态
        约束矩阵: ruling 必填（内容由人类给出）；若给 shares，须覆盖主张人且合计 1.0
        先验分布: estate.resolve_dispute（状态机层面）
        配置权边界: L2 场景层（**仅登记**）
        预期分配: 更新后的 flow（status=ADJUDICATED）
        审计轨迹: nca_refs（estate-dispute-flow-ruling，by=human）
        """
        flow = self._require_open_flow(subject_tdid)
        if not ruling:
            raise ShapleyError("裁决内容必填（由人类给出， 不代行）")
        if shares is not None:
            self._check_shares(shares, flow.claimants, label="裁决份额")
            flow.ruling_shares = dict(shares)
        from datetime import datetime
        flow.ruling = ruling
        flow.status = "ADJUDICATED"
        flow.resolved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        nca = self._gen.generate(type="estate-dispute-flow-ruling", layer=2,
                                 content={"subject_tdid": subject_tdid, "ruling": ruling,
                                          "shares": flow.ruling_shares, "by": "human",
                                          "simulated": True})
        flow.nca_refs.append(nca.nca_id)
        return flow

    # ---------- 观测 ----------
    def flow(self, subject_tdid: str) -> Optional[DisputeFlow]:
        return self._flows.get(subject_tdid)

    def is_executable(self, subject_tdid: str) -> bool:
        f = self._flows.get(subject_tdid)
        return bool(f and f.status == "ADJUDICATED")

    def _require_open_flow(self, subject_tdid: str) -> DisputeFlow:
        flow = self._flows.get(subject_tdid)
        if flow is None:
            raise ShapleyError(f"无争议流程: {subject_tdid}")
        if flow.status == "ADJUDICATED":
            raise ShapleyError("争议已裁决（幂等：不再受理变更）")
        return flow

    @staticmethod
    def _check_shares(shares: Dict[str, float], claimants: List[str], label: str = "份额") -> None:
        if not shares:
            raise ShapleyError(f"{label}不得为空")
        if any(x < 0 for x in shares.values()):
            raise ShapleyError(f"{label}不得为负")
        missing = [c for c in claimants if c not in shares]
        if missing:
            raise ShapleyError(f"{label}未覆盖主张人: {missing}")
        total = round(sum(shares.values()), 6)
        if abs(total - 1.0) > 1e-6:
            raise ShapleyError(f"{label}合计须为 1.0（当前 {total}）")
