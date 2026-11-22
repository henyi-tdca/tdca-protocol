# -*- coding: utf-8 -*-
"""DOCNAME-001（L1SI225）三步闸＋第⓿步族级入册测试。

覆盖：
- classify_a：A1~A5 各条正反例（乙类一律不拦：中文／下划线／全角括号／版本号 V0.x）。
- gate：⓿族未入册判语「待族入册后重过」、②族已入册件未入表仍拒、③显示名映射值违禁拒。
- 可重跑：同输入两次 gate 结论一致（纯函数无随机无时钟）。
- 存量巡检豁免锁定：白名单现存甲类病件集合 == 停手豁免清单（本令 S-5 停手 3 件），
  新增任何甲类病件即红（防回归）；豁免项整改后须同步收缩本清单。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from docname_gate import audit, classify_a, gate, load_registry

# 本令 S-5 停手 3 件（整改候裁中，白名单暂留）：(family, rel, hits)
EXPECTED_EXEMPTIONS = {
    ("regulation", "README.md", ("A1",)),
    # ENCNAME-002（L1SI226，创始人取甲）：EN/机读两件已改净名并退出扫描面，豁免随白名单同步收缩（3→1）；
    # 新名 regulation-相遇公开说明-en.md/.yaml 经 classify_a 零命中（A1~A5 全过），不再属豁免件。
}


def test_a1_bare_generic_name_only_without_prefix():
    assert classify_a("README.md") == ["A1"]
    assert classify_a("OPENING-LEDGER.md") == ["A1"]
    assert classify_a("hundred_schools/README.md") == []  # 目录前缀＝有区分信息，不病


def test_a2_spaces_half_and_full_width():
    assert classify_a("a b.md") == ["A2"]
    assert classify_a("第01百家-道德经 (道家根本经典).yaml") == ["A2"]
    assert classify_a("第01百家-道德经（道家根本经典）.yaml") == []  # 全角括号无空格＝过


def test_a3_over_80_chars():
    long_name = "x" * 81  # 81 字符即超（无扩展名也病）
    assert classify_a(long_name) == ["A3"]
    assert classify_a("x" * 80) == []
    # 判的是路径末段，不含目录前缀
    assert classify_a("dir/" + "x" * 81) == ["A3"]


def test_a4_tentative_markers_but_version_ok():
    for bad in ("X-DRAFT.md", "X-TENTATIVE.md", "X-待审.md", "X-待签批.md", "X-征求意见.md"):
        assert "A4" in classify_a(bad), bad
    assert classify_a("宪法（V0.1）.md") == []  # 版本号＝乙类 B4，⛔不拦（令面特别提醒）


def test_a5_hyphen_rules():
    assert "A5" in classify_a("a--b.md")
    assert "A5" in classify_a("-a.md")
    assert "A5" in classify_a("a-.md")
    assert classify_a("a-b.md") == []


def test_b_class_never_blocked():
    # B1 中文 / B2 下划线 / B3 全角括号 / B4 版本号——一律不过甲类
    assert classify_a("第01机制-机制设计（可审计）-V1.0-PUB.yaml") == []
    assert classify_a("COMPOSITION-REPORT-道德经_可审计决策.md") == []


def test_gate_family_not_registered_verdict_wording():
    docs, display = load_registry()
    v, r = gate("cognitive-compiler", "whatever.md", docs, display)
    assert v == "REJECT" and "待族入册后重过" in r
    assert "该文档不存在" not in r


def test_gate_registered_family_but_piece_not_listed():
    docs, display = load_registry()
    v, r = gate("cop-library", "never-listed-piece.md", docs, display)
    assert v == "REJECT" and "②未在册" in r


def test_gate_display_name_value_banned():
    docs, display = load_registry()
    docs = dict(docs)
    docs["cop-library"] = tuple(docs["cop-library"]) + ("demo-件.md",)
    v, r = gate("cop-library", "demo-件.md", docs,
                {"demo-件.md": "某制度（T-006 依据）.md"})
    assert v == "REJECT" and "③" in r
    v, _ = gate("cop-library", "demo-件.md", docs, {"demo-件.md": "某制度（V1.0）.md"})
    assert v == "PASS"


def test_gate_rerun_deterministic():
    docs, display = load_registry()
    samples = [("cop-library", "README.md"), ("cop-library", "cop-library-族索引说明.md"),
               ("papers", "never-listed.md"), ("paper", "TDCA-paper-CN.md")]
    for fam, rel in samples:
        assert gate(fam, rel, docs, display) == gate(fam, rel, docs, display)


def test_whitelist_audit_locked_to_exemptions():
    docs, _ = load_registry()
    actual = {(fam, rel, tuple(hits)) for fam, rel, hits in audit(docs)}
    assert actual == EXPECTED_EXEMPTIONS, (
        f"白名单甲类存量与豁免清单不符：新增 {actual - EXPECTED_EXEMPTIONS}，"
        f"已消 {EXPECTED_EXEMPTIONS - actual}（整改后须同步收缩清单）")
