# FC-ID: TDCA-TASK-CTS-L1-001 | CTS-L1 套件自测（≥15 例，含负例判别力验证）
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # tools/
from cts_l1.__main__ import main as cli_main  # noqa: E402
from cts_l1.report import build_report, issue_declaration  # noqa: E402
from cts_l1.reference.bad_agent import make_agent as make_bad  # noqa: E402
from cts_l1.reference.ref_agent import make_agent  # noqa: E402
from cts_l1.runners import ALL_CASES, run_all  # noqa: E402


@pytest.fixture()
def ref_results():
    return run_all(make_agent())


@pytest.fixture()
def bad_results():
    return run_all(make_bad())


# ---- 套件结构 ----

def test_case_count_covers_profile():
    """轮廓 L1 全部用例覆盖：C1×3 + C2×3 + C3×3 + C4×2 + C5×2 + C6×4 + G×2 = 19"""
    ids = [fn.__name__.upper().replace("_", "-") for fn in ALL_CASES]
    assert len(ALL_CASES) == 19
    for req in ("C1-", "C2-", "C3-", "C4-", "C5-", "C6-", "G1", "G2"):
        assert any(i.startswith(req) for i in ids), f"缺 {req} 用例"


def test_case_ids_unique():
    fns = [f.__name__ for f in ALL_CASES]
    assert len(fns) == len(set(fns))


# ---- 参考实现全过 ----

def test_ref_all_pass(ref_results):
    fails = [r.case_id for r in ref_results if not r.passed]
    assert not fails, f"参考实现应全过，实际 FAIL: {fails}"


def test_ref_all_simulated(ref_results):
    assert all(r.provenance == "simulated" for r in ref_results)


@pytest.mark.parametrize("cid", ["C1-T1", "C2-T2", "C3-T1", "C4-T1", "C5-T1", "C6-T4"])
def test_ref_spot_cases(ref_results, cid):
    r = next(x for x in ref_results if x.case_id == cid)
    assert r.passed, r.detail


# ---- 声明签发 ----

def test_declaration_issued_on_full_pass(ref_results):
    rep = build_report("ref-agent-001", "V2.1", ref_results)
    decl = issue_declaration(rep)
    assert decl and decl["declaration_type"] == "TDCA-Native-L1"
    assert decl["declaration_hash"].startswith("sha256:")
    assert len(decl["passed_cases"]) == 19


def test_declaration_withheld_on_fail(bad_results):
    rep = build_report("bad-agent-000", "V2.1", bad_results)
    assert issue_declaration(rep) is None


def test_report_counts(ref_results):
    rep = build_report("ref-agent-001", "V2.1", ref_results)
    assert rep["total"] == 19 and rep["passed"] == 19 and rep["all_pass"]
    assert rep["data_provenance"] == "simulated"


# ---- 负例判别力（A-4）----

def test_bad_agent_fails(bad_results):
    failed = {r.case_id for r in bad_results if not r.passed}
    # 坏实现至少须在以下关键用例被抓住
    assert {"C1-T2", "C3-T1", "C6-T1", "C6-T2", "C6-T4", "G-2"} <= failed, failed


def test_bad_calibration_attack_caught(bad_results):
    r = next(x for x in bad_results if x.case_id == "C6-T1")
    assert not r.passed


def test_bad_silent_rewrite_caught(bad_results):
    r = next(x for x in bad_results if x.case_id == "C6-T4")
    assert not r.passed


def test_bad_no_provenance_caught(bad_results):
    r = next(x for x in bad_results if x.case_id == "G-2")
    assert not r.passed


def test_bad_tax_rate_caught(bad_results):
    r = next(x for x in bad_results if x.case_id == "C3-T1")
    assert not r.passed


# ---- CLI ----

def test_cli_ref_exit_0(tmp_path, capsys):
    rc = cli_main(["--target", "cts_l1.reference.ref_agent",
                   "--json", str(tmp_path / "r.json"),
                   "--declaration", str(tmp_path / "d.json")])
    assert rc == 0
    rep = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    decl = json.loads((tmp_path / "d.json").read_text(encoding="utf-8"))
    assert rep["all_pass"] and decl["agent_id"] == "ref-agent-001"


def test_cli_bad_exit_1(tmp_path):
    rc = cli_main(["--target", "cts_l1.reference.bad_agent",
                   "--json", str(tmp_path / "r.json"),
                   "--declaration", str(tmp_path / "d.json")])
    assert rc == 1 and not (tmp_path / "d.json").exists()  # FAIL 不出声明


def test_cli_bad_target_exit_2():
    assert cli_main(["--target", "no.such.module:nope"]) == 2


def test_cli_md_report(tmp_path):
    rc = cli_main(["--target", "cts_l1.reference.ref_agent", "--md", str(tmp_path / "r.md")])
    text = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert rc == 0 and "CTS-L1 一致性报告" in text and "C6-T4" in text
