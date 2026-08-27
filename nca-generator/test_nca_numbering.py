# -*- coding: utf-8 -*-
"""NCA 编号机制补丁测试（GSEQ-0544 · 选项 B+C）

覆盖:
  T1 占用顺延      —— 目标编号被手动占用 → 顺延到 max+1，且不覆盖原文件
  T2 编号选取      —— GSEQ-0551 口径：中间断号（含 gap）后取 max+1（保留缺口，不回填）
  T3 链连续性      —— 连续生成 N 条，编号连续、无重叠、无缺口
  T4 手动分配拒绝  —— 传入 explicit_seq 触发 ValueError（禁止手动预分配）
  T5 并发模拟      —— 多线程同时生成，编号全部唯一（O_EXCL 原子预约）
  T6 纪律校验 lint —— verify_numbering_discipline 检出疑似手动预分配

运行: python test_nca_numbering.py   (或 pytest test_nca_numbering.py)
"""
import os
import sys
import glob
import tempfile
import threading
import datetime
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import nca_generator as NCA  # noqa: E402


def _today():
    return datetime.datetime.now().strftime("%Y%m%d")


def _mk_manual(nca_dir, seq, content=None):
    """手工造一个 NCA 文件（模拟人工预分配，不带 Generated-By 标记）"""
    path = os.path.join(nca_dir, f"TDCA-REASONIX-{_today()}-{seq:03d}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or (
            f"NCA-ID: TDCA-REASONIX-{_today()}-{seq:03d}\n"
            "Operation-Type: ManualPreAlloc\n"
        ))
    return path


class NcaNumberingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nca_test_")
        # 关键：把所有编号落盘指向临时目录，绝不触碰真实 .tdca-nca
        NCA.NCA_DIR = self.tmp
        self.assertTrue(NCA.NCA_DIR.startswith(self.tmp), "NCA_DIR 必须指向临时目录")

    def tearDown(self):
        for p in glob.glob(os.path.join(self.tmp, "*")):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(self.tmp)
        except OSError:
            pass

    def _gen(self, **kw):
        return NCA.generate_nca(
            operation_type=kw.pop("operation_type", "CodeGen"),
            scope=kw.pop("scope", "test-scope"),
            pre_state=kw.pop("pre_state", {"path": "(v)", "hash": None, "size": 0, "exists": False, "backup": None}),
            post_state=kw.pop("post_state", None),
            function_call_id=kw.pop("function_call_id", "TDCA-FC-TEST"),
            **kw,
        )

    # ---- T1 占用顺延（真实事故场景：手动占 001 → 顺延首个空闲位 002 且不覆盖） ----
    def test_T1_occupied_advance_no_overwrite(self):
        # 模拟旧事故：人工预分配了编号 001（旧机制会复用并覆盖它）
        manual_path = _mk_manual(self.tmp, 1, "NCA-ID: TDCA-REASONIX-%s-001\nOperation-Type: ManualPreAlloc\n" % _today())
        with open(manual_path, "r", encoding="utf-8") as f:
            original = f.read()
        nid, npath, _ = self._gen()
        # 落盘前扫盘：001 被占 → max+1 口径顺延到 002（保留缺口语义，见 GSEQ-0551）
        self.assertTrue(nid.endswith("-002"), f"占用 001 后应顺延到首个空闲位 002，实际 {nid}")
        self.assertNotEqual(npath, manual_path)
        # 手动预分配文件绝不被覆盖
        with open(manual_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), original)
        self.assertTrue(os.path.isfile(manual_path))

    # ---- T1b 高位手动占用也不被覆盖（原事故 155 复现，max+1 口径） ----
    def test_T1b_high_manual_occupied_not_overwritten(self):
        manual_path = _mk_manual(self.tmp, 155, "NCA-ID: TDCA-REASONIX-%s-155\nOperation-Type: ManualPreAlloc\n" % _today())
        with open(manual_path, "r", encoding="utf-8") as f:
            original = f.read()
        nid, _, _ = self._gen()
        self.assertFalse(nid.endswith("-155"), "不得复用被手动占用的 155")
        self.assertEqual(nid, "TDCA-REASONIX-%s-156" % _today(), "max+1 口径下高位占用 155 后应顺延到 156")
        with open(manual_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), original)

    # ---- T2 编号选取（GSEQ-0551 口径：中间断号 001..003 缺 002 → 取 max+1 = 004，保留缺口） ----
    def test_T2_first_free_slot_mid_gap(self):
        _mk_manual(self.tmp, 1)
        _mk_manual(self.tmp, 3)
        nid, _, _ = self._gen()
        self.assertTrue(nid.endswith("-004"), f"max+1 口径下中间断号应取 004（保留缺口），实际 {nid}")

    # ---- T3 链连续性（生成 50 条，编号恰好 {1..50} 连续无重叠） ----
    def test_T3_chain_continuity(self):
        seqs = []
        for _ in range(50):
            nid, _, _ = self._gen()
            seqs.append(int(nid.split("-")[-1]))
        self.assertEqual(sorted(seqs), list(range(1, 51)), "编号应连续 1..50 无缺口/无重叠")
        self.assertEqual(len(set(seqs)), 50, "编号不得重叠")

    # ---- T4 手动分配拒绝（explicit_seq 触发 ValueError） ----
    def test_T4_manual_prealloc_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._gen(explicit_seq=5)
        self.assertIn("禁止手动预分配编号", str(ctx.exception))
        # 不应产生任何文件
        self.assertEqual(len(NCA.list_ncas()), 0)

    # ---- T5 并发模拟（25 线程同时生成，编号全部唯一） ----
    def test_T5_concurrency_unique(self):
        N = 25
        barrier = threading.Barrier(N)
        results = []
        rlock = threading.Lock()

        def worker():
            barrier.wait()
            nid, npath, _ = self._gen()
            with rlock:
                results.append((nid, npath))

        threads = [threading.Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), N)
        ids = [r[0] for r in results]
        self.assertEqual(len(set(ids)), N, "并发下编号不得重复（O_EXCL 原子预约）")
        for nid, npath in results:
            self.assertTrue(os.path.isfile(npath), f"落盘文件应存在: {npath}")
        # 并发结果应落在 1..N 区间且占满
        seqs = sorted(int(i.split("-")[-1]) for i in ids)
        self.assertEqual(seqs, list(range(1, N + 1)), "并发生成应无缺口地占满 1..N")

    # ---- T6 纪律校验 lint（检出疑似手动预分配） ----
    def test_T6_discipline_lint(self):
        # 先经 API 生成一条（带 Generated-By 标记）→ 应通过
        self._gen()
        rep = NCA.verify_numbering_discipline(nca_dir=self.tmp, require_marker=True)
        self.assertTrue(rep["ok"], f"纯 API 生成应通过纪律校验: {rep['violations']}")
        # 手工造一个无标记文件 → 应被检出
        _mk_manual(self.tmp, 99)
        rep2 = NCA.verify_numbering_discipline(nca_dir=self.tmp, require_marker=True)
        self.assertFalse(rep2["ok"], "存在手动预分配文件时纪律校验应失败")
        self.assertTrue(
            any("疑似手动预分配" in v for v in rep2["violations"]),
            f"应检出手动预分配: {rep2['violations']}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
