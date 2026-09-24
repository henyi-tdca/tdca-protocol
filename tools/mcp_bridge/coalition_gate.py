# FC-ID: DCD-MCP-BRIDGE-001 | 模块 6 联盟可行性强制网关（生产链硬化 · D-3）
"""form_coalition 前置校验 + 出盒令牌网关（生产唯一语义源）。

来源与纪律（TDCA-HANDOFF-WORKBUDDY-ENG-GOV-B1-002 · D-3，GSEQ-0884）
-----------------------------------------------------------------------
* 规范源：TDCA-SANDBOX-COALITION-001 §3.2「前置校验确定性算法（硬编码，非可选）」
  + §二「强制网关」。
* 语义来源：本模块语义**逐行等价于**批次 1 已验收的 16/16 用例、600/600 负例拦截
  实现（`docs/cognitive-compiler/coldstart/sandbox_coalition_precheck/
  coalition_precheck_ref.py`），仅补齐「MCP JSON 参数 → 特征函数」的适配层。
  未另起炉灶（遵守「先搜不重复」ID90）。
* 命名纪律：本模块 `form_coalition` 指**规范 §3.2 的前置校验器**（φ≥BATNA 判定），
  与已重命名的贪心撮合 `compute.coalition.form_coalition_greedy` 彻底区分。
* Fail-closed：声明了联盟但特征函数不完整 ⇒ **无法证明** ∀i φᵢ ≥ BATNAᵢ
  ⇒ 判 INFEASIBLE（不静默放行）。

MCP 参数契约（JSON 可声明）
---------------------------
    "coalition": {
        "members": ["A", "B", "C"],
        "batna":   {"A": 12.0, "B": 10.0, "C": 8.0},
        "V":       {"": 0.0, "A": 12.0, "B": 10.0, "A|B": 30.0, ...}   # 键 = "|".join(sorted(子集))
    }
`V` 必须覆盖 members 的全部 2^n 个子集；缺失任一子集 ⇒ INFEASIBLE（unprovable）。
未声明 `coalition` ⇒ status=NA（不适用，网关放行并在存证中显式标注，不静默）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import comb
from typing import Callable, Dict, FrozenSet, Iterable

__all__ = [
    "SandboxEntryDenied",
    "CoalitionResult",
    "SandboxToken",
    "GateReport",
    "shapley",
    "form_coalition",
    "sandbox_validated_form_coalition",
    "emit_nca",
    "evaluate",
    "require_token",
]

# 浮点容差: 仅用于吸收 IEEE754 噪声, 不改变"严格小于"的规范语义
EPS = 1e-9

# 网关模式: enforce=拦截并拒绝发射; audit=仅记录不拦截（供灰度对照，默认 enforce）
GATE_MODE = "enforce"


class SandboxEntryDenied(Exception):
    """绕过沙盒强制网关(§二) —— 规范: 任何绕过触发 SandboxEntryDenied。"""


@dataclass
class CoalitionResult:
    """规范 §3.2 返回结构 + 试验闸衔接字段。"""

    status: str                       # COALITION_FEASIBLE / COALITION_NOT_FEASIBLE
    shapley: Dict[str, float] = field(default_factory=dict)
    batna: Dict[str, float] = field(default_factory=dict)
    infeasible_members: set = field(default_factory=set)
    suggestion: str = ""
    nca_emitted: bool = False         # 关键: 不可行 → False, 不发射 NCA
    nca_ref: str | None = None

    # ---- 与试验闸模板(TDCA-ENG-GATE-TRIAL-001) precheck.form_coalition 字段对齐 ----
    @property
    def precheck_form_coalition(self) -> str:
        """PASS / FAIL —— 试验闸 YAML 字段填值口径。"""
        return "PASS" if self.status == "COALITION_FEASIBLE" else "FAIL"

    @property
    def precheck_detail(self) -> str:
        """FAIL 时的机器可读原因, 供试验闸 negative_space 之外的第二判据记录。"""
        if self.status == "COALITION_FEASIBLE":
            return "forall_i_phi_i_ge_batna_i"
        return "CoalitionInfeasible:" + ",".join(sorted(self.infeasible_members))


def shapley(V: Callable[[FrozenSet[str]], float],
            candidates: Iterable[str]) -> Dict[str, float]:
    """精确 Shapley 值（通用特征函数签名, 与规范 §3.2 步骤 1 对齐）。

    权重复用既有 exact_shapley: w = 1 / (n * C(n-1, |S|)), 保证效率公理
    sum(phi_i) = V(N) - V(emptyset)。
    """
    ids = list(candidates)
    n = len(ids)
    if n == 0:
        return {}
    phi: Dict[str, float] = {i: 0.0 for i in ids}
    for i in ids:
        others = [x for x in ids if x != i]
        for r in range(len(others) + 1):
            w = 1.0 / (n * comb(len(others), r))
            for S in combinations(others, r):
                Sset = frozenset(S)
                phi[i] += w * (V(Sset | {i}) - V(Sset))
    return phi


def form_coalition(candidates, batna: Dict[str, float],
                   V: Callable[[FrozenSet[str]], float]) -> CoalitionResult:
    """联盟形成前置校验 —— 发射 NCA 之前必须数学证明 ∀i φᵢ ≥ BATNAᵢ。

    边界语义（规范 §3.2，已由批次 1 用例 A1–A4 实测确认）:
      φᵢ == BATNAᵢ      → 放行（严格小于才拦截, 等号在可行域内）
      φᵢ == BATNAᵢ - ε  → 拦截（ε > EPS）
    """
    phi = shapley(V, candidates)

    # 2. 逐成员校验（硬约束，不可跳过）—— 严格小于
    infeasible = {i for i in candidates if phi[i] < batna[i] - EPS}

    # 3. 存在 φ<BATNA → 拒绝发射联盟 NCA（不允许"计算但放行"）
    if infeasible:
        return CoalitionResult(
            status="COALITION_NOT_FEASIBLE",
            shapley=phi,
            batna=dict(batna),
            infeasible_members=infeasible,
            suggestion="调整 V 定义 / 剔除高 BATNA 成员 / 引入新互补维度",
            nca_emitted=False,
        )

    # 4. 全部通过 → 发射联盟 NCA，进入执行阶段
    return CoalitionResult(status="COALITION_FEASIBLE", shapley=phi,
                           batna=dict(batna), nca_emitted=True)


@dataclass(frozen=True)
class SandboxToken:
    """出盒令牌: 仅由 sandbox_validated_form_coalition 成功路径签发。"""

    coalition: frozenset
    feasible: bool


def sandbox_validated_form_coalition(candidates, batna: Dict[str, float],
                                     V: Callable[[FrozenSet[str]], float]
                                     ) -> tuple[CoalitionResult, SandboxToken | None]:
    """强制网关（规范 §二）: form_coalition 与 emit_nca 之间的唯一通道。

    返回 (result, token)。不可行时 token=None —— 物理上无法取得出盒令牌。
    """
    result = form_coalition(candidates, batna, V)
    if not result.nca_emitted:
        # 拦截即终止: 不签发令牌 → 下游 emit_nca 必然 SandboxEntryDenied
        return result, None
    return result, SandboxToken(coalition=frozenset(candidates), feasible=True)


def emit_nca(payload: dict, token: SandboxToken | None = None) -> str:
    """NCA 发射（受网关保护）。绕过网关（token=None）→ SandboxEntryDenied。"""
    if token is None or not token.feasible:
        raise SandboxEntryDenied(
            "emit_nca 被拒绝: 未持有有效沙盒出盒令牌 "
            "(须经 sandbox_validated_form_coalition 且 ∀i φᵢ ≥ BATNAᵢ)"
        )
    ref = "NCA-COALITION-%08d" % (
        abs(hash((tuple(sorted(token.coalition)), payload.get("scene", "")))) % 10 ** 8)
    return ref


# ---------------- MCP JSON 适配层（本模块新增，算法层未改动） ----------------

@dataclass
class GateReport:
    """precheck.form_coalition 字段载体（试验闸 TDCA-ENG-GATE-TRIAL-001 对齐）。"""

    status: str                       # FEASIBLE / INFEASIBLE / NA
    precheck_form_coalition: str      # PASS / FAIL / NA
    detail: str = ""
    shapley: Dict[str, float] = field(default_factory=dict)
    batna: Dict[str, float] = field(default_factory=dict)
    infeasible_members: list = field(default_factory=list)
    suggestion: str = ""

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "precheck.form_coalition": self.precheck_form_coalition,
            "detail": self.detail,
            "shapley": {k: round(v, 6) for k, v in self.shapley.items()},
            "batna": dict(self.batna),
            "infeasible_members": list(self.infeasible_members),
            "suggestion": self.suggestion,
        }


def _parse_coalition(decl: dict) -> tuple[list, Dict[str, float], Callable]:
    """把 JSON 声明解析为 (members, batna, V)。

    非法/不完整一律抛 ValueError —— 由 evaluate 转成 INFEASIBLE（fail-closed）。
    """
    if not isinstance(decl, dict):
        raise ValueError("coalition 声明必须是对象")
    members = decl.get("members")
    batna = decl.get("batna")
    table = decl.get("V")
    if not isinstance(members, list) or not members:
        raise ValueError("coalition.members 缺失或为空")
    if not isinstance(batna, dict) or not isinstance(table, dict):
        raise ValueError("coalition.batna / coalition.V 必须为对象")
    members = [str(m) for m in members]
    if len(set(members)) != len(members):
        raise ValueError("coalition.members 存在重复成员")

    missing_batna = [m for m in members if m not in batna]
    if missing_batna:
        raise ValueError("BATNA 缺失: " + ",".join(sorted(missing_batna)))

    # V 必须覆盖全部 2^n 个子集（不可证明 ⇒ 不可放行）
    norm: Dict[FrozenSet[str], float] = {}
    for k, v in table.items():
        key = frozenset(s for s in str(k).split("|") if s)
        norm[key] = float(v)
    need_subsets = []
    for r in range(len(members) + 1):
        for S in combinations(members, r):
            need_subsets.append(frozenset(S))
    missing = [S for S in need_subsets if S not in norm]
    if missing:
        raise ValueError("特征函数 V 子集缺失: " + ";".join(
            "|".join(sorted(S)) or "(空集)" for S in missing))

    bat = {m: float(batna[m]) for m in members}

    def V(S: FrozenSet[str]) -> float:
        return norm[frozenset(S)]

    return members, bat, V


def evaluate(arguments: dict) -> GateReport:
    """从 MCP 调用参数评估联盟可行性 —— precheck.form_coalition 字段来源。

    * 未声明 coalition ⇒ NA（不适用，不静默：存证显式标注）
    * 声明但不可证明 / 不可行 ⇒ INFEASIBLE（fail-closed）
    """
    decl = (arguments or {}).get("coalition")
    if decl is None:
        return GateReport(status="NA", precheck_form_coalition="NA",
                          detail="no_coalition_declared",
                          suggestion="本次调用未声明联盟，网关不适用"
                                     "（不静默：存证中显式标注 coalition_gate=NA）")
    try:
        members, bat, V = _parse_coalition(decl)
    except ValueError as e:
        return GateReport(status="INFEASIBLE", precheck_form_coalition="FAIL",
                          detail="CoalitionInfeasible:unprovable:" + str(e),
                          suggestion="补全 BATNA / 特征函数 V 的全部子集后重试")
    result, _token = sandbox_validated_form_coalition(members, bat, V)
    return GateReport(
        status="FEASIBLE" if result.nca_emitted else "INFEASIBLE",
        precheck_form_coalition=result.precheck_form_coalition,
        detail=result.precheck_detail,
        shapley=result.shapley,
        batna=result.batna,
        infeasible_members=sorted(result.infeasible_members),
        suggestion=result.suggestion,
    )


def require_token(arguments: dict,
                  report: "GateReport | dict | None" = None) -> SandboxToken | None:
    """发射 NCA 前的强制网关。INFEASIBLE ⇒ 抛 SandboxEntryDenied（不签发令牌）。

    NA ⇒ 返回 None 但**不抛异常**（不适用而非违规），由调用方在存证中显式标注；
    若需把 NA 也收口为拒绝，设置 GATE_MODE="strict_na"。

    report 可传 GateReport，也可传其 as_dict()（fuse.PrecheckResult 透传场景）；
    传 None 时按 arguments 现算。
    """
    if report is None:
        report = evaluate(arguments)
    if isinstance(report, GateReport):
        status, detail = report.status, report.detail
    else:
        status = str(report.get("status", "NA"))
        detail = str(report.get("detail", ""))

    if status == "INFEASIBLE":
        if GATE_MODE == "audit":
            return None
        raise SandboxEntryDenied(
            "coalition_gate: 联盟不可行，拒绝发射 NCA —— " + detail)
    if status == "NA":
        if GATE_MODE == "strict_na":
            raise SandboxEntryDenied(
                "coalition_gate: 未声明联盟且 GATE_MODE=strict_na，拒绝发射 NCA")
        return None
    members, bat, V = _parse_coalition(arguments["coalition"])
    _result, token = sandbox_validated_form_coalition(members, bat, V)
    return token
