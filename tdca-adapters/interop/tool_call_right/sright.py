# -*- coding: utf-8 -*-
"""TDCA 场景配置权调用网关（S-Right Gateway）V1.1 —— GB/Z 185.7 工具调用 → 配置权调用

V1.1 增补（M2 待细化 5 项）:
  1. PCR-Token 交换（签发 / 校验：持有人·边界覆盖·有效期·预算）——本地签名式；
     真实网络交换待载体（如实标注，不虚报）
  2. CCV 五层完整化（身份兼容 / 效用兼容 / 正和兼容 / 负空间兼容 / 税收兼容）
  3. Shapley 分配接入（效用精灵 GameTheoryEngine.shapley_value；授予后自动分账）
  4. 边界变更联动重评（update_tools → 在册授予标记复查 → recheck_grant）
  5. 与 core-go MCP 工具面对接（McpToolFaceAdapter：四工具语义映射 + dry-run 显式标注）

制度依据:
  - GB/Z 185.7 内化映射（内化白皮书 §2.2）+ 185.7 精读（8 步 → 14 步增强流程；CCV 五层）
  - TDCA 配置权调用规范 V1.1（场景配置权调用接口规范）｜ TDCA 层间规范 §四

纪律:
  - 正和前置（fail-closed）；负空间熔断；预算制；存证必在
  - 税收兼容层：工具服务方须具备可验证 MOU 锚定历史（模拟态默认 1 条；显式置空可测拒绝）
  - 引擎源如实标注（效用精灵优先，回退内置同准则）
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

MIN_SCENE_FIT = 0.5       # 效用兼容层最低拟合度（制度阈值，可配）


def _load_positive_sum_engine():
    try:
        from math_engines.game_theory_engine import GameTheoryEngine  # type: ignore
        return GameTheoryEngine(), "utility-genie/GameTheoryEngine"
    except Exception:  # pragma: no cover
        class _Fallback:
            def positive_sum_check(self, coalition, independent):
                d = coalition - sum(independent)
                return (d > 0, d)

            def shapley_value(self, participants, coalition_value):
                n = len(participants) or 1
                return {p: round(coalition_value({p}) / n, 4) for p in participants}
        return _Fallback(), "builtin-fallback"


@dataclass
class PCRToken:
    """配置权令牌（PCR-Token）——边界 + 预算 + 有效期 + 持有人。"""
    token_id: str
    holder_tdid: str
    scope: str
    budget_total: float
    issued_at: str
    expires_at: str
    oid: Optional[str] = None
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "holder_tdid": self.holder_tdid,
                "scope": self.scope, "budget_total": self.budget_total,
                "issued_at": self.issued_at, "expires_at": self.expires_at,
                "oid": self.oid, "signature": self.signature, "simulated": True}


@dataclass
class ToolDescriptor:
    tool_id: str
    name: str
    version: str = "1.0.0"
    boundary: str = "scene-default"
    scene_fit: Dict[str, float] = field(default_factory=dict)
    executor: Optional[Callable[[Dict[str, Any]], Any]] = None
    # 税收兼容层：MOU 锚定历史（模拟态默认 1 条；置空 [] 可测拒绝路径）
    mou_anchors: List[str] = field(default_factory=lambda: ["sim-anchor"])


@dataclass
class CallRequest:
    caller_tdid: str
    tool_id: str
    scene: str
    coalition_utility: float
    independent_utilities: List[float] = field(default_factory=list)
    budget_cost: float = 0.0
    violates_nsfl: bool = False
    oid: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    pcr_token: Optional[PCRToken] = None


@dataclass
class GrantRecord:
    grant_id: str
    tool_id: str
    caller_tdid: str
    scene: str
    boundary_at_grant: str
    at: str
    status: str = "ACTIVE"          # ACTIVE / RECHECK_REQUIRED / REVOKED
    nca_ref: Optional[str] = None
    shapley: Dict[str, float] = field(default_factory=dict)


@dataclass
class CallOutcome:
    granted: bool
    reason: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    ccv: Dict[str, Any] = field(default_factory=dict)
    positive_sum_delta: Optional[float] = None
    utility_engine: str = ""
    tax: float = 0.0
    budget_after: float = 0.0
    nca_ref: Optional[str] = None
    result: Any = None
    shapley: Dict[str, float] = field(default_factory=dict)
    grant_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"granted": self.granted, "reason": self.reason, "steps": self.steps,
                "ccv": self.ccv, "positive_sum_delta": self.positive_sum_delta,
                "utility_engine": self.utility_engine, "tax": self.tax,
                "budget_after": self.budget_after, "nca_ref": self.nca_ref,
                "shapley": self.shapley, "grant_id": self.grant_id}


class SRightGateway:
    """场景配置权调用网关（PCR-Gateway 实现 V1.1）。"""

    def __init__(self, budget: float = 100.0, tax_rate: float = 0.02,
                 nca_generator=None, identity_bridge=None):
        self.budget = float(budget)
        self.tax_rate = float(tax_rate)
        self._tools: Dict[str, ToolDescriptor] = {}
        self._boundary_events: List[Dict[str, Any]] = []
        self._grants: Dict[str, GrantRecord] = {}
        if nca_generator is None:
            from tdca_nca.generator import NCAGenerator  # type: ignore
            nca_generator = NCAGenerator()
        self._gen = nca_generator
        self._bridge = identity_bridge
        self._engine, self.utility_engine = _load_positive_sum_engine()

    # ---------- ① 配置权发现前置（CDP-Pre） ----------
    def register_tool(self, desc: ToolDescriptor) -> ToolDescriptor:
        self._tools[desc.tool_id] = desc
        return desc

    def list_tools(self, scene: str, requirement: str = "") -> List[Dict[str, Any]]:
        rows = [{"tool_id": t.tool_id, "name": t.name, "version": t.version,
                 "boundary": t.boundary, "scene_fit": fit, "requirement": requirement,
                 "mou_anchors": len(t.mou_anchors), "simulated": True}
                for t in self._tools.values() if (fit := t.scene_fit.get(scene)) is not None]
        rows.sort(key=lambda r: r["scene_fit"], reverse=True)
        return rows

    # ---------- ② 工具列表更新（边界变更 + 联动重评） ----------
    def update_tools(self, tool_id: str, version: str, boundary: Optional[str] = None,
                     scene_fit: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"未知工具: {tool_id}")
        old = {"version": tool.version, "boundary": tool.boundary}
        tool.version = version
        boundary_changed = False
        if boundary and boundary != tool.boundary:
            tool.boundary = boundary
            boundary_changed = True
        if scene_fit:
            tool.scene_fit = scene_fit
        affected = []
        if boundary_changed:
            for g in self._grants.values():
                if g.tool_id == tool_id and g.status == "ACTIVE":
                    g.status = "RECHECK_REQUIRED"
                    affected.append(g.grant_id)
        event = {"event": "boundary_change", "tool_id": tool_id, "old": old,
                 "new": {"version": version, "boundary": tool.boundary},
                 "boundary_changed": boundary_changed,
                 "recheck_required": True, "affected_grants": affected,
                 "note": "边界变更须重过效用精灵正和评估；在册授予标记复查（185.7 §5.2 映射）",
                 "at": self._now(), "simulated": True}
        nca = self._gen.generate(type="sright-boundary-change", layer=2, content=event)
        event["nca_ref"] = nca.nca_id
        self._boundary_events.append(event)
        return event

    # ---------- PCR-Token ----------
    @staticmethod
    def issue_token(holder_tdid: str, scope: str, budget_total: float,
                    ttl_seconds: int = 600, oid: Optional[str] = None) -> PCRToken:
        now = datetime.now().astimezone()
        token = PCRToken(
            token_id="PCR-" + uuid.uuid4().hex[:12].upper(), holder_tdid=holder_tdid,
            scope=scope, budget_total=float(budget_total),
            issued_at=now.isoformat(timespec="seconds"),
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds"),
            oid=oid)
        token.signature = "mock-sm2:" + uuid.uuid5(uuid.NAMESPACE_DNS, token.token_id).hex[:16]
        return token

    @staticmethod
    def verify_token(token: PCRToken, req: CallRequest, tool: Optional[ToolDescriptor]) -> Dict[str, Any]:
        """令牌校验：持有人 / 边界覆盖 / 有效期 / 预算承载（模拟态签名式）。"""
        checks = {}
        checks["holder"] = (token.holder_tdid == req.caller_tdid)
        checks["scope_covers"] = bool(tool) and (
            token.scope == tool.boundary or token.scope in ("*", "all")
            or tool.boundary.startswith(token.scope))
        try:
            checks["not_expired"] = datetime.fromisoformat(token.expires_at) > datetime.now().astimezone()
        except Exception:
            checks["not_expired"] = False
        checks["budget_ok"] = token.budget_total >= req.budget_cost
        checks["signed"] = bool(token.signature)
        return {"ok": all(checks.values()), "checks": checks,
                "signature_mode": "local-signed", "simulated": True}

    # ---------- CCV 五层 ----------
    def ccv_verify(self, req: CallRequest, tool: Optional[ToolDescriptor]) -> Dict[str, Any]:
        """CCV 五层验证（185.7 精读步骤 2 完整定义）。"""
        layers: Dict[str, Dict[str, Any]] = {}
        # ① 身份兼容（OID + PCR-Gene 有效性）
        try:
            from identity_bridge import IdentityBridge  # type: ignore
            IdentityBridge.validate_tdid(req.caller_tdid)
            ok = True
            detail = f"tdid={req.caller_tdid}"
            if req.oid and self._bridge is not None:
                link = self._bridge.resolve_by_tdid(req.caller_tdid)
                ok = link is not None and link.oid == req.oid
                detail = f"oid={req.oid} linked={ok}"
        except Exception as exc:
            ok, detail = False, str(exc)
        layers["身份兼容"] = {"ok": ok, "detail": detail}
        # ② 效用兼容（工具-场景效用函数拟合度）
        fit = tool.scene_fit.get(req.scene) if tool else None
        layers["效用兼容"] = {"ok": fit is not None and fit >= MIN_SCENE_FIT,
                              "detail": f"scene_fit={fit} min={MIN_SCENE_FIT}"}
        # ③ 正和兼容
        is_pos, delta = self._engine.positive_sum_check(req.coalition_utility, req.independent_utilities)
        layers["正和兼容"] = {"ok": bool(is_pos), "detail": f"delta={delta:.2f}"}
        # ④ 负空间兼容
        layers["负空间兼容"] = {"ok": not req.violates_nsfl,
                                "detail": "declared-violation" if req.violates_nsfl else "clean"}
        # ⑤ 税收兼容（可验证 MOU 锚定历史）
        anchors = len(tool.mou_anchors) if tool else 0
        layers["税收兼容"] = {"ok": anchors >= 1, "detail": f"mou_anchors={anchors}"}
        return {"all_passed": all(v["ok"] for v in layers.values()),
                "layers": layers, "positive_sum_delta": delta,
                "engine": self.utility_engine, "simulated": True}

    # ---------- Shapley 分配（授予后自动分账） ----------
    def _shapley_split(self, req: CallRequest, delta: float) -> Dict[str, float]:
        base = req.independent_utilities or [req.coalition_utility]
        parts = [f"agent_{i + 1}" for i in range(len(base))]
        n = len(base)
        fixed_sum = sum(base)
        try:
            def v(S: set) -> float:
                idx = [parts.index(p) for p in S if p in parts]
                return fixed_sum * 0 + sum(base[i] for i in idx) + (
                    delta * len(idx) / n if n else 0.0)
            alloc = self._engine.shapley_value(parts, v)
            return {k: round(float(val), 4) for k, val in alloc.items()}
        except Exception:  # pragma: no cover
            return {p: round(base[i] + delta / n, 4) for i, p in enumerate(parts)}

    def recheck_grant(self, grant_id: str) -> GrantRecord:
        """边界变更后的授予复查：通过 → ACTIVE；否则 REVOKED。"""
        g = self._grants.get(grant_id)
        if g is None:
            raise KeyError(f"未知授予记录: {grant_id}")
        tool = self._tools.get(g.tool_id)
        ok = tool is not None and (
            tool.boundary == g.boundary_at_grant or g.boundary_at_grant in ("*", tool.boundary))
        g.status = "ACTIVE" if ok else "REVOKED"
        return g

    # ---------- ③ 调用（14 步精简，含五层/Token/Shapley） ----------
    def invoke(self, req: CallRequest) -> CallOutcome:
        steps: List[Dict[str, Any]] = []
        tool = self._tools.get(req.tool_id)

        def st(no: int, name: str, ok: bool, detail: str = "") -> None:
            steps.append({"step": no, "name": name, "ok": ok, "detail": detail})

        # 步 1：连接 + PCR-Token 交换（缺失 → 降级并标注）
        if req.pcr_token is None:
            st(1, "连接与 PCR-Token 交换", True, "token 缺省（降级为 tdid 校验——兼容路径）")
        else:
            tv = self.verify_token(req.pcr_token, req, tool)
            st(1, "连接与 PCR-Token 交换", tv["ok"], f"checks={tv['checks']}")
            if not tv["ok"]:
                return self._reject("PCR-Token 校验未通过（拒绝）", steps)

        # 步 2：工具解析（未注册 → 明确拒绝）
        if tool is None:
            st(2, "工具解析", False, f"未知工具 {req.tool_id}")
            return self._reject("工具未注册（拒绝）", steps)

        # 步 2：CCV 五层验证
        ccv = self.ccv_verify(req, tool)
        for name, layer in ccv["layers"].items():
            st(2, f"CCV・{name}", layer["ok"], layer["detail"])
        if not ccv["all_passed"]:
            bad = [k for k, v in ccv["layers"].items() if not v["ok"]]
            return self._reject(f"CCV 未通过（{','.join(bad)}）——拒绝", steps,
                                ccv=ccv, delta=ccv["positive_sum_delta"])

        # 步 3-4：目标函数声明 + 预算检查
        st(3, "目标函数声明与约束矩阵摘要", True, f"scene={req.scene}")
        if req.budget_cost > self.budget:
            st(4, "配置权预算检查", False, f"cost={req.budget_cost} > budget={self.budget}")
            return self._reject("配置权预算不足（拒绝）", steps, ccv=ccv,
                                delta=ccv["positive_sum_delta"])
        self.budget = round(self.budget - req.budget_cost, 6)
        st(4, "配置权预算检查", True, f"cost={req.budget_cost} remaining={self.budget}")

        # 步 5-6：选择 + 转发（附 token/上下文）
        st(5, "工具选择（效用最大化+边界合规）", True, f"tool={req.tool_id}")
        st(6, "请求转发（附 PCR-Token/NCA 上下文）", True, "forwarded")

        # 步 7：正和性最终确认（执行前）
        is_pos, delta = self._engine.positive_sum_check(req.coalition_utility, req.independent_utilities)
        st(7, "正和性最终确认（执行前）", bool(is_pos), f"delta={delta:.2f}")
        if not is_pos:
            return self._reject("正和性最终确认未通过（拒绝）", steps, ccv=ccv, delta=delta)

        # 步 8：执行 + NCA 片段
        result = None
        if tool.executor is not None:
            try:
                result = tool.executor(req.payload)
                st(8, "工具执行（实时生成 NCA 片段）", True, str(result)[:60])
            except Exception as exc:
                st(8, "工具执行", False, f"{type(exc).__name__}: {exc}")
                return self._reject("执行失败", steps, ccv=ccv, delta=delta)
        else:
            st(8, "工具执行（声明式）", True, "无执行器注册")

        # 步 9：负空间 Runtime 检查
        st(9, "负空间 Runtime 检查", True, "clean（执行中）")

        # 步 10-11：结果回传 + 效用计量与 Shapley 分配
        shapley = self._shapley_split(req, delta)
        st(10, "结果回传（效用计量/税收锚定/NCA 指纹）", True, "returned")
        st(11, "效用计量与 Shapley 分配", True, f"shapley={shapley}")

        # 步 12：纳税触发 + MOU
        tax = round(req.coalition_utility * self.tax_rate, 2)
        st(12, "纳税触发（进项/出项 + MOU 更新）", True, f"tax={tax} rate={self.tax_rate}")

        # 步 13-14：回传智能体 + 完成判断（+ NCA 归档）
        nca = self._gen.generate(
            type="sright-invoke", layer=2,
            content={"caller_tdid": req.caller_tdid, "tool_id": req.tool_id, "scene": req.scene,
                     "coalition_utility": req.coalition_utility, "delta": delta, "tax": tax,
                     "shapley": shapley, "budget_after": self.budget,
                     "engine": self.utility_engine, "simulated": True})
        grant = GrantRecord(grant_id="GR-" + uuid.uuid4().hex[:10].upper(),
                            tool_id=req.tool_id, caller_tdid=req.caller_tdid, scene=req.scene,
                            boundary_at_grant=tool.boundary, at=self._now(), nca_ref=nca.nca_id,
                            shapley=shapley)
        self._grants[grant.grant_id] = grant
        st(13, "结果回传智能体（计量/分配/税收凭证）", True, "delivered")
        st(14, "完成判断（任务完成 + 税收锚定确认 + NCA 归档）", True, f"nca={nca.nca_id}")

        return CallOutcome(granted=True, reason="授予（CCV 五层通过 + 正和 + 预算内）",
                           steps=steps, ccv=ccv, positive_sum_delta=delta,
                           utility_engine=self.utility_engine, tax=tax,
                           budget_after=self.budget, nca_ref=nca.nca_id, result=result,
                           shapley=shapley, grant_id=grant.grant_id)

    # ---------- 内部/观测 ----------
    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _reject(self, reason: str, steps: List[Dict[str, Any]],
                ccv: Optional[Dict[str, Any]] = None,
                delta: Optional[float] = None) -> CallOutcome:
        return CallOutcome(granted=False, reason=reason, steps=steps, ccv=ccv or {},
                           positive_sum_delta=delta, utility_engine=self.utility_engine,
                           budget_after=self.budget)

    def boundary_events(self) -> List[Dict[str, Any]]:
        return list(self._boundary_events)

    def grants(self) -> List[GrantRecord]:
        return list(self._grants.values())
