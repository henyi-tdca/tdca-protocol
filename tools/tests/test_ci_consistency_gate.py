# -*- coding: utf-8 -*-
"""tools/ci_consistency_gate.py 的单元测试（GSEQ-2902 块 A）。

覆盖：
  · 嵌套块注释 /- … -/（含 /-! 文档注释）与 -- 行注释的剥离正确性；
  · claims-check 三规则（a CI 覆盖 / b sorry 与机验声称互斥 / c 矩阵交叉）正反例；
  · format-check：BOM / 混合行尾 / 正常件；
  · observe：基线 升 / 降 / 平 三分支（永远 exit 0）。

夹具全部落在 tmp_path，不触碰真实仓。
注：占位标记在测试中以拼接形式出现，避免本测试件自身混入真实仓的占位计数口径。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ci_consistency_gate as gate  # noqa: E402

MARK = "占" + "位"  # 两字占位标记（拼接，避免自计数）

YML_OK = (
    "on:\n  push:\n    paths:\n"
    '      - "core-go/docs/formal-proofs/lean/**"\n'
    '      - "core-go/docs/formal-proofs/lean-tdca/**"\n'
)
YML_LACKING = (
    "on:\n  push:\n    paths:\n"
    '      - "core-go/docs/formal-proofs/lean/**"\n'
)

LEAN_VERIFIED = (
    "/-\n  测试件头。\n  机验状态：本机已机验（2026-09-23，Lean 4.34.0-rc2）。\n-/\n"
    "namespace T\n/-- 恒真 -/\ntheorem t : True := trivial\nend T\n"
)
LEAN_SORRY_CLEAN_HEADER = (
    "/-\n  测试件头：证明尝试（未机验）。\n-/\n"
    "namespace T\ntheorem t : True := by sorry\nend T\n"
)
LEAN_SORRY_VERIFIED_HEADER = (
    "/-\n  机验状态：本机已机验（2026-09-23）。\n-/\n"
    "namespace T\ntheorem t : True := by sorry\nend T\n"
)

TDCA_REL = "core-go/docs/formal-proofs/lean-tdca/TDCA"
MATRIX_REL = "core-go/docs/formal-proofs/CLAIMS-MATRIX.md"
YML_REL = ".github/workflows/lean-verify.yml"


def make_root(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="")
    return tmp_path


# ---------------------------------------------------------------------------
# 注释剥离
# ---------------------------------------------------------------------------

class TestStrip:
    def test_nested_block_comment(self):
        text = "/- 外 /- 内 sorry -/ 仍注释 sorry -/ theorem t : True := by sorry\n"
        stripped = gate.strip_lean_comments(text)
        assert gate.code_sorry_count(text) == 1
        assert "sorry" in stripped
        # 注释内的 sorry 不得残留
        assert stripped.count("sorry") == 1

    def test_doc_comment_and_nested(self):
        text = "/-! 文档注释 /- 嵌套 -/ -/\ntheorem t : True := trivial\n"
        stripped = gate.strip_lean_comments(text)
        assert "文档注释" not in stripped
        assert "theorem t : True := trivial" in stripped

    def test_line_comment(self):
        text = "theorem t : True := by sorry -- 此处 sorry 字样在注释里\n-- sorry\n"
        assert gate.code_sorry_count(text) == 1

    def test_unclosed_block_swallows_rest(self):
        text = "theorem a : True := trivial\n/- 未闭合 sorry\n"
        assert gate.code_sorry_count(text) == 0

    def test_header_extraction(self):
        header = gate.extract_header_comments(LEAN_VERIFIED)
        assert "已机验" in header
        assert gate.header_has_verified_claim(LEAN_VERIFIED)
        assert not gate.header_has_verified_claim(LEAN_SORRY_CLEAN_HEADER)

    def test_header_stops_at_code(self):
        text = "/- 件头 -/\nnamespace T\n/- 这段不算件头 已机验 -/\n"
        assert not gate.header_has_verified_claim(text)


# ---------------------------------------------------------------------------
# claims-check 三规则正反例
# ---------------------------------------------------------------------------

class TestClaimsCheck:
    def test_rule_a_positive(self, tmp_path):
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_VERIFIED,
            YML_REL: YML_OK,
            MATRIX_REL: "| # | 声称 |\n",
        })
        assert gate.claims_check(root) == 0

    def test_rule_a_negative(self, tmp_path):
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_VERIFIED,
            YML_REL: YML_LACKING,
            MATRIX_REL: "| # | 声称 |\n",
        })
        assert gate.claims_check(root) == 1

    def test_rule_b_positive(self, tmp_path):
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_SORRY_CLEAN_HEADER,
            YML_REL: YML_OK,
            MATRIX_REL: "| # | 声称 |\n",
        })
        assert gate.claims_check(root) == 0

    def test_rule_b_negative(self, tmp_path):
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_SORRY_VERIFIED_HEADER,
            YML_REL: YML_OK,
            MATRIX_REL: "| # | 声称 |\n",
        })
        assert gate.claims_check(root) == 1

    def test_rule_c_missing_ref(self, tmp_path):
        root = make_root(tmp_path, {
            YML_REL: YML_OK,
            MATRIX_REL: "| A-9 | 声称 | `lean-tdca/TDCA/Ghost.lean` | ✅ |\n",
        })
        assert gate.claims_check(root) == 1

    def test_rule_c_pending_lag_negative(self, tmp_path):
        """[proof: pending] 行引用已机验件且同行无机验注记 → 登记滞后违规。"""
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_VERIFIED,
            YML_REL: YML_OK,
            MATRIX_REL: "| C-9 | 性质 | `lean-tdca/TDCA/Foo.lean` | [proof: pending] |\n",
        })
        assert gate.claims_check(root) == 1

    def test_rule_c_pending_lag_positive(self, tmp_path):
        """[proof: pending] 行引用已机验件，同行已注明机验 → 合规。"""
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_VERIFIED,
            YML_REL: YML_OK,
            MATRIX_REL: "| C-9 | 性质：`lean-tdca/TDCA/Foo.lean` 本机已机验（sorry=0）"
                        " | [proof: pending] |\n",
        })
        assert gate.claims_check(root) == 0

    def test_rule_c_done_with_sorry_negative(self, tmp_path):
        """✅ 机验声称引用 sorry>0 件 → 违规。"""
        root = make_root(tmp_path, {
            f"{TDCA_REL}/Foo.lean": LEAN_SORRY_CLEAN_HEADER,
            YML_REL: YML_OK,
            MATRIX_REL: "| A-9 | 声称 | `lean-tdca/TDCA/Foo.lean` | ✅ 已机验 |\n",
        })
        assert gate.claims_check(root) == 1

    def test_rule_c_research_side_ref_is_info(self, tmp_path):
        """research/ 路径引用属研究侧不入库件 → 不违规。"""
        root = make_root(tmp_path, {
            YML_REL: YML_OK,
            MATRIX_REL: "| A-3 | 声称 | `research/papers/formal/X-Candidate-V1.lean` | ✅ |\n",
        })
        assert gate.claims_check(root) == 0


# ---------------------------------------------------------------------------
# format-check
# ---------------------------------------------------------------------------

class TestFormatCheck:
    def test_normal_lf_file(self, tmp_path):
        p = tmp_path / "a.lean"
        p.write_bytes("theorem t : True := trivial\n".encode("utf-8"))
        assert gate.check_file_format(p) == []
        assert gate.format_check(None, ["a.lean"], root=tmp_path) == 0

    def test_consistent_crlf_ok(self, tmp_path):
        p = tmp_path / "a.lean"
        p.write_bytes(b"line1\r\nline2\r\n")
        assert gate.check_file_format(p) == []

    def test_bom_negative(self, tmp_path):
        p = tmp_path / "b.md"
        p.write_bytes(b"\xef\xbb\xbf# title\n")
        problems = gate.check_file_format(p)
        assert any("BOM" in x for x in problems)
        assert gate.format_check(None, ["b.md"], root=tmp_path) == 1

    def test_mixed_eol_negative(self, tmp_path):
        p = tmp_path / "c.lean"
        p.write_bytes(b"line1\r\nline2\n")
        problems = gate.check_file_format(p)
        assert any("行尾混用" in x for x in problems)
        assert gate.format_check(None, ["c.lean"], root=tmp_path) == 1

    def test_non_utf8_negative(self, tmp_path):
        p = tmp_path / "d.md"
        p.write_bytes(b"\xff\xfe not utf8\n")
        assert any("UTF-8" in x for x in gate.check_file_format(p))


# ---------------------------------------------------------------------------
# observe（永远 exit 0；基线升降平三分支）
# ---------------------------------------------------------------------------

def observe_root(tmp_path: Path, baseline: dict | None) -> Path:
    files = {
        f"{TDCA_REL}/Foo.lean": LEAN_VERIFIED,
        f"tools/probe.py": f"# {MARK} {MARK}\n",  # 2 处占位标记
    }
    if baseline is not None:
        files["tools/ci_observation_baseline.json"] = json.dumps(
            baseline, ensure_ascii=False)
    return make_root(tmp_path, files)


class TestObserve:
    def test_baseline_flat(self, tmp_path, capsys):
        root = observe_root(tmp_path, {"placeholders": 2})
        assert gate.observe(None, root=root) == 0
        out = capsys.readouterr().out
        assert "placeholders: 基线 2 → 现值 2（平）" in out

    def test_baseline_up(self, tmp_path, capsys):
        root = observe_root(tmp_path, {"placeholders": 0})
        assert gate.observe(None, root=root) == 0
        out = capsys.readouterr().out
        assert "⚠️ 计数上升（只报不挡）" in out

    def test_baseline_down(self, tmp_path, capsys):
        root = observe_root(tmp_path, {"placeholders": 5})
        assert gate.observe(None, root=root) == 0
        out = capsys.readouterr().out
        assert "placeholders: 基线 5 → 现值 2（降）" in out

    def test_no_baseline(self, tmp_path, capsys):
        root = observe_root(tmp_path, None)
        assert gate.observe(None, root=root) == 0
        assert "无基线" in capsys.readouterr().out

    def test_build_log_counts(self, tmp_path, capsys):
        root = observe_root(tmp_path, {"warnings": 0, "deprecations": 0})
        log = tmp_path / "build.log"
        log.write_text(
            "warning: declaration uses 'sorry'\n"
            "warning: `Foo` has been deprecated\n"
            "info: ok\n", encoding="utf-8")
        assert gate.observe(str(log), root=root) == 0
        out = capsys.readouterr().out
        assert "warnings: 基线 0 → 现值 2（⚠️ 计数上升（只报不挡））" in out
        assert "deprecations: 基线 0 → 现值 1（⚠️ 计数上升（只报不挡））" in out

    def test_missing_log_noted(self, tmp_path, capsys):
        root = observe_root(tmp_path, None)
        assert gate.observe(str(tmp_path / "nope.log"), root=root) == 0
        assert "不存在，记 0" in capsys.readouterr().out

    def test_note_age_metric(self, tmp_path, capsys):
        root = observe_root(tmp_path, {"max_note_age_days": 0})
        assert gate.observe(None, root=root) == 0
        out = capsys.readouterr().out
        assert "max_note_age_days" in out
