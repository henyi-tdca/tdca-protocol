# -*- coding: utf-8 -*-
"""统一入口：`python -m tools.mailbox.mailbox <action>`（ENG4-001 块6 归一形态）。

actions
-------
  seal     --file <件> [...] [--external] [--require-mail]
  check    --file <件> [...] [--external] [--require-mail]
  box      [--mailbox-root DIR] [--box NAME ...] [--external]
  selftest [-v]

统一参数
--------
  --mailbox-root  信箱根（默认 env TDCA_MAILBOX_ROOT；盒 = <root>/_MAILBOX/<NAME>）
  --box           盒名（FROM-EXEC／TO-EXEC／…；可多个）
  --file          件路径（可多个）
  --external      对外纪律：加扫内部编号式样
  --require-mail  投递件首行须 MAIL 起首（C-05）
  -v/--verbose    逐条读数

末行固定输出 MAILBOX_VERDICT=PASS|FAIL(n)|SKIP(无输入)。
"""
from __future__ import annotations

import argparse
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from .assertions import assert_box
from .seal import check_one, seal_one
from .selftest import run_selftest

DEFAULT_BOXES = ("FROM-EXEC",)


def _mail_root(a) -> str:
    root = a.mailbox_root or os.environ.get("TDCA_MAILBOX_ROOT", "")
    if not root:
        print("须给 --mailbox-root 或置 env TDCA_MAILBOX_ROOT")
        print("MAILBOX_VERDICT=SKIP(无信箱根)")
        sys.exit(2)
    return root


def main() -> int:
    ap = argparse.ArgumentParser(prog="tools.mailbox")
    ap.add_argument("action", choices=["seal", "check", "box", "selftest"])
    ap.add_argument("--file", nargs="*", default=None)
    ap.add_argument("--mailbox-root", default=None)
    ap.add_argument("--box", nargs="*", default=None)
    ap.add_argument("--external", action="store_true")
    ap.add_argument("--require-mail", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    if a.action == "selftest":
        ok, lines = run_selftest(verbose=a.verbose)
        for ln in lines:
            print(ln)
        return 0 if ok else 1

    if a.action in ("seal", "check"):
        if not a.file:
            print("用法: mailbox seal|check --file <件路径> [...]")
            print("MAILBOX_VERDICT=SKIP(无输入)")
            return 0
        total_fail = 0
        for p in a.file:
            print("—", os.path.basename(p))
            rows, fails = check_one(p, a.external)
            if a.require_mail:
                try:
                    _first = open(p, encoding="utf-8").readline()
                except Exception:
                    _first = ""
                if not _first.startswith("MAIL"):
                    rows.append(("FAIL", "C-05", "投递件首行须 MAIL 起首（现为非 MAIL）"))
                    fails += 1
            for level, code, msg in rows:
                mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "·"}[level]
                print(f"   {mark} {code} {msg}")
            total_fail += fails
            _pending = {c for lv, c, _ in rows if lv == "FAIL"} <= {"C-01", "C-04"}
            if (fails == 0 or (_pending and any(r[1] == "C-01" for r in rows))) \
                    and a.action == "seal":
                state, note = seal_one(p)
                print(f"   {'🔏' if state == 'SEALED' else '·'} 封签 {state}：{note}")
        print(f"MAILBOX_VERDICT={'PASS' if total_fail == 0 else f'FAIL({total_fail})'}")
        return 0 if total_fail == 0 else 1

    # box 断言集
    root = _mail_root(a)
    boxes = a.box or list(DEFAULT_BOXES)
    total_fail = 0
    for name in boxes:
        box_dir = os.path.join(root, "_MAILBOX", name)
        if not os.path.isdir(box_dir):
            # 兼容 root 直指 _MAILBOX 的给法
            alt = os.path.join(root, name)
            box_dir = alt if os.path.isdir(alt) else box_dir
        print(f"— 盒 {name}: {box_dir}")
        rows, fails, stat = assert_box(box_dir, external=a.external)
        for level, code, msg in rows:
            mark = {"PASS": "✅", "FAIL": "❌", "SKIP": "·"}[level]
            print(f"   {mark} {code} {msg}")
        total_fail += fails
    print(f"MAILBOX_VERDICT={'PASS' if total_fail == 0 else f'FAIL({total_fail})'}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
