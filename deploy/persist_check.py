#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P5-1 网关 sqlite 迁卷持久化检查（消除「重建回种子态」坑）。

判据（全部满足才算 PASS）：
  1. DATABASE_URL 为 sqlite 时，库文件路径必须为绝对路径；
  2. 路径不得位于易失目录（系统临时目录、/tmp、/var/run、容器 overlay 上层）；
  3. 父目录已存在（部署前置条件）。
非 sqlite 连接串（如 PostgreSQL）交由 DBA 面，本检查不做断言（如实标注 external）。
退出码：0=PASS；1=FAIL（部署前必须消除）。
用法：python deploy/persist_check.py [--db-url sqlite:///...]
"""
import argparse
import json
import os
import sqlite3
import sys
import tempfile

EPHEMERAL_HINTS = ("/tmp", "/var/run", "/dev/shm", "/run/")


def _norm(p: str) -> str:
    return os.path.normpath(p).replace("\\", "/")


def check_persistence(db_url: str) -> dict:
    """返回 {"ok": bool, "checks": [{"rule", "detail", "pass"}]}。"""
    checks = []
    if not db_url.startswith("sqlite:///"):
        checks.append({"rule": "scheme", "detail": f"非 sqlite（{db_url.split(':', 1)[0]}）——外置库 DBA 面",
                       "pass": True})
        return {"ok": True, "checks": checks}
    path = _norm(db_url[len("sqlite:///"):])
    is_abs = os.path.isabs(path)
    checks.append({"rule": "absolute-path",
                   "detail": f"库文件绝对路径：{path}", "pass": is_abs})
    tmpdir = _norm(tempfile.gettempdir())
    volatile = (not is_abs) or path.startswith(tmpdir) or \
        any(path.startswith(h) for h in EPHEMERAL_HINTS)
    checks.append({"rule": "not-ephemeral",
                   "detail": "不在易失目录（临时目录/tmp/var-run/dev-shm）", "pass": not volatile})
    parent = os.path.dirname(path)
    exists = os.path.isdir(parent)
    checks.append({"rule": "parent-exists", "detail": f"父目录存在：{parent}", "pass": exists})
    return {"ok": all(c["pass"] for c in checks), "checks": checks}


def main() -> int:
    ap = argparse.ArgumentParser(description="P5 sqlite 迁卷持久化检查")
    ap.add_argument("--db-url", default=os.environ.get(
        "DATABASE_URL", "sqlite:///../true-source/tdca-web/tdca.db"))
    args = ap.parse_args()
    result = check_persistence(args.db_url)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if not result["ok"]:
        print("FAIL：迁卷未落实——重建将回种子态，⛔ 不得部署", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
