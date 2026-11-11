# -*- coding: utf-8 -*-
"""G9 数据契约闸 v1.1（只读；合入 tools/ 供 gate-site 调用）

口径（照 TDCA-AMEND-PARITY-GATE-001）：
- 正本＝TDCA-SPEC-API-CONTRACT-001 之实况快照（本脚本内置首批登记）
- 副本＝线上实况（匿名取样，只取键名与类型，⛔ 取业务/个人数据内容）
- 三态：EQUAL／DIFF／UNREGISTERED；未登记端点 ⛔ 判通过 ⛔ 判失败
- 判定：G9 PASS 仅当已登记端点全 EQUAL 且零 DIFF
- 批 1 登记（2026-11-11 实测）：library/whitepaper·paper·terms·cop-library 条目字段
  =(has_content, slug, synced_at, title)；knowledge/terms 条目字段=(def, term)。
  /api/v1/library/kg 匿名 401，未登记、报「未覆盖」，不判。
- v1.1（L1SI209 GATE-AND-SVG-001 L4）：REGISTRY 增自描述三字段
  （source_spec／source_snapshot_sha256_16／synced_at）；标注未齐时输出
  SNAPSHOT=PENDING-SYNC（提示，不改 VERDICT、不判 FAIL）；运行输出
 《未契约化端点清单》（可匿名 200 而未登记者），单列不计入 VERDICT。

用法：python3 tools/ci_g9_contract_gate.py [--json]
"""
import gzip
import json
import re
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://tdca.com.cn"

# 正本：首批五端点（时点 2026-11-11T02:45+08）
# container=None 表示非容器形态（data 或顶层为字典，核其键集）；否则为 data 下的容器键
# 自描述三字段照 L1SI209 GATE-AND-SVG-001 L4：source_snapshot_sha256_16 为智库册正本快照前 16 位大写
# v1.2（L1SI209 SHAPE-F3-MERGE-001 任务二）：
#  · 智库册正本快照真值补登（GSEQ-7898 口径：正本四件 7850→7856→7863→7898 升序拼字节
#    取 sha256 前 16 位大写；执行侧复算全值一致 129E0616F75CBEFD…）
#  · 新增登记 13 端点＝令 §三 六端＋批2A 七端（2026-11-11 匿名实测观测，照表写）
#  · expect_anon_401=True 条目只探匿名状态码，401→ANON401(预期) 不计 DIFF，非 401→DIFF
#  · siblings 为 data 级同级键标注（annotation-only，比对逻辑不读）
_SOURCE_SPEC = ("TDCA-SPEC-API-CONTRACT-001＋TDCA-AMEND-PARITY-GATE-001(GSEQ-7851)"
                "＋TDCA-AMEND-3(GSEQ-7898)＋批2A(TDCA-AMEND-L1SI208-API-CONTRACT-002 §五)")
_SNAPSHOT_SHA16 = "129E0616F75CBEFD"
_SYNCED_AT = "2026-11-11T02:45+08"       # 批1 八条
_SYNCED_AT_B2 = "2026-11-11+08"          # 批2 新增 13 条（2026-11-11 实测日）
REGISTRY = [
    dict(ep="/api/site/docs", top=("count", "documents", "family", "principle", "source"),
         container="documents", nested=False,
         fields=("bytes", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/site/docs/regulation", top=("count", "documents", "family", "principle", "source"),
         container="documents", nested=False,
         fields=("bytes", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/announcements/list?limit=1", top=("data", "data_nature", "nca_watermark", "ts"),
         container="announcements", nested=True,
         fields=("announcement_id", "body", "published_at", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/library/whitepaper", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/library/paper", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/library/terms", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/library/cop-library", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    dict(ep="/api/v1/knowledge/terms?limit=1", top=("data", "data_nature", "nca_watermark", "ts"),
         container="terms", nested=True,
         fields=("def", "term"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT),
    # 未覆盖：/api/v1/library/kg 匿名 401（GSEQ 批1 读数，须登录，不登记不判）
    # ── 令 §三 六端（2026-11-11 匿名实测，逐字相符；容器名四异逐端写，⛔抽象列表键）──
    dict(ep="/api/v1/library/families", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("count", "family", "name"), siblings=("note",),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/library/laws", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"), siblings=("family", "name"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/library/law-notes", top=("data", "data_nature", "nca_watermark", "ts"),
         container="items", nested=True,
         fields=("has_content", "slug", "synced_at", "title"), siblings=("family", "name"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/assets/five-orders", top=("data", "data_nature", "nca_watermark", "ts"),
         container="assets", nested=True,
         fields=("count", "desc", "name", "order"), siblings=("note",),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/audit/ledger-public", top=("data", "data_nature", "nca_watermark", "ts"),
         container="events", nested=True,
         fields=("amount", "currency", "event_id", "ts", "type"),
         siblings=("total", "next_cursor", "note"),
         note="线上匿名 total=3、next_cursor 为空串，一次取全；游标语义由仓内 gateway 分页测试证",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/formal/conclusion/catalog", top=("data", "data_nature", "nca_watermark", "ts"),
         container="conclusions", nested=True,
         fields=("claim_text", "data_nature", "scope_summary"), siblings=("count", "note"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    # ── 批2A 七端（缺口实测；参数化端点以实例值探测）──
    dict(ep="/api/v1/intent", top=("data", "data_nature", "nca_watermark", "ts"),
         container=None, nested=True,
         fields=("action", "alternatives", "guide", "matched", "note", "route", "title"),
         note="data 为字典七键（非容器）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/public/registrations",
         top=("count", "face", "items", "labels", "proof_boundary"),
         container="items", nested=False,
         fields=("content_sha256_16", "family", "nca_ref", "record_id", "registered_at", "status", "title"),
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/library/paper/E1_cross_model_consistency",
         top=("data", "data_nature", "nca_watermark", "ts"),
         container=None, nested=True,
         fields=("body_md", "family", "note", "slug", "source_path", "synced_at", "title"),
         note="library/{family}/{slug} 实例：data 字典（非容器）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/site/docs/regulation/配置权市场规范（单一权威稿·中文人读版V1.0（现行））.md",
         top=("bytes", "content", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version"),
         container=None, nested=False,
         fields=("bytes", "content", "display_name", "family", "filename", "sha256", "sha256_16", "slug", "version"),
         note="site/docs/{family}/{slug} 实例：顶层单件九键（非容器；URL 含 CJK，fetch 须 quote）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/selfcheck/nca/NCA-SEED-001",
         top=("data", "data_nature", "nca_watermark", "ts"),
         container=None, nested=True,
         fields=("artifact_filename_note", "note", "page_disclaimer", "rec_hash_spec", "record", "sha256_8_note"),
         note="{nca_id} 实例（id 取仓内 PUBLIC-SELFCHECK-MANIFEST.yaml）：data 字典（非容器）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/me/nca", expect_anon_401=True,
         note="匿名 401 实测确认（登录态私域面，只认匿名→私域→401）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
    dict(ep="/api/v1/ops/logs", expect_anon_401=True,
         note="匿名 401 实测确认（登录态私域面，只认匿名→私域→401）",
         source_spec=_SOURCE_SPEC, source_snapshot_sha256_16=_SNAPSHOT_SHA16, synced_at=_SYNCED_AT_B2),
]

# 未契约化清单候选宇宙：批 2A 十五端点登记（TDCA-AMEND-L1SI208-API-CONTRACT-002 §五，
# 派生件 true-source/tdca-site/docs/shape-standard.yaml）∪ REGISTRY。
# openapi.json 匿名 404（2026-11-11 实测），端点宇宙不可在线枚举，候选以外者本闸不可见、照实不列。
# 参数化端点（/{family}/{slug}、/selfcheck/nca/{id}）须实例参数，本批以具体值探测。
CANDIDATES = [
    "/api/site/docs",
    "/api/site/docs/regulation",
    "/api/site/docs/terms",
    "/api/site/docs/laws",
    "/api/site/docs/whitepaper",
    "/api/site/docs/paper",
    "/api/v1/announcements/list",
    "/api/v1/assets/five-orders",
    "/api/v1/audit/ledger-public",
    "/api/v1/knowledge/terms",
    "/api/v1/library/families",
    "/api/v1/formal/conclusion/catalog",
    "/api/v1/library/whitepaper",
    "/api/v1/library/paper",
    "/api/v1/library/terms",
    "/api/v1/library/cop-library",
    "/api/v1/library/laws",
    "/api/v1/library/law-notes",
    "/api/v1/library/kg",
    "/api/v1/intent",
    "/api/v1/me/nca",
    "/api/v1/ops/logs",
    "/api/public/registrations",
    "/api/v1/selfcheck/nca/__probe__",
]


from urllib.parse import quote

def fetch(path):
    # URL 含 CJK slug（site/docs 实例）须 quote，保留 query 与路径分隔符
    req = urllib.request.Request(BASE + quote(path, safe="/?=&"), headers={"User-Agent": "tdca-g9/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8", "replace"))


def probe_status(path):
    """匿名 GET 只探状态码（取键名比对之外的清单探测用，⛔解析内容）。"""
    req = urllib.request.Request(BASE + quote(path, safe="/?=&"), headers={"User-Agent": "tdca-g9/1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def observe(spec):
    d = fetch(spec["ep"])
    top = tuple(sorted(d.keys()))
    holder = d.get("data") if spec["nested"] else d
    if spec["container"] is None:
        # 非容器形态：data（或顶层）为字典，核其键集
        if isinstance(holder, dict):
            return top, holder, tuple(sorted(holder.keys()))
        return top, None, None
    items = holder.get(spec["container"]) if isinstance(holder, dict) else None
    fields = None
    if isinstance(items, list) and items and isinstance(items[0], dict):
        fields = tuple(sorted(items[0].keys()))
    return top, items, fields


def snapshot_state():
    """正本快照标注自检：三字段齐全且 sha16 为 16 位大写十六进制才算 SYNCED。"""
    hex16 = re.compile(r"^[0-9A-F]{16}$")
    for s in REGISTRY:
        if not (s.get("source_spec") and s.get("synced_at")
                and hex16.match(str(s.get("source_snapshot_sha256_16", "")))):
            return "PENDING-SYNC"
    return "SYNCED"


def uncovered_endpoints():
    """可匿名 200 而未登记者（候选宇宙内），逐条 (path, status)。"""
    registered = {s["ep"].split("?")[0] for s in REGISTRY}
    out = []
    for c in CANDIDATES:
        code = probe_status(c)
        if code == 200 and c.split("?")[0] not in registered:
            out.append((c, code))
    return out


def main():
    as_json = "--json" in sys.argv
    rows, diffs = [], 0
    for spec in REGISTRY:
        if spec.get("expect_anon_401"):
            # 匿名 401 条目：只探状态码，401→预期（不计 DIFF），非 401→DIFF
            code = probe_status(spec["ep"])
            if code == 401:
                rows.append(dict(ep=spec["ep"], state="ANON401(预期)",
                                 note=spec.get("note", "匿名→私域面→401")))
            else:
                diffs += 1
                rows.append(dict(ep=spec["ep"], state="DIFF",
                                 note="匿名状态码=%s，预期 401" % code))
            continue
        try:
            top, items, fields = observe(spec)
        except Exception as e:
            rows.append(dict(ep=spec["ep"], state="ERR", note=str(e)[:80]))
            diffs += 1
            continue
        if items is None:
            what = ("非容器字典形态不符" if spec["container"] is None
                    else "容器键不存在：%s" % spec["container"])
            rows.append(dict(ep=spec["ep"], state="DIFF", note=what))
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

    snap = snapshot_state()
    uncovered = uncovered_endpoints()
    verdict = "PASS" if diffs == 0 else "FAIL"
    if as_json:
        print(json.dumps(dict(verdict=verdict, snapshot=snap,
                              uncovered=[dict(ep=p, status=c) for p, c in uncovered],
                              rows=rows), ensure_ascii=False, indent=1))
    else:
        print("=== G9 数据契约闸 v1.2（只读）===")
        print("正本：TDCA-SPEC-API-CONTRACT-001（批1 2026-11-11T02:45+08；批2 新增 13 端点 2026-11-11 实测）")
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
        if snap == "PENDING-SYNC":
            print("SNAPSHOT=PENDING-SYNC（正本快照 sha16 标注待智库册补登；提示，不改 VERDICT、不判 FAIL）")
        else:
            print("SNAPSHOT=SYNCED")
        print("--- 未契约化端点清单（单列，不计入 VERDICT）---")
        if uncovered:
            for p, c in uncovered:
                print("  %-46s %s" % (p, c))
        else:
            print("  （候选宇宙内无可匿名 200 而未登记者）")
        print("未契约化清单 %d 条；候选宇宙=批2A 十五登记∪REGISTRY（openapi 匿名 404 不可枚举）" % len(uncovered))
        print("VERDICT=%s" % verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
