# -*- coding: utf-8 -*-
"""引用件存在性检查（BULLETIN-FOLLOWUP-001 块二，告警模式 exit 0）。

扫描仓内文本文件（*.md/*.py/*.yaml/*.tsx）中形如
TDCA-[A-Z0-9]+(-[A-Z0-9]+)*-\\d{3} 的件号引用；
该件号出现在仓内任一文件名（相对路径含此串）→ 在位；
否则 → 「未在位引用」。命中豁免名单（docs/ops/citation-external-allowlist.txt，
一行一件号，⛔不通配）者计豁免。

用法：python tools/check_citation_exists.py [--root <仓根>]
输出：未在位引用 N 条／豁免 M 条 ＋ 命中清单（件号 + 出处文件 + 行号）。
⛔ 告警模式：永远 exit 0，不阻断 CI（两周观察期至 2026-11-17，升阻断须另出复议件）。
"""
import argparse
import os
import re
import sys

FAMILIES = ("GOV|ASSESS|WITNESS|RULING|HANDOFF|CHECK|SESSION|RECORD|AMEND|"
            "LIST|STD|SPEC|MEMO")
CIT_RE = re.compile(
    r"TDCA-(?:" + FAMILIES + r")(?:-[A-Z0-9]+)*-\d{3}")
SCAN_EXT = {".md", ".py", ".yaml", ".tsx"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv"}
ALLOWLIST = os.path.join("docs", "ops", "citation-external-allowlist.txt")


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    # 仓内全部相对路径（文件名在位判定用）
    rel_paths = []
    for p in walk_files(root):
        rel_paths.append(os.path.relpath(p, root).replace(os.sep, "/"))

    # 豁免名单：一行件号＋一行理由（三类之一）；无理由条目无效
    VALID_REASONS = {"EXT-HANDOFF", "HIST-RETIRED", "EXT-STD"}
    allowed = {}
    invalid_entries = []
    al_path = os.path.join(root, ALLOWLIST)
    if os.path.exists(al_path):
        with open(al_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        i = 0
        while i < len(lines):
            ref = lines[i]
            reason = lines[i + 1] if i + 1 < len(lines) and lines[i + 1] in VALID_REASONS else None
            if reason:
                allowed[ref] = reason
                i += 2
            else:
                invalid_entries.append(ref)
                i += 1

    # 扫描文本文件中的引用
    hits = {}  # ref -> list of (file, lineno)
    for p in walk_files(root):
        ext = os.path.splitext(p)[1].lower()
        if ext not in SCAN_EXT:
            continue
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    for m in CIT_RE.finditer(line):
                        hits.setdefault(m.group(0), []).append((rel, i))
        except OSError:
            continue

    missing = []
    exempt = []
    for ref in sorted(hits):
        in_place = any(ref in rp for rp in rel_paths)
        if in_place:
            continue
        if ref in allowed:
            exempt.append(ref)
        else:
            missing.append(ref)
    net = len(missing)

    print("引用件存在性检查（告警模式，exit 0）· 正则收窄十三族（AMEND-001 裁定一）")
    print(f"扫描根：{root}")
    print(f"在位引用：{len(hits) - len(missing) - len(exempt)} 件号")
    print(f"未在位引用 {len(missing)} 条（毛量）／豁免 {len(exempt)} 条")
    print(f"净量（毛量−豁免）＝{net}")
    print(f"豁免名单条目数＝{len(allowed)}（上限 150）")
    if invalid_entries:
        print(f"⚠ 无理由/无效豁免条目 {len(invalid_entries)} 条（照报不生效）：")
        for r in invalid_entries:
            print(f"  {r}")
    if len(allowed) > 150:
        print("⛔ 豁免条目超 150 上限——须停手再报（裁定三）")
    if missing:
        print("\n== 未在位引用清单 ==")
        for ref in missing:
            for rel, ln in hits[ref][:5]:
                print(f"{ref}  {rel}:{ln}")
            if len(hits[ref]) > 5:
                print(f"{ref}  …另 {len(hits[ref]) - 5} 处")
    if exempt:
        print("\n== 豁免命中 ==")
        for ref in exempt:
            print(f"{ref}")
    if not missing:
        print("\n无未在位引用。")
    sys.exit(0)


if __name__ == "__main__":
    main()
