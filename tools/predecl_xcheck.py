#!/usr/bin/env python3
"""predecl_xcheck.py —— 预声明文本版 ↔ 实现版 开跑前互校工具（交办存证号 GSEQ-2919）

用途
----
给定一份预声明文本件（含条款编号，如 A-1／R1／S-2／T08／J-1）与一份门侧实现
脚本（在注释 / docstring 中引用条款编号的 Python 脚本），逐条输出三类差异：
「仅文本」「仅实现」「口径不一致」，把「互校」做成可执行的一步。

调用
----
  python tools/predecl_xcheck.py --decl <预声明文本路径> --impl <实现脚本路径>
      [--id-pattern <正则>] [--context-lines N]

口径（合理简化，写死于此，不得随风改动）
----
1. 条款编号默认正则（可被 --id-pattern 整体覆盖）：
       \\b[A-Z]{1,3}-\\d+[a-z]?\\b|\\b[A-Z]\\d+\\b
   覆盖 A-1／R1／S-2／T08／J-1 等形态。
2. 预声明侧条款区间：自某编号「首次出现」的行起，至其后首个满足任一条件的行
   止（不含该行）：(a) 含任一条款编号的行；(b) 空白行；(c) 以 # 开头的节标题行。
   同一编号后续出现不再重复建档。每条记录：clause_id、文件、行号、原文区间。
3. 实现侧引用点：扫描脚本全文（含注释与 docstring），凡某行提及某 clause_id
   即记一条引用点：文件、行号、该行及后续 --context-lines 行（默认 2）为摘录。
4. 关键事实（用于「口径不一致」判定），两侧各自抽取后比对：
   (a) 数字字面：先从文本中剔除条款编号本身，再取全部数字字面
       （\\d+(?:\\.\\d+)?），按多重集合（排序后列表）比对；
   (b) 判定词集合：BLOCK / FUSE / DENY / PASS / 拒 / 拒绝 / 放行 / 拦截 / 拦，
       大小写不敏感，按集合比对。
   实现侧同一编号多个引用点的摘录合并后抽取。任一项不相合即判「口径不一致」，
   两侧摘录都列出；两侧都有且关键事实相合 → 无差异（仅汇总报「相合 N 条」）。
5. 摘录单行化（换行以 ⏎ 代替）后超过 80 字符截断并留 … 标记。

输出
----
每条差异一行（或多行），格式：
  <clause_id> ｜ 条款定位 <文件:行> ↔ 实现定位 <文件:行 或 —> ↔ <差异类型> ↔ 摘录：…
末尾必有汇总行（含「相合 N 条」）；无任何差异时显式输出一行「零差异」，不静默。

退出码
----
  0 ＝ 互校完成且零差异
  1 ＝ 互校完成但有差异
  2 ＝ 零态守卫或用法错误（输入缺失 / 为空（0 字节或纯空白）/ 不可读 /
      正则非法 / 预声明中一个条款编号都抽不到）；显式报错到 stderr，不出结论。

纪律
----
  · 只读输入：两输入均以只读方式打开；本工具不写任何文件（除 stdout/stderr）。
  · 一对一：一次只校一对（decl × impl），不提供跨文件批量模式。
  · ⛔ 不自动改件、无写回逻辑。
  · Python 3 标准库-only；⛔ 全程本地、不联网。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_ID_PATTERN = r"\b[A-Z]{1,3}-\d+[a-z]?\b|\b[A-Z]\d+\b"

# 判定词清单（大小写不敏感；中文词不受影响）
JUDGMENT_WORDS = ["BLOCK", "FUSE", "DENY", "PASS", "拒绝", "拒", "放行", "拦截", "拦"]

TRUNCATE_AT = 80
ELLIPSIS = "…"


# ---------------------------------------------------------------------------
# 零态守卫：只读打开 + 存在 / 非空 / 可读校验（失败显式报错到 stderr）
# ---------------------------------------------------------------------------

def read_guarded(path_str: str, role: str) -> str | None:
    """以只读方式读取输入；任一零态（缺失/为空/不可读）返回 None 并已报错。"""
    p = Path(path_str)
    if not p.is_file():
        print(f"::error::{role}输入不存在或不是文件: {path_str}", file=sys.stderr)
        return None
    try:
        with open(p, "r", encoding="utf-8") as fh:  # 只读打开，不写
            text = fh.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"::error::{role}输入不可读: {path_str}（{e}）", file=sys.stderr)
        return None
    if not text.strip():
        print(f"::error::{role}输入为空（0 字节或纯空白）: {path_str}", file=sys.stderr)
        return None
    return text


# ---------------------------------------------------------------------------
# 预声明侧：条款区间抽取
# ---------------------------------------------------------------------------

def _is_heading(line: str) -> bool:
    return line.lstrip().startswith("#")


def extract_decl_clauses(text: str, id_re: re.Pattern, path_str: str) -> list[dict]:
    """每条：clause_id / file / line（首次出现行，1 起）/ region（原文区间）。"""
    lines = text.splitlines()
    first_seen: dict[str, int] = {}
    order: list[str] = []
    for i, ln in enumerate(lines):
        for m in id_re.finditer(ln):
            cid = m.group(0)
            if cid not in first_seen:
                first_seen[cid] = i
                order.append(cid)
    clauses: list[dict] = []
    for cid in order:
        start = first_seen[cid]
        end = len(lines)
        for j in range(start + 1, len(lines)):
            ln = lines[j]
            if not ln.strip() or _is_heading(ln) or id_re.search(ln):
                end = j
                break
        clauses.append({
            "clause_id": cid,
            "file": path_str,
            "line": start + 1,
            "region": "\n".join(lines[start:end]),
        })
    return clauses


# ---------------------------------------------------------------------------
# 实现侧：引用点抽取（全文，含注释与 docstring）
# ---------------------------------------------------------------------------

def extract_impl_refs(text: str, id_re: re.Pattern, path_str: str,
                      context_lines: int) -> dict[str, list[dict]]:
    """clause_id -> [引用点…]；每点：file / line / excerpt（该行 + 后续 N 行）。"""
    lines = text.splitlines()
    refs: dict[str, list[dict]] = {}
    for i, ln in enumerate(lines):
        ids_here = {m.group(0) for m in id_re.finditer(ln)}
        for cid in sorted(ids_here):
            excerpt = "\n".join(lines[i:i + 1 + context_lines])
            refs.setdefault(cid, []).append({
                "file": path_str,
                "line": i + 1,
                "excerpt": excerpt,
            })
    return refs


# ---------------------------------------------------------------------------
# 关键事实：数字字面（多重集合）＋ 判定词集合
# ---------------------------------------------------------------------------

def key_facts(text: str, id_re: re.Pattern) -> tuple[list[str], set[str]]:
    scrubbed = id_re.sub(" ", text)  # 剔除条款编号本身，避免编号内数字混入
    numbers = sorted(re.findall(r"\d+(?:\.\d+)?", scrubbed))
    words = {w.upper() for w in JUDGMENT_WORDS
             if re.search(re.escape(w), scrubbed, re.IGNORECASE)}
    return numbers, words


# ---------------------------------------------------------------------------
# 输出整形
# ---------------------------------------------------------------------------

def fmt_excerpt(text: str) -> str:
    one_line = " ⏎ ".join(seg.strip() for seg in text.splitlines() if seg.strip())
    if len(one_line) > TRUNCATE_AT:
        return one_line[:TRUNCATE_AT] + ELLIPSIS
    return one_line


def emit_diff(cid: str, decl_loc: str, impl_loc: str, dtype: str, excerpt: str) -> None:
    print(f"{cid} ｜ 条款定位 {decl_loc} ↔ 实现定位 {impl_loc} ↔ {dtype} "
          f"↔ 摘录：{fmt_excerpt(excerpt)}")


# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="predecl_xcheck",
        description="预声明文本版 ↔ 实现版 开跑前互校（GSEQ-2919，只读、一对一）")
    ap.add_argument("--decl", required=True, help="预声明文本件路径（含条款编号）")
    ap.add_argument("--impl", required=True, help="门侧实现脚本路径")
    ap.add_argument("--id-pattern", default=DEFAULT_ID_PATTERN,
                    help="条款编号正则（覆盖默认形态）")
    ap.add_argument("--context-lines", type=int, default=2,
                    help="实现侧摘录上下文行数（默认 2，可 0）")
    args = ap.parse_args(argv)

    try:
        id_re = re.compile(args.id_pattern)
    except re.error as e:
        print(f"::error::--id-pattern 正则非法: {e}", file=sys.stderr)
        return 2
    if args.context_lines < 0:
        print("::error::--context-lines 不得为负", file=sys.stderr)
        return 2

    decl_text = read_guarded(args.decl, "预声明")
    if decl_text is None:
        return 2
    impl_text = read_guarded(args.impl, "实现脚本")
    if impl_text is None:
        return 2

    clauses = extract_decl_clauses(decl_text, id_re, args.decl)
    if not clauses:
        print(f"::error::预声明中未抽取到任何条款编号（零态守卫）: {args.decl}",
              file=sys.stderr)
        return 2
    refs = extract_impl_refs(impl_text, id_re, args.impl, args.context_lines)

    n_only_decl = n_only_impl = n_mismatch = n_agree = 0
    decl_ids = {c["clause_id"] for c in clauses}

    # 预声明顺序：仅文本 / 口径不一致
    for c in clauses:
        cid = c["clause_id"]
        decl_loc = f"{c['file']}:{c['line']}"
        if cid not in refs:
            n_only_decl += 1
            emit_diff(cid, decl_loc, "—", "仅文本",
                      c["region"] + "（实现侧零引用）")
            continue
        points = refs[cid]
        impl_loc = f"{points[0]['file']}:{points[0]['line']}"
        impl_merged = "\n".join(p["excerpt"] for p in points)
        d_num, d_words = key_facts(c["region"], id_re)
        i_num, i_words = key_facts(impl_merged, id_re)
        if d_num == i_num and d_words == i_words:
            n_agree += 1
            continue
        n_mismatch += 1
        emit_diff(cid, decl_loc, impl_loc, "口径不一致",
                  f"文本侧（数字={d_num or '无'} 判定词={sorted(d_words) or '无'}）"
                  f"｜原文：{c['region']}")
        emit_diff(cid, decl_loc, impl_loc, "口径不一致",
                  f"实现侧（数字={i_num or '无'} 判定词={sorted(i_words) or '无'}）"
                  f"｜原文：{impl_merged}")

    # 实现侧顺序：仅实现
    for cid in sorted(refs):
        if cid in decl_ids:
            continue
        n_only_impl += 1
        p0 = refs[cid][0]
        emit_diff(cid, "—", f"{p0['file']}:{p0['line']}", "仅实现",
                  p0["excerpt"] + "（预声明无此条）")

    n_diff = n_only_decl + n_only_impl + n_mismatch
    if n_diff == 0:
        print("零差异")
    print(f"汇总：仅文本 {n_only_decl} 条 ↔ 仅实现 {n_only_impl} 条 ↔ "
          f"口径不一致 {n_mismatch} 条 ↔ 相合 {n_agree} 条")
    return 1 if n_diff else 0


if __name__ == "__main__":
    sys.exit(main())
