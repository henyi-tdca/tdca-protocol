# -*- coding: utf-8 -*-
"""同源派生校验 gate（TDCA-HANDOFF-EXEC-L1SI196-SAMESOURCE-001）。

只读对账：站机公开只读文档面 vs 仓内白名单（git 对象，⛔ 不读工作树）。
门只报差：⛔ 自动修复、⛔ 自动改白名单、⛔ 自动开 PR 改内容、⛔ 存凭据、⛔ 日志含正文。

判据（令面 §一写死）：
  C-1 族级取数：对 _FAMILY_DIRS 各族逐一 GET /api/public/docs/{family}
  C-2 仓侧取数：git show <rev>:true-source/tdca-web/gateway/public_docs_ops.py 之 _PUBLIC_DOCS
  C-3 站有仓无 STATION_ONLY（空 ⟹ 该族过）
  C-4 仓有站无 REPO_ONLY（空 ⟹ 该族过；说明未部署或白名单未生效）
  C-5 count 与 documents 长度不等 ⟹ COUNT_MISMATCH
  C-6 件级哈希：每族抽首/末 2 件取 content 字段复算 sha256_16，与仓内 git blob 比
  C-7 站不可达（超时/5xx）⟹ UNKNOWN（⛔ 报 PASS）
  C-8 例外登记：具名例外一行一件（理由＋到期日），例外须经本侧裁后入表，脚本不自加

退出码：全过 0；有差 1；UNKNOWN 2（三分 ⛔ 混）。

用法：
  python tools/ops/samesource_check.py [--base-url URL] [--rev REV]
      [--exceptions tools/ops/samesource_exceptions.yaml] [--timeout 15] [--verify-tls]
"""
import argparse
import ast
import datetime
import hashlib
import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

OPS_PATH = "true-source/tdca-web/gateway/public_docs_ops.py"
DOCS_PREFIX = "docs"  # 白名单条目相对 docs/{family_dir}/ 落点（同 _docs_dir 口径）
SAMPLE_N = 2  # C-6：每族抽样件数（首/末）

GATE_ID = "TDCA-HANDOFF-EXEC-L1SI196-SAMESOURCE-001"


# ---------- git 对象读取（C-2：⛔ 读工作树） ----------

def git_blob(rev, path):
    r = subprocess.run(["git", "cat-file", "blob", f"{rev}:{path}"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout


def load_repo_state(rev):
    """返回 (family_dirs, public_docs)。读不到 ⟹ 抛异常（由主流程判 UNKNOWN）。"""
    src = git_blob(rev, OPS_PATH)
    if src is None:
        raise RuntimeError(f"git 对象不可读：{rev}:{OPS_PATH}")
    tree = ast.parse(src.decode("utf-8"))
    fam_dirs = pub = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if not isinstance(t, ast.Name):
                continue
            if t.id == "_FAMILY_DIRS":
                fam_dirs = ast.literal_eval(node.value)
            elif t.id == "_PUBLIC_DOCS":
                pub = {k: list(v) for k, v in ast.literal_eval(node.value).items()}
    if fam_dirs is None or pub is None:
        raise RuntimeError("_FAMILY_DIRS / _PUBLIC_DOCS 定位失败（⛔ 猜）")
    return fam_dirs, pub


def blob_sha16(rev, path):
    b = git_blob(rev, path)
    if b is None:
        return None
    return hashlib.sha256(b).hexdigest()[:16]


# ---------- 例外表（C-8） ----------

def load_exceptions(path):
    """逐行格式（一行一件，TAB 分隔四字段）：
        family <TAB> name <TAB> reason <TAB> expires(YYYY-MM-DD)
    空行与 # 注释行忽略。"""
    out = []
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return out
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) != 4:
            print(f"[warn] 例外表第 {ln} 行字段数非 4，跳过：{line[:80]}")
            continue
        fam, name, reason, expires = (p.strip() for p in parts)
        out.append({"family": fam, "name": name, "reason": reason,
                    "expires": expires, "expired": _is_expired(expires)})
    return out


def _is_expired(expires):
    try:
        return datetime.date.fromisoformat(expires) < datetime.date.today()
    except ValueError:
        return True  # 日期不可解析 = 视为过期（从严，只报不挡入表之外的差）


# ---------- 站机取数（C-1/C-7） ----------

def http_json(url, timeout, ctx):
    req = urllib.request.Request(url, headers={"User-Agent": f"{GATE_ID}-gate"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_family(base, family, timeout, ctx):
    return http_json(f"{base}/api/public/docs/{family}", timeout, ctx)


def fetch_content(base, family, slug, timeout, ctx):
    # slug 可能含子目录前缀与中文件名：逐段百分号编码（⛔ 裸中文进 URL）
    quoted = "/".join(urllib.parse.quote(seg) for seg in slug.split("/"))
    d = http_json(f"{base}/api/public/docs/{family}/{quoted}", timeout, ctx)
    return d.get("content")


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://47.76.42.139",
                    help="站机公开面基址（默认 https://47.76.42.139）")
    ap.add_argument("--rev", default="HEAD", help="仓内对比基准 rev（默认 HEAD）")
    ap.add_argument("--exceptions",
                    default="tools/ops/samesource_exceptions.yaml")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--verify-tls", action="store_true",
                    help="强制校验 TLS（默认关：站机证书自签，关校验只取公开只读面）")
    args = ap.parse_args()

    ctx = ssl.create_default_context() if args.verify_tls \
        else ssl._create_unverified_context()

    exceptions = load_exceptions(args.exceptions)
    exc_index = {(e["family"], e["name"]): e for e in exceptions}

    # C-2：仓侧（git 对象）
    try:
        fam_dirs, pub = load_repo_state(args.rev)
    except Exception as e:  # 仓侧不可判 ⟹ UNKNOWN
        print(f"UNKNOWN repo-side: {e}")
        return 2

    station_unreachable = False
    results = []

    for family, sub in fam_dirs.items():
        res = {"family": family, "station_count": None, "repo_count": len(pub.get(family, [])),
               "station_only": [], "repo_only": [], "content_drift": [],
               "count_mismatch": False, "excepted": [], "verdict": "PASS"}
        repo_names = set(pub.get(family, []))

        # C-1/C-7：站侧
        try:
            data = fetch_family(args.base_url, family, args.timeout, ctx)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            print(f"UNKNOWN station-side family={family}: {e}")
            station_unreachable = True
            res["verdict"] = "UNKNOWN"
            results.append(res)
            continue

        docs = data.get("documents") or []
        res["station_count"] = data.get("count")
        # C-5
        if data.get("count") != len(docs):
            res["count_mismatch"] = True

        station_names = []
        for d in docs:
            name = d.get("slug") or d.get("filename")
            if name:
                station_names.append(name)
        station_set = set(station_names)

        # C-3 / C-4（C-8 例外抵扣，过期例外照报）
        for n in sorted(station_set - repo_names):
            e = exc_index.get((family, n))
            if e and not e["expired"]:
                res["excepted"].append({"name": n, "reason": e["reason"],
                                        "expires": e["expires"]})
            else:
                res["station_only"].append(n)
        for n in sorted(repo_names - station_set):
            e = exc_index.get((family, n))
            if e and not e["expired"]:
                res["excepted"].append({"name": n, "reason": e["reason"],
                                        "expires": e["expires"]})
            else:
                res["repo_only"].append(n)
        expired = [f"{n}（表内已过期）" for (f, n), e in exc_index.items()
                   if f == family and e["expired"]
                   and n in (station_set ^ repo_names)]
        res["repo_only"].extend(expired)  # 过期例外 = 差，照报

        # C-6：抽样件级哈希（首/末各一，取 content 字段）
        if station_names:
            sample_idx = sorted({0, len(station_names) - 1})[:SAMPLE_N]
            for i in sample_idx:
                name = station_names[i]
                if name not in repo_names:
                    continue  # 站有仓无已由 C-3 报告，不再重复
                try:
                    content = fetch_content(args.base_url, family, name,
                                            args.timeout, ctx)
                except Exception as e:
                    print(f"UNKNOWN content family={family} name={name}: {e}")
                    station_unreachable = True
                    res["verdict"] = "UNKNOWN"
                    break
                if content is None:
                    continue
                st_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
                rp_sha = blob_sha16(args.rev, f"{DOCS_PREFIX}/{sub}/{name}")
                if rp_sha is None:
                    res["content_drift"].append(
                        {"name": name, "repo_blob": "MISSING",
                         "station_sha16": st_sha})
                elif st_sha.lower() != rp_sha.lower():
                    res["content_drift"].append(
                        {"name": name, "repo_sha16": rp_sha,
                         "station_sha16": st_sha})

        if res["verdict"] != "UNKNOWN":
            if res["station_only"] or res["repo_only"] or res["content_drift"] \
                    or res["count_mismatch"]:
                res["verdict"] = "DIFF"
            else:
                res["verdict"] = "PASS"
        results.append(res)

    # ---------- 输出：人读栏 ----------
    print("=" * 72)
    print(f"{GATE_ID} 同源派生校验 gate（只报差·只读）")
    print(f"base={args.base_url}  rev={args.rev}  "
          f"date={datetime.date.today().isoformat()}")
    print("=" * 72)
    for r in results:
        print(f"\n[{r['verdict']}] family={r['family']}  "
              f"站={r['station_count']} 仓={r['repo_count']}")
        if r["count_mismatch"]:
            print(f"  COUNT_MISMATCH: 站 count={r['station_count']} "
                  f"vs documents 实长（见 JSON 栏）")
        for n in r["station_only"]:
            print(f"  STATION_ONLY: {n}")
        for n in r["repo_only"]:
            print(f"  REPO_ONLY: {n}")
        for d in r["content_drift"]:
            print(f"  CONTENT_DRIFT: {d}")
        for e in r["excepted"]:
            print(f"  EXCEPTED: {e['name']}（{e['reason']}·{e['expires']}）")

    # ---------- 输出：机器可读栏 ----------
    print("\n--- JSON ---")
    print(json.dumps({"gate": GATE_ID, "base": args.base_url, "rev": args.rev,
                      "families": results}, ensure_ascii=False, indent=2))

    if station_unreachable:
        return 2
    if any(r["verdict"] == "DIFF" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
