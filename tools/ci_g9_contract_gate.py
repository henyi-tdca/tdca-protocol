# -*- coding: utf-8 -*-
"""G9 数据契约闸 v1（只读；合入 tools/ 供 gate-site 调用）

口径（照 TDCA-AMEND-PARITY-GATE-001）：
- 正本＝TDCA-SPEC-API-CONTRACT-001 之实况快照（本脚本内置首批登记）
- 副本＝线上实况（匿名取样，只取键名与类型，⛔ 取业务/个人数据内容）
- 三态：EQUAL／DIFF／UNREGISTERED；未登记端点 ⛔ 判通过 ⛔ 判失败
- 判定：G9 PASS 仅当已登记端点全 EQUAL 且零 DIFF
- 批 1 登记（2026-11-11 实测）：library/whitepaper·paper·terms·cop-library 条目字段
  =(has_content, slug, synced_at, title)；knowledge/terms 条目字段=(def, term)。
  /api/v1/library/kg 匿名 401，未登记、报「未覆盖」，不判。

用法：python3 tools/ci_g9_contract_gate.py [--json]
"""
import gzip
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://tdca.com.cn"

# 正本：首批五端点（时点 2026-11-11T02:45+08）
# container=None 表示条目在顶层键；否则为 data 下的容器键
REGISTRY = [
    dict(ep="/api/site/docs", top=("count", "documents", "family", "principle", "source"),
         container="documents", nested=False,
         fields=("bytes", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version")),
    dict(ep="/api/site/docs/regulation", top=("count", "documents", "family", "principle", "source"),
         container="documents", nested=False,
         fields=("bytes", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version")),
    dict(ep="/api/v1/announcements/list?limit=1", top=("data", "data_nature", "nca_watermark", "ts"),
         container="announcements", nested=True,
         fields=("announcement_id", "body", "published_at", "title")),
    dict(ep="/api/v1/library/whitepaper", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title")),
    dict(ep="/api/v1/library/paper", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title")),
    dict(ep="/api/v1/library/terms", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title")),
    dict(ep="/api/v1/library/cop-library", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title")),
    dict(ep="/api/v1/knowledge/terms?limit=1", top=("data", "data_nature", "nca_watermark", "ts"),
         container="terms", nested=True,
         fields=("def", "term")),
    # 未覆盖：/api/v1/library/kg 匿名 401（GSEQ 批1 读数，须登录，不登记不判）
]


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "tdca-g9/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8", "replace"))


def observe(spec):
    d = fetch(spec["ep"])
    top = tuple(sorted(d.keys()))
    holder = d.get("data") if spec["nested"] else d
    items = holder.get(spec["container"]) if isinstance(holder, dict) else None
    fields = None
    if isinstance(items, list) and items and isinstance(items[0], dict):
        fields = tuple(sorted(items[0].keys()))
    return top, items, fields


def main():
    as_json = "--json" in sys.argv
    rows, diffs = [], 0
    for spec in REGISTRY:
        try:
            top, items, fields = observe(spec)
        except Exception as e:
            rows.append(dict(ep=spec["ep"], state="ERR", note=str(e)[:80]))
            diffs += 1
            continue
        if items is None:
            rows.append(dict(ep=spec["ep"], state="DIFF", note="容器键不存在：%s" % spec["container"]))
            diffs += 1
            continue
        top_ok = set(spec["top"]) == set(top)
        if spec["fields"] is None:
            rows.append(dict(ep=spec["ep"], state="EQUAL(字段待补)", top_ok=top_ok,
                             note="容器 %s 存在；条目字段未登记，不判" % spec["container"]))
            if not top_ok:
                diffs += 1
            continue
        f_ok = set(spec["fields"]) == set(fields or ())
        state = "EQUAL" if (top_ok and f_ok) else "DIFF"
        if state == "DIFF":
            diffs += 1
        rows.append(dict(ep=spec["ep"], state=state, top_ok=top_ok, fields_ok=f_ok,
                         extra=sorted(set(fields or ()) - set(spec["fields"])),
                         missing=sorted(set(spec["fields"]) - set(fields or ()))))

    verdict = "PASS" if diffs == 0 else "FAIL"
    if as_json:
        print(json.dumps(dict(verdict=verdict, rows=rows), ensure_ascii=False, indent=1))
    else:
        print("=== G9 数据契约闸 v1（只读）===")
        print("正本：TDCA-SPEC-API-CONTRACT-001（2026-11-11T02:45+08；批1字段 2026-11-11 实测补登）")
        for r in rows:
            line = "  %-46s %s" % (r["ep"], r["state"])
            if r.get("missing"):
                line += "  缺=%s" % ",".join(r["missing"])
            if r.get("extra"):
                line += "  多=%s" % ",".join(r["extra"])
            if r.get("note"):
                line += "  (%s)" % r["note"]
            print(line)
        print("已登记端点一致：%d/%d" % (len(rows) - diffs, len(rows)))
        print("VERDICT=%s" % verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
