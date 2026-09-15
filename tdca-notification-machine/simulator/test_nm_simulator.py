# -*- coding: utf-8 -*-
"""通知机 SIL 模拟器测试（过渡方案，模拟态标注：硬件/签名/税收均为模拟，不构成真实配置权执行路径；通知机硬件未投产部署）。

覆盖:
  1. 上电 TDID 一致性（driver/engine/导出 identity 三处一致）
  2. L1 所有权登记（register_to_l1 成功 + NCA 引用）
  3. 端到端场景状态序列（CERTIFIED→ACTIVE→FUSED 物理不可逆）
  4. 物理/制度负空间 fuse_info 区分（SCENE-PHY-001 不可逆）
  5. .tdca 六组件导出完整性 + JSON 合法
"""
import json
import sys
from pathlib import Path

_SIM_DIR = Path(__file__).resolve().parent
if str(_SIM_DIR) not in sys.path:
    sys.path.insert(0, str(_SIM_DIR))

from nm_simulator import NmSimulator  # noqa: E402
from engine.notification_machine_engine import HardwareCallType, NmState  # noqa: E402


def _sim(tmp_path):
    return NmSimulator(out_dir=tmp_path)


# 1. 上电 TDID 一致性
def test_boot_tdid_consistency(tmp_path):
    sim = _sim(tmp_path)
    boot = sim.boot()
    # 模拟器 TDID == 引擎 TDID == driver 生成值（E-HW-1 公式）
    assert boot["tdid"] == sim.engine.tdid
    assert boot["tdid"].startswith("TDID-")
    assert boot["puf_hash"].startswith("sha256:")
    assert sim.driver.generate_td_id(sim.driver.read_puf(),
                                     "sha256:9beb123c50b5cf18775b5cfd5c2cf8fd08b224261119becbfe913e0e03b6d601",
                                     sim.driver.batch_id) == boot["tdid"]


# 2. L1 所有权登记
def test_l1_registration(tmp_path):
    sim = _sim(tmp_path)
    sim.boot()
    rec = sim.register_l1(config_right_hash="cfg-sim-001")
    assert rec["registered"] is True
    assert rec["l1_record"]["owner_did"] == "did:tdca:founder"
    assert rec["nca_ref"].startswith("NCA-TDID-")


# 3. 端到端场景状态序列（认证→日抛→化合×2→物理熔断）
def test_scenario_state_sequence(tmp_path):
    sim = _sim(tmp_path)
    sim.boot()
    sim.register_l1()
    records = sim.run_scenario()
    states = [r.state_snapshot["state"] for r in records]
    assert states[0] == NmState.CERTIFIED.value          # 认证 → CERTIFIED（经 REGISTERED）
    assert NmState.ACTIVE.value in states                 # 日抛/化合 → ACTIVE
    assert states[-1] == NmState.FUSED.value              # 物理熔断 → FUSED（不可逆）
    assert len(records) == 5


# 4. 物理负空间不可逆（SCENE-PHY-001）
def test_physical_fuse_irreversible(tmp_path):
    sim = _sim(tmp_path)
    sim.boot()
    rec = sim.call(HardwareCallType.FACT_CHAIN, violates_nsfl=True, nsfl_scene="SCENE-PHY-001")
    fuse = rec.state_snapshot["fuse_info"]
    assert fuse["type"] == "PHYSICAL"
    assert fuse["irreversible"] is True
    assert fuse["sc_phy_id"] == "SCENE-PHY-001"
    assert rec.state_snapshot["state"] == NmState.FUSED.value
    assert rec.nca_lite["nsfl"]["triggered"] is True


# 5. .tdca 六组件导出完整性 + JSON 合法
def test_export_tdca_complete(tmp_path):
    sim = _sim(tmp_path)
    sim.boot()
    sim.register_l1()
    records = sim.run_scenario()
    tdca_dir = sim.export_tdca(records)
    components = ["identity.tdca", "state.json",
                  "session-index/L0-state.nca", "session-index/L1-active.json",
                  "config/scene-binding.json", "config/call-rules.json"]
    for c in components:
        assert (tdca_dir / c).exists(), "缺少组件: {}".format(c)
    # 全部 JSON 合法
    for f in list(tdca_dir.rglob("*.json")) + [tdca_dir / "identity.tdca",
                                               tdca_dir / "session-index" / "L0-state.nca"]:
        json.loads(f.read_text(encoding="utf-8"))
    # fact-chain 块数 = 场景调用数
    blocks = list((tdca_dir / "fact-chain").glob("block-*.json"))
    assert len(blocks) == len(records)
    # nca-lite 记录数 = 场景调用数（含 service 类型）
    nca_files = [f for sub in ("fact", "auth", "mou", "service") for f in (tdca_dir / "nca-lite" / sub).glob("*.json")]
    assert len(nca_files) == len(records)


# 6. 链路验证报告全通过
def test_verify_all_passed(tmp_path):
    sim = _sim(tmp_path)
    sim.boot()
    sim.register_l1()
    records = sim.run_scenario()
    tdca_dir = sim.export_tdca(records)
    report = sim.verify(records, tdca_dir)
    assert report["all_passed"] is True, report["checks"]
