# -*- coding: utf-8 -*-
"""predecl_xcheck.py 互校工具断言（交办存证号 GSEQ-2919）

fixture 纪律：全部语料在 tmp_path 就地构造，⛔ 不依赖仓内任何既有文件做
fixture（唯一例外是被测工具本体 tools/predecl_xcheck.py 自身）。
所有测试语料均为虚构样本，文本内标注 SIMULATED 字样。
编码纪律：跨进程取输出显式声明 UTF-8，不依赖控制台默认。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
XCHECK = TOOLS / "predecl_xcheck.py"

CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_xcheck(*args):
    return subprocess.run([sys.executable, str(XCHECK)] + list(args),
                          capture_output=True, timeout=60, env=CHILD_ENV)


def stdout_of(p):
    return (p.stdout or b"").decode("utf-8", errors="replace")


def stderr_of(p):
    return (p.stderr or b"").decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# SIMULATED 语料（虚构，非仓内真实件）
# ---------------------------------------------------------------------------

# 三型差异各一条＋相合一条：A-1 仅文本；T08 口径不一致（数字 30↔60、BLOCK↔放行）；
# R1 相合；J-9 仅实现。
SIM_DECL_MIXED = """\
# SIMULATED 预声明样例（虚构测试语料，非仓内真实件）

A-1 每次开跑前必须完成互校
互校不通过不得开跑

R1 超时阈值为 30 秒，超时即 BLOCK

T08 重试上限 3 次，超限 DENY
"""

SIM_IMPL_MIXED = '''\
# SIMULATED 实现样例（虚构测试语料，非仓内真实件）
# 条款 R1：超时阈值 30 秒，超时即 BLOCK
def check_r1():
    pass

# 条款 T08：重试上限 5 次，超限放行
def check_t08():
    return True

# 条款 J-9：预声明没有这一条
def check_j9():
    return None
'''

SIM_DECL_CLEAN = """\
SIMULATED 预声明样例（虚构测试语料）
S-2 每批最多 100 条，超限拦截
"""

SIM_IMPL_CLEAN = '''\
# SIMULATED 实现样例：条款 S-2 每批最多 100 条，超限拦截
LIMIT = 100
'''

SIM_DECL_CASE = """\
SIMULATED 预声明样例（虚构测试语料）
B-3 检出即 block
"""

SIM_IMPL_CASE = '''\
# SIMULATED 实现样例：条款 B-3 检出即 BLOCK
def f():
    pass
'''

SIM_DECL_CUSTOM = """\
SIMULATED 预声明样例（虚构测试语料，自定义编号形态）
xq-7 阈值 9 即拒绝
"""

SIM_IMPL_CUSTOM = '''\
# SIMULATED 实现样例：条款 xq-7 阈值 9 即拒绝
T = 9
'''


@pytest.fixture()
def sandbox(tmp_path):
    d = tmp_path / "decl.txt"
    i = tmp_path / "impl.py"
    return {"dir": tmp_path, "decl": d, "impl": i}


def write(p: Path, text: str):
    p.write_text(text, encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# ① 有差异案例：三种差异类型各至少一条，exit 1，输出含各条款定位与类型
# ---------------------------------------------------------------------------

def test_three_diff_types(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_MIXED)
    impl = write(sandbox["impl"], SIM_IMPL_MIXED)
    p = run_xcheck("--decl", decl, "--impl", impl, "--context-lines", "0")
    o = stdout_of(p)
    assert p.returncode == 1, o + stderr_of(p)
    # 三型齐
    assert "仅文本" in o and "仅实现" in o and "口径不一致" in o
    # 各条款定位（文件:行）可核
    assert f"A-1 ｜ 条款定位 {decl}:3" in o
    assert f"J-9 ｜ 条款定位 — ↔ 实现定位 {impl}:10" in o
    assert f"T08 ｜ 条款定位 {decl}:8 ↔ 实现定位 {impl}:6" in o
    # 口径不一致两侧摘录都列出
    assert "文本侧" in o and "实现侧" in o
    # 汇总行：相合 1 条（R1）
    assert "相合 1 条" in o
    assert "零差异" not in o


# ---------------------------------------------------------------------------
# ② 零差异案例：exit 0 且显式输出「零差异」（不得静默）
# ---------------------------------------------------------------------------

def test_zero_diff(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_CLEAN)
    impl = write(sandbox["impl"], SIM_IMPL_CLEAN)
    p = run_xcheck("--decl", decl, "--impl", impl, "--context-lines", "0")
    o = stdout_of(p)
    assert p.returncode == 0, o + stderr_of(p)
    assert "零差异" in o
    assert "相合 1 条" in o


# ---------------------------------------------------------------------------
# ③ 零态守卫三子案：各 exit 2 且 stderr 有显式报错
# ---------------------------------------------------------------------------

def test_guard_decl_missing(sandbox):
    impl = write(sandbox["impl"], SIM_IMPL_CLEAN)
    p = run_xcheck("--decl", str(sandbox["dir"] / "nope.txt"), "--impl", impl)
    assert p.returncode == 2
    assert "不存在" in stderr_of(p)


def test_guard_decl_empty(sandbox):
    decl = write(sandbox["decl"], "")
    impl = write(sandbox["impl"], SIM_IMPL_CLEAN)
    p = run_xcheck("--decl", decl, "--impl", impl)
    assert p.returncode == 2
    assert "为空" in stderr_of(p)


def test_guard_impl_whitespace_only(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_CLEAN)
    impl = write(sandbox["impl"], "   \n\t\n  \n")
    p = run_xcheck("--decl", decl, "--impl", impl)
    assert p.returncode == 2
    assert "为空" in stderr_of(p)


def test_guard_decl_no_clause_ids(sandbox):
    decl = write(sandbox["decl"], "SIMULATED 纯文本，没有任何条款编号\n")
    impl = write(sandbox["impl"], SIM_IMPL_CLEAN)
    p = run_xcheck("--decl", decl, "--impl", impl)
    assert p.returncode == 2
    assert "未抽取到任何条款编号" in stderr_of(p)


# ---------------------------------------------------------------------------
# ④ 摘录超过 80 字符截断并留 … 标记
# ---------------------------------------------------------------------------

def test_truncation_ellipsis(sandbox):
    long_tail = "长" * 120
    decl = write(sandbox["decl"],
                 f"SIMULATED 预声明样例\nK-4 {long_tail}\n")
    impl = write(sandbox["impl"], "# SIMULATED 实现样例，无 K-4 引用\nx = 0\n")
    p = run_xcheck("--decl", decl, "--impl", impl)
    o = stdout_of(p)
    assert p.returncode == 1
    assert "…" in o
    assert "仅文本" in o


# ---------------------------------------------------------------------------
# ⑤ 判定词大小写不敏感（block ↔ BLOCK 判相合）
# ---------------------------------------------------------------------------

def test_judgment_word_case_insensitive(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_CASE)
    impl = write(sandbox["impl"], SIM_IMPL_CASE)
    p = run_xcheck("--decl", decl, "--impl", impl, "--context-lines", "0")
    o = stdout_of(p)
    assert p.returncode == 0, o
    assert "零差异" in o


# ---------------------------------------------------------------------------
# ⑥ --id-pattern 覆盖生效（自定义小写形态 xq-7，默认正则抽不到）
# ---------------------------------------------------------------------------

def test_id_pattern_override(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_CUSTOM)
    impl = write(sandbox["impl"], SIM_IMPL_CUSTOM)
    # 覆盖后：xq-7 两侧相合 → exit 0
    p = run_xcheck("--decl", decl, "--impl", impl,
                   "--id-pattern", r"\b[a-z]{2}-\d+\b", "--context-lines", "0")
    o = stdout_of(p)
    assert p.returncode == 0, o
    assert "零差异" in o
    # 不覆盖：默认正则抽不到 xq-7 → 零条款守卫 exit 2
    p2 = run_xcheck("--decl", decl, "--impl", impl)
    assert p2.returncode == 2
    assert "未抽取到任何条款编号" in stderr_of(p2)


# ---------------------------------------------------------------------------
# 附：正则非法 → 用法错误 exit 2
# ---------------------------------------------------------------------------

def test_bad_regex(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_CLEAN)
    impl = write(sandbox["impl"], SIM_IMPL_CLEAN)
    p = run_xcheck("--decl", decl, "--impl", impl, "--id-pattern", "[")
    assert p.returncode == 2
    assert "正则非法" in stderr_of(p)


# 可重复：同输入同输出（跑两遍逐字节一致）
def test_repeatable(sandbox):
    decl = write(sandbox["decl"], SIM_DECL_MIXED)
    impl = write(sandbox["impl"], SIM_IMPL_MIXED)
    a = run_xcheck("--decl", decl, "--impl", impl)
    b = run_xcheck("--decl", decl, "--impl", impl)
    assert a.returncode == b.returncode == 1
    assert a.stdout == b.stdout
