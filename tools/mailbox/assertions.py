# -*- coding: utf-8 -*-
"""信箱断言集（ENG4-001 块6）：件数 A1／旁注 A2／状态机 A3／四零立 Z1~Z4。

跑在「信箱盒」目录面（如 FROM-EXEC／TO-EXEC），对盒内全部件与旁注给断言读数。
每条断言 = (码, 级别, 说明)；级别 PASS/FAIL/SKIP。盒目录不存在按 SKIP（不误杀）。
"""
from __future__ import annotations

import os
import re

from .seal import (
    FIELD_RE, FINAL_TERMS, HEX16_RE, NAME_MAX, NEGATION, ZERO,
    check_one, file_state, first_line, is_mail, read_text,
    ST_DRAFT, ST_INTERNAL, ST_MISMATCH, ST_ORPHAN, ST_SEALED,
)

CONTENT_EXTS = (".md", ".json", ".txt")


def _is_content(name: str) -> bool:
    return name.endswith(CONTENT_EXTS) and not name.endswith(".sha256")


def _iter_box(box_dir: str):
    """返回 (content_files, sidecars) 全名列表；目录不存在返回 (None, None)。"""
    if not os.path.isdir(box_dir):
        return None, None
    names = sorted(os.listdir(box_dir))
    contents = [os.path.join(box_dir, n) for n in names if _is_content(n)]
    sides = [os.path.join(box_dir, n) for n in names if n.endswith(".sha256")]
    return contents, sides


def assert_box(box_dir: str, external: bool = False):
    """对单盒跑全部断言。返回 (断言条, fail 数, 统计 dict)。"""
    rows, fails = [], 0

    def add(level, code, msg):
        nonlocal fails
        rows.append((level, code, msg))
        if level == "FAIL":
            fails += 1

    contents, sides = _iter_box(box_dir)
    if contents is None:
        add("SKIP", "BOX", f"盒不存在：{box_dir}")
        return rows, fails, {"contents": 0, "sidecars": 0}

    stat = {"contents": len(contents), "sidecars": len(sides)}
    mail_contents = [c for c in contents if is_mail(read_text(c)[1])]

    # ---- A1 件数：投递件（MAIL 首行）与旁注一一对应；内部件（无 MAIL）无旁注义务 ----
    base_of_side = {s[:-len(".sha256")] for s in sides}
    content_set = set(contents)
    orphan_sides = sorted(s for s in sides if s[:-len(".sha256")] not in content_set)
    missing_sides = sorted(c for c in mail_contents if c not in base_of_side)
    ok = not orphan_sides and not missing_sides
    add("PASS" if ok else "FAIL", "A1",
        f"件数 {len(contents)}（投递 {len(mail_contents)}/内部 {len(contents) - len(mail_contents)}）"
        f"/旁注 {len(sides)}" +
        ("" if ok else f"；孤儿旁注 {len(orphan_sides)}、投递件缺旁注 {len(missing_sides)}"))
    stat["orphan_sides"] = len(orphan_sides)
    stat["missing_sides"] = len(missing_sides)

    # ---- A2 旁注：17B 且值符（逐件机验 C-04；投递件为义务面）----
    side_bad = []
    for c in mail_contents:
        side = c + ".sha256"
        if not os.path.exists(side):
            side_bad.append((c, "缺旁注"))
            continue
        from .seal import sha16
        sv = open(side, "rb").read()
        if not (len(sv) == 17 and sv.decode("utf-8", "replace").strip() == sha16(c)):
            side_bad.append((c, f"{len(sv)}B 值不符"))
    add("PASS" if not side_bad else "FAIL", "A2",
        f"投递件旁注符 {len(mail_contents) - len(side_bad)}/{len(mail_contents)}" +
        ("" if not side_bad else f"；不符 {len(side_bad)}（如 {os.path.basename(side_bad[0][0])} {side_bad[0][1]}）"))
    stat["side_bad"] = len(side_bad)

    # ---- A3 状态机：投递盒内 DRAFT/MISMATCH/ORPHAN 必须为 0 ----
    states = {}
    for c in contents:
        states[c] = file_state(c)
    for s in orphan_sides:
        states[s] = ST_ORPHAN
    bad_states = {p: st for p, st in states.items()
                  if st in (ST_DRAFT, ST_MISMATCH, ST_ORPHAN)}
    add("PASS" if not bad_states else "FAIL", "A3",
        "状态机净（全 SEALED/INTERNAL）" if not bad_states else
        f"状态机异常 {len(bad_states)}（" +
        "; ".join(f"{os.path.basename(p)}={st}" for p, st in list(bad_states.items())[:3]) + "）")
    stat["states"] = {os.path.basename(p): st for p, st in states.items()}
    stat["bad_states"] = len(bad_states)

    # ---- 四零立 ----
    # Z1 零占位残留：MAIL 首行仍为全 0 占位
    z1 = [c for c in contents
          if is_mail(read_text(c)[1]) and ZERO in first_line(read_text(c)[1])]
    add("PASS" if not z1 else "FAIL", "Z1",
        f"零占位残留 {len(z1)}" + ("" if not z1 else f"（如 {os.path.basename(z1[0])}）"))
    stat["z1"] = len(z1)

    # Z2 零孤儿旁注（与 A1 同源，独立断言便于四零立直读）
    add("PASS" if not orphan_sides else "FAIL", "Z2",
        f"孤儿旁注 {len(orphan_sides)}" +
        ("" if not orphan_sides else f"（如 {os.path.basename(orphan_sides[0])}）"))
    stat["z2"] = len(orphan_sides)

    # Z3 零超名（>110 字符）
    z3 = [c for c in contents if len(os.path.basename(c)) > NAME_MAX]
    add("PASS" if not z3 else "FAIL", "Z3",
        f"超名 {len(z3)}" + ("" if not z3 else f"（如 {os.path.basename(z3[0])[:40]}…）"))
    stat["z3"] = len(z3)

    # Z4 零终态字样（复用 C-18 逐件）
    z4 = []
    for c in contents:
        _, text = read_text(c)
        for ln in text.split("\n"):
            if any(n in ln for n in NEGATION):
                continue
            for m in FINAL_TERMS.finditer(ln):
                pre = ln[max(0, m.start() - 2):m.start()]
                if not any(ch in pre for ch in ("无", "非", "没")):
                    z4.append(c)
                    break
            else:
                continue
            break
    add("PASS" if not z4 else "FAIL", "Z4",
        f"终态字样 {len(z4)}" + ("" if not z4 else f"（如 {os.path.basename(z4[0])}）"))
    stat["z4"] = len(z4)

    # 附：逐件机验（C 组）读数汇总（投递件）
    c_fails = 0
    for c in contents:
        _, f = check_one(c, external=external, require_mail=False)
        c_fails += f
    add("PASS" if c_fails == 0 else "FAIL", "C组",
        f"逐件机验失败计数 {c_fails}")
    stat["c_fails"] = c_fails

    return rows, fails, stat
