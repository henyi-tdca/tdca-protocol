# -*- coding: utf-8 -*-
"""产物库批 2 入站载荷生成器（清洁五库；预检零命中者）

口径：
  · 仅取 git 跟踪件；slug = <子库>--<相对路径去扩展名，'/'→'__'>（单段式，URL 安全）
  · title = 文件名主干（在册名）；body_md = 文件原文逐字（UTF-8，不改一字）
  · source_path = tdca-protocol/<仓内路径>（与批一在册件同口径）
  · 在册重叠（同 source_path 已入库者）由 apply 侧跳过，本侧照列全量并标 has_overlap 示意
用法（仓库根目录）：
  python tools/cop10_build_payload.py <输出.jsonl>
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ["chengyu", "compositions", "games", "marxism", "microeconomics"]


def main() -> int:
    out_path = Path(sys.argv[1])
    files = subprocess.run(["git", "ls-files", "docs/cop-library"],
                           capture_output=True, cwd=ROOT).stdout.decode("utf-8").splitlines()
    rows = []
    seen = {}
    for f in files:
        parts = f.split("/")
        if len(parts) < 4 or parts[2] not in LIBS:
            continue
        sub = parts[2]
        rel = "/".join(parts[3:])
        stem = rel.rsplit(".", 1)[0]
        slug = f"{sub}--{stem.replace('/', '__')}"
        if slug in seen:
            print(f"SLUG_COLLISION: {slug} ({seen[slug]} vs {f})")
            return 1
        seen[slug] = f
        body = (ROOT / f).read_text(encoding="utf-8")
        rows.append({
            "slug": slug,
            "title": Path(stem).name,
            "body_md": body,
            "source_path": f"tdca-protocol/{f}",
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "sub_library": sub,
        })
    with out_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    per = {}
    for r in rows:
        per[r["sub_library"]] = per.get(r["sub_library"], 0) + 1
    print(f"# 载荷：{len(rows)} 件")
    for k in LIBS:
        print(f"  {k:18s} {per.get(k, 0)}")
    print(f"# 输出：{out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
