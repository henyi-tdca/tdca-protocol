#!/usr/bin/env python3
"""ci_consistency_gate.py —— GSEQ-2902 块 A 一致性闸门（档二②b②c＋档三引擎）

三档模型（只加严，既有豁免锁现状）：
  档二②b claims-check  声称-证据一致性硬闸（exit 1 = 违规）
  档二②c format-check   新增件格式硬闸（UTF-8 / 无 BOM / 行尾一致）
  档三   observe        观察门·只报不挡（永远 exit 0）

口径声明（写死，不得随风改动）：
  · sorry 占位判定：以「剥离注释后的代码级 sorry」为准（注释提及另计，不混算）；
    CI 侧以构建输出中 "declaration uses 'sorry'" 警告计数为准。
  · 注释剥离：支持 Lean 嵌套块注释 /- … -/（可嵌套，/-! 与 /-- 文档注释同属块注释）
    与 -- 行注释；剥离时保留换行以维持行号。
  · 「占位」计数：tdca-adapters/ 与 tools/ 下全部 *.py（排除 __pycache__）中
    两字占位标记的纯字面出现次数之和（含本脚本注释中的字面出现，口径固定不自欺除外）。
  · 注记时效：lean-tdca 各件头「本机已机验（YYYY-MM-DD…）」中可解析日期，
    报距今最长天数；无日期的「已机验」件单列提示。
  · 研究侧引用：CLAIMS-MATRIX 中路径含 research/ 的 *.lean 引用属「研究侧、不入库」
    件（披露口径见 lean-tdca/README.md 头注），存在性检查降级为 INFO，不作违规；
    仓内路径引用一律硬查。

Python 3.12 标准库；⛔ 不联网。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

VERIFIED_MARK = "已机验"
SORRY_WARN_RE = re.compile(r"declaration uses .?sorry.?")
LEAN_REF_RE = re.compile(r"[A-Za-z0-9_./-]+\.lean")
VERIFIED_DATE_RE = re.compile(r"本机已机验（(\d{4})-(\d{2})-(\d{2})")
PLACEHOLDER_MARK = "占" + "位"  # 两字占位标记（拼接以免本行混入自计数，口径见模块 docstring）


def _tdca_dir(root: Path) -> Path:
    return root / "core-go" / "docs" / "formal-proofs" / "lean-tdca" / "TDCA"


def _lean_tdca_dir(root: Path) -> Path:
    return root / "core-go" / "docs" / "formal-proofs" / "lean-tdca"


def _claims_matrix(root: Path) -> Path:
    return root / "core-go" / "docs" / "formal-proofs" / "CLAIMS-MATRIX.md"


def _lean_verify_yml(root: Path) -> Path:
    return root / ".github" / "workflows" / "lean-verify.yml"


def _baseline_json(root: Path) -> Path:
    return root / "tools" / "ci_observation_baseline.json"


# ---------------------------------------------------------------------------
# Lean 注释剥离（嵌套块注释 /- … -/ 与行注释 --）
# ---------------------------------------------------------------------------

def strip_lean_comments(text: str) -> str:
    """剥离 Lean 注释，保留换行与非注释字符的相对位置（注释字符替换为空格）。

    状态机：code / line_comment / block_comment(depth，支持嵌套)。
    不支持字符串字面量内的 /-（本仓工程件无此形态；若有须另议口径）。
    """
    out: list[str] = []
    i, n = 0, len(text)
    depth = 0
    in_line = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line:
            if ch == "\n":
                in_line = False
                out.append(ch)
            else:
                out.append(" ")
            i += 1
        elif depth > 0:
            if ch == "/" and nxt == "-":
                depth += 1
                out.append("  ")
                i += 2
            elif ch == "-" and nxt == "/":
                depth -= 1
                out.append("  ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
        else:
            if ch == "-" and nxt == "-":
                in_line = True
                out.append("  ")
                i += 2
            elif ch == "/" and nxt == "-":
                depth = 1
                out.append("  ")
                i += 2
            else:
                out.append(ch)
                i += 1
    return "".join(out)


def extract_header_comments(text: str) -> str:
    """提取「件头」：文件起始处连续的注释区（块注释 + 行注释 + 空白）。"""
    parts: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
        elif ch == "-" and i + 1 < n and text[i + 1] == "-":
            j = text.find("\n", i)
            j = n if j == -1 else j
            parts.append(text[i:j])
            i = j
        elif ch == "/" and i + 1 < n and text[i + 1] == "-":
            depth, j = 1, i + 2
            while j < n and depth > 0:
                if text[j] == "/" and j + 1 < n and text[j + 1] == "-":
                    depth += 1
                    j += 2
                elif text[j] == "-" and j + 1 < n and text[j + 1] == "/":
                    depth -= 1
                    j += 2
                else:
                    j += 1
            parts.append(text[i:j])
            i = j
        else:
            break
    return "\n".join(parts)


def code_sorry_count(text: str) -> int:
    """代码级 sorry 计数（剥离注释后，按标识符边界计）。"""
    stripped = strip_lean_comments(text)
    return len(re.findall(r"(?<![A-Za-z0-9_])sorry(?![A-Za-z0-9_'])", stripped))


def header_has_verified_claim(text: str) -> bool:
    return VERIFIED_MARK in extract_header_comments(text)


# ---------------------------------------------------------------------------
# 仓内 .lean 索引
# ---------------------------------------------------------------------------

def build_lean_index(root: Path) -> list[Path]:
    return sorted(root.rglob("*.lean"))


def resolve_lean_ref(token: str, index: list[Path], root: Path) -> Path | None:
    """矩阵中的 .lean 引用 → 仓内文件。匹配口径：仓内相对路径后缀匹配，或文件名匹配。"""
    norm = token.replace("\\", "/").lstrip("./")
    hits = [p for p in index
            if p.relative_to(root).as_posix().endswith(norm) or p.name == norm]
    return hits[0] if hits else None


# ---------------------------------------------------------------------------
# 档二②b claims-check（硬闸）
# ---------------------------------------------------------------------------

def claims_check(root: Path = REPO_ROOT) -> int:
    violations: list[str] = []
    infos: list[str] = []

    tdca_dir = _tdca_dir(root)
    tdca_files = sorted(tdca_dir.glob("*.lean")) if tdca_dir.is_dir() else []
    yml_path = _lean_verify_yml(root)
    yml_text = yml_path.read_text(encoding="utf-8") if yml_path.is_file() else ""
    trigger_covered = "lean-tdca/**" in yml_text

    # 规则 a：件头含「已机验」→ 必须被 CI 覆盖
    print("== 规则 a：已机验件 CI 覆盖核对 ==")
    for f in tdca_files:
        text = f.read_text(encoding="utf-8")
        if not header_has_verified_claim(text):
            continue
        in_project = _lean_tdca_dir(root) in f.parents
        covered = trigger_covered and in_project
        status = "✅ 被覆盖" if covered else "❌ 未覆盖"
        print(f"  {f.name}: 件头「已机验」→ {status}")
        if not covered:
            violations.append(
                f"规则a: {f.relative_to(root)} 件头声称已机验，但未被 lean-verify.yml "
                f"lean-tdca/** 触发路径覆盖")
    if not trigger_covered:
        infos.append("lean-verify.yml 未见 lean-tdca/** 触发路径")

    # 规则 b：代码级 sorry>0 → 件头不得含「已机验」「proved」声称
    print("== 规则 b：sorry 占位与机验声称互斥 ==")
    for f in tdca_files:
        text = f.read_text(encoding="utf-8")
        sc = code_sorry_count(text)
        if sc > 0:
            header = extract_header_comments(text)
            bad = [m for m in (VERIFIED_MARK, "proved") if m in header]
            if bad:
                violations.append(
                    f"规则b: {f.relative_to(root)} 代码级 sorry={sc}，"
                    f"件头却含声称标记 {bad}")
                print(f"  {f.name}: ❌ sorry={sc} 且件头含 {bad}")
            else:
                print(f"  {f.name}: sorry={sc}（件头无机验声称，合规）")

    # 规则 c：CLAIMS-MATRIX 交叉
    print("== 规则 c：CLAIMS-MATRIX 交叉核对 ==")
    index = build_lean_index(root)
    matrix_path = _claims_matrix(root)
    matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.is_file() else ""
    for lineno, line in enumerate(matrix.splitlines(), 1):
        refs = LEAN_REF_RE.findall(line)
        if not refs:
            continue
        resolved = []
        for tok in refs:
            norm = tok.replace("\\", "/")
            if "research/" in norm:
                infos.append(f"  第{lineno}行: {tok} 为研究侧引用（不入库），存在性检查降级 INFO")
                continue
            p = resolve_lean_ref(tok, index, root)
            if p is None:
                violations.append(f"规则c: 第{lineno}行引用 {tok} 在仓内不存在")
                print(f"  第{lineno}行: ❌ {tok} 不存在")
            else:
                resolved.append((tok, p))
        # c-2：[proof: pending] 行引用已机验（sorry=0）件 → 同行须有机验注记，否则登记滞后
        if "[proof: pending]" in line:
            for tok, p in resolved:
                text = p.read_text(encoding="utf-8")
                if code_sorry_count(text) == 0 and header_has_verified_claim(text):
                    if VERIFIED_MARK not in line:
                        violations.append(
                            f"规则c: 第{lineno}行 [proof: pending] 引用了已机验件 {tok}"
                            f"（sorry=0 且件头标已机验），同行无机验注记 → 登记滞后")
                        print(f"  第{lineno}行: ❌ 登记滞后（{tok}）")
        # c-3：[proof: done] / ✅ 机验声称 → 引用件须存在且 sorry=0
        if "[proof: done]" in line or "✅" in line:
            for tok, p in resolved:
                text = p.read_text(encoding="utf-8")
                sc = code_sorry_count(text)
                if sc > 0:
                    violations.append(
                        f"规则c: 第{lineno}行 ✅/done 机验声称引用 {tok}，"
                        f"但该件代码级 sorry={sc}")
                    print(f"  第{lineno}行: ❌ {tok} sorry={sc}")

    for msg in infos:
        print(msg)
    print(f"\nclaims-check: 违规 {len(violations)} 处")
    for v in violations:
        print(f"  VIOLATION: {v}")
    return 1 if violations else 0


# ---------------------------------------------------------------------------
# 档二②c format-check（硬闸）
# ---------------------------------------------------------------------------

def check_file_format(path: Path) -> list[str]:
    problems: list[str] = []
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.append(f"非 UTF-8 可解码（{e}）")
        return problems
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("含 UTF-8 BOM")
    body = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
    # 行尾一致性：剥离 CRLF 后，剩余裸 \r 或裸 \n 与 CRLF 并存即混用
    crlf = body.count(b"\r\n")
    rest = body.replace(b"\r\n", b"")
    lone_cr = rest.count(b"\r")
    lone_lf = rest.count(b"\n")
    kinds = sum(1 for k in (crlf, lone_cr, lone_lf) if k > 0)
    if kinds > 1:
        problems.append(f"行尾混用（CRLF={crlf} 裸CR={lone_cr} 裸LF={lone_lf}）")
    return problems


def format_check(base: str | None, files: list[str] | None,
                 root: Path = REPO_ROOT) -> int:
    targets: list[Path] = []
    if files:
        targets = [Path(f) if Path(f).is_absolute() else root / f for f in files]
    elif base:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
            cwd=root, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"::error::git diff 失败（base={base}）：{proc.stderr.strip()}")
            return 1
        targets = [root / line.strip() for line in proc.stdout.splitlines()
                   if line.strip().endswith((".lean", ".md"))]
    else:
        print("::error::format-check 需要 --base 或 --files")
        return 1

    print(f"format-check: 新增件 {len(targets)} 件")
    violations = 0
    for t in targets:
        if not t.is_file():
            print(f"  ❌ {t}: 不存在")
            violations += 1
            continue
        problems = check_file_format(t)
        rel = t.relative_to(root) if root in t.parents else t
        if problems:
            violations += 1
            for p in problems:
                print(f"  ❌ {rel}: {p}")
        else:
            print(f"  ✅ {rel}")
    print(f"format-check: 违规 {violations} 处")
    return 1 if violations else 0


# ---------------------------------------------------------------------------
# 档三 observe（观察门·只报不挡，永远 exit 0）
# ---------------------------------------------------------------------------

def count_placeholder(root: Path = REPO_ROOT) -> int:
    total = 0
    for base in (root / "tdca-adapters", root / "tools"):
        if not base.is_dir():
            continue
        for f in base.rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            try:
                total += f.read_text(encoding="utf-8", errors="replace").count(PLACEHOLDER_MARK)
            except OSError:
                pass
    return total


def note_age_days(root: Path = REPO_ROOT,
                  today: date | None = None) -> tuple[int | None, list[str]]:
    """lean-tdca 各件头「本机已机验（YYYY-MM-DD）」距今最长天数；附无日期件清单。"""
    best: int | None = None
    undated: list[str] = []
    today = today or date.today()
    lean_dir = _lean_tdca_dir(root)
    if not lean_dir.is_dir():
        return None, []
    for f in sorted(lean_dir.rglob("*.lean")):
        try:
            header = extract_header_comments(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        if VERIFIED_MARK not in header:
            continue
        m = VERIFIED_DATE_RE.search(header)
        if m:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            age = (today - d).days
            best = age if best is None else max(best, age)
        else:
            undated.append(f.name)
    return best, undated


def observe(build_log: str | None, root: Path = REPO_ROOT) -> int:
    print("== 观察门·只报不挡（档三，本命令永远 exit 0）==")

    # 指标① 构建日志 warning / deprecation 计数
    warnings_n = deprecations_n = 0
    log_note = "未提供构建日志，记 0"
    if build_log and Path(build_log).is_file():
        lines = Path(build_log).read_text(encoding="utf-8", errors="replace").splitlines()
        warnings_n = sum(1 for ln in lines if re.search(r"(?i)\bwarning\b", ln))
        deprecations_n = sum(1 for ln in lines if re.search(r"(?i)deprecat", ln))
        log_note = f"日志 {build_log}"
    elif build_log:
        log_note = f"日志 {build_log} 不存在，记 0"

    # 指标② 占位声明计数
    placeholder_n = count_placeholder(root)

    # 指标③ 注记时效
    age, undated = note_age_days(root)
    age_val = age if age is not None else 0

    # 基线对比
    baseline: dict = {}
    baseline_path = _baseline_json(root)
    if baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"⚠️ 基线文件 {baseline_path} 解析失败，按无基线处理")

    metrics = [
        ("warnings", warnings_n, log_note),
        ("deprecations", deprecations_n, log_note),
        ("placeholders", placeholder_n, "tdca-adapters/ 与 tools/ 下 *.py 字面计数"),
        ("max_note_age_days", age_val, "lean-tdca 件头机验日期距今最长天数"),
    ]
    lines_out = ["## 观察门·只报不挡（GSEQ-2902 档三）", "",
                 "| 指标 | 基线 | 现值 | 变化 |", "|---|---|---|---|"]
    for key, cur, note in metrics:
        base_val = baseline.get(key)
        if isinstance(base_val, dict):
            base_val = base_val.get("value")
        if base_val is None:
            trend = "无基线"
        elif cur > base_val:
            trend = "⚠️ 计数上升（只报不挡）"
        elif cur < base_val:
            trend = "降"
        else:
            trend = "平"
        row = f"| {key} | {base_val if base_val is not None else '—'} | {cur} | {trend} |"
        print(f"{key}: 基线 {base_val if base_val is not None else '—'} → 现值 {cur}（{trend}）｜{note}")
        lines_out.append(row)
    if undated:
        msg = f"注记时效：{len(undated)} 件标「已机验」但件头无可解析日期：{', '.join(undated)}"
        print(msg)
        lines_out += ["", f"- {msg}"]

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines_out) + "\n")
    print("observe: 完成（exit 0，只报不挡）")
    return 0


# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci_consistency_gate",
                                 description="GSEQ-2902 块 A 一致性闸门（三档模型）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("claims-check", help="声称-证据一致性硬闸")
    fp = sub.add_parser("format-check", help="新增件格式硬闸")
    fp.add_argument("--base", default=None, help="可比 base 引用（git diff base...HEAD）")
    fp.add_argument("--files", nargs="*", default=None, help="直传文件清单（无可比 base 时）")
    op = sub.add_parser("observe", help="观察门·只报不挡（永远 exit 0）")
    op.add_argument("--build-log", default=None, help="构建日志路径（warning/deprecation 计数）")
    args = ap.parse_args(argv)

    if args.cmd == "claims-check":
        return claims_check()
    if args.cmd == "format-check":
        return format_check(args.base, args.files)
    if args.cmd == "observe":
        return observe(args.build_log)
    return 2


if __name__ == "__main__":
    sys.exit(main())
