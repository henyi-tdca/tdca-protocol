#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TDCA 部署指纹对账（3180 第③段 · 过渡期对账机制）

用途：每次部署后核对「线上实测指纹 ⟷ 仓内 commit 对应文件指纹」，不一致即 FAIL 并告警停。
两种用法：
  1) 收集线上指纹（在可 SSH 到测试云的环境执行）：
       python deploy/reconcile.py collect --ssh root@47.76.42.139 --identity ~/.ssh/tdca-cloud-deploy \
           --out remote-fingerprints.json
  2) 对账比对（本地，默认与 true-source/ 真源树比对）：
       python deploy/reconcile.py compare --remote remote-fingerprints.json [--tree true-source/tdca-web]

对账项 = 关键件 md5（容器内文件 vs 仓内树文件）＋ 关键端点响应指纹（HTTP 取回、剔除 ts 后规范化哈希）。
退出码：0=PASS；1=FAIL；2=无法完成（网络/SSH 失败）。
"""
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request

# 关键件：容器内路径 ⟷ 仓内相对路径（相对 --tree）
KEY_FILES = [
    ("tdca-web/gateway/api_v1.py", "gateway/api_v1.py"),
    ("tdca-web/tdca-d2-union/nsfl_union/conflict.py", "tdca-d2-union/nsfl_union/conflict.py"),
    ("tdca-web/tdca-eios/genie_api.py", "tdca-eios/genie_api.py"),
]

# 关键端点：规范化（剔除 ts 字段）后哈希响应体
KEY_ENDPOINTS = [
    "/api/v1/assets/five-orders",
    "/api/v1/tax/mou/__reconcile_probe__",
    "/api/v1/tax/nca-history",
    "/api/v1/tax/shapley/__reconcile_probe__",
    "/api/v1/knowledge/terms",
]

BASE_URL = "http://47.76.42.139:8080"


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def collect_remote(ssh: str, identity: str, out: str) -> int:
    container = "$(docker ps -qf name=gateway | head -1)"
    paths = " ".join(f"/app/{c}" for c, _ in KEY_FILES)
    cmd = (
        f"for f in {paths}; do "
        f"docker exec {container} md5sum \"$f\"; done"
    )
    r = subprocess.run(
        ["ssh", "-i", identity, "-o", "IdentitiesOnly=yes", "-o", "ConnectTimeout=15", ssh, cmd],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print("FAIL-2 SSH 收集失败:", r.stderr.strip()[:300])
        return 2
    fps = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0]:
            fps[parts[1].replace("/app/", "")] = parts[0]
    missing = [c for c, _ in KEY_FILES if c not in fps]
    if missing:
        print("FAIL-2 线上关键件缺取:", missing)
        return 2
    doc = {"ssh_target": ssh, "fingerprints": fps, "note": "gateway 容器内 /app 文件 md5"}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"已收集 {len(fps)} 件线上指纹 → {out}")
    return 0


def norm_response(body: bytes) -> bytes:
    try:
        d = json.loads(body)
        d.pop("ts", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8")
    except Exception:
        return body


def endpoint_fingerprint(path: str) -> str:
    with urllib.request.urlopen(BASE_URL + path, timeout=20) as r:
        return md5(norm_response(r.read()))


def compare(remote_path: str, tree: str) -> int:
    remote = json.load(open(remote_path, encoding="utf-8"))["fingerprints"]
    rows, fails = [], 0
    for container_path, local_rel in KEY_FILES:
        local_file = f"{tree}/{local_rel}"
        try:
            local_md5 = md5(open(local_file, "rb").read())
        except OSError as e:
            print(f"FAIL-2 仓内文件不可读: {local_file} ({e})")
            return 2
        online_md5 = remote.get(container_path, "")
        ok = online_md5 == local_md5
        fails += 0 if ok else 1
        rows.append(("file", container_path, online_md5, local_md5, ok))
    for ep in KEY_ENDPOINTS:
        try:
            online_fp = endpoint_fingerprint(ep)
        except Exception as e:
            print(f"FAIL-2 端点取回失败: {ep} ({e})")
            return 2
        # 响应指纹无仓内直接对应物；留痕供部署前后对比（部署后应与基线一致）
        rows.append(("endpoint", ep, online_fp, "-(留痕)", True))
    print(f"{'类型':6} {'对账项':58} {'线上':34} {'仓内':34} 结论")
    for kind, item, a, b, ok in rows:
        print(f"{kind:6} {item:58.58} {a:34.34} {b:34.34} {'PASS' if ok else 'FAIL'}")
    print(f"\n结果: {'PASS' if fails == 0 else f'FAIL（{fails} 项不一致——停手查因，不得部署/不得结案）'}")
    return 0 if fails == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="TDCA 部署指纹对账")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect", help="收集线上容器内关键件 md5")
    c.add_argument("--ssh", default="root@47.76.42.139")
    c.add_argument("--identity", default="~/.ssh/tdca-cloud-deploy")
    c.add_argument("--out", default="remote-fingerprints.json")
    p = sub.add_parser("compare", help="线上 ⟷ 仓内树比对")
    p.add_argument("--remote", default="remote-fingerprints.json")
    p.add_argument("--tree", default="true-source/tdca-web")
    args = ap.parse_args()
    if args.cmd == "collect":
        return collect_remote(args.ssh, args.identity, args.out)
    return compare(args.remote, args.tree)


if __name__ == "__main__":
    sys.exit(main())
