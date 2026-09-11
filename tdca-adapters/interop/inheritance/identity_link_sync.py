# -*- coding: utf-8 -*-
"""主体消亡 → 身份桥接链接失效同步（G3 深化 / #18）

制度依据:
  - TDCA 身份管理规范 §3.2 **R-8 范围与链接层衔接**：死亡事实与跨域继承属"走出 TDCA 范围"
    的法律层输入——经国标身份链接层（TDID↔OID 桥接）对接；TDCA 提供技术框架与接口，
    **不替代法律确权**（L0 不越级）
  - TDCA 身份管理规范 §六（失效联动：令牌失效／注销应触发 `revoke`）与 §八-2（待细化项）
  - 权益承接口径件（法理定性），内部存证）法理定性：争议裁决权属**司法部门**；
    无司法可验证正式文件（`judicial_ref`）前 TDCA **不得有任何其他动作，只能让其休眠**；
    无归属、无争议、满一年 → 公共品（善意管理／无因管理，**无需裁决引用**）

联动规则（纪律，强制）:
  1. **法律事实前置**：消亡认定须引用外部法律文书（`legal_ref` 必填）——与
     `estate.report_death` 同口径；缺失即拒（fail-closed，TDCA 不越级判定）
  2. **争议零动作（AMEND-2）**：存在未决争议（`escheat.dispute_open` 或
     `DisputeRegistry` 流程 OPEN/PROPOSED）且无 `judicial_ref` → **不得 revoke**（只休眠，计时继续）
  3. **仅终态联动**：身份处置 `disposition="deregister"`（或 `dormancy` DEREGISTERED 终态、
     权益已托管公共品、令牌日抛失效终态）方触发；`continue` / `dormant` **零动作**
  4. **幂等**：无活跃链接 → no-op（如实标注 `no-active-link`，不报错）
  5. **存证**：每次判定生成一条 `identity-link-sync` 存证；`revoke` 本身另生成 `identity-unlink`
  6. **不回写内部基线**：仅终止外部链接字段，内部主键始终 TDID（STD-AGENT-ID-003 §四-5）

数据性质: **模拟态** —— OID 链接为模拟态占位，不构成真实国标注册

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional, Union


from identity_bridge import ACTIVE, IdentityBridge, IdentityBridgeError  # noqa: E402

try:                                            # 包内导入
    from .estate import DISPOSITIONS
except ImportError:                             # 顶层导入（sys.path 含 inheritance/）
    from estate import DISPOSITIONS             # type: ignore[no-redef]

# 消亡/终态触发（demise-legal-fact 走 on_demise；其余走 sync_terminal）
DEMISE_TRIGGERS = ("demise-legal-fact", "dormancy-timeout",
                   "escheat-public-goods", "token-expiry")
TERMINAL_TRIGGERS = ("dormancy-timeout", "escheat-public-goods", "token-expiry")
SYNC_ACTIONS = ("revoked", "no-active-link", "deferred-dispute", "not-terminal")
_OPEN_DISPUTE_STATES = ("OPEN", "PROPOSED")


class IdentityLinkSyncError(Exception):
    """身份链接联动纪律违例（法律事实缺失／触发非法／同步失败）。"""


class _LocalSeal:
    """离线可用轻量存证桩（tdca_nca 不可用时兜底；接口与 NCAGenerator 最小面一致）。"""

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
class SyncOutcome:
    """一次联动判定的结果（含零动作分支——零动作亦如实留痕）。"""

    subject_tdid: str
    trigger: str
    action: str                       # revoked / no-active-link / deferred-dispute / not-terminal
    reason: str
    disposition: Optional[str] = None
    legal_ref: Optional[str] = None
    judicial_ref: Optional[str] = None
    dispute_open: bool = False
    dispute_trace: bool = False
    oid: Optional[str] = None
    nca_refs: List[str] = field(default_factory=list)
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"subject_tdid": self.subject_tdid, "trigger": self.trigger, "action": self.action,
                "reason": self.reason, "disposition": self.disposition, "legal_ref": self.legal_ref,
                "judicial_ref": self.judicial_ref, "dispute_open": self.dispute_open,
                "dispute_trace": self.dispute_trace,
                "oid": self.oid, "nca_refs": list(self.nca_refs), "simulated": True}


class IdentityLinkSync:
    """主体消亡/终态 → 身份桥接链接失效同步（#18）。

    依赖注入（均可选，注册表缺省时对应终态校验退化为"调用方自证"）:
      - `bridge`   : `IdentityBridge`（缺省自建；`revoke` 为其既有接口）
      - `dormancy` : `DormancyRegistry`（提供 DEREGISTERED 终态校验）
      - `escheat`  : `EscheatRegistry`（提供争议痕迹与公共品托管校验）
      - `dispute`  : `DisputeRegistry`（提供未决争议流程校验）
    """

    def __init__(self, bridge=None, *, dormancy=None, escheat=None, dispute=None,
                 nca_generator=None):
        self._bridge = bridge if bridge is not None else IdentityBridge()
        self._dormancy = dormancy
        self._escheat = escheat
        self._dispute = dispute
        self._gen = _make_generator(nca_generator)

    # ---------------------------------------------------------------- 主体消亡（法律事实路径）
    def on_demise(self, subject_tdid: str, *, disposition: str, legal_ref: str,
                  judicial_ref: Optional[str] = None,
                  actor: str = "identity-link-sync") -> SyncOutcome:
        """主体消亡处置 → 身份链接失效同步（法律事实路径）。

        目标函数: 创建主体消亡后，注销处置（`deregister`）⇒ 外部身份链接同步失效
        约束矩阵: `legal_ref` 必填（消亡认定须外部法律文书，L0 不越级）；
                  `disposition ∈ {continue, dormant, deregister}`（非注销即零动作）；
                  争议未决且无 `judicial_ref` ⇒ 零动作（只休眠，AMEND-2）
        先验分布: STD-AGENT-ID-002 §3.2 R-8 ｜ estate.report_death 口径 ｜ AMEND-2
        配置权边界: L2 场景层（仅终止外部链接字段，不回写内部基线）
        预期分配: `SyncOutcome`（action ∈ SYNC_ACTIONS；每次判定均生成 NCA）
        审计轨迹: nca_refs（identity-link-sync；revoke 另生成 identity-unlink）
        """
        self._bridge.validate_tdid(subject_tdid)          # 格式强校验（复用桥接口径）
        if disposition not in DISPOSITIONS:
            raise IdentityLinkSyncError(
                f"身份处置须为 {DISPOSITIONS} 之一（当前 {disposition!r}）")
        if not legal_ref:
            raise IdentityLinkSyncError(
                "消亡认定须引用外部法律文书（legal_ref 必填，TDCA 不越级判定）")

        if disposition != "deregister":
            return self._finish(
                subject_tdid, trigger="demise-legal-fact", action="not-terminal",
                reason=f"身份处置为 {disposition}（非注销终态）→ 零动作，链接维持",
                disposition=disposition, legal_ref=legal_ref,
                judicial_ref=judicial_ref, actor=actor)

        return self._sync(subject_tdid, trigger="demise-legal-fact", disposition=disposition,
                          legal_ref=legal_ref, judicial_ref=judicial_ref, actor=actor)

    # ---------------------------------------------------------------- 终态联动（非死亡事实路径）
    def sync_terminal(self, subject_tdid: str, *, trigger: str,
                      legal_ref: Optional[str] = None,
                      judicial_ref: Optional[str] = None,
                      actor: str = "identity-link-sync") -> SyncOutcome:
        """TDCA 内部终态 → 身份链接失效同步（休眠期满注销／公共品托管／令牌失效）。

        目标函数: 覆盖消亡事实之外的终态场景（无需司法文件者照常联动；
                  有争议痕迹者仍按 AMEND-2 零动作）
        约束矩阵: trigger ∈ {dormancy-timeout, escheat-public-goods, token-expiry}；
                  提供注册表时须实测终态（DORMANT/未托管 → 零动作）；
                  争议未决且无 `judicial_ref` ⇒ 零动作
        先验分布: dormancy.sweep（窗口期满转 DEREGISTERED）｜ escheat.escheat（公共品不可逆）｜
                  STD-AGENT-ID-003 §六（令牌失效 → revoke）
        配置权边界: L2 场景层
        预期分配: `SyncOutcome`（action ∈ SYNC_ACTIONS）
        审计轨迹: nca_refs（identity-link-sync）
        """
        if trigger not in TERMINAL_TRIGGERS:
            raise IdentityLinkSyncError(f"终态联动触发须为 {TERMINAL_TRIGGERS}（消亡事实请用 on_demise）")
        self._bridge.validate_tdid(subject_tdid)

        if trigger == "dormancy-timeout" and self._dormancy is not None:
            state = self._dormancy.state_of(subject_tdid)
            if state != "DEREGISTERED":
                return self._finish(
                    subject_tdid, trigger=trigger, action="not-terminal",
                    reason=f"休眠态为 {state}（非注销终态）→ 零动作，链接维持",
                    legal_ref=legal_ref, judicial_ref=judicial_ref, actor=actor)
        if trigger == "escheat-public-goods" and self._escheat is not None:
            if not self._escheat.is_public_goods(subject_tdid):
                return self._finish(
                    subject_tdid, trigger=trigger, action="not-terminal",
                    reason="权益未托管为公共品 → 零动作，链接维持",
                    legal_ref=legal_ref, judicial_ref=judicial_ref, actor=actor)

        return self._sync(subject_tdid, trigger=trigger, disposition=None,
                          legal_ref=legal_ref, judicial_ref=judicial_ref, actor=actor)

    # ---------------------------------------------------------------- 批量
    def sync_batch(self, subject_tdids: Iterable[str], *, trigger: str,
                   judicial_ref_of: Optional[Union[Callable[[str], Optional[str]],
                                                   Dict[str, str]]] = None,
                   legal_ref: Optional[str] = None,
                   actor: str = "identity-link-sync") -> List[SyncOutcome]:
        """批量终态联动（如 `dormancy.sweep` 后一次性同步）。

        目标函数: 终态扫描后的成批失效同步（逐主体独立判定，互不影响）
        约束矩阵: 同 `sync_terminal`；单主体失败以 `deferred-dispute` / `not-terminal` 如实返回，
                  **不吞异常**（纪律违例仍抛出，由调用方处置）
        先验分布: 本模块 sync_terminal
        配置权边界: L2 场景层
        预期分配: [SyncOutcome]（顺序与入参一致）
        审计轨迹: 每主体一条 identity-link-sync 存证
        """
        out: List[SyncOutcome] = []
        for tdid in subject_tdids:
            jref: Optional[str] = None
            if callable(judicial_ref_of):
                jref = judicial_ref_of(tdid)
            elif isinstance(judicial_ref_of, dict):
                jref = judicial_ref_of.get(tdid)
            out.append(self.sync_terminal(tdid, trigger=trigger, legal_ref=legal_ref,
                                          judicial_ref=jref, actor=actor))
        return out

    # ---------------------------------------------------------------- 观测
    def pending_links(self) -> List[Dict[str, Any]]:
        """仍处 ACTIVE 的外部链接（**只读**；供悬挂链接审计）。

        目标函数: 给出"主体已终态但仍悬挂外部链接"的审计视图
        约束矩阵: 只读；不改变任何状态
        先验分布: bridge.export()
        配置权边界: L2 场景层
        预期分配: [link dict]（status=ACTIVE）
        审计轨迹: 调用方登记 NCA
        """
        return [l for l in self._bridge.export() if l.get("status") == ACTIVE]

    def dispute_open(self, subject_tdid: str) -> bool:
        """该主体是否存在**未决**争议（只读；供调用方预检）。"""
        return self._dispute_open(subject_tdid)

    def has_dispute_trace(self, subject_tdid: str) -> bool:
        """该主体是否存在**争议痕迹**（未决争议 ∪ 争议史且无司法文件结案 ∪ 争议流程存在）。

        口径与 `escheat.escheat`（AMEND-2 落点）一致：**存在争议痕迹即须凭 `judicial_ref`**——
        TDCA 内部裁决登记不构成司法裁决、不得作为处分依据（AMEND-2 第 1 条）。
        """
        return self._dispute_trace(subject_tdid)

    # ---------------------------------------------------------------- 内部
    def _dispute_open(self, subject_tdid: str) -> bool:
        """未决争议判定：escheat 未决痕迹优先，其次争议流程状态（OPEN/PROPOSED）。"""
        if self._escheat is not None:
            rec = self._escheat.record(subject_tdid)
            if rec is not None and getattr(rec, "dispute_open", False):
                return True
        if self._dispute is not None:
            flow = self._dispute.flow(subject_tdid)
            if flow is not None and getattr(flow, "status", None) in _OPEN_DISPUTE_STATES:
                return True
        return False

    def _dispute_trace(self, subject_tdid: str) -> bool:
        """争议痕迹判定（AMEND-2 口径：痕迹存在即须司法文件）。

        - escheat 记录：未决 / 有争议事由 / 有主张人 ⇒ 痕迹；**已凭 `judicial_ref` 结案者除外**
        - 争议流程：存在流程即痕迹（含 ADJUDICATED——人类裁决登记**不构成司法裁决**）
        """
        if self._escheat is not None:
            rec = self._escheat.record(subject_tdid)
            if rec is not None:
                has_marks = bool(getattr(rec, "dispute_open", False)
                                 or getattr(rec, "dispute_grounds", None)
                                 or getattr(rec, "claimants", None))
                settled_by_judicial = bool(getattr(rec, "judicial_ref", None))
                if has_marks and not settled_by_judicial:
                    return True
        if self._dispute is not None:
            if self._dispute.flow(subject_tdid) is not None:
                return True
        return False

    def _sync(self, subject_tdid: str, *, trigger: str, disposition: Optional[str],
              legal_ref: Optional[str], judicial_ref: Optional[str], actor: str) -> SyncOutcome:
        open_dispute = self._dispute_open(subject_tdid)
        trace = self._dispute_trace(subject_tdid)

        # 规则 2：争议痕迹零动作（AMEND-2）——无司法可验证正式文件前不得有任何动作
        if trace and not judicial_ref:
            return self._finish(
                subject_tdid, trigger=trigger, action="deferred-dispute",
                reason=("存在争议痕迹（未决争议／争议史／内部裁决登记）：争议裁决非 TDCA 职责；"
                        "无司法可验证正式文件（judicial_ref）前 TDCA 不得有任何动作，"
                        "只能让其休眠（计时继续）"),
                disposition=disposition, legal_ref=legal_ref, judicial_ref=judicial_ref,
                dispute_open=open_dispute, dispute_trace=trace, actor=actor)

        active = self._bridge.resolve_by_tdid(subject_tdid)
        if active is None:
            return self._finish(
                subject_tdid, trigger=trigger, action="no-active-link",
                reason="无活跃外部链接（幂等：无需联动）",
                disposition=disposition, legal_ref=legal_ref, judicial_ref=judicial_ref,
                dispute_open=open_dispute, dispute_trace=trace, actor=actor)

        basis = (f"司法文件 {judicial_ref}" if judicial_ref
                 else (f"法律文书 {legal_ref}" if legal_ref else "内部终态判定"))
        reason = f"{trigger}；依据：{basis}"
        try:
            link = self._bridge.revoke(subject_tdid, reason=reason, actor=actor)
        except IdentityBridgeError as exc:                     # fail-closed 传递
            raise IdentityLinkSyncError(f"失效同步失败：{exc}") from exc

        return self._finish(
            subject_tdid, trigger=trigger, action="revoked",
            reason=f"主体终态 → 外部链接已失效同步（{reason}）",
            disposition=disposition, legal_ref=legal_ref, judicial_ref=judicial_ref,
            dispute_open=open_dispute, dispute_trace=trace, oid=link.oid, actor=actor,
            bridge_ref=link.nca_ref)

    def _finish(self, subject_tdid: str, *, trigger: str, action: str, reason: str,
                disposition: Optional[str] = None, legal_ref: Optional[str] = None,
                judicial_ref: Optional[str] = None, dispute_open: bool = False,
                dispute_trace: bool = False, oid: Optional[str] = None,
                actor: str = "identity-link-sync",
                bridge_ref: Optional[str] = None) -> SyncOutcome:
        """收束：生成判定存证（零动作分支同样留痕）并组装结果。"""
        if action not in SYNC_ACTIONS:
            raise IdentityLinkSyncError(f"判定动作非法: {action!r}")
        outcome = SyncOutcome(subject_tdid=subject_tdid, trigger=trigger, action=action,
                              reason=reason, disposition=disposition, legal_ref=legal_ref,
                              judicial_ref=judicial_ref, dispute_open=bool(dispute_open),
                              dispute_trace=bool(dispute_trace), oid=oid)
        nca = self._gen.generate(
            type="identity-link-sync", layer=2,
            content={"subject_tdid": subject_tdid, "trigger": trigger, "action": action,
                     "reason": reason, "disposition": disposition, "legal_ref": legal_ref,
                     "judicial_ref": judicial_ref, "dispute_open": bool(dispute_open),
                     "dispute_trace": bool(dispute_trace),
                     "oid": oid, "bridge_nca_ref": bridge_ref, "actor": actor,
                     "simulated": True})
        outcome.nca_refs.append(nca.nca_id)
        return outcome
