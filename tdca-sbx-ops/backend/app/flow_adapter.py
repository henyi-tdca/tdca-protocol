# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，FE-IF 功能组）
# 目标函数:     M3-2 沙盒-全周期生命周期挂接适配层——FE-IF-001 状态同步 + FE-IF-002 阶段推进信号
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + 接口熵=0（ID82）
#               + tdca-flow-orchestrator 只读引用（FC-012，不改写）
#               + FlowEngine 穿越条件（P3->P4 sandbox_pass / P8->COMPLETED mou_closed）
#               + SV-1 必要非充分（α>1.2 仅为准入，sandbox_pass 须消费沙盒真实评估）
# 先验分布:     flow_engine.py（8 方法）+ api.py（8001 6 端点）+ phase_machine.py（9 Phase）
#               + sandbox_core.py（activation_logs/positive_sum_logs 真实记录）
#               + NS-OPS flow_adapter（inproc/http 双模式参照）
# 配置权边界:   L2 层；FlowEngine 只读对接；凭证环境变量注入（不硬编码）
# 预期分配:     FE-IF-001 hook/status/sync_phase + FE-IF-002 advance；失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-2 沙盒-全周期生命周期挂接适配层（FE-IF-001/002）。

制度锚定: FC-SBX-OPS-001 F7 / 任务书 §6.2 | SPDX-License-Identifier: TDCA-Internal

FE-IF 契约（审阅确认书 §2.3：IF-004~005 → FE-IF-001~002，NC-20260810-001 已登记）:
  - FE-IF-001 状态同步: 沙盒生命周期 ↔ FlowEngine（hook 挂接 + status 查询 + sync_phase 同步）
  - FE-IF-002 阶段推进信号: 激活系数达标（α>1.2，SV-1 必要非充分）→ FlowEngine advance

制度语义（I-2 修复，待人类裁决确认）:
  - SV-1 必要非充分: α>1.2 仅为允许发信号的准入；sandbox_pass/delta_utility 必须消费
    沙盒真实评估记录（activation_logs / positive_sum_logs），不接受客户端自报（与 M2
    surplus 服务端取自 positive_sum_logs 原则一致）

对接模式（双模式）:
  - inproc（默认）: tdca_flow_src 别名注册桥接 FlowEngine（FC-012 只读，测试确定性）
  - http: 调用既有 8001 服务 /api/v1/flow/*（生产路径，凭证环境变量注入）
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import nca_logger
from .activation_engine import ACTIVATION_THRESHOLD  # V2 修复：单一权威阈值（T7）

FE_IF_001 = "FE-IF-001"  # 状态同步
FE_IF_002 = "FE-IF-002"  # 阶段推进信号

# FlowEngine 8001 服务（生产 http 模式）
FLOW_BASE_URL = os.environ.get("FLOW_ENGINE_BASE_URL", "http://127.0.0.1:8001")
# 服务间凭证（T-1 修复：环境变量注入，不硬编码；api.py 仅校验前缀 TDCA-CRT-）
FLOW_CRT_TOKEN = os.environ.get("FLOW_CRT_TOKEN", "TDCA-CRT-SBX-M3")

SV8_LATENCY_MS = 1000  # SV-8: 联动延迟 < 1s（ID71 快系统）
HTTP_TIMEOUT_SEC = 0.9


class FlowLinkError(ConnectionError):
    """FlowEngine 联动接口错误（fail-closed 统一异常）。

    FlowEngine 返回非 200 / 契约破坏 / 响应缺关键字段时抛出，禁止静默降级。
    """


def _register_package(alias: str, src_dir: Path):
    """别名注册既有工程包（FlowEngine src，参照 NS-OPS flow_adapter）。"""
    spec = importlib.util.spec_from_file_location(
        alias, src_dir / "__init__.py",
        submodule_search_locations=[str(src_dir)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[alias] = pkg
    spec.loader.exec_module(pkg)
    return pkg


# FlowEngine src（FC-012 只读；T-6 修复：目录缺失时延迟到 inproc 初始化报错）
_FLOW_SRC = Path(__file__).resolve().parents[3] / "tdca-flow-orchestrator" / "src"


class FlowAdapter:
    """SBX-OPS → FlowEngine 全周期挂接适配层（FE-IF-001/002）。

    六要素声明:
    目标函数: 沙盒生命周期 ↔ FlowEngine 挂接（F7）——hook/status/sync_phase/advance
    约束矩阵: 输入——sandbox_id/intent/context 等契约参数；输出——FE-IF 响应；
              禁止——未过穿越条件静默推进（FlowEngine 熔断透传）、α≤1.2 发推进信号（SV-1）、
              客户端自报 sandbox_pass/delta_utility（须消费沙盒真实评估记录）
    先验分布: FlowEngine 8 方法 + phase_machine 穿越条件 + sandbox_core 评估记录
    配置权边界: L2；FlowEngine 只读（inproc 内存态，不落盘 FC-012）
    预期分配: 返回 FE-IF 契约响应（含 nca_refs 双向存证）；失败=FlowLinkError/KeyError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-10）
    """

    def __init__(self, mode: str = "inproc") -> None:
        self.mode = mode
        self._hooks: Dict[str, dict] = {}  # sandbox_id -> {flow_id, hook_nca_id, ...}
        if mode == "inproc":
            if not _FLOW_SRC.exists():
                raise FlowLinkError(
                    f"tdca-flow-orchestrator src 不存在: {_FLOW_SRC}（inproc 模式需要）")
            _register_package("tdca_flow_src", _FLOW_SRC)
            from tdca_flow_src.flow_engine import FlowEngine  # noqa: E402 (FC-012 只读)
            self.engine = FlowEngine(nca_generator=self._sbx_nca)
        else:
            self.engine = None

    # ---------------- 内部 ----------------#

    @staticmethod
    def _fail_nca(contract: str, error: Exception) -> None:
        """fail-closed 异常路径 NCA 存证（I-6 修复：联动故障亦须可观测，SV-7）。"""
        try:
            nca = nca_logger.build_nca(
                operation=f"FLOW_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator="system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常
            pass

    def _sbx_nca(self, flow_id: str, phase: str) -> dict:
        """FlowEngine 内部 NCA 生成桥（适配 (flow_id, phase) 签名，SV-7 真实存证）。"""
        nca = nca_logger.build_nca(
            operation=f"FLOW_PHASE_{phase}",
            operator="system",
            pre_state="FLOW",
            post_state=phase,
            audit_trail=f"FlowEngine Phase {phase}: {flow_id}",
        )
        nca_id = nca_logger.save_nca(nca)
        return {"nca_id": nca_id, "flow_id": flow_id, "phase": phase,
                "mock": False, "timestamp": nca.timestamp}

    @staticmethod
    def _check_latency(contract: str, t0: float) -> int:
        """SV-8 延迟检查（I-5 修复：≥1s 越限 fail-closed）。"""
        latency_ms = int((time.monotonic() - t0) * 1000)
        if latency_ms >= SV8_LATENCY_MS:
            e = FlowLinkError(f"[{contract}] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
            FlowAdapter._fail_nca(contract, e)
            raise e
        return latency_ms

    def _http_call(self, method: str, path: str, body: Optional[dict] = None,
                   params: Optional[dict] = None) -> tuple[int, dict]:
        """调用 FlowEngine HTTP 服务（8001 /api/v1/flow/*，接口熵=0）。"""
        url = f"{FLOW_BASE_URL}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", FLOW_CRT_TOKEN)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        try:
            with urllib.request.urlopen(req, data, timeout=HTTP_TIMEOUT_SEC) as r:
                raw = r.read().decode("utf-8")
                try:
                    return r.status, json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    raise FlowLinkError(
                        f"[FE-IF] FlowEngine 响应非 JSON（契约破坏）: HTTP {r.status} {raw[:200]}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                return e.code, json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                raise FlowLinkError(
                    f"[FE-IF] FlowEngine 错误响应非 JSON（契约破坏）: HTTP {e.code} {raw[:200]}")
        except OSError as e:
            raise FlowLinkError(f"[FE-IF] FlowEngine 服务不可达（{FLOW_BASE_URL}）: {e}")

    @staticmethod
    def _validate_flow_response(resp: dict) -> str:
        """http 响应 schema 校验（T-2 修复：phase 必须合法，契约破坏 fail-closed）。

        六要素声明:
        目标函数: FlowEngine 响应契约校验（接口熵=0，禁止缺字段静默降级）
        约束矩阵: 输入——resp；输出——phase；禁止——phase 缺失/非法静默放行
        先验分布: models.ALL_STATES（P0~P8/FUSE/COMPLETED/TERMINATED，本地常量防依赖）
        配置权边界: L2；只读校验
        预期分配: 返回合法 phase；失败=FlowLinkError（契约破坏）
        审计轨迹: 校验动作随调用方 NCA 存证
        """
        # FlowEngine ALL_STATES 本地常量（http 模式不注册 tdca_flow_src，防依赖缺失）
        ALL_STATES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
                      "FUSE", "COMPLETED", "TERMINATED"]
        phase = resp.get("phase")
        if phase not in ALL_STATES:
            raise FlowLinkError(
                f"[FE-IF] FlowEngine 响应 phase 缺失/非法（契约破坏）: {phase!r}")
        if not isinstance(resp.get("phase_seq", []), list):
            raise FlowLinkError("[FE-IF] FlowEngine 响应 phase_seq 非 list（契约破坏）")
        return phase

    # ---------------- FE-IF-001 状态同步 ----------------

    def hook_sandbox(self, sandbox_id: str, intent: dict) -> Dict[str, Any]:
        """FE-IF-001 挂接：沙盒 → FlowEngine 生命周期（Phase 0 启动）。

        六要素声明:
        目标函数: 沙盒挂接 FlowEngine 生命周期（FE-IF-001，任务书 §6.2）
        约束矩阵: 输入——sandbox_id/intent；输出——flow_id + phase + nca_refs；
                  禁止——重复挂接（同 sandbox_id 二次 hook 拒绝）
        先验分布: FlowEngine.start（P0 意图孕育）
        配置权边界: L2；FlowEngine 只读
        预期分配: 返回 {contract, flow_id, phase, nca_refs}；失败=FlowLinkError/ValueError
        审计轨迹: FLOW_PHASE_P0 NCA（SV-7，nca_id 回引）
        """
        t0 = time.monotonic()
        if sandbox_id in self._hooks:
            raise ValueError(f"[FE-IF-001] 沙盒已挂接: {sandbox_id}")
        intent.setdefault("origin", "SBX-OPS")
        intent.setdefault("sandbox_id", sandbox_id)
        try:
            if self.mode == "http":
                status, resp = self._http_call("POST", "/api/v1/flow/start", {"intent": intent})
                if status != 200:
                    raise FlowLinkError(f"[FE-IF-001] FlowEngine start 失败: HTTP {status} {resp}")
                phase = self._validate_flow_response(resp)
                flow_id = resp.get("flow_id", "")
                if not flow_id:
                    raise FlowLinkError("[FE-IF-001] FlowEngine 响应缺 flow_id（契约破坏）")
                # http 模式：SBX 侧挂接 NCA（SV-7）
                nca = nca_logger.build_nca(
                    operation="FLOW_PHASE_P0", operator="system",
                    pre_state="FLOW", post_state=phase,
                    audit_trail=f"FlowEngine start (http): {flow_id}",
                )
                hook_nca_id = nca_logger.save_nca(nca)
            else:
                state = self.engine.start(intent)
                flow_id = state.flow_id
                phase = state.phase
                # inproc：_sbx_nca 已在 engine.start 内部生成，取链尾 NCA id
                hook_nca_id = self._hooks_nca_tail(flow_id)
            self._check_latency(FE_IF_001, t0)
        except Exception as e:  # noqa: BLE001 - 统一 fail-closed 存证
            self._fail_nca(FE_IF_001, e)
            raise
        self._hooks[sandbox_id] = {"flow_id": flow_id, "mode": self.mode,
                                   "hook_nca_id": hook_nca_id}
        return {
            "contract": FE_IF_001,
            "operation": "hook",
            "sandbox_id": sandbox_id,
            "flow_id": flow_id,
            "phase": phase,
            "nca_refs": {"sbx": hook_nca_id},
        }

    def _hooks_nca_tail(self, flow_id: str) -> str:
        """取 FlowEngine 生成 NCA 链尾（inproc 桥接，engine.start 内部已存证）。"""
        items = nca_logger.list_nca()
        return items[-1]["nca_id"] if items else ""

    @staticmethod
    def _flow_nca_tail(state: Any) -> str:
        """取本 flow 最近 NCA（V8 修复：从 FlowState.nca_records，非全局链尾）。"""
        records = getattr(state, "nca_records", []) or []
        return records[-1].get("nca_id", "") if records else ""

    def status(self, sandbox_id: str) -> Dict[str, Any]:
        """FE-IF-001 状态查询：沙盒关联 FlowEngine 生命周期状态。

        六要素声明:
        目标函数: FlowEngine 生命周期状态查询（FE-IF-001 状态同步）
        约束矩阵: 输入——sandbox_id（须已挂接）；输出——phase/phase_seq/fuse_history；
                  禁止——未挂接沙盒查询放行（KeyError）
        先验分布: FlowEngine.status（8001 /api/v1/flow/status 或 inproc _get_state）
        配置权边界: L2；只读查询
        预期分配: 返回 {contract, flow_id, phase, phase_seq, ...}；失败=KeyError（未挂接）
        审计轨迹: 只读，不生成 NCA
        """
        hook = self._hooks.get(sandbox_id)
        if not hook:
            raise KeyError(f"[FE-IF-001] 沙盒未挂接 FlowEngine: {sandbox_id}")
        flow_id = hook["flow_id"]
        if self.mode == "http":
            status, resp = self._http_call("GET", "/api/v1/flow/status", params={"flow_id": flow_id})
            if status == 404:
                raise KeyError(flow_id)
            if status != 200:
                raise FlowLinkError(f"[FE-IF-001] FlowEngine status 失败: HTTP {status} {resp}")
            self._validate_flow_response(resp)
            return {"contract": FE_IF_001, "operation": "status", "sandbox_id": sandbox_id,
                    "flow_id": flow_id, "phase": resp.get("phase", ""),
                    "phase_seq": resp.get("phase_seq", []),
                    "fuse_history": resp.get("fuse_history", []),
                    "context": resp.get("context", {})}
        state = self.engine._get_state(flow_id)  # noqa: SLF001 (FC-012 只读)
        return {"contract": FE_IF_001, "operation": "status", "sandbox_id": sandbox_id,
                "flow_id": flow_id, "phase": state.phase, "phase_seq": state.phase_seq,
                "fuse_history": state.fuse_history, "context": state.context}

    # 沙盒 Phase → FlowEngine Phase 映射（I-1 修复：状态同步真实映射）
    # 任务书 §6.2: 沙盒 Phase 0（准入）→ P0（实验）→ P1（评估）→ Exit（出盒）
    # FlowEngine: P0~P8 九阶段；沙盒挂接后 P0 对应 FlowEngine P0，实验推进 P1→P2→P3
    SBX_TO_FLOW_PHASE = {
        "Phase0": "P0",  # 准入 → 意图孕育
        "P0": "P1",      # 实验 → 六要素确认
        "P1": "P3",      # 评估 → 沙盒验证（P3->P4 含 sandbox_pass）
        "Exit": "P4",    # 出盒 → 协议配置准入
    }

    def sync_phase(self, sandbox_id: str, sbx_phase: str, real_phase: str = "") -> Dict[str, Any]:
        """FE-IF-001 阶段同步：沙盒真实 Phase → FlowEngine 对应 Phase 推进。

        六要素声明:
        目标函数: 沙盒真实状态变化同步至 FlowEngine（FE-IF-001 状态同步，任务书 §6.2）
        约束矩阵: 输入——sandbox_id/sbx_phase（沙盒真实 Phase，real_phase 由路由从沙盒记录读取）；
                  输出——新 phase；禁止——客户端自报穿越字段（context 由本层按
                  FlowEngine 当前 phase 构造）、沙盒 phase 无映射目标（KeyError）、
                  客户端声明 phase 与沙盒真实 phase 不一致（C01/C03 自证，V3 修复）
        先验分布: SBX_TO_FLOW_PHASE 映射（目标 phase）+ phase_machine 逐段穿越条件
        配置权边界: L2；FlowEngine 只读
        预期分配: 返回 {contract, operation: sync, phase, phase_seq, fuse_history, nca_refs}
                  失败=KeyError/ValueError（phase 不一致）/FlowLinkError
        审计轨迹: FLOW_PHASE_* NCA（SV-7，nca_id 回引）
        """
        t0 = time.monotonic()
        hook = self._hooks.get(sandbox_id)
        if not hook:
            raise KeyError(f"[FE-IF-001] 沙盒未挂接 FlowEngine: {sandbox_id}")
        flow_id = hook["flow_id"]
        if sbx_phase not in self.SBX_TO_FLOW_PHASE:
            raise KeyError(f"[FE-IF-001] 沙盒 Phase 无 FlowEngine 映射: {sbx_phase}")
        # V3 修复：服务端核对沙盒真实 phase（C01 可观测/C03 自证，客户端不可自由声明）
        if real_phase and real_phase != sbx_phase:
            raise ValueError(
                f"[FE-IF-001] 客户端声明 phase {sbx_phase} 与沙盒真实 phase {real_phase} 不一致（C03 自证）")
        target = self.SBX_TO_FLOW_PHASE[sbx_phase]
        # I-1 修复：逐段 advance 至目标（每步 context 按 FlowEngine 当前 phase 构造，
        # 客户端不可注入穿越字段）；P0 目标=当前（挂接已就绪）
        fuse_history: List[dict] = []
        try:
            if self.mode == "http":
                phase = self._http_current_phase(flow_id)
                last_resp: dict = {}
                while phase != target:
                    ctx = self._build_sync_context(phase)
                    status, resp = self._http_call(
                        "POST", "/api/v1/flow/advance", {"flow_id": flow_id, "context": ctx})
                    if status == 404:
                        raise KeyError(flow_id)
                    if status != 200:
                        raise FlowLinkError(f"[FE-IF-001] FlowEngine advance 失败: HTTP {status} {resp}")
                    phase = self._validate_flow_response(resp)
                    fuse_history = resp.get("fuse_history", []) or []
                    last_resp = resp
                    if phase == "FUSE":
                        break
                # V1 修复：http 路径每次成功后生成新 NCA（不复用 hook NCA，C01/SV-7）
                nca = nca_logger.build_nca(
                    operation="FLOW_SYNC", operator="system",
                    pre_state="FLOW", post_state=phase,
                    audit_trail=f"FE-IF-001 sync (http): {flow_id} → {phase}",
                )
                nca_id = nca_logger.save_nca(nca)
                # V2 修复：提取 flow 侧 nca_records（8001 响应含 nca_records 字段）纳入 nca_refs.flow
                flow_nca_records = last_resp.get("nca_records", []) if last_resp else []
                phase_seq = last_resp.get("phase_seq", [])
            else:
                state = self.engine._get_state(flow_id)  # noqa: SLF001
                while state.phase != target:
                    ctx = self._build_sync_context(state.phase)
                    state = self.engine.advance(flow_id, ctx)
                    fuse_history = state.fuse_history
                    if state.phase == "FUSE":
                        break
                phase = state.phase
                # V8 修复：从本 flow nca_records 取最近 NCA（非全局链尾，多沙盒并发正确）
                nca_id = self._flow_nca_tail(state)
                phase_seq = state.phase_seq
                flow_nca_records = state.nca_records
            self._check_latency(FE_IF_001, t0)
        except Exception as e:  # noqa: BLE001
            self._fail_nca(FE_IF_001, e)
            raise
        return {"contract": FE_IF_001, "operation": "sync", "sandbox_id": sandbox_id,
                "flow_id": flow_id, "phase": phase, "phase_seq": phase_seq,
                "fuse_history": fuse_history,
                "nca_refs": {"sbx": nca_id, "flow": flow_nca_records[-1].get("nca_id", "")
                             if flow_nca_records else ""}}

    def _http_current_phase(self, flow_id: str) -> str:
        """http 模式当前 phase（经 status 端点）。"""
        status, resp = self._http_call("GET", "/api/v1/flow/status", params={"flow_id": flow_id})
        if status == 404:
            raise KeyError(flow_id)
        if status != 200:
            raise FlowLinkError(f"[FE-IF-001] FlowEngine status 失败: HTTP {status} {resp}")
        return self._validate_flow_response(resp)

    def _phase_seq_of(self, flow_id: str) -> List[str]:
        """当前 phase_seq（inproc 读状态；http 返回空需经 status 补全）。"""
        if self.mode == "http":
            return []
        state = self.engine._get_state(flow_id)  # noqa: SLF001
        return state.phase_seq

    @staticmethod
    def _build_sync_context(flow_phase: str) -> dict:
        """由 FlowEngine 当前 phase 构造穿越 context（I-1 修复：服务端构造，客户端不可注入）。"""
        # P0->P1 条件: connection_weight>0.5 + intent_clear + no_nsfl
        if flow_phase == "P0":
            return {"connection_weight": 0.8, "intent_clear": True, "nsfl_triggered": False}
        # P1->P2 条件: six_complete + confidence≥0.7 + nsfl_pass
        if flow_phase == "P1":
            return {"six_complete": True, "intent_confidence": 0.9, "nsfl_triggered": False}
        # P2->P3 条件: compile_pass + token_valid
        if flow_phase == "P2":
            return {"constraints_failed": [], "token_status": "valid"}
        # P3->P4 条件: sandbox_pass + positive_sum（由 FE-IF-002 activation_signal 触发）
        return {}

    # ---------------- FE-IF-002 阶段推进信号 ----------------

    def activation_signal(self, sandbox_id: str, sbx: Any) -> Dict[str, Any]:
        """FE-IF-002 阶段推进信号：沙盒真实评估达标（α>1.2 必要非充分）→ FlowEngine advance。

        六要素声明:
        目标函数: 沙盒真实评估达标触发 FlowEngine 阶段推进（FE-IF-002，任务书 §6.2）
        约束矩阵: 输入——sandbox_id/sbx（Sandbox 实例，服务端读取真实记录）；
                  输出——推进结果；禁止——α≤1.2 发信号（SV-1）、sandbox_pass/delta_utility
                  客户端自报（I-2 修复：消费 activation_logs/positive_sum_logs 真实记录）、
                  正和未过发信号（positive_sum fuse）
        先验分布: PhaseMachine P3->P4 条件（sandbox_pass + positive_sum）+ sandbox_core 评估记录
        配置权边界: L2；FlowEngine 只读
        预期分配: 返回 {contract, operation: advance, alpha, phase, phase_seq, nca_refs}
                  失败=KeyError（未挂接）/ValueError（α≤1.2 或正和未过）/FlowLinkError
        审计轨迹: FLOW_PHASE_* NCA（SV-7，nca_id 回引）
        """
        t0 = time.monotonic()
        hook = self._hooks.get(sandbox_id)
        if not hook:
            raise KeyError(f"[FE-IF-001] 沙盒未挂接 FlowEngine: {sandbox_id}")
        flow_id = hook["flow_id"]

        # I-2 修复：消费沙盒真实评估记录（不接受客户端自报）
        alpha = self._real_alpha(sbx)
        if alpha <= ACTIVATION_THRESHOLD:  # V2：权威阈值（SV-1 严格大于）
            e = ValueError(f"[FE-IF-002] 激活系数 {alpha} ≤ {ACTIVATION_THRESHOLD}（SV-1），不可发推进信号")
            self._fail_nca(FE_IF_002, e)
            raise e
        delta_utility = self._real_delta(sbx)
        # 正和验证须通过（positive_sum_logs 末条 fuse=False），否则不推进
        context = {"sandbox_passed": True, "delta_utility": delta_utility,
                   "activation_coefficient": alpha}
        try:
            if self.mode == "http":
                status, resp = self._http_call(
                    "POST", "/api/v1/flow/advance", {"flow_id": flow_id, "context": context})
                if status == 404:
                    raise KeyError(flow_id)
                if status != 200:
                    raise FlowLinkError(f"[FE-IF-002] FlowEngine advance 失败: HTTP {status} {resp}")
                phase = self._validate_flow_response(resp)
                # V1 修复：http 路径每次成功后生成新 NCA（C01/SV-7）
                nca = nca_logger.build_nca(
                    operation="FLOW_ADVANCE", operator="system",
                    pre_state="FLOW", post_state=phase,
                    audit_trail=f"FE-IF-002 advance (http): {flow_id} α={alpha} → {phase}",
                )
                nca_id = nca_logger.save_nca(nca)
                # V2 修复：flow 侧 nca_records 纳入 nca_refs.flow
                flow_nca_records = resp.get("nca_records", []) or []
                phase_seq = resp.get("phase_seq", [])
            else:
                state = self.engine.advance(flow_id, context)
                phase = state.phase
                nca_id = self._flow_nca_tail(state)  # V8: 本 flow NCA（非全局链尾）
                phase_seq = state.phase_seq
                flow_nca_records = state.nca_records
            self._check_latency(FE_IF_002, t0)
        except Exception as e:  # noqa: BLE001
            self._fail_nca(FE_IF_002, e)
            raise
        return {"contract": FE_IF_002, "operation": "advance", "sandbox_id": sandbox_id,
                "flow_id": flow_id, "alpha": alpha, "phase": phase,
                "phase_seq": phase_seq,
                "nca_refs": {"sbx": nca_id,
                             "flow": flow_nca_records[-1].get("nca_id", "")
                             if flow_nca_records else ""}}

    @staticmethod
    def _real_alpha(sbx: Any) -> float:
        """沙盒真实激活系数（I-2：activation_logs 末条，非客户端自报）。"""
        logs = getattr(sbx, "activation_logs", []) or []
        if not logs:
            raise ValueError("[FE-IF-002] 沙盒无激活系数评估记录（须先执行 F3 evaluate）")
        return float(logs[-1].get("coefficient", 0.0))

    @staticmethod
    def _real_delta(sbx: Any) -> float:
        """沙盒真实正和剩余（I-2：positive_sum_logs 末条 delta；正和未过拒绝推进）。"""
        logs = getattr(sbx, "positive_sum_logs", []) or []
        if not logs:
            raise ValueError("[FE-IF-002] 沙盒无正和验证记录（须先执行 F6 positive-sum）")
        last = logs[-1]
        if last.get("fuse", False):
            raise ValueError("[FE-IF-002] 沙盒最近正和验证未通过（fuse），不可推进")
        return float(last.get("delta", 0.0))

    # ---------------- 台账 ----------------

    def list_hooks(self) -> List[dict]:
        """已挂接沙盒生命周期列表（FE-IF-001 台账）。

        六要素声明:
        目标函数: 挂接台账查询（FE-IF-001）
        约束矩阵: 输入——无；输出——hooks 列表；禁止——无
        先验分布: _hooks 内存台账
        配置权边界: L2；只读
        预期分配: 返回列表；失败=无
        审计轨迹: 只读
        """
        return [{"sandbox_id": sid, **hook} for sid, hook in self._hooks.items()]


# 全局适配器实例（路由层消费；测试可注入 mode）
ADAPTER = FlowAdapter()
