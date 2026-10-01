#!/usr/bin/env python3
"""
TDCA 站点内容同步脚本（草案 v2 · 前置整改后 · 本地跑，只读源，单向出站）
============================================================
管线：本地工作区（内容真源）→ 脱敏复扫 → content/ 清单 → 入库或生成静态页

铁律：
  ⛔ 只读源文件，绝不回写
  ⛔ 脱敏硬约束（v2 扩充）：内部治理编号 / 在册编号形态（GSEQ-、NCA-、T-、DCD-、KB-）
    / 凭据值形态 / 人名 —— 命中即拒入站，并落拒绝清单（rejected.json）
  ⛔ 源内只记本地相对路径（可追溯），不记任何平台 URL
用法：
  python scripts/sync_content.py --root ".." --check      # 只扫不产物（预检）
  python scripts/sync_content.py --root ".." --out content/
人名检测（依裁 ⓑ）：不设名单、不建 denylist_names.txt；脚本保持名单机制但输出如实标
  「不设名单（依裁 ⓑ），改由发布前人工核 + 对外件零人名纪律」——⛔ 不编造名单，⛔ 不写成「已检」。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
NAME_LIST_FILE = SCRIPT_DIR / "denylist_names.txt"

# ── 内容族 ← 本地工作区映射（一期范围）────────────────────────────────────
FAMILIES: dict[str, list[str]] = {
    "whitepaper":  ["tdca-protocol/docs/whitepapers"],
    "paper":       ["tdca-protocol/docs/papers"],
    "regulation":  ["tdca-protocol/docs/regulations"],
    "cop-library": ["tdca-protocol/docs/cop-library"],
    "weekly":      ["weekly", "周刊"],
}
ALLOWED_SUFFIX = {".md", ".txt"}

# ── 脱敏复扫（命中即拒入站，零容忍）────────────────────────────────────────
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("governance-id", re.compile(r"\bID\s?\d{2,}\b")),           # 内部治理编号
    ("gseq",          re.compile(r"\bGSEQ-\d{4,}\b")),            # 在册编号形态
    ("nca-ref",       re.compile(r"\bNCA-[A-Za-z0-9][A-Za-z0-9-]+\b")),  # 含字母形态（如 NCA-<字母>-…-<数字>）
    ("t-ref",         re.compile(r"\bT-[A-Za-z0-9][A-Za-z0-9-]+\b")),    # 含字母形态（如 T-ANCHOR／T-036）
    ("dcd",           re.compile(r"\bDCD-[A-Z0-9-]+\b")),
    ("kb",            re.compile(r"\bKB-\d{3,}\b")),
    ("api-key",       re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")),    # 形态密钥
    ("gh-pat",        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws-key",       re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("tdid",          re.compile(r"\bTDID-[A-Z0-9-]+\b")),        # 保留类实值
]
MAX_LINE_SNIPPET = 80  # 命中行只回显截断片段，便于人工复核


def load_name_patterns() -> tuple[list[tuple[str, re.Pattern]], bool]:
    """人名检测式：从 denylist_names.txt 载入（每行一名）。返回 (模式, 是否启用)。"""
    if not NAME_LIST_FILE.exists():
        return [], False
    pats = []
    for line in NAME_LIST_FILE.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            pats.append(("person-name", re.compile(re.escape(name))))
    return pats, True


@dataclass
class Hit:
    family: str
    path: str
    line_no: int
    kind: str
    snippet: str


@dataclass
class Manifest:
    ok: bool = True
    files: list[dict] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)
    name_check_enabled: bool = False


def scan_text(text: str, family: str, rel: str,
              all_patterns: list[tuple[str, re.Pattern]],
              manifest: Manifest) -> bool:
    clean = True
    for i, line in enumerate(text.splitlines(), 1):
        for kind, pat in all_patterns:
            if pat.search(line):
                manifest.hits.append(Hit(family, rel, i, kind,
                                         line.strip()[:MAX_LINE_SNIPPET]))
                clean = False
    return clean


def collect(root: Path, check_only: bool, out: Path | None) -> Manifest:
    m = Manifest()
    name_pats, enabled = load_name_patterns()
    m.name_check_enabled = enabled
    all_patterns = PATTERNS + name_pats
    for family, dirs in FAMILIES.items():
        for d in dirs:
            base = root / d
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if f.suffix.lower() not in ALLOWED_SUFFIX or not f.is_file():
                    continue
                rel = f.relative_to(root).as_posix()
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                except OSError as e:
                    print(f"[warn] 读取失败 {rel}: {e}", file=sys.stderr)
                    continue
                if scan_text(text, family, rel, all_patterns, m):
                    m.files.append({"family": family, "path": rel,
                                    "bytes": f.stat().st_size})
                else:
                    print(f"[reject] 脱敏命中，拒入站: {rel}")
    if m.hits:
        m.ok = False
    if out:
        out.mkdir(parents=True, exist_ok=True)
        if not check_only and m.ok:
            (out / "manifest.json").write_text(
                json.dumps({"generated_by": "sync_content.py v2",
                            "files": m.files}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            print(f"[ok] 清单已写 {out / 'manifest.json'}（{len(m.files)} 件）")
        if m.hits:
            # 拒绝清单：命中件逐条落盘（含行号/类型/截断片段），供按族处置
            (out / "rejected.json").write_text(
                json.dumps({"generated_by": "sync_content.py v2",
                            "rejected": [h.__dict__ for h in m.hits]},
                           ensure_ascii=False, indent=2),
                encoding="utf-8")
            print(f"[reject-list] 已写 {out / 'rejected.json'}（{len(m.hits)} 处命中）")
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="本地工作区根（内容真源）")
    ap.add_argument("--check", action="store_true", help="只扫不产物")
    ap.add_argument("--out", default="content", help="清单输出目录")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    manifest = collect(root, args.check, Path(args.out))

    print(f"\n═══ 复扫结果 ═══")
    print(f"入站候选 {len(manifest.files)} 件；脱敏命中 {len(manifest.hits)} 处")
    print(f"人名检测：不设名单（依裁 ⓑ）——改由发布前人工核 + 对外件零人名纪律")
    for h in manifest.hits:
        print(f"  [{h.kind}] {h.path}:{h.line_no}  {h.snippet}")
    if not manifest.ok:
        print("结论：存在命中，清单未产出。须先处置源件（⛔ 脚本不改源）。")
        return 2
    print("结论：零命中。" + ("（--check 预检模式）" if args.check else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
