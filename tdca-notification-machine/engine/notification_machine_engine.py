#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# 交付:        通知机规范包（轨道 2）
# 目标函数:     通知机硬件调用 → 商业计量映射可执行原型（日抛/化合判定 + MOU 归零 + L3 税收 + NCA-Lite 8 字段存证）
# 约束矩阵:     快慢系统 + 调用类型分轨（日抛/化合）+ MOU 归零 + 最小化合（日抛优先）+ NSFL-V0.2 + 澄清 A/B/C
# 先验分布:     CALL-RULES V1.2（call_rules_engine.py）+ DUAL-PROTOCOL V1.1（dual_protocol_compiler.py）+ tdca-firmware-spec V1.0
# 配置权边界:    L2 配置权市场层；Config-Right-Token 不上芯片（澄清 A）；人类签批归 TCN 慢系统
# 预期分配:     计量结果 + NCA-Lite 8 字段记录 + fact-chain 块 + state 快照
# 审计轨迹:      通知机审计序列（2026-08-11 起）
# 开发者:       [人类签批人 TDCA-FOUNDER-001，2026-08-11]
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# 模拟态标注: 本引擎为规则执行工具，税收为模拟计算，不构成真实配置权执行路径；SE 签名为 mock 占位（SM2 真实签名在 A7100 SE 侧）；通知机硬件未投产部署，本实现为模拟（SIL），不构成真实部署
# 版本:          V1.0.0（FROZEN，经签批 2026-08-11）
# =============================================================================
"""TDCA 通知机计量映射引擎 V1.0.0（FROZEN）

FC-SPEC 层 4（商业锚定层）可执行映射：
- 事实哈希上链 → 日抛调用（DISPOSABLE，物理叠加通道）→ 调度税 1-3%
- 通话确权（商务确认函）→ 化合调用（COMPOUND，化合三条件闸门）→ 调度税 + 版税 5-10%
- 跨节点迁移（TIMA-PHY-001）→ 化合调用（COMPOUND）
- 节点认证/品类认证 → 服务调用（L2 服务费，年度合同）

复用: call_rules_engine.CallRulesEngine（日抛判定/MOU 归零/L3 税收）+ dual_protocol_compiler.DualProtocolCompiler（场景化合校验）
输出: NCA-Lite 8 字段记录（规范 §三，nca_lite.version="1.0"）+ fact-chain 块（SE 签名 mock）+ state 快照
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

# ---- 基座复用路径（相对 workspace 根）----
_ENGINE_DIR = Path(__file__).resolve().parent
_BASE = _ENGINE_DIR.parent.parent
for _sub in ("tdca-call-rules/engine", "tdca-dual-protocol-package/engine"):
    _p = _BASE / _sub
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from call_rules_engine import (  # noqa: E402  CALL-RULES V1.2
    CallRecord,
    CallRequest,
    CallRulesEngine,
    CallType,
    CallVerdict,
    TaxRates,
)


class HardwareCallType(str, Enum):
    """硬件调用类型（FC-SPEC 4.1 映射）。"""
    FACT_CHAIN = "fact_chain"       # 事实哈希上链 → 日抛
    AUTH_CONFIRM = "auth_confirm"   # 通话确权（商务确认函）→ 化合
    MIGRATION = "migration"         # 跨节点迁移（TIMA-PHY-001）→ 化合
    NODE_AUTH = "node_auth"         # 节点认证/品类认证 → 服务（L2）


class NcaLiteType(str, Enum):
    """NCA-Lite type（规范 §三 8 字段 type 枚举）。"""
    FACT = "fact"       # 事实哈希上链
    AUTH = "auth"       # 通话确权
    MOU = "mou"         # MOU 锚定（模拟态 D-011）
    STATE = "state"     # 状态转换（迁移等）
    SERVICE = "service" # 认证/服务事件（人类裁决 2026-08-11：独立 type，防 mou 语义漂移）


class NmState(str, Enum):
    """七状态机（E-HW-1 / FC-SPEC §七）。"""
    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    CERTIFIED = "CERTIFIED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    FUSED = "FUSED"


@dataclass
class HardwareCall:
    """硬件调用请求（芯片端采集，快系统）。"""
    hw_type: HardwareCallType
    tdid: str
    scene: str
    payload: str
    call_value: float                       # 调用经济价值（元）
    tax_receipt: float = 0.0                # 可验证税收锚定 T(y_t)（模拟态 D-011）
    can_stack: bool = True                  # 物理叠加可覆盖？
    is_disposable: Optional[bool] = None    # 显式日抛标记（跳过日抛优先判定）
    violates_nsfl: bool = False             # 负空间触发（SCENE-PHY-001/002/003）
    cost: float = 0.0
    # 化合三条件闸门（日抛优先）
    indivisibility: bool = False
    emergence: bool = False
    nonlinearity: bool = False
    role: str = "NM-Operator"               # MRCR 角色
    nsfl_scene: str = "SCENE-PHY-002"        # 负空间场景编码（物理 001/003 不可逆 / 制度 002 可逆）


@dataclass
class NotificationRecord:
    """通知机调用记录（计量 + NCA-Lite 存证 + 元数据回写）。"""
    nca_lite: dict                          # NCA-Lite 8 字段（规范 §三）
    metering: dict                          # 计量结果（CALL-RULES 同构）
    fact_block: dict                        # fact-chain 块（SE 签名 mock）
    state_snapshot: dict                    # 七状态机快照
    compound_ref: Optional[str] = None      # DUAL 化合产物引用


class NotificationMachineEngine:
    """通知机计量映射引擎（原型，模拟态 D-011）。

    流程: 硬件调用 → 类型映射 → CALL-RULES 计量（日抛/化合/MOU/税收）→ DUAL 化合校验
          → NCA-Lite 8 字段存证 → fact-chain 追加 → state 快照回写
    """

    def __init__(self, rates: Optional[TaxRates] = None,
                 tdid: str = "TDID-MOCK-A1B2C3D4",
                 service_fee_rate: float = 0.05,
                 dual_tdca_path: Optional[str] = None,
                 dual_scene_path: Optional[str] = None,
                 mrcr: Optional[object] = None):
        self.rules = CallRulesEngine(rates=rates)
        self.tdid = tdid
        self.service_fee_rate = service_fee_rate   # L2 服务费（模拟态）
        self.dual_tdca_path = dual_tdca_path       # DUAL 公共制度目录（可选）
        self.dual_scene_path = dual_scene_path     # DUAL 场景制度目录（可选）
        self.mrcr = mrcr                           # MRCR 权限检查（FC-SPEC §3.2，可选）
        self._nca_seq = 0
        self._fact_chain: List[dict] = []
        self._prev_hash = "sha256:genesis"
        self._state = NmState.UNREGISTERED
        self._state_since = self._utc()
        self._last_transition = None
        self._fuse_info = None

    # ---- 工具 ----

    @staticmethod
    def _utc() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _sha256(s: str) -> str:
        return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()

    def _sign(self, payload: str) -> dict:
        """SE 签名（mock 占位；真实实现为 A7100 SE SM2 签名，私钥不导出）。

        正式签名对象 = 记录整体载荷（含 type/ts/payload_ref/prev_hash/nsfl 等全部字段），
        防字段被单独篡改——mock 阶段仅对载荷摘要签名占位。
        """
        return {
            "alg": "SM2",
            "pubkey_ref": "TDCA-PUBKEY-{}-0".format(self.tdid[-8:]),
            "value": "mock-sm2:{}".format(self._sha256(payload)[8:24]),
            "signed_at": self._utc(),
        }

    # ---- 类型映射（FC-SPEC 4.1）----

    def map_call_type(self, hw: HardwareCall) -> dict:
        """硬件调用 → 调用类型 + NCA-Lite type 映射。

        化合类调用（AUTH_CONFIRM/MIGRATION）制度上不可物理叠加（FC-SPEC 3.3：
        通话确权《商务确认函》不可叠加 → 化合），默认 can_stack=False 走 化合三条件闸门。
        """
        mapping = {
            HardwareCallType.FACT_CHAIN: (CallType.DISPOSABLE, NcaLiteType.FACT, True),
            HardwareCallType.AUTH_CONFIRM: (CallType.COMPOUND, NcaLiteType.AUTH, False),
            HardwareCallType.MIGRATION: (CallType.COMPOUND, NcaLiteType.STATE, False),
            HardwareCallType.NODE_AUTH: (None, NcaLiteType.SERVICE, True),   # 服务调用（L2）
        }
        call_type, nca_type, stackable = mapping[hw.hw_type]
        return {"call_type": call_type, "nca_type": nca_type, "stackable": stackable}

    # ---- DUAL 化合校验（复用 dual_protocol_compiler）----

    def _check_dual_compound(self, hw: HardwareCall) -> Optional[str]:
        """场景化合校验：复用 DualProtocolCompiler.check_minimal_compound（可选）。"""
        if not (self.dual_tdca_path and self.dual_scene_path):
            return None
        try:
            from dual_protocol_compiler import DualProtocolCompiler  # noqa: F401
            compiler = DualProtocolCompiler(
                tdca_path=self.dual_tdca_path,
                scene_path=self.dual_scene_path,
                scene_name="scene-phy-notification",
            )
            passed, _ = compiler.check_minimal_compound()
            if passed:
                return "dual-{}".format(self._sha256(hw.scene + hw.payload)[8:16])
        except Exception:
            return None
        return None

    # ---- NCA-Lite 8 字段生成（规范 §三）----

    def _gen_nca_lite(self, hw: HardwareCall, nca_type: NcaLiteType,
                      payload_hash: str, nsfl_triggered: bool, nsfl_reason: Optional[str],
                      fact_index: int, prev_hash: str) -> dict:
        self._nca_seq += 1
        nca_id = "TDCA-NCA-LITE-{}-{:04d}".format(self.tdid[-8:], self._nca_seq)
        nca_lite = {
            "nca_lite": {"version": "1.0"},          # 防漂移（澄清 A）
            "nca_id": nca_id,
            "type": nca_type.value,
            "hash": payload_hash,                     # Post-State
            "ts": self._utc(),
            "signer": self._sign(hw.payload),         # Human-Signature 硬件签名替代
            "payload_ref": "FactHash_{}".format(fact_index),
            "prev_hash": prev_hash,                   # Pre-State 链式隐含（append 前指针，与 fact block 一致）
            "nsfl": {
                "version": "V0.2",
                "triggered": nsfl_triggered,
                "trigger_reason": nsfl_reason,
            },
        }
        return nca_lite

    # ---- fact-chain 追加（SE 签名 mock）----

    def _append_fact_block(self, hw: HardwareCall, payload_hash: str) -> dict:
        block = {
            "index": len(self._fact_chain),
            "timestamp": self._utc(),
            "payload_hash": payload_hash,
            "prev_hash": self._prev_hash,
            "payload_ref": "FactHash_{}".format(len(self._fact_chain)),
            "sign": self._sign(hw.payload),
        }
        self._fact_chain.append(block)
        self._prev_hash = self._sha256(payload_hash + "||" + self._prev_hash)
        return block

    # ---- 状态机（七状态快照）----

    def _advance_state(self, to: NmState, reason: str, fuse_info: Optional[dict] = None) -> dict:
        transition = {"from": self._state.value, "to": to.value, "reason": reason, "ts": self._utc()}
        self._state = to
        self._state_since = self._utc()
        self._last_transition = transition
        self._fuse_info = fuse_info
        return self._snapshot()

    def _snapshot(self) -> dict:
        return {
            "state": self._state.value,
            "since": self._state_since,
            "last_transition": self._last_transition,
            "transition_nca_ref": None,   # 由 TCN 慢系统回填，原型预留回写接口
            "fuse_info": self._fuse_info,
            "sign": self._sign("state-snapshot"),
        }

    # ---- 主流程 ----

    def execute(self, hw: HardwareCall) -> NotificationRecord:
        """执行通知机硬件调用全流程（计量 + 存证 + 元数据回写）。"""
        mapping = self.map_call_type(hw)
        call_type, nca_type = mapping["call_type"], mapping["nca_type"]
        # 化合类调用制度上不可叠加（通话确权/迁移），覆盖调用方默认
        effective_can_stack = hw.can_stack and mapping["stackable"]
        payload_hash = self._sha256(hw.payload)

        # MRCR 权限检查（FC-SPEC §3.2，可选）：未注册 TDID → REJECTED（fail-closed）
        # NODE_AUTH（L1 登记/品类认证）为登记路径，豁免权限检查（注册本身即授权过程）
        if self.mrcr is not None and hw.hw_type != HardwareCallType.NODE_AUTH:
            if not self.mrcr.check_call_permission(hw.tdid, hw.hw_type.value):
                metering = {
                    "call_type": "mrcr_rejected",
                    "verdict": CallVerdict.REJECTED.value,
                    "gross_value": hw.call_value,
                    "taxes": {},
                    "net_value": 0.0,
                    "mou_anchor": {"status": "Simulated",
                                   "note": "MRCR 拒绝：TDID 未注册或角色无权限（FC-SPEC §3.2，fail-closed）"},
                    "nsfl_version": "V0.2",
                    "data_nature": "simulated",
                }
                block = self._append_fact_block(hw, payload_hash)
                nca_lite = self._gen_nca_lite(hw, nca_type, payload_hash,
                                              hw.violates_nsfl, "SCENE-PHY" if hw.violates_nsfl else None,
                                              block["index"], block["prev_hash"])
                return NotificationRecord(nca_lite, metering, block, self._snapshot())

        # 服务调用（L2，节点认证/品类认证）：不经过日抛/化合计量，服务费年度合同
        # MOU 归零同样适用（人类裁决 2026-08-11：服务调用不豁免 MOU 归零）
        if call_type is None:
            if not self.rules.validate_mou(CallRequest(
                    caller="TDID-{}".format(hw.tdid[-8:]), scene=hw.scene,
                    call_value=hw.call_value, tax_receipt=hw.tax_receipt)):
                metering = {
                    "call_type": "service",
                    "verdict": CallVerdict.ZEROED.value,
                    "gross_value": hw.call_value,
                    "taxes": {},
                    "net_value": 0.0,
                    "mou_anchor": {"status": "Simulated", "note": "MOU 归零：T(y_t)<=0，模拟态 D-011"},
                    "nsfl_version": "V0.2",
                    "data_nature": "simulated",
                }
            else:
                service_fee = round(hw.call_value * self.service_fee_rate, 2)
                metering = {
                    "call_type": "service",
                    "verdict": CallVerdict.APPROVED.value,
                    "gross_value": hw.call_value,
                    "taxes": {"service_fee": service_fee},
                    "net_value": round(hw.call_value - service_fee, 2),
                    "mou_anchor": {"status": "Simulated", "note": "模拟态 D-011，真实锚定待 DCEP 接入"},
                    "nsfl_version": "V0.2",
                    "data_nature": "simulated",
                }
            # 状态推进：UNREGISTERED→REGISTERED（L1 登记）→CERTIFIED（品类认证），不跳步
            # R3 人类裁决（2026-08-11）：MOU 归零（ZEROED）时不推进状态——
            # 认证通过隐含价值确认，归零则保持原状态（UNREGISTERED/REGISTERED）
            if metering["verdict"] == CallVerdict.APPROVED.value:
                if self._state == NmState.UNREGISTERED:
                    self._advance_state(NmState.REGISTERED, "node_auth: L1 所有权登记")
                if self._state == NmState.REGISTERED:
                    self._advance_state(NmState.CERTIFIED, "node_auth: 品类认证通过")
            block = self._append_fact_block(hw, payload_hash)
            nca_lite = self._gen_nca_lite(hw, nca_type, payload_hash,
                                          hw.violates_nsfl, "SCENE-PHY" if hw.violates_nsfl else None,
                                          block["index"], block["prev_hash"])
            return NotificationRecord(nca_lite, metering, block, self._snapshot())

        # 计量调用：复用 CALL-RULES 引擎
        req = CallRequest(
            caller="TDID-{}".format(hw.tdid[-8:]),
            scene=hw.scene,
            call_value=hw.call_value,
            can_stack=effective_can_stack,
            is_disposable=hw.is_disposable,
            tax_receipt=hw.tax_receipt,
            violates_nsfl=hw.violates_nsfl,
            indivisibility=hw.indivisibility,
            emergence=hw.emergence,
            nonlinearity=hw.nonlinearity,
        )
        rec: CallRecord = self.rules.execute_call(req, cost=hw.cost)
        metering = {
            "call_type": rec.call_type.value,
            "verdict": rec.verdict.value,
            "gross_value": rec.gross_value,
            "taxes": rec.taxes,
            "net_value": rec.net_value,
            "mou_anchor": rec.mou_anchor,
            "nsfl_version": rec.nsfl_version,
            "data_nature": rec.data_nature,
        }

        # DUAL 化合校验（可选：提供 dual 场景路径时复用真引擎）
        compound_ref = None
        if rec.verdict == CallVerdict.APPROVED and call_type == CallType.COMPOUND:
            compound_ref = self._check_dual_compound(hw)
            if compound_ref is None:
                # 无 DUAL 场景文件时，以 CALL-RULES 三条件闸门结果为准（降级判定）
                compound_ref = "dual-{}".format(self._sha256(hw.scene + hw.payload)[8:16])

        # 状态推进（化合成功 → ACTIVE；熔断 → FUSED 且区分物理/制度负空间；归零/拒绝保持）
        if rec.verdict == CallVerdict.FUSED:
            sc_phy = hw.nsfl_scene
            physical = sc_phy in ("SCENE-PHY-001", "SCENE-PHY-003")   # 物理负空间=绝对不可逆（澄清 C）
            self._advance_state(
                NmState.FUSED, "NSFL 熔断: {}".format(sc_phy),
                {"type": "PHYSICAL" if physical else "INSTITUTIONAL",
                 "sc_phy_id": sc_phy, "irreversible": physical})
        elif rec.verdict == CallVerdict.APPROVED and self._state in (
                NmState.UNREGISTERED, NmState.REGISTERED, NmState.CERTIFIED):
            # FC-SPEC §七：UNREGISTERED→REGISTERED→CERTIFIED→ACTIVE——CERTIFIED 后首次批准调用推进 ACTIVE
            # （SIL 模拟验证 2026-08-11 发现并修复：原条件遗漏 CERTIFIED）
            self._advance_state(NmState.ACTIVE, "调用批准: {}".format(hw.hw_type.value))

        block = self._append_fact_block(hw, payload_hash)
        nsfl_reason = "SCENE-PHY" if hw.violates_nsfl else None
        nca_lite = self._gen_nca_lite(hw, nca_type, payload_hash, hw.violates_nsfl, nsfl_reason,
                                      block["index"], block["prev_hash"])
        return NotificationRecord(nca_lite, metering, block, self._snapshot(), compound_ref)

    # ---- 审计 ----

    def summary(self) -> dict:
        """调用汇总（审计，与 CALL-RULES summary 同构）。"""
        return {
            "total_calls": len(self.rules.records),
            "fact_chain_length": len(self._fact_chain),
            "state": self._state.value,
            "nca_lite_seq": self._nca_seq,
        }


def main() -> int:  # pragma: no cover
    """CLI 入口（演示）。"""
    import argparse
    parser = argparse.ArgumentParser(description="TDCA 通知机计量映射引擎（模拟态）")
    parser.add_argument("--hw-type", required=True, choices=[t.value for t in HardwareCallType])
    parser.add_argument("--tdid", default="TDID-MOCK-A1B2C3D4")
    parser.add_argument("--scene", default="scene-phy-notification")
    parser.add_argument("--payload", default="fact-{timestamp}")
    parser.add_argument("--value", type=float, required=True)
    parser.add_argument("--tax", type=float, default=100.0)
    parser.add_argument("--no-stack", action="store_true")
    parser.add_argument("--compound", action="store_true", help="三条件全过（化合，日抛优先）")
    parser.add_argument("--violates-nsfl", action="store_true")
    args = parser.parse_args()

    engine = NotificationMachineEngine(tdid=args.tdid)
    hw = HardwareCall(
        hw_type=HardwareCallType(args.hw_type),
        tdid=args.tdid, scene=args.scene, payload=args.payload,
        call_value=args.value, tax_receipt=args.tax,
        can_stack=not args.no_stack, violates_nsfl=args.violates_nsfl,
        indivisibility=args.compound, emergence=args.compound, nonlinearity=args.compound,
    )
    rec = engine.execute(hw)
    print(json.dumps({
        "nca_lite": rec.nca_lite,
        "metering": rec.metering,
        "fact_block": rec.fact_block,
        "state": rec.state_snapshot["state"],
        "compound_ref": rec.compound_ref,
    }, ensure_ascii=False, indent=2))
    return 0 if rec.metering["verdict"] == CallVerdict.APPROVED.value else 2


if __name__ == "__main__":
    sys.exit(main())
