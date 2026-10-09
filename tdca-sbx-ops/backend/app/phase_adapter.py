# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，PM-IF 功能组）
# 目标函数:     M3-3 沙盒-阶段机联动适配层——PM-IF-001 激活系数达标 → PhaseMachine 阶段推进
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + 接口熵=0（ID82）
#               + tdca-flow-orchestrator phase_machine.py 只读引用（FC-012，不改写）
#               + SV-1 必要非充分（α>1.2 仅准入，sandbox_pass/delta 消费沙盒真实评估记录）
#               + C03 自证（current_phase 服务端核对沙盒真实 FlowEngine phase）
# 先验分布:     phase_machine.py（transition/get_conditions + 9 Phase 穿越条件）
#               + M3-2 flow_adapter 参照（inproc 桥接 + fail-closed + 双向存证）
# 配置权边界:   L2 层；PhaseMachine 只读引用
# 预期分配:     PM-IF-001 advance_signal + conditions 查询；失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-3 沙盒-阶段机联动适配层（PM-IF-001）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.2 | SPDX-License-Identifier: TDCA-Internal

PM-IF 契约（审阅确认书 §2.3：IF-006 → PM-IF-001，NC-20260810-001 已登记）:
  - PM-IF-001: 激活系数达标（α>1.2，SV-1 必要非充分）→ PhaseMachine 阶段推进信号
  - PM-IF-001b: 穿越条件查询（PhaseMachine.get_conditions）

与 M3-2（FE-IF）边界（T4 声明）: PM-IF-001 为**出盒评估后原子推进信号**（直连
PhaseMachine，无 FlowEngine 生命周期关联）；返回 `flow_linked: false` 显式标注。
M3-2 FE-IF-002 经 FlowEngine 封装驱动全周期生命周期（含 flow_id 关联）——两条路径
独立，审计以 flow_linked 标注区分。边界裁决待人类确认（交付确认书登记）。

PhaseMachine 无独立 HTTP 服务（api.py 仅 FlowEngine 端点）→ inproc 直接桥接
（tdca_flow_src 别名注册，FC-012 只读）。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from . import nca_logger
from .activation_engine import ACTIVATION_THRESHOLD  # T7: 单一权威阈值（SV-1）

PM_IF_001 = "PM-IF-001"  # 激活系数达标 → 阶段推进
PM_IF_001B = "PM-IF-001b"  # 穿越条件查询
PM_IF_001C = "PM-IF-001c"  # 状态集合查询（entropy-guard WARN 修复：独立契约标注）

SV8_LATENCY_MS = 1000  # SV-8: 联动延迟 < 1s（ID71 快系统）

# 允许作为推进起点的 phase（T5/E1 修复：仅 P0~P8，终态/FUSE 起点拒绝）
VALID_START_PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")


def _register_package(alias: str, src_dir: Path):
    """别名注册既有工程包（FlowEngine src，参照 M3-2 flow_adapter）。"""
    spec = importlib.util.spec_from_file_location(
        alias, src_dir / "__init__.py",
        submodule_search_locations=[str(src_dir)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[alias] = pkg
    spec.loader.exec_module(pkg)
    return pkg


_FLOW_SRC = Path(__file__).resolve().parents[3] / "tdca-flow-orchestrator" / "src"


class PhaseLinkError(ConnectionError):
    """PhaseMachine 联动接口错误（fail-closed 统一异常）。

    PhaseMachine 穿越条件不满足/契约破坏时抛出，禁止静默降级。
    """


class PhaseAdapter:
    """SBX-OPS → PhaseMachine 阶段机联动适配层（PM-IF-001）。

    六要素声明:
    目标函数: 激活系数达标触发 PhaseMachine 阶段推进（任务书 §6.2 事件触发）
    约束矩阵: 输入——sandbox_id/sbx（Sandbox 实例，消费真实评估记录）/current_phase；
              输出——推进结果；禁止——α≤1.2 发信号（SV-1 必要非充分）、sandbox_pass/delta
              客户端自报、穿越条件不满足静默推进、终态/FUSE 起点推进、current_phase 与
              沙盒真实 FlowEngine phase 不一致（C03 自证）
    先验分布: phase_machine.transition（9 Phase + 穿越条件）+ sandbox_core 评估记录
    配置权边界: L2；PhaseMachine 只读（FC-012，内存态）
    预期分配: 返回 PM-IF-001 契约响应（含 nca_refs + flow_linked）；失败=PhaseLinkError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-7）+ 推进结果回写沙盒链（F8）
    """

    def __init__(self) -> None:
        if not _FLOW_SRC.exists():
            raise PhaseLinkError(f"tdca-flow-orchestrator src 不存在: {_FLOW_SRC}")
        _register_package("tdca_flow_src", _FLOW_SRC)
        from tdca_flow_src.phase_machine import PhaseMachine  # noqa: E402 (FC-012 只读)
        self.machine = PhaseMachine()

    # ---------------- 内部 ----------------#

    @staticmethod
    def _fail_nca(contract: str, error: Exception) -> None:
        """fail-closed 异常路径 NCA 存证（联动故障亦须可观测，SV-7）。"""
        try:
            nca = nca_logger.build_nca(
                operation=f"PHASE_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator="system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常
            pass

    @staticmethod
    def _real_alpha(sbx: Any) -> float:
        """沙盒真实激活系数（activation_logs 末条，非客户端自报）。"""
        logs = getattr(sbx, "activation_logs", []) or []
        if not logs:
            raise ValueError("[PM-IF-001] 沙盒无激活系数评估记录（须先执行 F3 evaluate）")
        return float(logs[-1].get("coefficient", 0.0))

    @staticmethod
    def _real_delta(sbx: Any) -> float:
        """沙盒真实正和剩余（T6 修复：向后搜索含 delta 的非 DELIVERY_CONFIRM 记录，
        与 sandbox_core.chem_combine 对齐；无有效记录/正和 fuse 拒绝推进）。"""
        logs = getattr(sbx, "positive_sum_logs", []) or []
        valid = [r for r in reversed(logs)
                 if isinstance(r, dict) and "delta" in r
                 and r.get("operation") != "DELIVERY_CONFIRM"]
        if not valid:
            raise ValueError("[PM-IF-001] 沙盒无正和验证记录（须先执行 F6 positive-sum）")
        last = valid[0]
        if last.get("fuse", False):
            raise ValueError("[PM-IF-001] 沙盒最近正和验证未通过（fuse），不可推进")
        return float(last.get("delta", 0.0))

    def _nca(self, operation: str, pre: str, post: str, audit: str) -> str:
        """SBX 侧 NCA 存证（SV-7，返回 nca_id）。"""
        nca = nca_logger.build_nca(
            operation=operation, operator="system",
            pre_state=pre, post_state=post, audit_trail=audit,
        )
        return nca_logger.save_nca(nca)

    # ---------------- PM-IF-001 阶段推进信号 ----------------

    def advance_signal(self, sandbox_id: str, sbx: Any,
                       current_phase: str, real_phase: str = "") -> Dict[str, Any]:
        """PM-IF-001 激活系数达标 → PhaseMachine 阶段推进（ADVANCE 事件）。

        六要素声明:
        目标函数: 激活系数达标（α>1.2，SV-1 必要非充分）触发 PhaseMachine ADVANCE
        约束矩阵: 输入——sandbox_id/sbx（真实评估记录）/current_phase/real_phase（服务端核对）；
                  输出——推进结果（new_phase/fuse）；禁止——α≤1.2 发信号、客户端自报
                  sandbox_pass/delta、穿越条件不满足静默推进、终态/FUSE 起点（T5）、
                  客户端声明 phase 与沙盒真实 phase 不一致（C03 自证，T2）
        先验分布: PhaseMachine.transition（P3->P4 需 sandbox_pass + positive_sum）
        配置权边界: L2；PhaseMachine 只读
        预期分配: 返回 {contract, operation, alpha, from_phase, phase, fuse, flow_linked, nca_refs}
                  失败=ValueError/PhaseLinkError；推进结果回写沙盒 nca_ids（F8 链）
        审计轨迹: PHASE_ADVANCE NCA（SV-7）+ 回写 sb.nca_ids + save_sandbox（T3）
        """
        t0 = time.monotonic()
        # T5/E1: 起点白名单（终态/FUSE 起点拒绝）
        if current_phase not in VALID_START_PHASES:
            e = ValueError(f"[PM-IF-001] current_phase 非法起点: {current_phase}（仅 P0~P8）")
            self._fail_nca(PM_IF_001, e)
            raise e
        # T2/C03: 服务端核对沙盒真实 FlowEngine phase（不一致拒绝）
        if real_phase and real_phase != current_phase:
            e = ValueError(
                f"[PM-IF-001] 客户端声明 phase {current_phase} 与沙盒真实 phase {real_phase} 不一致（C03 自证）")
            self._fail_nca(PM_IF_001, e)
            raise e
        # SV-1 必要非充分：消费沙盒真实评估记录（拒绝客户端自报）
        alpha = self._real_alpha(sbx)
        if alpha <= ACTIVATION_THRESHOLD:  # T7: 权威阈值（SV-1 严格大于）
            e = ValueError(
                f"[PM-IF-001] 激活系数 {alpha} ≤ {ACTIVATION_THRESHOLD}（SV-1 必要非充分），不可发推进信号")
            self._fail_nca(PM_IF_001, e)
            raise e
        # T1: _real_delta 异常亦纳入 fail-closed 存证
        try:
            delta = self._real_delta(sbx)
        except ValueError as e:
            self._fail_nca(PM_IF_001, e)
            raise
        # V6: sandbox_pass 显式提取（从真实评估记录，非硬编码推断）——
        # α>1.2（财政自给性达成）∧ 正和通过（delta 有效且非 fuse）→ sandbox_pass=True
        act_status = (getattr(sbx, "activation_logs", []) or [])[-1].get("status", "")
        sandbox_pass = act_status == "财政自给性达成"
        # V5: 负空间状态消费（SV-3/ID86）——沙盒 negative_space_refs 含熔断标记则拒绝推进
        ns_refs = getattr(sbx, "negative_space_refs", []) or []
        ns_flags = [r for r in ns_refs if isinstance(r, str) and ("fuse" in r.lower() or "熔断" in r)]
        if ns_flags:
            e = PhaseLinkError(f"[PM-IF-001] 沙盒已触碰负空间（{ns_flags}），SV-3/ID86 拒绝推进")
            self._fail_nca(PM_IF_001, e)
            raise e
        if not sandbox_pass:
            e = PhaseLinkError(
                "[PM-IF-001] 沙盒评估未达财政自给性（sandbox_pass=False，SV-1），不可推进")
            self._fail_nca(PM_IF_001, e)
            raise e
        context = {"sandbox_passed": sandbox_pass, "delta_utility": delta,
                   "activation_coefficient": alpha,
                   "nsfl_triggered": bool(ns_flags)}  # V5: 显式传 nsfl_triggered（不依赖缺省放行）
        try:
            new_phase, nca_required, fuse = self.machine.transition(
                current_phase, "ADVANCE", context)
            latency_ms = int((time.monotonic() - t0) * 1000)
            if latency_ms >= SV8_LATENCY_MS:
                raise PhaseLinkError(f"[PM-IF-001] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
        except PhaseLinkError as e:
            self._fail_nca(PM_IF_001, e)
            raise
        except Exception as e:  # noqa: BLE001
            self._fail_nca(PM_IF_001, e)
            raise
        fuse_record = None
        if fuse:
            fuse_record = {"level": fuse.get("level"), "reason": fuse.get("reason"),
                           "target": fuse.get("target")}
            post = "FUSE"
        else:
            post = new_phase
        # V3: C03 核对状态（未挂接 FlowEngine 时显式标注 c03_verified=false，不静默跳过）
        c03_verified = bool(real_phase)
        audit = (f"PM-IF-001 {sandbox_id} α={alpha} delta={delta} {current_phase}→{post} "
                 f"nca_required={nca_required} c03_verified={c03_verified}")
        nca_id = self._nca("PHASE_ADVANCE", current_phase, post, audit)
        # V4: SV-10 双向存证——PhaseMachine 侧无独立 NCA，以 transition 返回指纹作侧链证据
        resp_fingerprint = hashlib.sha256(
            json.dumps({"new_phase": new_phase, "nca_required": nca_required,
                        "fuse": fuse}, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        # T3: 推进结果回写沙盒 nca_ids（F8 审计链完整）
        try:
            nca_ids = list(getattr(sbx, "nca_ids", []) or [])
            nca_ids.append(nca_id)
            sbx.nca_ids = nca_ids
            from . import store as _store
            _store.save_sandbox(sbx)
        except Exception:  # noqa: BLE001 - 回写失败不阻断（NCA 已存证，可观测优先）
            pass
        return {
            "contract": PM_IF_001,
            "operation": "advance",
            "sandbox_id": sandbox_id,
            "alpha": alpha,
            "from_phase": current_phase,
            "phase": new_phase,
            "fuse": fuse_record,
            "flow_linked": False,  # T4: 出盒评估后原子推进信号（无 FlowEngine 生命周期关联）
            "c03_verified": c03_verified,  # V3: 未挂接核对显式标注（不静默）
            "nca_refs": {"sbx": nca_id, "pm_fingerprint": resp_fingerprint},  # V4: 指纹侧链
        }

    # ---------------- PM-IF-001b 穿越条件查询 ----------------

    def conditions(self, from_phase: str, to_phase: str) -> Dict[str, Any]:
        """PM-IF-001b 穿越条件查询（PhaseMachine.get_conditions）。

        六要素声明:
        目标函数: PhaseMachine 穿越条件查询（前端/审计用）
        约束矩阵: 输入——from_phase/to_phase；输出——条件名列表；禁止——无
        先验分布: PhaseMachine.get_conditions
        配置权边界: L2；只读
        预期分配: 返回 {contract, from_phase, to_phase, conditions}；失败=无
        审计轨迹: 只读，不生成 NCA
        """
        names = self.machine.get_conditions(from_phase, to_phase)
        return {"contract": PM_IF_001B, "from_phase": from_phase, "to_phase": to_phase,
                "conditions": names}

    # ---------------- 台账 ----------------

    def state_table(self) -> List[str]:
        """PhaseMachine 状态集合（9 Phase + 终态，审计/前端参考）。

        六要素声明:
        目标函数: PhaseMachine 状态全集查询
        约束矩阵: 输入——无；输出——状态列表；禁止——无
        先验分布: models.ALL_STATES
        配置权边界: L2；只读
        预期分配: 返回状态列表；失败=无
        审计轨迹: 只读
        """
        from tdca_flow_src.models import ALL_STATES  # noqa: E402 (FC-012 只读)
        return list(ALL_STATES)


# 全局适配器实例（路由层消费；测试可注入）
ADAPTER = PhaseAdapter()
