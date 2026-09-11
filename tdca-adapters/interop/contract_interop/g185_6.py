# -*- coding: utf-8 -*-
"""GB/Z 185.6 交互内容元素映射 + 群组/混合参与方权限（M4 / #11 + #12）

**#11 内容元素（GB/Z 185.6 §7）——字段名权威 = 国标原文**:
  - 数据 data（§7.3）    : `type` / `metadata` / `payload`
  - 消息 message（§7.4） : `senderRole` / `senderId` / `sessionId` / `taskId` / `id` /
                          `artifact` / `final` / `chunkIndex` / `lastChunk` / `dataItems`
  - 任务 task（§7.5）    : 任务标识符 `taskId` / 会话标识符 `sessionId` / `state` /
                          `stateChangedAt` / `messages` / `artifacts`
  - 会话 session（§7.6） : 会话标识符 `sessionId` / `sender` / `receivers` / `context`
  - 关系（§7.2）         : 会话由请求智能体管理；任务存在于会话；消息可含 taskId、任务可含消息；
                          消息内容封装于数据；特定场景经任务交互；特定场景经消息交互

**#12 参与方权限（GB/Z 185.6 §6.3 / §6.4 + MRCR）**:
  - 群组（§6.3）：创建/配置/管理由**请求智能体**发起并维护，或由**第三方机构**预先配置；
    可直接邀请服务智能体加入，也可审核处理加入申请；第三方可代为发起邀请或审核申请
  - 混合（§6.4）：交互同时存在点对点与群组模式，**由请求智能体决定**服务智能体参与的模式；
    同一服务智能体可同时参与点对点交互和群组交互
  - **MRCR（「多角色兼容性」）**：同一主体**不可同时持有冲突的协议层角色**；
    触发口径（tp-rules 规则 3）：`|Scenes(agent)| > 1 ∧ ¬Isolated(agent, scenes)` → `WARN_AND_AUDIT`

纪律:
  - 字段名不自造；缺失即如实标注（`missing`），**不推测填补**（沿用入向宽容口径）
  - 群组写操作须经授权主体（创建者/被授权第三方）；越权即拒
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------- 国标原文口径
G185_6_MODES = ("p2p", "group", "hybrid")                      # §6.1
G185_6_FIELDS: Dict[str, Tuple[str, ...]] = {
    "data": ("type", "metadata", "payload"),                   # §7.3
    "message": ("senderRole", "senderId", "sessionId", "taskId", "id", "artifact",
                "final", "chunkIndex", "lastChunk", "dataItems"),   # §7.4
    "task": ("taskId", "sessionId", "state", "stateChangedAt", "messages",
             "artifacts"),                                     # §7.5
    "session": ("sessionId", "sender", "receivers", "context"),  # §7.6
}
G185_6_REQUIRED = {
    "data": ("type", "payload"),
    "message": ("senderRole", "senderId", "sessionId", "id", "dataItems"),
    "task": ("taskId", "sessionId", "state"),
    "session": ("sessionId", "sender", "receivers"),
}
G185_6_RELATIONS: Tuple[Tuple[str, str], ...] = (              # §7.2（逐条）
    ("1)", "会话由请求智能体管理（创建/维护/注销）；创建时决定参与的服务智能体与交互模式"),
    ("2)", "任务存在于会话中；会话内可有多个任务；请求智能体管理任务（创建/维护/注销）"),
    ("3)", "消息中可包含任务标识符（taskId）；任务中可包含消息（messages）"),
    ("4)", "消息中的具体内容封装在数据（dataItems）中；消息与数据是必要元素"),
    ("5)", "特定场景下请求智能体通过**任务**与服务智能体交互（任务应含 taskId/sessionId/state）"),
    ("6)", "特定场景下请求智能体通过**消息**与服务智能体交互"),
)
MRCR_RULE_ACTION = "WARN_AND_AUDIT"                            # / tp-rules 规则 3
PARTY_ROLES = ("requestor", "service", "third-party-manager")
GROUP_CREATOR_KINDS = ("requestor", "third-party")             # §6.3
MEMBERSHIP_STATES = ("INVITED", "REQUESTED", "APPROVED", "REJECTED", "REMOVED")
HYBRID_MODES = ("p2p", "group")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- §7 内容元素
@dataclass
class Data:
    """§7.3 数据：type / metadata / payload。"""
    type: str
    payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "metadata": self.metadata, "payload": self.payload,
                "simulated": True}


@dataclass
class Message:
    """§7.4 消息（字段名 = 国标原文）。"""
    senderRole: str                                # 请求智能体 / 服务智能体
    senderId: str
    sessionId: str
    id: str
    dataItems: List[Data] = field(default_factory=list)
    taskId: Optional[str] = None
    artifact: Optional[str] = None
    final: bool = False
    chunkIndex: int = 0
    lastChunk: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"senderRole": self.senderRole, "senderId": self.senderId,
                "sessionId": self.sessionId, "taskId": self.taskId, "id": self.id,
                "artifact": self.artifact, "final": self.final,
                "chunkIndex": self.chunkIndex, "lastChunk": self.lastChunk,
                "dataItems": [d.to_dict() if isinstance(d, Data) else d for d in self.dataItems],
                "simulated": True}


@dataclass
class Task:
    """§7.5 任务（字段名 = 国标原文）。"""
    taskId: str
    sessionId: str
    state: str = "created"
    stateChangedAt: str = ""
    messages: List[Message] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"taskId": self.taskId, "sessionId": self.sessionId, "state": self.state,
                "stateChangedAt": self.stateChangedAt,
                "messages": [m.to_dict() if isinstance(m, Message) else m for m in self.messages],
                "artifacts": list(self.artifacts), "simulated": True}


@dataclass
class Session:
    """§7.6 会话（字段名 = 国标原文）。"""
    sessionId: str
    sender: str
    receivers: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"sessionId": self.sessionId, "sender": self.sender,
                "receivers": list(self.receivers), "context": self.context,
                "simulated": True}


def validate_element(kind: str, obj: Any) -> Dict[str, Any]:
    """按国标字段表核验元素（缺失**如实标注**，不推测填补）。"""
    if kind not in G185_6_FIELDS:
        raise KeyError(f"未知元素类型: {kind}（期望 {tuple(G185_6_FIELDS)}）")
    d = obj.to_dict() if hasattr(obj, "to_dict") else dict(obj or {})
    present = [f for f in G185_6_FIELDS[kind] if f in d]
    missing = [f for f in G185_6_REQUIRED[kind] if d.get(f) in (None, "", [])]
    unknown = [k for k in d if k not in G185_6_FIELDS[kind] and k != "simulated"]
    return {"kind": kind, "ok": not missing, "present": present, "missing": missing,
            "unknown_keys": unknown, "warnings": [f"missing:{m}" for m in missing]
            + [f"unknown_key:{u}" for u in unknown], "simulated": True}


def field_coverage() -> Dict[str, Any]:
    """#11 验收口径：字段覆盖对账表（国标原文 → 实现字段，逐字段）。"""
    return {"standard": "GB/Z 185.6-2026 §7.3~§7.6", "elements": {
        k: {"fields": list(v), "required": list(G185_6_REQUIRED[k])}
        for k, v in G185_6_FIELDS.items()},
        "relations": [{"no": n, "text": t} for n, t in G185_6_RELATIONS],
        "simulated": True}


def project_interaction(ev: Any, *, session_id: str, task_id: Optional[str] = None,
                        data_type: str = "application/tdca-interaction",
                        chunk_index: int = 0, last_chunk: bool = True) -> Dict[str, Any]:
    """interop.InteractionEvent → 185.6 四元素投影（§7.2 关系随之成立）。

    规则（§7.2）：会话由请求智能体创建（sender = from_agent，receivers = to_agents）；
    任务存在于会话；消息含 sessionId/dataItems，可含 taskId；消息内容封装在数据中。
    """
    mode = getattr(ev, "mode", None)
    if mode not in G185_6_MODES:
        raise ValueError(f"未知交互模式: {mode}（期望 {G185_6_MODES}）")
    session = Session(sessionId=session_id, sender=ev.from_agent,
                      receivers=list(ev.to_agents),
                      context={"mode": mode, "action": getattr(ev, "action", "invoke")})
    data = Data(type=data_type,
                payload={"action": getattr(ev, "action", "invoke"),
                         "value": getattr(ev, "value", 0.0),
                         "payload": dict(getattr(ev, "payload", {}) or {})},
                metadata={"event_id": getattr(ev, "event_id", None),
                          "oid": getattr(ev, "oid", None)})
    message = Message(senderRole="requestor", senderId=ev.from_agent, sessionId=session_id,
                      id=f"MSG-{getattr(ev, 'event_id', 'NA')}", dataItems=[data],
                      taskId=task_id, artifact=None, final=True,
                      chunkIndex=chunk_index, lastChunk=last_chunk)
    task = Task(taskId=task_id or f"TASK-{getattr(ev, 'event_id', 'NA')}",
                sessionId=session_id, state="requested", stateChangedAt=_now(),
                messages=[message], artifacts=[])
    out = {"session": session.to_dict(), "message": message.to_dict(),
           "task": task.to_dict(), "data": data.to_dict(), "mode": mode,
           "relations_held": [n for n, _ in G185_6_RELATIONS], "simulated": True}
    return out


# ---------------------------------------------------------------- §6.3 群组与参与方权限
@dataclass
class GroupMember:
    tdid: str
    role: str = "service"                          # requestor / service / third-party-manager
    state: str = "INVITED"
    at: str = ""
    acted_by: Optional[str] = None                 # 邀请/审核动作主体（可追溯）

    def to_dict(self) -> Dict[str, Any]:
        return {"tdid": self.tdid, "role": self.role, "state": self.state, "at": self.at,
                "acted_by": self.acted_by, "simulated": True}


@dataclass
class InteractionGroup:
    """§6.3 群组：创建/配置/管理由请求智能体维护，或由第三方机构预先配置。"""
    group_id: str
    session_id: str
    creator_tdid: str
    creator_kind: str = "requestor"                # requestor / third-party
    members: Dict[str, GroupMember] = field(default_factory=dict)
    created_at: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)

    def active(self) -> List[GroupMember]:
        return [m for m in self.members.values() if m.state == "APPROVED"]

    def to_dict(self) -> Dict[str, Any]:
        return {"group_id": self.group_id, "session_id": self.session_id,
                "creator_tdid": self.creator_tdid, "creator_kind": self.creator_kind,
                "members": [m.to_dict() for m in self.members.values()],
                "created_at": self.created_at, "simulated": True}


class GroupPermissionError(Exception):
    """群组写操作越权（非创建者/未被授权第三方）。"""


class GroupRegistry:
    """群组登记与参与方权限（§6.3；**写操作须经授权主体**）。"""

    def __init__(self, nca_generator=None):
        self._groups: Dict[str, InteractionGroup] = {}
        self._seq = 0
        if nca_generator is None:
            try:
                from tdca_nca.generator import NCAGenerator  # type: ignore
                nca_generator = NCAGenerator()
            except Exception:                                  # noqa: BLE001
                nca_generator = _LocalSeal()
        self._gen = nca_generator

    # ---- 创建（§6.3：请求方发起并维护 / 第三方预先配置） ----
    def create_group(self, *, creator_tdid: str, session_id: str,
                     creator_kind: str = "requestor") -> InteractionGroup:
        if creator_kind not in GROUP_CREATOR_KINDS:
            raise ValueError(f"创建方类型须为 {GROUP_CREATOR_KINDS}（§6.3）")
        self._seq += 1
        gid = f"GRP-{self._seq:04d}"
        group = InteractionGroup(group_id=gid, session_id=session_id,
                                 creator_tdid=creator_tdid, creator_kind=creator_kind,
                                 created_at=_now())
        group.members[creator_tdid] = GroupMember(
            tdid=creator_tdid,
            role="requestor" if creator_kind == "requestor" else "third-party-manager",
            state="APPROVED", at=group.created_at, acted_by=creator_tdid)
        group.history.append({"at": group.created_at, "event": "create",
                              "by": creator_tdid, "kind": creator_kind})
        self._groups[gid] = group
        self._seal(group, "interop-1856-group-create",
                   {"group_id": gid, "creator": creator_tdid, "kind": creator_kind})
        return group

    # ---- 授权判定（§6.3：创建者 / 被授权第三方） ----
    def _assert_authority(self, group: InteractionGroup, actor_tdid: str) -> None:
        creator_ok = actor_tdid == group.creator_tdid
        delegate = group.members.get(actor_tdid)
        delegate_ok = bool(delegate and delegate.role == "third-party-manager"
                           and delegate.state == "APPROVED")
        if not (creator_ok or delegate_ok):
            raise GroupPermissionError(
                f"{actor_tdid} 无权管理群组 {group.group_id}（§6.3：仅请求智能体或被授权第三方机构）")

    # ---- 邀请 / 申请 / 审核（§6.3） ----
    def invite(self, group_id: str, member_tdid: str, *, by: str,
               role: str = "service") -> GroupMember:
        group = self._require(group_id)
        self._assert_authority(group, by)
        if role not in PARTY_ROLES:
            raise ValueError(f"角色须为 {PARTY_ROLES}")
        m = group.members.get(member_tdid) or GroupMember(tdid=member_tdid)
        m.role, m.state, m.at, m.acted_by = role, "INVITED", _now(), by
        group.members[member_tdid] = m
        group.history.append({"at": m.at, "event": "invite", "by": by, "member": member_tdid})
        self._seal(group, "interop-1856-group-invite", {"member": member_tdid, "by": by})
        return m

    def request_join(self, group_id: str, member_tdid: str) -> GroupMember:
        group = self._require(group_id)
        m = group.members.get(member_tdid) or GroupMember(tdid=member_tdid)
        m.state, m.at = "REQUESTED", _now()
        group.members[member_tdid] = m
        group.history.append({"at": m.at, "event": "request-join", "member": member_tdid})
        self._seal(group, "interop-1856-group-request", {"member": member_tdid})
        return m

    def approve(self, group_id: str, member_tdid: str, *, by: str) -> GroupMember:
        """审核加入申请/邀请（§6.3：请求方可直接邀请，也可审核申请；第三方可代为审核）。"""
        group = self._require(group_id)
        self._assert_authority(group, by)
        m = group.members.get(member_tdid)
        if m is None or m.state not in ("INVITED", "REQUESTED"):
            raise GroupPermissionError(f"无可审核的入群事项: {member_tdid}")
        m.state, m.at, m.acted_by = "APPROVED", _now(), by
        group.history.append({"at": m.at, "event": "approve", "by": by, "member": member_tdid})
        self._seal(group, "interop-1856-group-approve", {"member": member_tdid, "by": by})
        return m

    def remove(self, group_id: str, member_tdid: str, *, by: str) -> GroupMember:
        group = self._require(group_id)
        self._assert_authority(group, by)
        m = group.members.get(member_tdid)
        if m is None:
            raise GroupPermissionError(f"成员不存在: {member_tdid}")
        m.state, m.at, m.acted_by = "REMOVED", _now(), by
        group.history.append({"at": m.at, "event": "remove", "by": by, "member": member_tdid})
        self._seal(group, "interop-1856-group-remove", {"member": member_tdid, "by": by})
        return m

    def group(self, group_id: str) -> Optional[InteractionGroup]:
        return self._groups.get(group_id)

    def _require(self, group_id: str) -> InteractionGroup:
        g = self._groups.get(group_id)
        if g is None:
            raise KeyError(f"未知群组: {group_id}")
        return g

    def _seal(self, group: InteractionGroup, kind: str, content: Dict[str, Any]) -> None:
        nca = self._gen.generate(type=kind, layer=2,
                                 content={"group_id": group.group_id, **content,
                                          "simulated": True})
        group.history.append({"at": _now(), "event": "nca", "kind": kind,
                              "nca_ref": getattr(nca, "nca_id", None)})


class _LocalSeal:
    """离线可用轻量存证桩（tdca_nca 不可用时兜底）。"""

    def __init__(self) -> None:
        self._n = 0

    def generate(self, *, type: str, layer: int, content: Dict[str, Any]):
        from types import SimpleNamespace
        self._n += 1
        return SimpleNamespace(nca_id=f"NCA-1856-{self._n:04d}", type=type, content=content)


# ---------------------------------------------------------------- §6.4 混合模式参与决策
def plan_hybrid(requestor_tdid: str, decisions: Dict[str, str],
                *, group_id: Optional[str] = None) -> Dict[str, Any]:
    """§6.4 混合模式：**由请求智能体决定**各服务智能体参与的交互模式。

    同一服务智能体可同时参与点对点交互与群组交互（decisions 中的成员各自独立取值）。
    """
    bad = {k: v for k, v in decisions.items() if v not in HYBRID_MODES}
    if bad:
        raise ValueError(f"参与模式须为 {HYBRID_MODES}：{bad}")
    return {"requestor": requestor_tdid, "group_id": group_id,
            "participation": dict(decisions),
            "p2p_members": sorted(k for k, v in decisions.items() if v == "p2p"),
            "group_members": sorted(k for k, v in decisions.items() if v == "group"),
            "decided_by": requestor_tdid, "authority": "requestor（§6.4）",
            "at": _now(), "simulated": True}


# ---------------------------------------------------------------- MRCR 场景隔离
def mrcr_check(agent_tdid: str, assignments: List[Dict[str, str]],
               *, isolated: bool = False) -> Dict[str, Any]:
    """MRCR 多角色兼容性核验（****）——同一主体**不可同时持有冲突的协议层角色**。

    触发口径（tp-rules-v1.0 规则 3）：`|Scenes(agent)| > 1 ∧ ¬Isolated(agent, scenes)`
    → 动作 `WARN_AND_AUDIT`（不阻断，但须审计留痕）。

    assignments: [{"scene": "scene-a", "role": "requestor"}, ...]
    """
    scenes = sorted({a.get("scene", "") for a in assignments if a.get("scene")})
    roles = sorted({a.get("role", "") for a in assignments if a.get("role")})
    multi_scene = len(scenes) > 1
    conflict = multi_scene and not isolated
    # 同一场景内不得同时为请求方与服务方（协议层角色冲突）
    per_scene: Dict[str, set] = {}
    for a in assignments:
        per_scene.setdefault(a.get("scene", ""), set()).add(a.get("role", ""))
    role_conflicts = sorted(s for s, rs in per_scene.items()
                            if "requestor" in rs and "service" in rs)
    return {"agent_tdid": agent_tdid, "scenes": scenes, "roles": roles,
            "multi_scene": multi_scene, "isolated": bool(isolated),
            "conflict": bool(conflict or role_conflicts),
            "role_conflicts": role_conflicts,
            "rule": " / tp-rules 规则 3",
            "action": MRCR_RULE_ACTION if (conflict or role_conflicts) else "ALLOW",
            "detail": ("多场景且未隔离 → WARN_AND_AUDIT" if conflict
                       else ("同场景内请求/服务角色冲突 → WARN_AND_AUDIT" if role_conflicts
                             else "无冲突")),
            "simulated": True}
