# -*- coding: utf-8 -*-
"""
ci_authwrite_gate_step —— CIGATE-001（gate-write-auth.yml 追加步）判定器

令：TDCA-HANDOFF-EXEC-L1SI222-CIGATE-001（2026-11-20，落既有 gate-write-auth.yml
现有闸步骤之后加一步，取甲案文件级真跑；⛔新开 workflow ⛔改既有步 ⛔改触发面/paths）。

步逻辑：
  判 PR/push diff 是否触及
    (a) 统一写鉴权依赖本体 true-source/tdca-web/gateway/ops_auth_gate.py，或
    (b) 任一 require_write_privilege( 挂载点 —— 挂载面以现有
        tools/ci_write_auth_gate.py 之口径为准（⛔另立键）：
        gateway/ 顶层 endswith("_ops.py") 或 ∈ {"api_v1.py"} 的扫描面内，
        diff 增/删行含 require_write_privilege( 者即触及挂载。
  命中 ⟹ 真跑 pytest tests/test_authwrite_four_tiers.py（须 10 passed；
           缺文件或跑数不满 ⟹ 红，fail-closed）。
  未命中 ⟹ 打印「未触及」并直接绿（免空跑，⛔默红）。

事件面：
  pull_request       —— fetch GITHUB_BASE_REF 后 git diff origin/<base>...HEAD
                        （浅克隆无 merge-base 时回退两点 diff）。
  push               —— 读 GITHUB_EVENT_PATH before/after，两点 diff；
                        新分支（before 全零）无 diff 可比 ⟹ 按命中真跑（fail-closed）。
  workflow_dispatch  —— 无 diff 可比 ⟹ 按命中真跑。
  其他/无法判定       —— fail-closed 打红（CI 环境恒为上述三者之一）。

本地实测：python3 tools/ci_authwrite_gate_step.py <base> <head>

SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# git diff 路径恒为正斜杠——凡与 diff 比对之常量一律正斜杠，文件系统拼接另用 _FS 变体
GATEWAY_DIR = "true-source/tdca-web/gateway"
GATEWAY_DIR_FS = os.path.join("true-source", "tdca-web", "gateway")
GATEWAY_PREFIX = GATEWAY_DIR + "/"
AUTH_GATE = GATEWAY_PREFIX + "ops_auth_gate.py"
# 与 tools/ci_write_auth_gate.py 同口径之扫描面（⛔另立键）
SCAN_FILES = ("api_v1.py",)
MOUNT_MARK = "require_write_privilege("
TEST_RELPATH = GATEWAY_DIR + "/tests/test_authwrite_four_tiers.py"
TEST_PATH_FS = os.path.join(GATEWAY_DIR_FS, "tests", "test_authwrite_four_tiers.py")
NEED_PASSED = 10


def _is_scan_surface(relpath: str) -> bool:
    """是否属 ci_write_auth_gate.py 之扫描面（gateway/ 顶层 *_ops.py 或 api_v1.py）。"""
    if not relpath.startswith(GATEWAY_PREFIX):
        return False
    rest = relpath[len(GATEWAY_PREFIX):]
    if "/" in rest:  # 子目录不入闸面（tests/、kg/ 等）
        return False
    return rest.endswith("_ops.py") or rest in SCAN_FILES


def _git_diff(three_dot: str, two_dot: str) -> str:
    p = subprocess.run(
        ["git", "diff", three_dot],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if p.returncode == 0 and p.stdout:
        return p.stdout
    p2 = subprocess.run(
        ["git", "diff", two_dot],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return p2.stdout if p2.returncode == 0 else ""


def _diff_pr() -> str:
    base = os.environ["GITHUB_BASE_REF"]
    subprocess.run(
        ["git", "fetch", "--depth=100", "origin", base],
        capture_output=True, text=True, check=False,
    )
    ref = f"origin/{base}"
    return _git_diff(f"{ref}...HEAD", f"{ref}..HEAD")


def _diff_push() -> tuple[str, bool]:
    """返回 (diff 文本, 是否强制命中)。新分支无 before 可比 ⟹ 强制命中。"""
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    before = event.get("before") or ""
    after = event.get("after") or ""
    if not before or set(before) == {"0"}:
        return "", True
    for rev, depth in ((before, "2"), (after, "2")):
        subprocess.run(
            ["git", "fetch", "--depth=" + depth, "origin", rev],
            capture_output=True, text=True, check=False,
        )
    return _git_diff(f"{before}..{after}", f"{before}..{after}"), False


def analyze(diff_text: str) -> tuple[bool, list[str]]:
    """解析 diff：返回 (是否触及依赖本体, 触及挂载点之文件清单)。"""
    touched_dep = False
    mount_files: list[str] = []
    cur: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            cur = line[len("+++ b/"):].strip()
            continue
        if line.startswith("+++") or line.startswith("---"):
            cur = None
            continue
        if cur is None:
            continue
        if cur == AUTH_GATE:
            touched_dep = True
        if not _is_scan_surface(cur):
            continue
        if line[:1] in "+-" and MOUNT_MARK in line[1:]:
            if cur not in mount_files:
                mount_files.append(cur)
    return touched_dep, mount_files


def run_fourtier() -> bool:
    """命中后真跑四档五断言专测：须 NEED_PASSED passed，缺文件/跑数不满 ⟹ 红。"""
    test_abs = os.path.join(REPO_ROOT, TEST_PATH_FS)
    if not os.path.isfile(test_abs):
        print(f"::error::缺测试件 {TEST_RELPATH}（须 10 用例在位）——RED")
        return False
    print(f"命中——真跑 pytest {TEST_RELPATH}（须 {NEED_PASSED} passed）")
    # 依赖就位（与 gate-gateway.yml 同款装法；失败不中止，交由 pytest 判定）
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "pytest"],
        capture_output=True, check=False,
    )
    req = os.path.join(GATEWAY_DIR_FS, "requirements.txt")
    if os.path.isfile(os.path.join(REPO_ROOT, req)):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", req],
            capture_output=True, check=False,
        )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (env.get("PYTHONPATH", ""), REPO_ROOT) if p
    )
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_authwrite_four_tiers.py", "-q"],
        cwd=os.path.join(REPO_ROOT, GATEWAY_DIR_FS),
        env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    tail = ((p.stdout or "")[-3000:]) + "\n" + ((p.stderr or "")[-2000:])
    print(tail)
    if p.returncode != 0:
        print("::error::四档五断言专测未全绿——RED")
        return False
    m = re.search(r"(\d+)\s+passed", p.stdout or "")
    n = int(m.group(1)) if m else 0
    if n < NEED_PASSED:
        print(f"::error::须 {NEED_PASSED} passed，实测 {n}——RED")
        return False
    print(f"专测通过：{n} passed（门槛 ≥ {NEED_PASSED}）")
    return True


def main() -> int:
    os.chdir(REPO_ROOT)
    if len(sys.argv) >= 3:  # 本地实测模式：python3 本脚本 <base> <head>
        diff_text = _git_diff(f"{sys.argv[1]}...{sys.argv[2]}",
                              f"{sys.argv[1]}..{sys.argv[2]}")
        forced = False
    else:
        event = os.environ.get("GITHUB_EVENT_NAME", "")
        if event == "pull_request":
            diff_text = _diff_pr()
            forced = False
        elif event == "push":
            diff_text, forced = _diff_push()
        elif event == "workflow_dispatch":
            diff_text, forced = "", True
        else:
            print(f"::error::无法判定 diff（事件 {event or '未知'}）——fail-closed RED")
            return 1
    if forced:
        print("无 diff 可比（workflow_dispatch／push 新分支）——按命中真跑（fail-closed）")
        ok = run_fourtier()
    else:
        touched_dep, mounts = analyze(diff_text)
        if touched_dep:
            print(f"diff 触及统一写鉴权依赖本体：{AUTH_GATE}")
        for fn in mounts:
            print(f"diff 触及挂载点行：{fn}")
        if touched_dep or mounts:
            ok = run_fourtier()
        else:
            print("未触及统一写鉴权依赖本体（ops_auth_gate.py）或任一 "
                  "require_write_privilege( 挂载点——本步直接绿")
            ok = True
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
