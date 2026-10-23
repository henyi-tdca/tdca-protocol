# -*- coding: utf-8 -*-
"""docs_ingest.py — 文档/知识库入站脚本（A-15 文库面 docs 表）

制度水印:
  FC-ID: TDCA-FC-OPS-INGEST-001 | 交办: TDCA-HANDOFF-SITE-CONTENT-INGEST-001-IMPL-001/002
  口径: 单一事实源=主仓；本脚本把仓内 docs/regulations 与 docs/cop-library 之未入站件
        幂等补入 docs 表；⛔ 不改 library_ops 只读语义；⛔ 不造内容；⛔ 不覆盖既有。

用法:
  python docs_ingest.py --repo <仓路径> --db <sqlite 路径> [--family F] [--dry-run]

幂等（IMPL-002 认可案：查重双键）:
  - 差额侦测按 source_path：库内已有同 source_path 者跳过（重跑零新增；
    对上本轮对账口径——cop-library 源 617 件在册 619，差 3 即源路径未登记者）。
  - 插入按 slug（全表 UNIQUE）：同 slug 已占（他件）→ 加 -N 后缀（对上 README-1 旧例）。
  - 重复执行不产生重复行（回报须附幂等实证）。

范围与安全闸:
  - 仅受理扩展名 .md / .yaml / .py（IMPL-002 在册差额含 cop-library 两件 .py：
    tdca_core/compile_tdca_core.py、enforce_entry.py；paper 之 .gitattributes、
    evidence/artifact_hashes.json 两件非文献差额已关闭，永不受理；⛔ 不造内容）。
  - paper 族仅 .md 可入（证据 md 已在册，自然跳过）。

slug 取法（对齐库内既有惯例，实测 README-1 / TDCA-INSURANCE-RULES-001）:
  文件名 stem 截于首个 CJK 或 （/( 处，去尾分隔符；空则回退全 stem。
DRAFT/待签批标注在文件名者照录（内容照抄，不加不删）。

范围: 六映射目录（docs/regulations→regulation、docs/cop-library→cop-library 等）；
      laws/law-notes 两族为 LAWINGEST-001（TDCA-HANDOFF-EXEC-L1SI169-LAWINGEST-001，
      批C-C2）新增：docs/laws→laws（法律原文）、docs/law-notes→law-notes（适用说明）；
      paper 两件非文献差额已关闭（IMPL-002），本脚本不涉 paper 之 .gitattributes 等。
data_nature: 既有 652 行全 'real'，新行同值对齐。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

FAMILY_MAP = {
    "docs/regulations": "regulation",
    "docs/whitepapers": "whitepaper",
    "docs/papers": "paper",
    "docs/cop-library": "cop-library",
    "docs/laws": "laws",
    "docs/law-notes": "law-notes",
}

_SRC_PREFIX = "tdca-protocol/"
_CJK = re.compile(r"[　-鿿＀-￯]")
_HEADING = re.compile(r"^#\s+(.+?)\s*$")


def slug_base(stem: str) -> str:
    m = _CJK.search(stem)
    base = stem[: m.start()] if m else stem
    base = base.rstrip("-_·. ")
    return base or stem


def make_slug(stem: str, taken: set[str]) -> str:
    base = slug_base(stem)
    slug, n = base, 1
    while slug in taken:
        n += 1
        slug = f"{base}-{n}"
    return slug


def extract_title(text: str, stem: str) -> str:
    for line in text.splitlines():
        m = _HEADING.match(line.strip())
        if m:
            return m.group(1).strip()
    return stem


def iter_sources(repo: Path, only_family: str = ""):
    for rel, family in sorted(FAMILY_MAP.items()):
        if only_family and family != only_family:
            continue
        d = repo / rel
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file() and f.name != "README.md" and f.suffix in (".md", ".yaml", ".py"):
                yield family, rel, f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--family", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo)
    rows = list(iter_sources(repo, args.family))
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    taken = {r[0] for r in cur.execute("SELECT slug FROM docs")}
    have_src = {r[0] for r in cur.execute("SELECT source_path FROM docs")}

    plan, n_skip, n_add = [], 0, 0
    for family, rel, f in rows:
        src = _SRC_PREFIX + f.relative_to(repo).as_posix()
        if src in have_src:
            n_skip += 1
            plan.append(("SKIP", family, slug_base(f.stem), f.name))
            continue
        slug = make_slug(f.stem, taken)
        taken.add(slug)
        text = f.read_text(encoding="utf-8")
        title = extract_title(text, f.stem)
        n_add += 1
        plan.append(("ADD", family, slug, f.name))
        if not args.dry_run:
            cur.execute(
                "INSERT INTO docs (family, slug, title, body_md, source_path, data_nature)"
                " VALUES (?, ?, ?, ?, ?, 'real')",
                (family, slug, title, text, src),
            )

    if not args.dry_run:
        conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    conn.close()

    print(f"plan: add={n_add} skip={n_skip} total_after={total} dry_run={args.dry_run}")
    for act, family, slug, fname in plan:
        print(f"  {act:4} [{family}] {slug}  <- {fname}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
