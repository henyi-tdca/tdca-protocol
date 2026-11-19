#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TDCA 部署门禁 · 站点机侧校验（CI-GATE-001 §一交付物②）

用法: python3 deploy_gate.py <待发dist包路径>
退出码: 0=放行(GREEN/WARN) 1=拒部署  2=配置错（凭证缺失/不可读）

判据（定死，勿改）:
  1. deploy-receipt.json 的 sha256 与其 .sha256 旁注一致
  2. failed == 0
  3. dist_sha256 与实际待发包一致
  4. commit == atomgit main 头（40 位）
  5. ts 在 24h 内
skipped 如实记；skipped > 基线(1) 时降级 WARN（放行但回报点名）。
"""
import sys, os, json, hashlib, subprocess, datetime, urllib.request

RECEIPT = "/root/tdca/deploy/deploy-receipt.json"
RECEIPT_SHA = RECEIPT + ".sha256"
BASELINE_SKIPPED = 1
REMOTE = "https://atomgit.com/siweihanshuzhineng/siweihanshuzhineng-TDCA.git"

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fail(msg):
    print(f"GATE=RED reason={msg}")
    sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("usage: deploy_gate.py <待发dist包路径>"); sys.exit(2)
    dist = sys.argv[1]
    if not os.path.exists(RECEIPT):
        fail(f"凭证缺失: {RECEIPT}")
    if not os.path.exists(RECEIPT_SHA):
        fail(f"凭证旁注缺失: {RECEIPT_SHA}")
    noted = open(RECEIPT_SHA, encoding="utf-8").read().split()[0].strip().lower()
    actual = sha256_of(RECEIPT)
    if noted != actual:
        fail(f"凭证旁注不符: noted={noted[:16]} actual={actual[:16]}")
    try:
        r = json.load(open(RECEIPT, encoding="utf-8"))
    except Exception as e:
        fail(f"凭证非合法JSON: {e}")
    for k in ("commit", "dist_sha256", "passed", "failed", "skipped", "ts", "ci_host"):
        if k not in r:
            fail(f"凭证缺字段: {k}")
    if int(r["failed"]) != 0:
        fail(f"failed={r['failed']} != 0")
    if not os.path.exists(dist):
        fail(f"待发包不存在: {dist}")
    if sha256_of(dist) != str(r["dist_sha256"]).lower():
        fail("dist_sha256 与实际待发包不一致")
    head = subprocess.run(
        ["git", "ls-remote", REMOTE, "refs/heads/main"],
        capture_output=True, text=True, timeout=60).stdout.split()[0]
    if str(r["commit"]) != head:
        fail(f"commit={r['commit'][:12]} != main头={head[:12]}")
    try:
        ts = datetime.datetime.fromisoformat(str(r["ts"]))
    except Exception:
        fail(f"ts 非 ISO 格式: {r['ts']}")
    age = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))) - ts.astimezone()
    if age > datetime.timedelta(hours=24) or age < -datetime.timedelta(minutes=5):
        fail(f"ts 超 24h 窗口: age={age}")
    level = "GREEN"
    if int(r["skipped"]) > BASELINE_SKIPPED:
        level = "WARN"
    print(f"GATE={level} passed={r['passed']} failed={r['failed']} "
          f"skipped={r['skipped']}(baseline<={BASELINE_SKIPPED}) commit={head[:12]} ci_host={r['ci_host']}")
    sys.exit(0)

if __name__ == "__main__":
    main()
