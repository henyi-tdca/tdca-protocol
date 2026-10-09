# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，GE-IF 功能组）
# 目标函数:     M3-4 效用精灵深度对接适配层——GE-IF-001 正和评估实时回调
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + 接口熵=0（ID82）
#               + tdca-utility-genie 只读引用（ID24，不改写）
#               + 正和验证不可 mock（KB-ECON-001 §3: S_synergy > 0，效用精灵真实计算）
#               + 非正和 → FUSE 熔断标记（SV-3 方向）
# 先验分布:     tdca_utility_genie.py（四大功能）+ positive_sum_solver.py（ID84）
#               + M2 utility_genie_adapter（positive_sum_check/solve_positive_sum）
# 配置权边界:   L2 层；效用精灵只读引用
# 预期分配:     GE-IF-001 evaluate（实时求解）+ GE-IF-001b check（快路径校验）；
#               失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-4 效用精灵深度对接适配层（GE-IF-001 正和评估实时回调）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.3 | SPDX-License-Identifier: TDCA-Internal

GE-IF 契约（审阅确认书 §2.3：IF-007 → GE-IF-001，NC-20260810-001 已登记）:
  - GE-IF-001: 正和评估实时回调（沙盒实验迭代自动触发效用精灵 solve_positive_sum）
  - GE-IF-001b: 正和快路径校验（实时迭代轻量评估，S_synergy > 0 公式快路径）

与 M2（F6 按需）边界: M2 为请求-响应按需调用（positive-sum 端点）；M3-4 为
**迭代驱动实时回调**——沙盒运行迭代自动触发效用精灵评估并实时记录（深度对接）。

正和公式（KB-ECON-001 §3）: S_synergy = U_actual − ΣU_individual > 0
效用精灵只读引用（开发纪律）: 正和判定必须走效用精灵计算，不可 mock 降级。
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import nca_logger

GE_IF_001 = "GE-IF-001"  # 正和评估实时回调
GE_IF_001B = "GE-IF-001b"  # 正和快路径校验

SV8_LATENCY_MS = 1000  # SV-8: 联动延迟 < 1s（ID71 快系统）

# 效用精灵工程目录（只读引用，M2 同模式）
GENIE_DIR = Path(__file__).resolve().parents[3] / "tdca-utility-genie"


class GenieLinkError(ConnectionError):
    """效用精灵联动接口错误（fail-closed 统一异常）。

    效用精灵不可用/非正和判定时抛出，禁止静默降级（正和验证不可 mock）。
    """


def _load_genie() -> Any:
    """加载效用精灵（只读引用；不可用时显式失败，不 mock）。"""
    if not GENIE_DIR.exists():
        raise GenieLinkError(f"效用精灵工程不存在: {GENIE_DIR}（正和验证不可 mock）")
    if str(GENIE_DIR) not in sys.path:
        sys.path.insert(0, str(GENIE_DIR))
    try:
        from tdca_utility_genie import TDCAUtilityGenie
        return TDCAUtilityGenie()
    except ImportError as e:
        raise GenieLinkError(f"效用精灵加载失败（正和验证不可 mock）: {e}") from e


class GenieCallback:
    """SBX-OPS → 效用精灵深度对接适配层（GE-IF-001 实时回调）。

    六要素声明:
    目标函数: 沙盒实验迭代自动触发效用精灵正和评估（任务书 §6.3 实时回调）
    约束矩阵: 输入——sandbox_id/participants/objective_functions 等契约参数；输出——评估结果；
              禁止——正和判定 mock 降级、非正和判通过（→ FUSE 熔断标记）
    先验分布: TDCAUtilityGenie.solve_positive_sum（ID84）+ positive_sum_check（KB-ECON-001 §3）
    配置权边界: L2；效用精灵只读引用（ID24）
    预期分配: 返回 GE-IF 契约响应（含 nca_refs）；失败=GenieLinkError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-10）
    """

    def __init__(self) -> None:
        # T2 修复：惰性加载——import 期不加载效用精灵（目录缺失时服务仍可启动，503 分支可达）
        self._genie = None

    @property
    def genie(self) -> Any:
        """效用精灵惰性实例（首次联动调用时加载，正和验证不可 mock）。"""
        if self._genie is None:
            self._genie = _load_genie()
        return self._genie

    # ---------------- 内部 ----------------#

    @staticmethod
    def _fail_nca(contract: str, error: Exception) -> None:
        """fail-closed 异常路径 NCA 存证（联动故障亦须可观测，SV-7）。"""
        try:
            nca = nca_logger.build_nca(
                operation=f"GENIE_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator="system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常
            pass

    def _nca(self, operation: str, pre: str, post: str, audit: str,
             negative_space_check: str = "PASS") -> str:
        """SBX 侧 NCA 存证（SV-7，返回 nca_id）。"""
        nca = nca_logger.build_nca(
            operation=operation, operator="system",
            pre_state=pre, post_state=post, audit_trail=audit,
            negative_space_check=negative_space_check,
        )
        return nca_logger.save_nca(nca)

    @staticmethod
    def _parse_objective_functions(specs: List[Dict[str, Any]]) -> List[Any]:
        """解析可序列化公式描述为 callable（T1 修复：REST/JSON 契约可表达）。

        支持: {"type": "linear", "factor": f} → f(x) = factor * x
        非法描述 → ValueError（422 语义）
        """
        import math
        fns = []
        for spec in specs or []:
            if not isinstance(spec, dict) or spec.get("type") != "linear":
                raise ValueError(f"[GE-IF-001] objective_functions 描述非法: {spec!r}（支持 linear）")
            factor = spec.get("factor")
            if not isinstance(factor, (int, float)) or not math.isfinite(float(factor)):
                raise ValueError(f"[GE-IF-001] objective_functions factor 非法: {factor!r}（须有限数值）")
            fns.append(lambda x, f=float(factor): f * x)
        if not fns:
            raise ValueError("[GE-IF-001] objective_functions 为空")
        return fns

    # ---------------- GE-IF-001 正和评估实时回调 ----------------

    def evaluate(self, sandbox_id: str, participants: List[Dict[str, Any]],
                 objective_functions: List[Any],
                 reservation_utilities: List[float],
                 nsfl_boundaries: Optional[List[str]] = None,
                 time_budget: float = 5.0) -> Dict[str, Any]:
        """GE-IF-001 正和评估实时回调（效用精灵 solve_positive_sum 完整求解）。

        六要素声明:
        目标函数: 沙盒实验迭代实时正和评估（任务书 §6.3，GE-IF-001）
        约束矩阵: 输入——participants/objective_functions/reservation_utilities/nsfl_boundaries；
                  输出——评估结果（delta/is_positive_sum/fuse）；禁止——正和判定 mock、
                  非正和判通过（→ FUSE）、效用精灵不可用降级
        先验分布: TDCAUtilityGenie.solve_positive_sum（ID84）+ PositiveSumSolver.Agent
        配置权边界: L2；效用精灵只读
        预期分配: 返回 {contract, is_positive_sum, delta, total_utility, fuse, nca_refs}
                  失败=GenieLinkError（效用精灵不可用）/ValueError（参数非法）
        审计轨迹: GENIE_EVALUATE NCA（fuse 时 negative_space_check=FUSE，SV-10）
        """
        t0 = time.monotonic()
        # T3: 参数完整性校验（工作规范 §4.2）
        if not participants or not objective_functions or not reservation_utilities:
            e = ValueError("[GE-IF-001] participants/objective_functions/reservation_utilities 必填")
            self._fail_nca(GE_IF_001, e)
            raise e
        if len(participants) != len(objective_functions) or len(participants) != len(reservation_utilities):
            e = ValueError("[GE-IF-001] 三方数组长度须一致（参与者/目标函数/保留效用）")
            self._fail_nca(GE_IF_001, e)
            raise e
        import math
        # #5（compliance-auditor P0/P1）: evaluate 参数有限性校验（inf/NaN 不可伪造正和，C02）
        if not all(math.isfinite(r) and r >= 0 for r in reservation_utilities):
            e = ValueError("[GE-IF-001] reservation_utilities 须为有限非负数")
            self._fail_nca(GE_IF_001, e)
            raise e
        for p in participants:
            if not isinstance(p, dict) or not p.get("agent_id"):
                e = ValueError(f"[GE-IF-001] participants 缺 agent_id: {p!r}")
                self._fail_nca(GE_IF_001, e)
                raise e
            cap = p.get("capability", 1.0)
            if not isinstance(cap, (int, float)) or not math.isfinite(float(cap)) or float(cap) <= 0:
                e = ValueError(f"[GE-IF-001] participants capability 非法: {cap!r}（须有限正数）")
                self._fail_nca(GE_IF_001, e)
                raise e
        for b in (nsfl_boundaries or []):
            if not isinstance(b, str):
                e = ValueError(f"[GE-IF-001] nsfl_boundaries 元素须 str: {b!r}")
                self._fail_nca(GE_IF_001, e)
                raise e
        try:
            # T1 修复：公式描述解析为 callable（REST/JSON 契约可表达）
            obj_fns = self._parse_objective_functions(objective_functions)
        except ValueError:
            raise  # 参数错误（422 语义），不包装
        try:
            # T2 修复：先触发效用精灵惰性加载（GENIE_DIR 入 sys.path）再 import solvers
            _ = self.genie
            from solvers.positive_sum_solver import Agent  # noqa: E402 (效用精灵工程)
            agents = [Agent(agent_id=p["agent_id"], capability=p.get("capability", 1.0))
                      for p in participants]
            solution = self.genie.solve_positive_sum(
                participants=agents,
                objective_functions=obj_fns,
                constraint_matrix=[],
                reservation_utilities=reservation_utilities,
                time_budget=time_budget,
                nsfl_boundaries=nsfl_boundaries or [],
            )
            latency_ms = int((time.monotonic() - t0) * 1000)
            if latency_ms >= SV8_LATENCY_MS:
                e = GenieLinkError(f"[GE-IF-001] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
                self._fail_nca(GE_IF_001, e)  # P2 修复：latency 超时亦存证（C01 可观测）
                raise e
        except GenieLinkError:
            raise
        except ValueError as e:
            # P4 修复：效用精灵 validate 抛 ValueError（非正和）→ 包装为 GenieLinkError（503 业务熔断）
            self._fail_nca(GE_IF_001, e)
            raise GenieLinkError(f"[GE-IF-001] 非正和（效用精灵 validate 熔断）: {e}") from e
        except Exception as e:  # noqa: BLE001 - 效用精灵异常统一 fail-closed
            self._fail_nca(GE_IF_001, e)
            raise GenieLinkError(f"[GE-IF-001] 效用精灵评估失败: {e}") from e

        d = solution.to_dict() if hasattr(solution, "to_dict") else vars(solution)
        is_positive = bool(d.get("is_positive_sum", False))
        touched_nsfl = bool(d.get("touched_nsfl", False))
        fuse = (not is_positive) or touched_nsfl
        post = "FUSE" if fuse else "POSITIVE_SUM"
        # #2（compliance-auditor P0）: SV-10 双向存证——效用精灵侧 nca_trace 指纹侧链（对齐 M3-1 T1 SHA-256）
        import hashlib
        nca_trace = d.get("nca_trace", []) or []
        genie_fingerprint = hashlib.sha256(
            json.dumps(nca_trace, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16] if nca_trace else ""
        nca_id = self._nca(
            "GENIE_EVALUATE", "IN-SBX", post,
            f"GE-IF-001 {sandbox_id} delta={d.get('delta')} total={d.get('total_utility')} "
            f"touched_nsfl={touched_nsfl} genie_fingerprint={genie_fingerprint or '-'}",
            negative_space_check="FUSE" if fuse else "PASS",
        )
        return {
            "contract": GE_IF_001,
            "operation": "evaluate",
            "sandbox_id": sandbox_id,
            "is_positive_sum": is_positive,
            "delta": d.get("delta"),
            "total_utility": d.get("total_utility"),
            "independent_sum": d.get("independent_sum"),
            "touched_nsfl": touched_nsfl,
            "fuse": fuse,
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id, "genie_fingerprint": genie_fingerprint},
        }

    # ---------------- GE-IF-001b 正和快路径校验 ----------------

    def check(self, sandbox_id: str, coalition_utility: float,
              independent_utilities: List[float]) -> Dict[str, Any]:
        """GE-IF-001b 正和快路径校验（S_synergy > 0，轻量实时迭代评估）。

        契约语义声明（entropy-guard WARN-1 修复）: GE-IF-001b 为 M2 F6 positive-sum
        的**实时回调变体**——同一底层 positive_sum_check（S_synergy>0），差异在非正和
        行为：M2 抛 422 阻断（按需阻断语义）；GE-IF-001b 返回 200 + fuse=true 熔断标记
        （实时回调语义，由调用方决策）。契约两行为显式区分，调用方按端点选择语义。

        六要素声明:
        目标函数: 实时迭代轻量正和校验（KB-ECON-001 §3 公式快路径，GE-IF-001b）
        约束矩阵: 输入——coalition_utility/independent_utilities（非空且≥0）；输出——判定；
                  禁止——非正和判通过（→ FUSE 熔断标记）、inf/NaN 伪造（P1）
        先验分布: KB-ECON-001 §3（S_synergy = U_actual − ΣU_individual > 0）
        配置权边界: L2；纯计算快路径
        预期分配: 返回 {contract, is_positive_sum, delta, positive_sum_index, fuse, nca_refs}
                  失败=ValueError（参数非法）
        审计轨迹: GENIE_CHECK NCA（fuse 时 negative_space_check=FUSE）
        """
        import math
        # P1 修复：有限性二次校验（pydantic allow_inf_nan=False 兜底；直接调用亦拦截）
        if not math.isfinite(coalition_utility) or coalition_utility <= 0:
            e = ValueError("[GE-IF-001b] coalition_utility 须为有限正数（S_synergy 不可被 inf 伪造）")
            self._fail_nca(GE_IF_001B, e)
            raise e
        if not all(math.isfinite(u) and u >= 0 for u in independent_utilities):
            e = ValueError("[GE-IF-001b] independent_utilities 须为有限非负数")
            self._fail_nca(GE_IF_001B, e)
            raise e
        t0 = time.monotonic()
        from . import utility_genie_adapter as _m2  # 复用 M2 公式快路径（只读）
        result = _m2.positive_sum_check(coalition_utility, independent_utilities)
        latency_ms = int((time.monotonic() - t0) * 1000)
        # #6（compliance-auditor P1）: check 亦执行 SV-8 延迟断言（契约对称）
        if latency_ms >= SV8_LATENCY_MS:
            e = GenieLinkError(f"[GE-IF-001b] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
            self._fail_nca(GE_IF_001B, e)
            raise e
        fuse = bool(result["fuse"])
        post = "FUSE" if fuse else "POSITIVE_SUM"
        nca_id = self._nca(
            "GENIE_CHECK", "IN-SBX", post,
            f"GE-IF-001b {sandbox_id} delta={result['delta']} index={result['positive_sum_index']} "
            f"latency_ms={latency_ms}",
            negative_space_check="FUSE" if fuse else "PASS",
        )
        return {
            "contract": GE_IF_001B,
            "operation": "check",
            "sandbox_id": sandbox_id,
            "is_positive_sum": result["is_positive_sum"],
            "delta": result["delta"],
            "positive_sum_index": result["positive_sum_index"],
            "fuse": fuse,
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id},
        }


# 全局适配器实例（路由层消费；测试可注入）
ADAPTER = GenieCallback()
