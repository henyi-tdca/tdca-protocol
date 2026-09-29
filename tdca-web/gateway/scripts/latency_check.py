# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M2 | 目标函数: 关键查询延迟验收（<200ms）
# 约束矩阵: 验收③——七条关键 GET 端点对演示库（gateway/tdca.db）实测延迟
# 先验分布: SQLite 本地文件库，行量级 <100，预期远低于 200ms
# 审计轨迹: NCA-KIMIWEB-006/007
# =============================================================================
"""M2 验收③：关键查询延迟实测。在 gateway/ 目录下运行：python scripts/latency_check.py"""
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_WS = _ROOT.parent
for _sub in ("tdca-d2-union", "tdca-cscp", "tdca-workbuddy",
             "tdca-translator-market", "tdca-cross-scene", "tdca-eios"):
    _p = str(_WS / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

_ENDPOINTS = [
    "/api/v1/system/overview",
    "/api/v1/tax/mou/AGENT-GENIE",
    "/api/v1/sandbox/sea-status",
    "/api/v1/notifier/mrcr-status",
    "/api/v1/eios/cluster-status",
    "/api/v1/audit/ledger-public",
    "/api/v1/attestation/queue",
]
_THRESHOLD_MS = 200.0
_WARMUP = 2       # 预热（惰性引擎绑定 + SQLite 连接）
_RUNS = 5         # 计时轮次取最大（最保守口径）


def main() -> int:
    client = TestClient(app)
    ok = True
    print(f"{'端点':<38} {'max(ms)':>9}  阈值  结论")
    for ep in _ENDPOINTS:
        for _ in range(_WARMUP):
            client.get(ep)
        worst = 0.0
        for _ in range(_RUNS):
            t0 = time.perf_counter()
            r = client.get(ep)
            worst = max(worst, (time.perf_counter() - t0) * 1000)
            assert r.status_code == 200, f"{ep} → {r.status_code}"
        passed = worst < _THRESHOLD_MS
        ok = ok and passed
        print(f"{ep:<38} {worst:>9.2f}  <200  {'PASS' if passed else 'FAIL'}")
    print("latency check:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
