# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M4 | 目标函数: 活体部署验证（验收②重启持久化 + 验收③五页面回归）
# 约束矩阵: 起真实 uvicorn 进程（非 TestClient）；写→杀→重启→读回；结束必清理进程
# 审计轨迹: NCA-KIMIWEB-011/012
# =============================================================================
"""M4 活体验证：两轮服务器生命周期（写 → 重启 → 读回）+ 五页面端点回归。
在 gateway/ 目录下运行：python scripts/m4_live_check.py"""
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx

_ROOT = Path(__file__).resolve().parents[1]
_PORT = 8123
_BASE = f"http://127.0.0.1:{_PORT}"

# 五页面数据源端点（/studio 无后端依赖，见 F3 签批件；此处覆盖有后端的数据源端点）
_READS = [
    ("/", "/api/v1/system/overview"),
    ("/tax", "/api/v1/tax/mou/AGENT-GENIE"),
    ("/sandbox", "/api/v1/sandbox/sea-status"),
    ("/notifier", "/api/v1/notifier/mrcr-status"),
    ("/academy", "/api/v1/knowledge/terms"),
    ("/audit", "/api/v1/audit/ledger-public"),
    ("/attestation", "/api/v1/attestation/queue"),
    ("/cluster", "/api/v1/eios/cluster-status"),
]

_ENV = dict(os.environ, TDCA_GATEWAY_AUTH="1",
            TDCA_GATEWAY_TOKEN="m4-live-check", PYTHONUTF8="1")
_CRT = {"Authorization": "TDCA-CRT-m4-live-check"}   # 静态降级令牌（不触碰真实口令）


def _start() -> subprocess.Popen:
    p = subprocess.Popen(
        [sys.executable, "scripts/serve.py", "--port", str(_PORT)],
        cwd=str(_ROOT), env=_ENV,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            if httpx.get(f"{_BASE}/api/v1/system/overview", timeout=2).status_code == 200:
                return p
        except Exception:
            time.sleep(0.5)
    p.kill()
    raise RuntimeError("服务器 60 次探测内未就绪")


def _stop(p: subprocess.Popen):
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()


def main() -> int:
    db = _ROOT / "tdca.db"
    before = sqlite3.connect(str(db)).execute(
        "SELECT COUNT(*) FROM sandbox_applications").fetchone()[0]
    ok = True
    p = _start()
    try:
        # 第一轮：读回归 + 一次写（鉴权启用态，CRT 降级令牌）
        for page, ep in _READS:
            r = httpx.get(f"{_BASE}{ep}", timeout=5)
            good = r.status_code == 200
            ok &= good
            print(f"[轮1] {page:<14} {ep:<38} {r.status_code} {'PASS' if good else 'FAIL'}")
        # 轮1 写入载荷带时间戳：apply 主键 = sha256(sponsor_did+scene_ids)，
        # 唯一载荷保证每轮插入新行，「行数增长」断言在重复执行时仍成立
        payload = {"sponsor_did": f"did:tdca:m4-live-check:{time.time()}"}
        r = httpx.post(f"{_BASE}/api/v1/sandbox/apply", json=payload, headers=_CRT, timeout=10)
        print(f"[轮1] 写 sandbox/apply（带令牌）      {r.status_code} "
              f"{'PASS' if r.status_code == 200 else 'FAIL'}")
        ok &= r.status_code == 200
        sbx = r.json()["data"]["sandbox_id"] if r.status_code == 200 else None
        r = httpx.post(f"{_BASE}/api/v1/sandbox/apply", json={}, timeout=10)
        print(f"[轮1] 写 sandbox/apply（无令牌）      {r.status_code} "
              f"{'PASS' if r.status_code == 401 else 'FAIL'}（fail-closed）")
        ok &= r.status_code == 401
    finally:
        _stop(p)
    print("[重启] 服务器已停止，重新启动……")
    p = _start()
    try:
        # 第二轮：读回——验收② 重启后数据不丢
        if sbx:
            hit = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM sandbox_applications WHERE apply_id=?",
                (sbx,)).fetchone()[0]
            print(f"[轮2] 重启后读回 sandbox_applications[{sbx}] 存在={bool(hit)} "
                  f"{'PASS' if hit else 'FAIL'}（持久化）")
            ok &= bool(hit)
        after = sqlite3.connect(str(db)).execute(
            "SELECT COUNT(*) FROM sandbox_applications").fetchone()[0]
        print(f"[轮2] sandbox_applications 行数 {before} → {after}（重启后保留）")
        ok &= after > before
        for page, ep in _READS[:3]:
            r = httpx.get(f"{_BASE}{ep}", timeout=5)
            ok &= r.status_code == 200
            print(f"[轮2] {page:<14} {ep:<38} {r.status_code}")
    finally:
        _stop(p)
    print("m4 live check:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
