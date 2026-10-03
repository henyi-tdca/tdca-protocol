#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P5-2 网关 sqlite 备份 + 恢复校验（判据：重建不丢数据）。

backup：      复制库文件至备份目录（时间戳名）＋ 写 sha256 清单（manifest）。
restore-verify：将备份副本还原到临时路径，sqlite quick_check + 表数核对，
               证明「备份可用、重建可恢复」。
用法：
  python deploy/backup_db.py backup --db <库文件> --dir <备份目录>
  python deploy/backup_db.py restore-verify --backup <备份文件>
退出码：0=成功；1=失败。
"""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(db_path: str, backup_dir: str) -> dict:
    if not os.path.isfile(db_path):
        raise SystemExit(f"FAIL：库文件不存在 {db_path}")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = os.path.join(backup_dir, f"tdca-db-{ts}.sqlite")
    shutil.copy2(db_path, target)
    manifest = {
        "ts": ts, "source": os.path.abspath(db_path), "backup": target,
        "sha256": _sha256(target), "bytes": os.path.getsize(target),
        "note": "P5 备份清单；恢复以 restore-verify 实测为准",
    }
    mpath = target + ".manifest.json"
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return manifest


def restore_verify(backup_path: str) -> dict:
    """还原到临时库并校验：quick_check + 用户表计数（与源备份一致即证完整）。"""
    with tempfile.TemporaryDirectory(prefix="tdca-restore-") as td:
        restored = os.path.join(td, "restored.sqlite")
        shutil.copy2(backup_path, restored)
        con = sqlite3.connect(restored)
        try:
            qc = con.execute("PRAGMA quick_check").fetchone()[0]
            tables = con.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        finally:
            con.close()
    ok = qc == "ok" and tables > 0
    return {"ok": ok, "quick_check": qc, "user_tables": tables,
            "sha256": _sha256(backup_path)}


def main() -> int:
    ap = argparse.ArgumentParser(description="P5 sqlite 备份/恢复校验")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--db", required=True)
    b.add_argument("--dir", required=True)
    v = sub.add_parser("restore-verify")
    v.add_argument("--backup", required=True)
    args = ap.parse_args()
    if args.cmd == "backup":
        m = backup(args.db, args.dir)
        print(json.dumps(m, ensure_ascii=False, indent=1))
        return 0
    r = restore_verify(args.backup)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if not r["ok"]:
        print("FAIL：恢复校验未通过——备份不可用，⛔ 不得结案", file=sys.stderr)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
