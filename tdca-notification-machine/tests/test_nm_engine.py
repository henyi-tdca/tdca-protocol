# -*- coding: utf-8 -*-
"""通知机计量映射引擎测试套件（轨道 2，V0.1 原型）。

模拟态标注: 本测试为模拟数据验证（MOU 锚定 D-011），不构成真实配置权执行路径；通知机硬件未投产部署。

覆盖（2026-08-11 制度裁决 P1 验收 + REV-NM-001 修复验证）：
  1. 事实哈希上链 → 日抛判定 + 调度税
  2. 通话确权（三条件全过）→ 化合判定 + 版税 + compound_ref
  3. 跨节点迁移 → 化合判定
  4. 节点认证/品类认证 → 服务调用（L2 服务费，独立 type=service）
  5. 服务调用 MOU 归零（不豁免，人类裁决 2026-08-11）
  6. MOU 归零（计量分支 T(y_t)=0 → ZEROED）
  7. 负空间熔断（NSFL → FUSED + nsfl.triggered）
  8. 物理/制度负空间区分（fuse_info.type/irreversible，REV-NM-001 违规 3）
  9. NCA-Lite 8 字段完整性（规范 §三 + nca_lite.version="1.0"）
  10. fact-chain 链式增长 + 七状态机快照回写（含 REGISTERED 中间态）
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent   # tdca-notification-machine/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine.notification_machine_engine import (  # noqa: E402
    HardwareCall,
    HardwareCallType,
    NotificationMachineEngine,
    NmState,
)


def _mk_engine(**kw):
    return NotificationMachineEngine(tdid="TDID-MOCK-A1B2C3D4", **kw)


def _call(hw_type, value=1000.0, tax=100.0, compound=False, **kw):
    return HardwareCall(
        hw_type=hw_type,
        tdid="TDID-MOCK-A1B2C3D4",
        scene="scene-phy-notification",
        payload="payload-{}".format(hw_type.value),
        call_value=value,
        tax_receipt=tax,
        indivisibility=compound, emergence=compound, nonlinearity=compound,
        **kw,
    )


# 1. 事实哈希上链 → 日抛 + 调度税
def test_fact_chain_disposable():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN))
    assert rec.metering["call_type"] == "disposable"
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["taxes"]["dispatch_tax"] == round(1000.0 * 0.02, 2)
    assert "royalty" not in rec.metering["taxes"]
    assert rec.nca_lite["type"] == "fact"


# 2. 通话确权（化合三条件全过）→ 化合 + 版税 + compound_ref
def test_auth_confirm_compound():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.AUTH_CONFIRM, compound=True))
    assert rec.metering["call_type"] == "compound"
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["taxes"]["royalty"] == round(1000.0 * 0.075, 2)
    assert rec.compound_ref is not None and rec.compound_ref.startswith("dual-")
    assert rec.nca_lite["type"] == "auth"


# 3. 跨节点迁移（TIMA-PHY-001）→ 化合
def test_migration_compound():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.MIGRATION, compound=True))
    assert rec.metering["call_type"] == "compound"
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.compound_ref is not None
    assert rec.nca_lite["type"] == "state"


# 4. 节点认证/品类认证 → 服务调用（L2 服务费，独立 type=service，不扣调度税）
def test_node_auth_service():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.NODE_AUTH))
    assert rec.metering["call_type"] == "service"
    assert rec.metering["verdict"] == "APPROVED"
    assert rec.metering["taxes"] == {"service_fee": round(1000.0 * 0.05, 2)}
    assert "dispatch_tax" not in rec.metering["taxes"]
    assert rec.nca_lite["type"] == "service"                    # 独立 type（REV-NM-001 违规 4）
    assert rec.state_snapshot["state"] == NmState.CERTIFIED.value
    # 状态机不跳步：UNREGISTERED→REGISTERED→CERTIFIED（REV-NM-001 违规 5）
    assert rec.state_snapshot["last_transition"]["from"] == NmState.REGISTERED.value


# 5. 服务调用 MOU 归零（MOU 归零不豁免，人类裁决 2026-08-11；REV-NM-001 违规 1）
def test_service_mou_zeroed():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.NODE_AUTH, tax=0.0))
    assert rec.metering["call_type"] == "service"
    assert rec.metering["verdict"] == "ZEROED"
    assert rec.metering["net_value"] == 0.0
    assert rec.metering["taxes"] == {}
    # R3 人类裁决（2026-08-11）：归零时不推进状态（保持 UNREGISTERED）
    assert rec.state_snapshot["state"] == NmState.UNREGISTERED.value


# 5. MOU 归零（T(y_t)=0 → ZEROED）
def test_mou_zeroed():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN, tax=0.0))
    assert rec.metering["verdict"] == "ZEROED"
    assert rec.metering["net_value"] == 0.0
    assert rec.metering["taxes"] == {}


# 6. 负空间熔断（NSFL → FUSED + nsfl.triggered + state FUSED）
def test_nsfl_fused():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN, violates_nsfl=True))
    assert rec.metering["verdict"] == "FUSED"
    assert rec.nca_lite["nsfl"]["triggered"] is True
    assert rec.nca_lite["nsfl"]["version"] == "V0.2"
    assert rec.state_snapshot["state"] == NmState.FUSED.value


# 8. 物理/制度负空间区分（REV-NM-001 违规 3：fuse_info 落实）
def test_physical_vs_institutional_fuse():
    eng = _mk_engine()
    # 物理负空间（SCENE-PHY-001 拆解/篡改）：硬件 BLOCK 不可逆
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN, violates_nsfl=True, nsfl_scene="SCENE-PHY-001"))
    fi = rec.state_snapshot["fuse_info"]
    assert fi["type"] == "PHYSICAL" and fi["irreversible"] is True
    assert fi["sc_phy_id"] == "SCENE-PHY-001"
    # 制度负空间（SCENE-PHY-002 固件版本）：NSFL BLOCK，可上报慢系统
    eng2 = _mk_engine()
    rec2 = eng2.execute(_call(HardwareCallType.FACT_CHAIN, violates_nsfl=True, nsfl_scene="SCENE-PHY-002"))
    fi2 = rec2.state_snapshot["fuse_info"]
    assert fi2["type"] == "INSTITUTIONAL" and fi2["irreversible"] is False


# 9. NCA-Lite 8 字段完整性（规范 §三 + nca_lite.version="1.0"）
def test_nca_lite_fields():
    eng = _mk_engine()
    rec = eng.execute(_call(HardwareCallType.FACT_CHAIN))
    nl = rec.nca_lite
    assert nl["nca_lite"]["version"] == "1.0"                       # 防漂移（澄清 A）
    assert nl["nca_id"].startswith("TDCA-NCA-LITE-")                # NCA-ID
    assert nl["type"] == "fact"                                     # Operation-Type
    assert nl["hash"].startswith("sha256:")                         # Post-State
    assert nl["ts"].endswith("Z")                                   # Timestamp（UTC）
    assert nl["signer"]["alg"] == "SM2"                             # Human-Signature 硬件替代
    assert nl["payload_ref"] == "FactHash_0"                        # Audit-Trail 链式引用
    assert nl["prev_hash"] == "sha256:genesis"                      # Pre-State 链式隐含
    assert nl["nsfl"]["version"] == "V0.2"                          # Negative-Space-Check
    assert set(nl.keys()) == {"nca_lite", "nca_id", "type", "hash", "ts",
                              "signer", "payload_ref", "prev_hash", "nsfl"}  # 8 字段 + 协议头


# 10. fact-chain 链式增长 + 状态机推进（含 REGISTERED 中间态）+ payload_ref 顺序
def test_fact_chain_growth_and_state():
    eng = _mk_engine()
    r1 = eng.execute(_call(HardwareCallType.FACT_CHAIN))
    r2 = eng.execute(_call(HardwareCallType.FACT_CHAIN))
    assert r1.fact_block["index"] == 0 and r1.fact_block["payload_ref"] == "FactHash_0"
    assert r2.fact_block["index"] == 1 and r2.fact_block["payload_ref"] == "FactHash_1"
    # 链式一致性（REV-NM-001 违规 8：删弱断言）：记录 prev_hash == 所属块 prev_hash，且链已推进
    assert r2.nca_lite["prev_hash"] == r2.fact_block["prev_hash"]
    assert r2.fact_block["prev_hash"] != r1.fact_block["prev_hash"]
    assert r1.nca_lite["nca_id"] != r2.nca_lite["nca_id"]       # seq 递增
    assert r1.state_snapshot["state"] == NmState.ACTIVE.value   # 批准 → ACTIVE
    s = eng.summary()
    assert s["fact_chain_length"] == 2 and s["nca_lite_seq"] == 2
