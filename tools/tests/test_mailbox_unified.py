# -*- coding: utf-8 -*-
# FC-ID: ENG4-MAILBOX-001-T | 信箱归一三态自测（committed 夹具版）
"""tools/mailbox 归一形态测试：判据移植等价性 + 三态自测 + 统一入口。"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.mailbox.assertions import assert_box
from tools.mailbox.seal import check_one, seal_one
from tools.mailbox.selftest import GOOD_MAIL, _make_sealed, _write, run_selftest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_check_equivalence_with_legacy_tool():
    """归一库 check_one 与 TOOL-SEAL-001 v1.2 对同一件给同一 C 组读数。"""
    legacy = r"C:/Users/22850/Desktop/TDCA交付取件/TOOL-SEAL-001/_deliver_seal_v1.py"
    if not os.path.exists(legacy):
        pytest.skip("TOOL-SEAL-001 不在本机")
    import tempfile
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "EQ-样件.md")
    _write(p, GOOD_MAIL.replace("{zero}", "0" * 16))
    seal_one(p)
    mine, my_fails = check_one(p)
    r = subprocess.run([sys.executable, legacy, "--check", p],
                       capture_output=True, text=True, encoding="utf-8")
    assert my_fails == 0, mine
    assert "DELIVER_VERDICT=PASS" in r.stdout


def test_seal_idempotent_and_refuse_mismatch():
    import tempfile
    tmp = tempfile.mkdtemp()
    p = _make_sealed(tmp, "IDEM.md")
    assert seal_one(p)[0] == "KEEP"
    _write(p + ".sha256", "F" * 16 + "\n")
    assert seal_one(p)[0] == "REFUSE"


def test_three_state_selftest():
    ok, lines = run_selftest()
    assert ok, lines
    assert any("SELFTEST_VERDICT=PASS" in ln for ln in lines)


def test_cli_selftest_entry():
    r = subprocess.run([sys.executable, "-m", "tools.mailbox.mailbox", "selftest"],
                       cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert "MAILBOX" not in r.stdout or "VERDICT=PASS" in r.stdout


def test_box_assertion_counts():
    import tempfile
    tmp = tempfile.mkdtemp()
    box = os.path.join(tmp, "FROM-EXEC")
    os.makedirs(box)
    _make_sealed(box, "T1.md")
    _make_sealed(box, "T2.md")
    rows, fails, stat = assert_box(box)
    assert fails == 0
    assert stat["contents"] == 2 and stat["sidecars"] == 2
    codes = [c for _, c, _ in rows]
    assert {"A1", "A2", "A3", "Z1", "Z2", "Z3", "Z4", "C组"} <= set(codes)
