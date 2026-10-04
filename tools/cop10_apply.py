# -*- coding: utf-8 -*-
"""产物库批 2 入库执行（容器内跑；幂等）

读 JSONL 载荷，按 source_path 去重在 docs 表插入新行（family=cop-library, real）。
⛔ 不改既有行；⛔ 不动其他族。重复执行安全（已入册者跳过）。
用法（网关容器内）：
  python /tmp/cop10_apply.py /tmp/cop10_payload.jsonl
"""
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.environ.get("DATABASE_URL", "sqlite:////data/tdca.db").replace("sqlite:///", "/", 1)


def main() -> int:
    payload_path = sys.argv[1]
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    existing = {r["source_path"] for r in conn.execute("SELECT source_path FROM docs")}
    inserted, skipped, bad = 0, 0, []
    now = datetime.now(timezone.utc).isoformat()
    with open(payload_path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["source_path"] in existing:
                skipped += 1
                continue
            digest = hashlib.sha256(r["body_md"].encode("utf-8")).hexdigest()
            if digest != r["body_sha256"]:
                bad.append((r["slug"], "sha256 不符"))
                continue
            conn.execute(
                "INSERT INTO docs (family, slug, title, body_md, source_path, data_nature, synced_at)"
                " VALUES (?, ?, ?, ?, ?, 'real', ?)",
                ("cop-library", r["slug"], r["title"], r["body_md"], r["source_path"], now))
            existing.add(r["source_path"])
            inserted += 1
    conn.commit()
    counts = {r["family"]: r["n"] for r in conn.execute("SELECT family, COUNT(*) AS n FROM docs GROUP BY family")}
    per = {r["k"]: r["n"] for r in conn.execute(
        "SELECT substr(slug, 1, instr(slug, '--') - 1) AS k, COUNT(*) AS n"
        " FROM docs WHERE family='cop-library' AND instr(slug, '--') > 0 GROUP BY k")}
    print(json.dumps({"inserted": inserted, "skipped_overlap": skipped, "bad": bad,
                      "family_counts": counts, "cop_sub_counts": per}, ensure_ascii=False, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
