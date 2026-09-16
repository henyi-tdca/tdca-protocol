#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# 交付:        通知机规范包（过渡方案模拟）
# 目标函数:     通知机软件在环（SIL）模拟器——硬件未生产（E-HW-2 未到位），用 NMDeviceDriver
#               mock 驱动模拟硬件层，联动 notification_machine_engine 验证协议包 V1.0 端到端链路
# 约束矩阵:     快慢系统 + MOU 归零 + 最小化合（日抛优先）+ NSFL-V0.2 + tdca-firmware-spec V1.0
# 先验分布:     NMDeviceDriver（E-HW-1 mock，tdca-eios/src）+ notification_machine_engine V1.0.0 + .tdca 模板 ×8
# 配置权边界:    L2 配置权市场层；SE 签名为 mock 占位（真实 SM2 在 A7100 SE 侧）；MOU 模拟态 D-011
# 预期分配:     端到端场景序列 + .tdca 元数据目录落盘 + 链路验证报告
# 审计轨迹:      通知机审计序列（2026-08-11 起）
# 开发者:       [人类签批人 TDCA-FOUNDER-001，2026-08-11]
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# 模拟态标注: 本模拟器为验证工具，硬件/签名/税收均为模拟，不构成真实配置权执行路径；通知机硬件未投产部署，不构成真实部署；
#               硬件到位后仅需替换 NMDeviceDriver 为真实驱动（E-HW-2），引擎与 .tdca 输出不变
# 版本:          V1.0.0（协议包 V1.0 过渡方案）
# =============================================================================
"""通知机 SIL（软件在环）模拟器 V1.0.0

过渡方案：硬件未生产，以 NMDeviceDriver mock 驱动模拟硬件层，
联动通知机协议包 V1.0 计量引擎，走通端到端链路并落盘 .tdca 元数据目录。

链路: 上电（PUF→TDID）→ L1 所有权登记 → 品类认证（NODE_AUTH）
      → 事实哈希上链（FACT_CHAIN 日抛）→ 通话确权（AUTH_CONFIRM 化合）
      → 跨节点迁移（MIGRATION 化合）→ 物理熔断（SCENE-PHY-001 不可逆）
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# ---- 复用路径 ----
_SIM_DIR = Path(__file__).resolve().parent
_NM_DIR = _SIM_DIR.parent                      # tdca-notification-machine/
_WS = _NM_DIR.parent                           # workspace 根
_EIOS_SRC = _WS / "tdca-eios" / "src"
for _p in (str(_NM_DIR), str(_EIOS_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nm_device_driver import NMDeviceDriver            # noqa: E402  mock 硬件（E-HW-1 兼容）
from engine.notification_machine_engine import (       # noqa: E402  协议包 V1.0 计量引擎
    HardwareCall,
    HardwareCallType,
    NmState,
    NotificationMachineEngine,
)

# 模拟宪法哈希（与 nm_device_driver 演示一致，模拟态）
CONSTITUTION_HASH = "sha256:9beb123c50b5cf18775b5cfd5c2cf8fd08b224261119becbfe913e0e03b6d601"


class NmSimulator:
    """通知机 SIL 模拟器（过渡方案）。"""

    def __init__(self, batch_id: str = "B20260811",
                 owner_did: str = "did:tdca:founder",
                 out_dir: Optional[Path] = None):
        self.driver = NMDeviceDriver(batch_id=batch_id)   # mock 硬件层
        self.owner_did = owner_did
        self.out_dir = out_dir or (_SIM_DIR / "out")
        self.tdid: Optional[str] = None
        self.puf_hash: Optional[str] = None
        self.engine: Optional[NotificationMachineEngine] = None
        self.l1_record: Optional[dict] = None

    # ---- 1. 上电：PUF → TDID → 引擎初始化 ----

    def boot(self) -> dict:
        """上电：读取 PUF 指纹 → 生成 TDID → 初始化计量引擎 → S-2 启动回读续号。"""
        puf = self.driver.read_puf()
        tdid = self.driver.generate_td_id(puf, CONSTITUTION_HASH, self.driver.batch_id)
        self.tdid = tdid
        self.puf_hash = "sha256:" + hashlib.sha256(puf.encode("utf-8")).hexdigest()
        self.engine = NotificationMachineEngine(tdid=tdid)
        resumed = self._resume_nca_seq_if_any()
        return {"tdid": tdid, "puf_hash": self.puf_hash, "batch_id": self.driver.batch_id,
                "nca_seq_resumed_from": resumed}

    # ---- 1.1 启动回读（S-2 修复：seq 持久化 ＋ 连续性校验 ＋ 日抛终态续号）----

    def _resume_nca_seq_if_any(self) -> Optional[int]:
        """若 .tdca/state.json 已存在（先前会话持久化），回读 nca_lite_seq 并校验链序连续：

        - 快照序号须与盘上 nca-lite 记录文件之最大序号一致（不一致 ⟹ fail-closed 拒绝启动）；
        - 校验过则引擎续号（⛔ 不复位、不复用、不跳号）。
        - ⭐ 日抛终态处置（明示）：日抛（DISPOSABLE）会话终结后序号封存于 state.json，
          新会话（同一 out_dir 再次 boot）自封存值续号 —— ⛔ 不复位；
          本机制只处置序号连续性，⛔ 不改「日抛优先」判定规则本身（map_call_type 未动）。
        - 旧版快照无 nca_lite_seq 字段（S-2 修复前产物）⟹ 视为无序号可续，返回 None。
        """
        state_path = self.out_dir / ".tdca" / "state.json"
        if not state_path.exists():
            return None
        snap = json.loads(state_path.read_text(encoding="utf-8"))
        seq = snap.get("nca_lite_seq")
        if seq is None:
            return None
        max_on_disk = self._max_nca_seq_on_disk()
        if max_on_disk != seq:
            raise RuntimeError(
                "[NSFL-TRIGGER] 启动连续性校验失败：快照 seq={}，盘上最大 seq={}".format(seq, max_on_disk))
        self.engine.resume_nca_seq(seq)
        return seq

    def _max_nca_seq_on_disk(self) -> int:
        """盘上 nca-lite 记录文件（TDCA-NCA-LITE-*-NNNN.json）之最大序号；无记录 = 0。"""
        n = 0
        d = self.out_dir / ".tdca" / "nca-lite"
        if d.exists():
            for p in d.rglob("TDCA-NCA-LITE-*-*.json"):
                try:
                    n = max(n, int(p.stem.rsplit("-", 1)[1]))
                except ValueError:
                    raise RuntimeError("[NSFL-TRIGGER] nca-lite 文件名序号不可解析：{}".format(p.name))
        return n

    # ---- 2. L1 所有权登记（快系统采集 + 所有权锚定）----

    def register_l1(self, config_right_hash: str = "cfg-001") -> dict:
        """L1 所有权登记（委托 NMDeviceDriver.register_to_l1）。"""
        if self.tdid is None:
            raise RuntimeError("[NSFL-TRIGGER] 未上电：先调用 boot()")
        self.l1_record = self.driver.register_to_l1(
            self.tdid, {"owner_did": self.owner_did, "config_right_hash": config_right_hash})
        return self.l1_record

    # ---- 3. 硬件调用（引擎计量）----

    def call(self, hw_type: HardwareCallType, value: float = 1000.0, tax: float = 100.0,
             compound: bool = False, violates_nsfl: bool = False,
             nsfl_scene: str = "SCENE-PHY-002", **kw):
        """构造硬件调用并执行计量（NCA-Lite 8 字段 + fact-chain + state 回写）。"""
        if self.engine is None:
            raise RuntimeError("[NSFL-TRIGGER] 未上电：先调用 boot()")
        hw = HardwareCall(
            hw_type=hw_type, tdid=self.tdid, scene="scene-phy-notification",
            payload="sim-{}".format(hw_type.value),
            call_value=value, tax_receipt=tax,
            indivisibility=compound, emergence=compound, nonlinearity=compound,
            violates_nsfl=violates_nsfl, nsfl_scene=nsfl_scene, **kw)
        return self.engine.execute(hw)

    # ---- 4. 典型场景序列 ----

    def run_scenario(self) -> List[dict]:
        """端到端场景序列：认证 → 日抛 → 化合（通话确权）→ 化合（迁移）→ 物理熔断。"""
        seq = []
        seq.append(self.call(HardwareCallType.NODE_AUTH, value=2000.0))                       # → CERTIFIED
        seq.append(self.call(HardwareCallType.FACT_CHAIN, value=500.0))                       # → ACTIVE（日抛）
        seq.append(self.call(HardwareCallType.AUTH_CONFIRM, value=3000.0, compound=True))     # 化合（通话确权）
        seq.append(self.call(HardwareCallType.MIGRATION, value=4000.0, compound=True))        # 化合（迁移）
        seq.append(self.call(HardwareCallType.FACT_CHAIN, value=100.0,
                             violates_nsfl=True, nsfl_scene="SCENE-PHY-001"))                 # 物理熔断（不可逆）
        return seq

    # ---- 5. .tdca 元数据目录落盘（规范 §一 六组件）----

    def export_tdca(self, records: List[dict]) -> Path:
        """按 tdca-firmware-spec V1.0 生成 .tdca 目录（六组件）。"""
        d = self.out_dir / ".tdca"
        (d / "session-index").mkdir(parents=True, exist_ok=True)
        (d / "nca-lite" / "fact").mkdir(parents=True, exist_ok=True)
        (d / "nca-lite" / "auth").mkdir(parents=True, exist_ok=True)
        (d / "nca-lite" / "mou").mkdir(parents=True, exist_ok=True)
        (d / "nca-lite" / "service").mkdir(parents=True, exist_ok=True)
        (d / "fact-chain").mkdir(parents=True, exist_ok=True)
        (d / "config").mkdir(parents=True, exist_ok=True)

        # ① identity.tdca（SE 签名 mock）
        identity = {
            "tdid": self.tdid,
            "puf_hash": self.puf_hash,
            "constitution_hash": CONSTITUTION_HASH,
            "sm2_pubkey": "mock-sm2-pubkey-{}-0".format(self.tdid[-8:]),
            "five_anchor": [{"name": n, "value": "sim-{}".format(n)} for n in
                            ("address", "line", "hardware", "cost", "subject")],
            "firmware_version": "1.0.0-sim",
            "sign": {"alg": "SM2", "value": "mock", "signed_at": "sim"},
        }
        (d / "identity.tdca").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

        # ② session-index（L0 + L1）
        l0 = {"si_id": "TDCA-SI-CHIP-{}-0001".format(self.tdid[-8:]),
              "layer": "L0",
              "constitutional_digest": {"version": "TDCA-CONST-v3.1.2", "delta_items": []},
              "integrity": {"sm3_full": "sm3:sim", "sha256_full": "sha256:sim"},
              "sign": {"alg": "SM2", "value": "mock"}}
        (d / "session-index" / "L0-state.nca").write_text(json.dumps(l0, ensure_ascii=False, indent=2), encoding="utf-8")
        l1 = {"scene_id": "scene-phy-notification", "role": "NM-Operator",
              "config_right_hash": "sha256:sim", "binding_ref": "config/scene-binding.json", "expires": None}
        (d / "session-index" / "L1-active.json").write_text(json.dumps(l1, ensure_ascii=False, indent=2), encoding="utf-8")

        # ③④⑤ 状态快照 + fact-chain + nca-lite 记录（取自引擎执行结果）
        last = records[-1].state_snapshot
        (d / "state.json").write_text(json.dumps(last, ensure_ascii=False, indent=2), encoding="utf-8")
        for r in records:
            blk = r.fact_block
            (d / "fact-chain" / "block-{:04d}.json".format(blk["index"])).write_text(
                json.dumps(blk, ensure_ascii=False, indent=2), encoding="utf-8")
            nl = r.nca_lite
            sub = {"fact": "fact", "auth": "auth", "mou": "mou", "state": "fact", "service": "service"}[nl["type"]]
            (d / "nca-lite" / sub / "{}.json".format(nl["nca_id"])).write_text(
                json.dumps(nl, ensure_ascii=False, indent=2), encoding="utf-8")

        # ⑥ config（SE 签名对象，SE-SIGN-5）
        scene_binding = {"tdca_version": "v3.1.2", "scene_type": "notification-machine",
                         "physical_anchor": {"tdid": self.tdid, "puf_hash": self.puf_hash,
                                             "five_anchor": ["address", "line", "hardware", "cost", "subject"]},
                         "scene_nsfl_ext": ["SCENE-PHY-001", "SCENE-PHY-002", "SCENE-PHY-003"],
                         "scene_review": ["REV-PHY-001", "REV-PHY-002", "REV-PHY-003"],
                         "compound_ref": None, "sign": {"alg": "SM2", "value": "mock"}}
        (d / "config" / "scene-binding.json").write_text(
            json.dumps(scene_binding, ensure_ascii=False, indent=2), encoding="utf-8")
        call_rules = {"call_type": "mixed", "tax_rates": {"dispatch_tax": 0.02, "royalty": 0.075},
                      "mou_mode": "simulated", "nsfl_version": "V0.2", "sign": {"alg": "SM2", "value": "mock"}}
        (d / "config" / "call-rules.json").write_text(
            json.dumps(call_rules, ensure_ascii=False, indent=2), encoding="utf-8")
        return d

    # ---- 6. 链路验证 ----

    def verify(self, records: List[dict], tdca_dir: Path) -> dict:
        """端到端链路断言（模拟验证报告）。"""
        checks = {}
        # TDID 一致性：模拟器/引擎/导出 identity 三处一致
        identity = json.loads((tdca_dir / "identity.tdca").read_text(encoding="utf-8"))
        checks["tdid_consistency"] = (identity["tdid"] == self.tdid == self.engine.tdid)
        # 状态序列：UNREGISTERED→CERTIFIED→ACTIVE→ACTIVE→ACTIVE→FUSED（物理不可逆）
        states = [r.state_snapshot["state"] for r in records]
        checks["state_sequence"] = (states[0] == NmState.CERTIFIED.value
                                    and NmState.FUSED.value in states
                                    and states[-1] == NmState.FUSED.value)
        # 物理熔断不可逆
        fuse = records[-1].state_snapshot["fuse_info"]
        checks["physical_fuse_irreversible"] = (fuse["type"] == "PHYSICAL" and fuse["irreversible"] is True
                                                and fuse["sc_phy_id"] == "SCENE-PHY-001")
        # NCA-Lite 链式：记录 prev_hash 与所属 fact-block 一致
        checks["nca_lite_chain"] = (records[1].nca_lite["prev_hash"]
                                    == records[1].fact_block["prev_hash"])
        # fact-chain 增长 + 序号连续
        idxs = [r.fact_block["index"] for r in records]
        checks["fact_chain_contiguous"] = (idxs == list(range(len(idxs))))
        # .tdca 六组件齐全
        components = ["identity.tdca", "state.json", "session-index/L0-state.nca",
                      "session-index/L1-active.json", "config/scene-binding.json",
                      "config/call-rules.json"]
        checks["tdca_components"] = all((tdca_dir / c).exists() for c in components)
        # 税务模拟：日抛调度税 2% 且 MOU 有效
        m = [r.metering for r in records if r.metering["call_type"] == "disposable"]
        checks["disposable_tax"] = (len(m) >= 1 and m[0]["taxes"]["dispatch_tax"] == round(500.0 * 0.02, 2))
        return {"all_passed": all(checks.values()), "checks": checks, "states": states}


def main() -> int:  # pragma: no cover（演示）
    """SIL 模拟演示。"""
    sim = NmSimulator()
    boot = sim.boot()
    l1 = sim.register_l1()
    records = sim.run_scenario()
    tdca_dir = sim.export_tdca(records)
    report = sim.verify(records, tdca_dir)
    print("=== 通知机 SIL 模拟（过渡方案，模拟态）===")
    print("TDID:", boot["tdid"])
    print("L1 登记:", l1["registered"], "| NCA 引用:", l1["nca_ref"])
    print("状态序列:", " → ".join(report["states"]))
    for k, v in report["checks"].items():
        print("  [{}] {}".format("PASS" if v else "FAIL", k))
    print(".tdca 落盘:", tdca_dir)
    print("链路验证:", "[OK] 全部通过" if report["all_passed"] else "[FAIL] 有失败项")
    return 0 if report["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
