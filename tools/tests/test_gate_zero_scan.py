# -*- coding: utf-8 -*-
"""守门器零扫描/范围声明通则断言（TDCA-STD-GATE-ZERO-SCAN-001 · Q-1~Q-9）

沙盒验证：全部样本建于 tmp_path，不扫主干、不改仓库。
六类样本：空输入 / 空目录 / 不存在路径 / 机制核正例 / 语料区负例 / 自扫。
误伤率须为 0（语料区不得判违规）；同输入同输出（可重复）。
编码纪律（GATE-SCOPE-FIX-001）：跨进程取输出显式声明 UTF-8，不依赖控制台默认。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
GATE = TOOLS / "stance_neutrality.py"

MECH_COP = 'decision: [{"if": "我方得算 > 敌方", "call": "f", "action": "战"}]'
MECH_CLEAN = 'decision: [{"if": "态势占优", "call": "f", "action": "行"}]'
CORPUS_PY = '"decision": "我方得算 > 敌方", "call": "f"\n'

# 显式声明编码：子进程 stdout/stderr 一律 UTF-8（gbk/cp936 控制台亦可复跑）
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_gate(*args, cwd=None):
    return subprocess.run([sys.executable, str(GATE)] + list(args),
                          capture_output=True, timeout=60,
                          cwd=str(cwd or TOOLS), env=CHILD_ENV)


def out(p):
    return (p.stdout or b"").decode("utf-8", errors="replace") + \
           (p.stderr or b"").decode("utf-8", errors="replace")


@pytest.fixture()
def sandbox(tmp_path):
    """六类样本目录"""
    mech = tmp_path / "mech"
    mech.mkdir()
    (mech / "good.yaml").write_text(MECH_CLEAN, encoding="utf-8")
    (mech / "bad.yaml").write_text(MECH_COP, encoding="utf-8")
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    (clean_dir / "ok.yaml").write_text(MECH_CLEAN, encoding="utf-8")
    corpus = tmp_path / "corpus" / "docs" / "cop-library" / "hundred_schools" / "demo"
    corpus.mkdir(parents=True)
    (corpus / "build.py").write_text(CORPUS_PY, encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    return {"mech": mech, "clean": clean_dir, "corpus": tmp_path / "corpus", "empty": empty}


# Q-1 不带任何目标 ⟹ 非 0
def test_q1_no_target_fails():
    p = run_gate("check")
    assert p.returncode != 0
    assert "未提供目标" in out(p)

# Q-2 路径不存在 ⟹ 非 0 ＋明确报错
def test_q2_missing_path_fails(sandbox):
    p = run_gate("check", str(sandbox["mech"] / "nope"))
    assert p.returncode != 0
    assert "目标路径不存在" in out(p)

# Q-3 空目录（零扫描）⟹ 非 0 ＋「零扫描即失守」
def test_q3_empty_dir_fails(sandbox):
    p = run_gate("check", str(sandbox["empty"]))
    assert p.returncode != 0
    assert "零扫描" in out(p)

# Q-4 输出含扫描根绝对路径、文件计数、命中计数
def test_q4_counts_and_root(sandbox):
    p = run_gate("check", str(sandbox["clean"]))
    o = out(p)
    assert p.returncode == 0
    assert "扫描根: %s" % sandbox["clean"].resolve() in o
    assert "文件: 1" in o and "机制核命中: 0" in o

# Q-5 可区分「未扫到」与「已扫且无违规」
def test_q5_distinguish_no_scan_vs_clean(sandbox):
    o_empty = out(run_gate("check", str(sandbox["empty"])))
    o_clean = out(run_gate("check", str(sandbox["clean"])))
    assert "零扫描" in o_empty and "CHECK FAIL" in o_empty
    assert "零扫描" not in o_clean and "CHECK PASS" in o_clean

# Q-6 语料区命中不判违规（豁免/分档）
def test_q6_corpus_exempt(sandbox):
    p = run_gate("check", str(sandbox["corpus"]))
    o = out(p)
    assert p.returncode == 0, o
    assert "语料区(豁免)命中: 2" in o or "语料区(豁免)命中: 1" in o
    assert "CHECK PASS" in o

# Q-7 机制核含立场词 ⟹ 判违规（非 0）
def test_q7_mech_violation_fails(sandbox):
    p = run_gate("check", str(sandbox["mech"] / "bad.yaml"))
    assert p.returncode != 0
    assert "CHECK FAIL" in out(p)

# Q-8 守门器自身/配置不自命中
def test_q8_no_self_hit():
    p = run_gate("scan", "compiler")
    o = out(p)
    assert p.returncode == 0, o
    assert "stance_neutrality.py (" not in o
    assert "stance_separation_check.py (" not in o

# Q-9 扫描范围在输出中显式声明（扫什么/不扫什么）
def test_q9_scope_declared(sandbox):
    o = out(run_gate("check", str(sandbox["clean"])))
    assert "扫描范围声明" in o and "不扫:" in o and "分档:" in o

# 可重复：同输入同输出（跑两遍逐字节一致）
def test_repeatable(sandbox):
    a = run_gate("check", str(sandbox["corpus"]))
    b = run_gate("check", str(sandbox["corpus"]))
    assert a.returncode == b.returncode == 0
    assert a.stdout == b.stdout
