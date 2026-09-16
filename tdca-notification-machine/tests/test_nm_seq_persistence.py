# -*- coding: utf-8 -*-
"""S-2 修复验收测试：seq 持久化 ＋ 启动回读 ＋ 连续性校验 ＋ 日抛终态续号。

模拟态标注: 本测试为模拟数据验证（MOU 锚定 D-011），不构成真实配置权执行路径；通知机硬件未投产部署。

覆盖（对应回报第 10 项之日抛终态实证）：
  1. _snapshot() 纳入 nca_lite_seq（迁移单测）
  2. resume_nca_seq 正例（续号）＋ 反例（负值/布尔/回退皆拒）
  3. 启动连续性校验：快照 seq 与盘上最大序号不一致 ⟹ 拒绝启动（fail-closed）
  4. 日抛终态实证：日抛调用 → 会话终结（export）→ 新会话 boot ⟹ seq 续号不复位（正例）；
     篡改快照序号（+5 无对应记录）⟹ 新会话被拒（反例）
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine.notification_machine_engine import (  # noqa: E402
    HardwareCall,
    HardwareCallType,
    NotificationMachineEngine,
)
from simulator.nm_simulator import NmSimulator  # noqa: E402


def _mk_call(tdid: str) -> HardwareCall:
    return HardwareCall(
        hw_type=HardwareCallType.FACT_CHAIN, tdid=tdid,
        scene="scene-phy-notification", payload="seq-test",
        call_value=500.0, tax_receipt=100.0,
    )


class TestSeqSnapshotAndResume(unittest.TestCase):
    """引擎侧：快照纳入 seq ＋ 回读校验。"""

    def test_snapshot_contains_seq(self):
        eng = NotificationMachineEngine(tdid="TDID-MOCK-SEQTEST1")
        eng.execute(_mk_call(eng.tdid))
        snap = eng.summary()  # summary 含 nca_lite_seq
        self.assertEqual(snap["nca_lite_seq"], 1)
        # 状态快照（持久化载体）亦含 seq
        rec_snap = eng.execute(_mk_call(eng.tdid)).state_snapshot
        self.assertIn("nca_lite_seq", rec_snap)
        self.assertEqual(rec_snap["nca_lite_seq"], 2)

    def test_resume_positive_continues(self):
        eng = NotificationMachineEngine(tdid="TDID-MOCK-SEQTEST2")
        eng.resume_nca_seq(7)
        rec = eng.execute(_mk_call(eng.tdid))
        self.assertTrue(rec.nca_lite["nca_id"].endswith("-0008"), rec.nca_lite["nca_id"])

    def test_resume_negative_rejected(self):
        eng = NotificationMachineEngine(tdid="TDID-MOCK-SEQTEST3")
        for bad in (-1, True, 1.5, "7", None):
            with self.assertRaises(ValueError, msg="bad seq %r 应拒" % bad):
                eng.resume_nca_seq(bad)  # type: ignore[arg-type]

    def test_resume_regression_rejected(self):
        eng = NotificationMachineEngine(tdid="TDID-MOCK-SEQTEST4")
        eng.execute(_mk_call(eng.tdid))  # 内存序号 → 1
        with self.assertRaises(ValueError):
            eng.resume_nca_seq(0)  # ⛔ 回退拒绝


class TestBootSeqContinuity(unittest.TestCase):
    """模拟器侧：启动回读 ＋ 连续性校验 ＋ 日抛终态续号。"""

    def test_disposable_terminal_seq_continues_across_sessions(self):
        """正例：日抛调用 → export（会话终结）→ 新会话 boot ⟹ 续号不复位。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            # 会话 1：上电 → 日抛调用 → 终结落盘
            sim1 = NmSimulator(batch_id="BSEQ1", out_dir=out)
            sim1.boot()
            recs = [sim1.call(HardwareCallType.FACT_CHAIN, value=500.0)]  # 日抛（DISPOSABLE）
            sim1.export_tdca(recs)
            seq1 = recs[-1].state_snapshot["nca_lite_seq"]
            self.assertGreaterEqual(seq1, 1)
            # 盘上 state.json 须携带 seq（持久化证据）
            disk = json.loads((out / ".tdca" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(disk["nca_lite_seq"], seq1)
            # 会话 2：同一 out_dir 重新上电 ⟹ 回读续号
            sim2 = NmSimulator(batch_id="BSEQ1", out_dir=out)
            boot_info = sim2.boot()
            self.assertEqual(boot_info["nca_seq_resumed_from"], seq1)
            rec2 = sim2.call(HardwareCallType.FACT_CHAIN, value=600.0)
            self.assertTrue(rec2.nca_lite["nca_id"].endswith("-{:04d}".format(seq1 + 1)),
                            rec2.nca_lite["nca_id"])

    def test_tampered_seq_refused_at_boot(self):
        """反例：快照序号被篡改（+5 无对应记录）⟹ 连续性校验拒绝启动。"""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sim1 = NmSimulator(batch_id="BSEQ2", out_dir=out)
            sim1.boot()
            recs = [sim1.call(HardwareCallType.FACT_CHAIN, value=500.0)]
            sim1.export_tdca(recs)
            state_path = out / ".tdca" / "state.json"
            snap = json.loads(state_path.read_text(encoding="utf-8"))
            snap["nca_lite_seq"] = snap["nca_lite_seq"] + 5  # 篡改：跳号
            state_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
            sim2 = NmSimulator(batch_id="BSEQ2", out_dir=out)
            with self.assertRaises(RuntimeError) as cm:
                sim2.boot()
            self.assertIn("连续性校验失败", str(cm.exception))

    def test_fresh_boot_no_resume(self):
        """对照：全新目录 boot 无回读（resumed_from=None），序号自 1 起。"""
        with tempfile.TemporaryDirectory() as td:
            sim = NmSimulator(batch_id="BSEQ3", out_dir=Path(td))
            info = sim.boot()
            self.assertIsNone(info["nca_seq_resumed_from"])
            rec = sim.call(HardwareCallType.FACT_CHAIN, value=100.0)
            self.assertTrue(rec.nca_lite["nca_id"].endswith("-0001"))


if __name__ == "__main__":
    unittest.main()
