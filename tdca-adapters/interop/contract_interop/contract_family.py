# -*- coding: utf-8 -*-
"""C01-C16 制度映射合约族对接（M4 / #10）

**现状与缺口（INTEROP-001 §八-1）**：`interop.py` 仅生成**自造编号**的合约调用意图
（`C-TAX-PREPAY-<event>`）。本模块实现**真实对接**：以 `official-kb` 的
`contract-templates-v1.0.yaml`（`合约模板集`）为**权威源**装载合约族——

| 模板 | 类型 | 制度锚 |
|---|---|---|
| `CONST-ENFORCE-001` | 宪法十六条强制执行 | 术语库 §2.1 宪法十六条 /（含 **C01~C16 条款编码**） |
| `NSFL-FUSE-001` | 负空间熔断执行 | NSFL // |
| `MOU-ANCHOR-001` | MOU 税收锚定 | 术语库 §2.4 // |
| `CONFIG-RIGHT-SCHEDULE-001` | 配置权调度（七元组 + Shapley + **MRCR**） | 术语库 §2.2 / / |
| `DCEP-MOU-001` | 数字人民币智能合约对接 |// |

**对接语义**：交互事件 → **模板选择**（按动作/价值/负空间声明）→ **调用装配**（template_id +
`functions` 参数面）→ **条款核验**（C01~C16 逐条给据）→ 存证。

纪律:
  - `official-kb` **只读**（权威源不可被本层改写；仅读取）
  - 条款核验三态：`pass` / `fail` / **`not_evaluated`**（无法据实评估者如实标注，不默认为通过）
  - 未在模板中定义的合约号一律拒（`ContractBindingError`）——不自造
  - 数据性质: 模拟态

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

_WS = Path(__file__).resolve().parents[2]
# 权威源可注入：默认在**包外层目录**查找同名模板集（缺失则构造时明确报错，见 README 依赖契约）
DEFAULT_TEMPLATES = _WS / "contract-templates-v1.0.yaml"

# 交互动作 → 首选模板（映射依据：内化白皮书 §4.1 交互日志=税收事件触发器）
ACTION_TEMPLATE_HINTS: Dict[str, str] = {
    "invoke": "MOU-ANCHOR-001",
    "tax-prepay": "MOU-ANCHOR-001",
    "tax-settle": "MOU-ANCHOR-001",
    "config-right": "CONFIG-RIGHT-SCHEDULE-001",
    "schedule": "CONFIG-RIGHT-SCHEDULE-001",
    "admit": "CONST-ENFORCE-001",
    "enforce": "CONST-ENFORCE-001",
}
NSFL_TEMPLATE = "NSFL-FUSE-001"
CORE_CLAUSES = ("C01", "C02", "C03", "C04", "C05")
CLAUSE_STATES = ("pass", "fail", "not_evaluated")


class ContractBindingError(Exception):
    """合约族对接纪律违例（模板缺失 / 未定义合约号 / 装配非法）。"""


@dataclass
class ClauseCheck:
    """C01~C16 单条核验结果（三态：pass / fail / not_evaluated）。"""
    code: str
    name: str
    state: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "name": self.name, "state": self.state,
                "detail": self.detail, "simulated": True}


@dataclass
class ContractBinding:
    """一次装配好的合约调用（以模板为权威）。"""
    template_id: str
    name: str
    type: str
    anchor: str
    params: Dict[str, Any] = field(default_factory=dict)
    clause_checks: List[ClauseCheck] = field(default_factory=list)
    at: str = ""
    nca_ref: Optional[str] = None
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"template_id": self.template_id, "name": self.name, "type": self.type,
                "anchor": self.anchor, "params": self.params,
                "clause_checks": [c.to_dict() for c in self.clause_checks],
                "at": self.at, "nca_ref": self.nca_ref, "simulated": True}

    @property
    def blocked(self) -> bool:
        return any(c.state == "fail" for c in self.clause_checks)


class ContractFamily:
    """C01-C16 制度映射合约族（**只读**装载 official-kb 模板）。"""

    def __init__(self, templates_path: Optional[Path] = None, nca_generator=None):
        self.path = Path(templates_path or DEFAULT_TEMPLATES)
        if not self.path.exists():
            raise ContractBindingError(f"合约模板权威源缺失: {self.path}")
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.version: str = (raw.get("smart_contracts") or {}).get("version", "unknown")
        self.constitutional_base: str = (raw.get("smart_contracts") or {}).get(
            "constitutional_base", "")
        self._templates: Dict[str, Dict[str, Any]] = {
            t["contract_id"]: t for t in (raw.get("smart_contracts") or {}).get("templates", [])}
        if not self._templates:
            raise ContractBindingError("模板集为空（权威源结构异常）")
        if nca_generator is None:
            try:
                from tdca_nca.generator import NCAGenerator  # type: ignore
                nca_generator = NCAGenerator()
            except Exception:                                  # noqa: BLE001
                nca_generator = _Seal()
        self._gen = nca_generator

    # ---------- 观测 ----------
    def template_ids(self) -> List[str]:
        return sorted(self._templates)

    def template(self, template_id: str) -> Dict[str, Any]:
        t = self._templates.get(template_id)
        if t is None:
            raise ContractBindingError(
                f"未在权威源中定义的合约号: {template_id}（不得自造；可用 {self.template_ids()}）")
        return t

    def clause_codes(self) -> Dict[str, str]:
        """C01~C16 条款编码（取自 CONST-ENFORCE-001.state.clause_encoding.clauses）。"""
        tpl = self._templates.get("CONST-ENFORCE-001", {})
        return dict(((tpl.get("state") or {}).get("clause_encoding") or {}).get("clauses") or {})

    def functions_of(self, template_id: str) -> List[Dict[str, Any]]:
        return list(self.template(template_id).get("functions") or [])

    # ---------- 模板选择（交互 → 合约族） ----------
    def select(self, *, action: str = "invoke", violates_nsfl: bool = False,
               mode: Optional[str] = None) -> str:
        """按交互语义选择模板：负空间声明 → NSFL 熔断模板；其余按动作映射；未知动作 → 税收锚定。"""
        if violates_nsfl:
            return NSFL_TEMPLATE
        return ACTION_TEMPLATE_HINTS.get(action, "MOU-ANCHOR-001")

    # ---------- 条款核验（C01~C16，逐条给据，三态） ----------
    def check_clauses(self, context: Optional[Dict[str, Any]] = None) -> List[ClauseCheck]:
        """C01~C05 逐条核验；C06~C16 无逐条定义 → `not_evaluated`（如实标注）。"""
        ctx = dict(context or {})
        codes = self.clause_codes()
        out: List[ClauseCheck] = []

        def add(code: str, state: str, detail: str) -> None:
            out.append(ClauseCheck(code=code, name=codes.get(code, code), state=state,
                                   detail=detail))

        nca_ref = ctx.get("nca_ref")
        add("C01", "pass" if nca_ref else "fail",
            f"可观测性：nca_ref={nca_ref}" if nca_ref else "可观测性缺失（无 NCA 引用）")

        delta = ctx.get("positive_sum_delta", None)
        if delta is None:
            add("C02", "not_evaluated", "正和聚合：未提供 delta（不默认通过）")
        else:
            add("C02", "pass" if float(delta) > 0 else "fail", f"正和聚合：delta={delta}")

        evidence = ctx.get("evidence_hash")
        add("C03", "pass" if evidence else "not_evaluated",
            f"自证性：evidence_hash={evidence}" if evidence else "自证性：未提供证据哈希")

        cr = ctx.get("config_right") or ctx.get("seven_tuple")
        add("C04", "pass" if cr else "not_evaluated",
            f"配置权第三极：{cr}" if cr else "配置权第三极：未提供七元组/调度声明")

        ok_line = ctx.get("essential_line_ok", None)
        add("C05", "pass" if ok_line else ("fail" if ok_line is False else "not_evaluated"),
            f"刚需线保护：essential_line_ok={ok_line}")

        for code in sorted(codes):
            if code in CORE_CLAUSES:
                continue
            add(code, "not_evaluated", "扩展硬约束：权威源未给逐条判定依据（如实标注）")
        return out

    # ---------- 调用装配（真对接） ----------
    def bind(self, template_id: str, *, params: Dict[str, Any],
             context: Optional[Dict[str, Any]] = None,
             function: Optional[str] = None) -> ContractBinding:
        """按模板装配合约调用（含条款核验 + 存证）。

        约束：`template_id` 必须在权威源中；`function`（若给）须在该模板 functions 内。
        """
        tpl = self.template(template_id)
        funcs = [f.get("name") for f in (tpl.get("functions") or [])]
        if function is not None and function not in funcs:
            raise ContractBindingError(
                f"模板 {template_id} 无此函数: {function}（可用 {funcs}）")
        clause_checks = self.check_clauses(context)
        binding = ContractBinding(
            template_id=template_id, name=tpl.get("name", ""), type=tpl.get("type", ""),
            anchor=tpl.get("anchor", ""), params=dict(params), clause_checks=clause_checks,
            at=self._now())
        nca = self._gen.generate(
            type="interop-contract-binding", layer=2,
            content={"template_id": template_id, "type": binding.type, "anchor": binding.anchor,
                     "function": function, "params": binding.params,
                     "clause_checks": [c.to_dict() for c in clause_checks],
                     "blocked": binding.blocked, "source": str(self.path),
                     "version": self.version, "simulated": True})
        binding.nca_ref = getattr(nca, "nca_id", None)
        return binding

    def call_for_interaction(self, ev: Any, *, context: Optional[Dict[str, Any]] = None,
                             function: Optional[str] = None) -> ContractBinding:
        """交互事件 → 装配好的合约调用（替代 interop 自造合约号的路径）。"""
        action = str(getattr(ev, "action", "invoke"))
        value = float(getattr(ev, "value", 0.0) or 0.0)
        violates = bool(getattr(ev, "violates_nsfl", False))
        template_id = self.select(action=action, violates_nsfl=violates,
                                  mode=getattr(ev, "mode", None))
        params = {"event_id": getattr(ev, "event_id", None), "value": value,
                  "from_agent": getattr(ev, "from_agent", None),
                  "to_agents": list(getattr(ev, "to_agents", []) or []),
                  "mode": getattr(ev, "mode", None), "oid": getattr(ev, "oid", None)}
        ctx = dict(context or {})
        if not violates:
            ctx.setdefault("positive_sum_delta", value if value else None)
        return self.bind(template_id, params=params, context=ctx, function=function)

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")


class _Seal:
    """离线轻量存证桩。"""

    def __init__(self) -> None:
        self._n = 0

    def generate(self, *, type: str, layer: int, content: Dict[str, Any]):
        from types import SimpleNamespace
        self._n += 1
        return SimpleNamespace(nca_id=f"NCA-CFAM-{self._n:04d}", type=type, content=content)
