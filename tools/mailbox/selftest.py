# -*- coding: utf-8 -*-
"""三态自测（夹具·不指向真实信箱）：正常态／异常态／边界态。

* 态一 正常：2 件封签齐＋1 内部件 → 断言全 PASS。
* 态二 异常：注入五缺陷（孤儿旁注／零占位残留／超名／终态字样／旁注值不符）
  → A1/A2/A3/Z1~Z4 各给 FAIL 读数，verdict FAIL。
* 态三 边界：空盒 SKIP 不误杀；非 MAIL 件在投递盒内由机验 C 组判（断言 A 组不炸）。
"""
from __future__ import annotations

import os
import shutil
import tempfile

from .assertions import assert_box
from .seal import ZERO, read_text, seal_one

GOOD_MAIL = (
    "MAIL id=SELFTEST-001 sha256_16={zero} 口径=乙 from=执行侧 to=信箱TO-EXEC "
    "性质=内部件 事由=三态自测夹具\n\n# 夹具件\n\n正文占位。\n"
)


def _write(path: str, text: str):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _make_sealed(box: str, name: str) -> str:
    p = os.path.join(box, name)
    _write(p, GOOD_MAIL.replace("{zero}", "0" * 16))
    seal_one(p)
    return p


def run_selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """返回 (全过?, 读数行)。"""
    log: list[str] = []
    tmp = tempfile.mkdtemp(prefix="mailbox-selftest-")
    try:
        # ── 态一 正常态 ──
        box1 = os.path.join(tmp, "normal", "FROM-EXEC")
        os.makedirs(box1)
        _make_sealed(box1, "TDCA-SELFTEST-STATE1-A-样件一.md")
        _make_sealed(box1, "TDCA-SELFTEST-STATE1-B-样件二.md")
        _write(os.path.join(box1, "INTERNAL-NOTE-无邮件头.md"),
               "# 内部件\n\n无 MAIL 首行，不投箱语义无旁注义务。\n")
        rows1, fails1, _ = assert_box(box1)
        ok1 = fails1 == 0
        log.append(f"态一 正常：断言 {len(rows1)} 条，FAIL={fails1} → {'PASS' if ok1 else 'FAIL'}")
        if verbose:
            log += [f"   {lv} {code} {msg}" for lv, code, msg in rows1]

        # ── 态二 异常态（五缺陷注入）──
        box2 = os.path.join(tmp, "abnormal", "FROM-EXEC")
        os.makedirs(box2)
        good = _make_sealed(box2, "TDCA-SELFTEST-STATE2-GOOD.md")
        # 缺陷1 孤儿旁注
        _write(os.path.join(box2, "orphan-side.sha256"), "0" * 16 + "\n")
        # 缺陷2 零占位残留（MAIL 件未封签即入盒）
        _write(os.path.join(box2, "TDCA-SELFTEST-STATE2-DRAFT.md"),
               GOOD_MAIL.replace("{zero}", "0" * 16))
        # 缺陷3 超名（>110）；ASCII 填充——Linux NAME_MAX 按字节计（长*120=386B 触发
        # ENAMETOOLONG 使夹具创建即崩），字符数>110 判据意图不变，双平台可建
        long_name = "TDCA-SELFTEST-STATE2-" + "x" * 120 + ".md"
        _write(os.path.join(box2, long_name), GOOD_MAIL.replace("{zero}", "0" * 16))
        # 缺陷4 终态字样
        _write(os.path.join(box2, "TDCA-SELFTEST-STATE2-FINAL.md"),
               GOOD_MAIL.replace("{zero}", "0" * 16).replace("# 夹具件", "# 夹具件\n\n本件为最终版。"))
        # 缺陷5 旁注值不符（先封签再破坏旁注）
        bad = _make_sealed(box2, "TDCA-SELFTEST-STATE2-BADSIDE.md")
        _write(bad + ".sha256", "F" * 16 + "\n")
        rows2, fails2, stat2 = assert_box(box2)
        expected_fail_codes = {"A1", "A2", "A3", "Z1", "Z2", "Z3", "Z4"}
        got_fail_codes = {code for lv, code, _ in rows2 if lv == "FAIL"}
        ok2 = fails2 > 0 and expected_fail_codes <= got_fail_codes
        log.append(
            f"态二 异常：断言 {len(rows2)} 条，FAIL={fails2}，命中码 {sorted(got_fail_codes)} "
            f"→ {'PASS' if ok2 else 'FAIL'}")
        if verbose:
            log += [f"   {lv} {code} {msg}" for lv, code, msg in rows2]

        # ── 态三 边界态 ──
        box3 = os.path.join(tmp, "edge", "FROM-EXEC")
        os.makedirs(box3)  # 空盒
        rows3a, fails3a, _ = assert_box(box3)
        _write(os.path.join(box3, "NOTE.md"), "# 内部说明\n\n无邮件头。\n")
        rows3b, fails3b, _ = assert_box(box3)
        ok3 = fails3a == 0 and fails3b == 0 and all(
            lv != "FAIL" for lv, _, _ in rows3a + rows3b)
        log.append(
            f"态三 边界：空盒 FAIL={fails3a}；含非 MAIL 件 FAIL={fails3b} → {'PASS' if ok3 else 'FAIL'}")
        if verbose:
            log += [f"   {lv} {code} {msg}" for lv, code, msg in rows3b]

        all_ok = ok1 and ok2 and ok3
        log.append(f"SELFTEST_VERDICT={'PASS' if all_ok else 'FAIL'}")
        return all_ok, log
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ok, lines = run_selftest(verbose="-v" in os.sys.argv)
    for ln in lines:
        print(ln)
    raise SystemExit(0 if ok else 1)
