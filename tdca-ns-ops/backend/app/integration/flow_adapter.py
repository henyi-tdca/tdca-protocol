# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 冻结 + M3 增量：HTTP 模式）
# 目标函数:     NS-OPS → FlowEngine 全周期挂接（Phase 0 前置，M2-1）
# 约束矩阵:     FC-NS-OPS-001 接口链（NS-OPS → FlowEngine Phase 0 → PhaseMachine）
#               + 快慢分离（NS-011：调整确定（慢）→ FlowEngine 生命周期（快））
#               + 只读既有工程（tdca-flow-orchestrator 不改动）
# 先验分布:     tdca-flow-orchestrator/src/flow_engine.py（8 方法接口）
# 配置权边界:    L2 层；适配器仅桥接，不代行人类裁决
# 预期分配:     调整确定后创建 FlowEngine 生命周期 + 按 Phase 推进；失败=接口异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2-1 全周期挂接：NS-OPS → FlowEngine（Phase 0 前置）适配器。

制度锚定: FC-NS-OPS-001 接口链 | NS-011 快慢分离 | SPDX-License-Identifier: TDCA-Internal

挂接方式: 直接 import tdca-flow-orchestrator/src（进程内桥接，M2 原型）；
         生产可切换为 HTTP 调用（port 8001 /api/v1/flow/*），接口熵=0。
"""

from __future__ import annotations

import sys

# 复用 tdca-flow-orchestrator（只读引用，不改动）
# 参照 edu_simulator 既有复用模式（_register_package 别名注册，支持相对导入）
from pathlib import Path
import importlib.util

_WS = Path(__file__).resolve().parents[4]  # global-workspace
_FLOW_SRC = _WS / "tdca-flow-orchestrator" / "src"


def _register_package(alias: str, src_dir: Path):
    spec = importlib.util.spec_from_file_location(
        alias, src_dir / "__init__.py",
        submodule_search_locations=[str(src_dir)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[alias] = pkg
    spec.loader.exec_module(pkg)
    return pkg


_flow_pkg = _register_package("tdca_flow_src", _FLOW_SRC)
from tdca_flow_src.flow_engine import FlowEngine  # noqa: E402  (既有工程，只读)

from ..store import generate_nca, hash_text  # noqa: E402


class FlowAdapter:
    """NS-OPS → FlowEngine 全周期挂接适配器。

    六要素声明:
    目标函数: 将一次已确定的负空间调整（冻结态）挂接为 FlowEngine 生命周期（Phase 0 前置）
    约束矩阵: 输入——adjustment_id + 确定记录；输出——flow_id + 挂接 NCA；
              禁止——未确定（冻结）的调整不可挂接、不代行人类签批
    先验分布: flow_engine.FlowEngine 接口 + M1 调整权状态机（determination 冻结态）
    配置权边界: L2；适配器只桥接，不修改 FlowEngine/PhaseMachine 行为
    预期分配: 返回 flow_id + 首 NCA；失败=KeyError/ValueError（未确定）
    审计轨迹: 挂接 NCA（Flow-Hook）+ 每 Phase 推进 NCA
    """

    def __init__(self, mode: str = "inproc") -> None:
        """初始化 FlowAdapter。

        M3-2：mode 支持 inproc（默认，进程内桥接）/ http（调用既有 8001 服务，接口熵=0）。
        HTTP 模式不加载 FlowEngine（走既有服务），仅记录 NS-OPS 侧台账。
        """
        self.mode = mode
        self._hooks: dict[str, dict] = {}  # flow_id -> {adjustment_id, constraint_id, ...}
        if mode == "inproc":
            # N2 修复：注入 NS-OPS NCA 生成器（消除 FlowEngine 内部 mock 占位存证，BV-5）
            self.engine = FlowEngine(nca_generator=self._nsops_nca)
        else:
            self.engine = None

    # ---- HTTP 模式（M3-2：调用既有 FlowEngine 服务 port 8001，不改既有工程） ----

    @staticmethod
    def _http_call(method: str, path: str, body: dict | None = None,
                   params: dict | None = None) -> tuple[int, dict]:
        """调用既有 FlowEngine HTTP 服务（8001 /api/v1/flow/*）。

        六要素声明:
        目标函数: 桥接调用既有 FlowEngine HTTP 服务（接口熵=0，ID82）
        约束矩阵: 输入——method/path/body/params 契约；输出——(status, json)；
                  禁止——非 JSON 响应抛未处理异常（容错降级）、绕过鉴权
        先验分布: tdca-flow-orchestrator/src/api.py（8001 接口契约）
        配置权边界: L2；仅调用既有服务，不修改
        预期分配: 返回 (status, parsed_json)；失败=ConnectionError（服务不可达）
        审计轨迹: 调用结果由调用方 NCA 存证
        """
        import json
        import urllib.error
        import urllib.request
        import urllib.parse

        url = f"http://127.0.0.1:8001{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "TDCA-CRT-NSOPS-M3")
        data = json.dumps(body).encode() if body else None
        try:
            with urllib.request.urlopen(req, data) as r:
                raw = r.read().decode(errors="replace")
                try:
                    return r.status, json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    # REV-T1：2xx 非 JSON 响应容错降级（接口契约稳定）
                    return r.status, {"raw": raw[:200]}
        except urllib.error.HTTPError as e:
            # REV-N4：非 JSON 响应体（如 502 HTML）容错降级
            raw = e.read().decode(errors="replace")
            try:
                return e.code, json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return e.code, {"raw": raw[:200]}
        except OSError as e:
            raise ConnectionError(f"[M3-2] FlowEngine HTTP 服务不可达（8001）: {e}")

    @staticmethod
    def _nsops_nca(flow_id: str, phase: str) -> dict:
        """FlowEngine 内部 NCA 生成桥（适配 (flow_id, phase) 签名）。

        替代既有工程降级 mock 分支——存证走 NS-OPS 真实 NCA 引擎（BV-5）。
        """
        nca = generate_nca(
            "TDCA-FC-NS-OPS-001", f"Flow-Phase-{phase}",
            f"生命周期 Phase {phase}: {flow_id}",
            hash_text(flow_id), hash_text(phase),
            nca_type="AUDIT",
            human_signature_required=False,
        )
        return {
            "nca_id": nca["NCA-ID"],
            "flow_id": flow_id,
            "phase": phase,
            "mock": False,
            "timestamp": nca["Timestamp"],
        }

    # ---- 挂接 ----

    def hook_adjustment(
        self,
        adjustment_id: str,
        constraint_id: str,
        final_version: int,
        effective_date: str,
        trigger: str = "",
        human_signature: str = "",
    ) -> dict:
        """将已确定的调整挂接为 FlowEngine 生命周期（Phase 0 启动）。

        快慢分离（NS-011）：调整确定=慢系统人类产物 → 挂接=快系统自动推进。
        M3-2：mode=http 时调用既有 FlowEngine 服务（8001 /api/v1/flow/start）。
        """
        intent = {
            "type": "ns_ops_adjustment",
            "adjustment_id": adjustment_id,
            "constraint_id": constraint_id,
            "final_version": final_version,
            "effective_date": effective_date,
            "trigger": trigger,
            "origin": "NS-OPS",
        }
        if self.mode == "http":
            status, resp = self._http_call("POST", "/api/v1/flow/start", {"intent": intent})
            # REV-T4：接受 2xx（200-299）为成功（既有服务契约可能返回 201 创建）
            if not (200 <= status < 300):
                raise ConnectionError(f"[M3-2] FlowEngine start 失败: HTTP {status} {resp}")
            flow_id = resp.get("flow_id", "")
            # REV-N-1：2xx 但响应缺 flow_id（契约破坏）→ 显式失败，不静默挂接空台账
            if not flow_id:
                raise ConnectionError(
                    f"[M3-2] FlowEngine start 响应缺少 flow_id（契约破坏）: {resp}")
            state_phase = resp.get("phase", "P0")
        else:
            # FlowEngine.start 创建 P0 意图孕育状态
            state = self.engine.start(intent)
            flow_id = state.flow_id
            state_phase = state.phase
        self._hooks[flow_id] = {
            "adjustment_id": adjustment_id,
            "constraint_id": constraint_id,
            "final_version": final_version,
            "effective_date": effective_date,
            "trigger": trigger,
            "mode": self.mode,
        }
        # 挂接 NCA 存证（BV-5）
        nca = generate_nca(
            "TDCA-FC-NS-OPS-001", "Flow-Hook",
            f"全周期挂接[{self.mode}]: 调整 {adjustment_id} → FlowEngine {flow_id}（Phase 0）",
            hash_text(adjustment_id),
            hash_text(f"{flow_id}|{final_version}|{effective_date}"),
            nca_type="AUDIT",
            signer=human_signature or None,
        )
        return {"flow_id": flow_id, "phase": state_phase, "nca_ref": nca["NCA-ID"], "mode": self.mode}

    # ---- 生命周期推进 ----

    def advance(self, flow_id: str, context: dict, human_signature: str = "") -> dict:
        """推进 FlowEngine 到下一 Phase（含穿越条件检查 + 熔断）。

        注（REV-#5）：human_signature 预留为推进 NCA 签名记录（M3 接身份时启用）；
        当前阶段 P0→P1 推进由路由提供上下文（intent_clear 等），scope 限定原型。
        REV-#6：HTTP 模式调用既有服务 /api/v1/flow/advance。
        """
        if self.mode == "http":
            status, resp = self._http_call(
                "POST", "/api/v1/flow/advance",
                {"flow_id": flow_id, "context": context})
            # REV-N1：404 → KeyError（与 inproc 对齐，路由层 404）；其余 → ConnectionError
            if status == 404:
                raise KeyError(flow_id)
            if status != 200:
                raise ConnectionError(f"[M3-2] FlowEngine advance 失败: HTTP {status} {resp}")
            phase = resp.get("phase", "")
            phase_seq = resp.get("phase_seq", [])
            nca = generate_nca(
                "TDCA-FC-NS-OPS-001", "Flow-Advance",
                f"生命周期推进[http]: {flow_id} → {phase}",
                hash_text(flow_id), hash_text(f"{phase}|{','.join(phase_seq)}"),
                nca_type="AUDIT", signer=human_signature or None,
            )
            return {
                "flow_id": flow_id, "phase": phase, "phase_seq": phase_seq,
                "fuse_history": resp.get("fuse_history", []),
                "context": resp.get("context", {}),
                "nca_ref": nca["NCA-ID"], "mode": "http",
            }
        try:
            state = self.engine.advance(flow_id, context)
        except KeyError as e:
            raise KeyError(str(e))
        # 推进 NCA 存证（BV-5），签名者记录（若提供）
        nca = generate_nca(
            "TDCA-FC-NS-OPS-001", "Flow-Advance",
            f"生命周期推进: {flow_id} → {state.phase}",
            hash_text(flow_id), hash_text(f"{state.phase}|{','.join(state.phase_seq)}"),
            nca_type="AUDIT", signer=human_signature or None,
        )
        return {
            "flow_id": flow_id,
            "phase": state.phase,
            "phase_seq": state.phase_seq,
            "fuse_history": state.fuse_history,
            "context": state.context,
            "nca_ref": nca["NCA-ID"],
        }

    def status(self, flow_id: str) -> dict:
        """查询生命周期状态（Phase 0 挂接台账）。REV-#6：HTTP 模式走既有服务。"""
        if self.mode == "http":
            status, resp = self._http_call("GET", "/api/v1/flow/status",
                                           params={"flow_id": flow_id})
            # REV-N1：404 → KeyError（与 inproc 对齐）
            if status == 404:
                raise KeyError(flow_id)
            if status != 200:
                raise ConnectionError(f"[M3-2] FlowEngine status 失败: HTTP {status} {resp}")
            return {
                "flow_id": flow_id,
                "phase": resp.get("phase", ""),
                "phase_seq": resp.get("phase_seq", []),
                "hook": self._hooks.get(flow_id, {}),
                "fuse_history": resp.get("fuse_history", []),
                "nca_records": resp.get("nca_records", []),
                "mode": "http",
            }
        try:
            state = self.engine._get_state(flow_id)
        except KeyError as e:
            raise KeyError(str(e))
        return {
            "flow_id": flow_id,
            "phase": state.phase,
            "phase_seq": state.phase_seq,
            "hook": self._hooks.get(flow_id, {}),
            "fuse_history": state.fuse_history,
            "nca_records": state.nca_records,
        }

    def trajectory(self, flow_id: str) -> list:
        """全流程 NCA 轨迹。REV-I1：HTTP 模式调用既有服务 /api/v1/flow/trajectory。"""
        if self.mode == "http":
            status, resp = self._http_call(
                "GET", "/api/v1/flow/trajectory",
                params={"flow_id": flow_id})
            if status == 404:
                raise KeyError(flow_id)
            if status != 200:
                raise ConnectionError(f"[M3-2] FlowEngine trajectory 失败: HTTP {status} {resp}")
            return resp if isinstance(resp, list) else []
        return self.engine.trajectory(flow_id)

    # ---- 台账 ----

    def list_hooks(self) -> list[dict]:
        """已挂接生命周期列表。"""
        return [
            {"flow_id": fid, **hook} for fid, hook in self._hooks.items()
        ]


# 全局适配器实例
FLOW = FlowAdapter()
