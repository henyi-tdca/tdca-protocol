# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动，CB-IF 功能组）
# 目标函数:     M3-5 数字人民币 MOU 锚定适配层——CB-IF-001 税收数据实时同步（模拟过渡）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 + SV-8 + 接口熵=0（ID82）
#               + tdca-fos/tdca_adapters 只读引用（mou_pipeline/dcep_adapter，不改写）
#               + ID79（MOU=Tax_in+Tax_out；30 天≥28 天验证窗口 + 连续无税收熔断归零
#                 ——窗口判定由出盒评估网关 TP 层（inference_engine 规则 4）强制，
#                 M3-5 锚定链路不重复实现，模拟过渡语义；M4 真实对接时桥接窗口判定）
#               + ID92（模拟显式标记 SIMULATED-TAX-AUTHORITY，真实锚定永不）
#               + 模拟不得伪装真实（NSFL 经济负空间）
# 先验分布:     mou_pipeline.py（SimulatedTaxAuthority + MOUPipeline）+ dcep_adapter.py（DCEPAdapter）
#               + tdca-mou-anchor skill（模拟锚定执行）
# 配置权边界:   L2 层；tdca-fos 只读引用；真实锚定永不执行（mou.anchor_real 永不授权）
# 预期分配:     CB-IF-001 anchor（模拟锚定）+ CB-IF-001b mou 查询；失败=契约破坏显式失败
# 审计轨迹:     TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-5 数字人民币 MOU 锚定适配层（CB-IF-001 模拟过渡）。

制度锚定: FC-SBX-OPS-001 / 任务书 §6.1 | SPDX-License-Identifier: TDCA-Internal

CB-IF 契约（审阅确认书 §2.3：IF-008 → CB-IF-001，NC-20260810-001 已登记）:
  - CB-IF-001: MOU 税收锚定（MOUPipeline 模拟过渡，SIMULATED-TAX-AUTHORITY 显式标记）
  - CB-IF-001b: MOU 锚定状态查询（沙盒 MOU 记录）

「模拟过渡期真实锚定永不执行（mou.anchor_real 永不授权）；M4 经人类签批 + 真实数据源就绪后启用（mou.anchor_real 授权）」——ID92 真实性守卫

真实锚定永不执行（ID92）: 模拟过渡期禁止真实锚定（mou.anchor_real 永不授权）；
M4 真实数据源就绪 + 人类签批后启用（授权切换需 DCD 变更）。无税收数据禁止伪造 MOU（NSFL）。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import nca_logger

CB_IF_001 = "CB-IF-001"  # MOU 税收锚定（模拟过渡）
CB_IF_001B = "CB-IF-001b"  # MOU 锚定状态查询

SV8_LATENCY_MS = 1000  # SV-8: 联动延迟 < 1s（ID71 快系统）

# tdca-fos/tdca_adapters（只读引用）
_FOS_DIR = Path(__file__).resolve().parents[3] / "tdca-fos"


class CbdcLinkError(ConnectionError):
    """数字人民币 MOU 锚定联动接口错误（fail-closed 统一异常）。

    锚定管线不可用/校验失败时抛出，禁止静默降级。
    """


def _load_adapters() -> Any:
    """加载 MOU 锚定管线（tdca-fos 只读；不可用时显式失败）。"""
    if not _FOS_DIR.exists():
        raise CbdcLinkError(f"tdca-fos 不存在: {_FOS_DIR}（MOU 锚定管线不可用）")
    if str(_FOS_DIR) not in sys.path:
        sys.path.insert(0, str(_FOS_DIR))
    try:
        from tdca_adapters.mou_pipeline import SimulatedTaxAuthority, MOUPipeline
        from tdca_adapters.dcep_adapter import DCEPAdapter
        return SimulatedTaxAuthority, MOUPipeline, DCEPAdapter
    except ImportError as e:
        raise CbdcLinkError(f"MOU 锚定管线加载失败: {e}") from e


class _SimDcepClient:
    """模拟数字人民币智能合约客户端（锚定管线 DCEPAdapter 依赖）。"""

    def __init__(self) -> None:
        self._anchors: Dict[str, dict] = {}

    def execute_contract(self, contract_type: str, params: dict) -> dict:
        tx_hash = f"TX-SIM-{params.get('transaction_id', '')[:8]}-{int(time.time())}"
        self._anchors[params["transaction_id"]] = params
        return {"tx_hash": tx_hash}

    def query_contract(self, transaction_id: str) -> Optional[dict]:
        return self._anchors.get(transaction_id)


class _DcepNcaBridge:
    """DCEP 合约层 NCA 桥（适配 dcep_adapter 的 nca.generate(type/layer/content) 调用形态）。

    V2：SV-10 双向存证——DCEP 合约层生成独立 NCA（含 simulated 标记，ID92）。
    """

    def __init__(self, adapter: "CbdcAnchor") -> None:
        self._adapter = adapter

    def generate(self, type: str = "ECONOMIC", layer: int = 3,
                 content: Optional[dict] = None) -> dict:
        nca = nca_logger.build_nca(
            operation="CBDC_DCEP_ANCHOR", operator="system",
            pre_state="DCEP-CONTRACT", post_state="ANCHORED",
            audit_trail=f"DCEP 合约锚定 type={type} layer={layer} content={content} simulated=True",
        )
        return {"NCA-ID": nca_logger.save_nca(nca)}


class CbdcAnchor:
    """SBX-OPS → 数字人民币 MOU 锚定适配层（CB-IF-001 模拟过渡）。

    六要素声明:
    目标函数: 沙盒出盒评估时 MOU 税收锚定（任务书 §6.1，CB-IF-001）
    约束矩阵: 输入——sandbox_id/tax_in/tax_out；输出——锚定结果（mou/verified/simulated）；
              禁止——无税收数据伪造 MOU（NSFL）、真实锚定永不执行（ID92）、负税收
    先验分布: MOUPipeline.run（SimulatedTaxAuthority + DCEPAdapter）
    配置权边界: L2；tdca-fos 只读引用；模拟显式标记
    预期分配: 返回 CB-IF 契约响应（含 nca_refs + simulated）；失败=CbdcLinkError/ValueError
    审计轨迹: 每契约调用生成 SBX-OPS 侧 NCA（SV-10）
    """

    def __init__(self) -> None:
        # 惰性加载（import 期不加载 tdca-fos，503 分支可达）
        self._pipeline = None
        self._nca_sbx = None

    @property
    def pipeline(self) -> Any:
        """MOU 锚定管线惰性实例（首次锚定调用时加载）。

        V2 修复：DCEPAdapter 注入 nca_generator（DCEP 合约层亦生成 NCA，SV-10 双向）。
        """
        if self._pipeline is None:
            SimulatedTaxAuthority, MOUPipeline, DCEPAdapter = _load_adapters()
            self._pipeline = MOUPipeline(
                tax_source=SimulatedTaxAuthority(),
                dcep_adapter=DCEPAdapter(
                    dcep_client=_SimDcepClient(),
                    nca_generator=_DcepNcaBridge(self),
                ),
            )
        return self._pipeline

    # ---------------- 内部 ----------------#

    @staticmethod
    def _fail_nca(contract: str, error: Exception) -> None:
        """fail-closed 异常路径 NCA 存证（联动故障亦须可观测，SV-7）。"""
        try:
            nca = nca_logger.build_nca(
                operation=f"CBDC_FAIL_CLOSED_{contract.replace('-', '_')}",
                operator="system",
                pre_state="LINK",
                post_state="ERROR",
                audit_trail=f"{contract} fail-closed: {type(error).__name__}: {error}",
                negative_space_check="FUSE",
            )
            nca_logger.save_nca(nca)
        except Exception:  # noqa: BLE001 - 存证失败不掩盖原始异常
            pass

    def _nca(self, operation: str, pre: str, post: str, audit: str) -> str:
        """SBX 侧 NCA 存证（SV-7，返回 nca_id）。"""
        nca = nca_logger.build_nca(
            operation=operation, operator="system",
            pre_state=pre, post_state=post, audit_trail=audit,
        )
        return nca_logger.save_nca(nca)

    # ---------------- CB-IF-001 MOU 税收锚定 ----------------

    def anchor(self, sandbox_id: str, tax_in: int, tax_out: int,
               transaction_id: str = "") -> Dict[str, Any]:
        """CB-IF-001 MOU 税收锚定（模拟过渡，SIMULATED-TAX-AUTHORITY 显式标记）。

        六要素声明:
        目标函数: 沙盒出盒 MOU 税收锚定（任务书 §6.1，CB-IF-001）
        约束矩阵: 输入——sandbox_id/tax_in/tax_out（≥0）；输出——锚定结果；
                  禁止——负税收、无数据伪造 MOU（NSFL）、真实锚定永不执行（ID92）
        先验分布: MOUPipeline.run（SimulatedTaxAuthority + DCEPAdapter，模拟显式标记）
        配置权边界: L2；tdca-fos 只读；模拟数据不伪装真实
        预期分配: 返回 {contract, mou, contract_tx, verified, simulated, nca_refs}
                  失败=ValueError（参数非法）/CbdcLinkError（管线不可用）
        审计轨迹: CBDC_ANCHOR NCA（含 simulated 标记，SV-10）
        """
        t0 = time.monotonic()
        if tax_in is None or tax_out is None or tax_in < 0 or tax_out < 0:
            e = ValueError("[CB-IF-001] tax_in/tax_out 须为非负整数（无数据禁止伪造 MOU，NSFL）")
            self._fail_nca(CB_IF_001, e)
            raise e
        tid = transaction_id or f"SBX-{sandbox_id[-8:]}-{int(time.time())}"
        try:
            result = self.pipeline.run(tid, tax_in=tax_in, tax_out=tax_out, require_real=False)
            latency_ms = int((time.monotonic() - t0) * 1000)
            if latency_ms >= SV8_LATENCY_MS:
                e = CbdcLinkError(f"[CB-IF-001] 联动延迟 {latency_ms}ms 超 SV-8（<1s）")
                self._fail_nca(CB_IF_001, e)  # #1 修复：SV-8 超时亦存证（C01/SV-7）
                raise e
        except CbdcLinkError as e:
            self._fail_nca(CB_IF_001, e)  # #1 修复：所有 CbdcLinkError 路径统一存证
            raise
        except ValueError as e:
            self._fail_nca(CB_IF_001, e)
            raise CbdcLinkError(f"[CB-IF-001] MOU 锚定管线拒绝: {e}") from e
        except Exception as e:  # noqa: BLE001
            self._fail_nca(CB_IF_001, e)
            raise CbdcLinkError(f"[CB-IF-001] MOU 锚定失败: {e}") from e

        simulated = result.get("simulated")
        # #3 修复（compliance-auditor P1）: simulated 缺省即失败（fail-closed，ID92 不得 fail-open）
        if simulated is None:
            e = CbdcLinkError("[CB-IF-001] 管线结果缺 simulated 标记（ID92 真实性守卫，fail-closed）")
            self._fail_nca(CB_IF_001, e)
            raise e
        simulated = bool(simulated)
        # #2 修复：模拟过渡期硬断言——真实锚定未经授权禁止执行（ID92/AGENT-EXEC-001）
        if not simulated:
            e = CbdcLinkError("[CB-IF-001] 真实锚定未经授权（ID92/AGENT-EXEC-001 §四.3），禁止执行")
            self._fail_nca(CB_IF_001, e)
            raise e
        post = "ANCHORED" if result.get("verified") else "ANCHOR_FAILED"
        nca_id = self._nca(
            "CBDC_ANCHOR", "OUT-SBX", post,
            f"CB-IF-001 {sandbox_id} mou={result.get('mou')} tx={result.get('contract_tx')} "
            f"simulated={simulated} verified={result.get('verified')}",
        )
        return {
            "contract": CB_IF_001,
            "operation": "anchor",
            "sandbox_id": sandbox_id,
            "transaction_id": tid,
            "mou": result.get("mou"),
            "contract_tx": result.get("contract_tx"),
            "verified": result.get("verified"),
            "simulated": simulated,  # ID92: 模拟显式标记，下游必须承认
            "source": "SIMULATED-TAX-AUTHORITY" if simulated else "REAL-TAX-AUTHORITY",
            # V1 修复：ID79 窗口判定显式声明（由出盒评估网关 TP 层强制，M3-5 锚定链路不重复实现）
            "id79_window_check": {
                "enforced_by": "TP-EVALUATION-GATEWAY",
                "rule": "MOUContinuousVerification（inference_engine 规则 4）",
                "scope": "30d>=28d + 连续无税收熔断归零",
                "in_anchor_link": False,  # M3-5 模拟过渡：M4 桥接窗口判定
            },
            "latency_ms": latency_ms,
            "nca_refs": {"sbx": nca_id, "dcep": (result.get("nca") or {}).get("NCA-ID", "")},  # #13
        }

    # ---------------- CB-IF-001b MOU 锚定状态查询 ----------------

    def mou_status(self, sandbox_id: str, transaction_id: str = "") -> Dict[str, Any]:
        """CB-IF-001b MOU 锚定状态查询。

        六要素声明:
        目标函数: MOU 锚定状态查询（CB-IF-001b，出盒评估辅助）
        约束矩阵: 输入——sandbox_id/transaction_id；输出——锚定状态；禁止——无
        先验分布: 沙盒 MOU 记录（anchor 结果回写）
        配置权边界: L2；只读查询
        预期分配: 返回 {contract, transaction_id, mou, verified, simulated}；失败=无
        审计轨迹: 只读，不生成 NCA
        """
        from . import store as _store
        sb = _store.load_sandbox(sandbox_id)
        logs = getattr(sb, "mou_logs", []) if sb else []
        if transaction_id:
            logs = [r for r in logs if r.get("transaction_id") == transaction_id]
        latest = logs[-1] if logs else {}
        return {
            "contract": CB_IF_001B,
            "sandbox_id": sandbox_id,
            "transaction_id": latest.get("transaction_id", ""),
            "mou": latest.get("mou"),
            "verified": latest.get("verified", False),
            "simulated": latest.get("simulated", None),
            "count": len(logs),
        }


# 全局适配器实例（路由层消费；测试可注入）
ADAPTER = CbdcAnchor()
