# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-1 真实 NS-OPS 对接 E2E 冒烟（NS-IF-001~003 全链路）
# 约束矩阵:     FC-SBX-OPS-001 SV-8（<1s）/ SV-10（双向存证）
# 先验分布:     交付报告 M3-1 + nsops_adapter.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-1 真实 NS-OPS 对接 E2E 冒烟（NS-IF-001~003）。

前置: NS-OPS 8123 服务在线（`uvicorn app.main:app --port 8123`）。
用法: 直接运行本脚本（进程内适配层真实 HTTP 调用 NS-OPS，不依赖 SBX-OPS 8000 起服务）。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.nsops_adapter import NSOpsAdapter  # noqa: E402

ADAPTER = NSOpsAdapter()


def main() -> int:
    # [1] NS-IF-001 约束查询（真实 NS-OPS 8123）
    r = ADAPTER.query_constraints()
    assert r["contract"] == "NS-IF-001" and r["count"] >= 1, r
    assert r["latency_ms"] < 1000, r  # SV-8
    layers = {c["layer"] for c in r["constraints"]}
    assert "institutional" in layers, layers  # 制度层（L0）约束存在
    print(f"[1] NS-IF-001 约束查询: count={r['count']} latency={r['latency_ms']}ms NCA={r['nca_refs']['sbx']}")

    # [2] NS-IF-002 边界校验：合规行为 allow（无熔断）
    r2 = ADAPTER.check_and_fuse(actor="agent-x", action="提交六要素声明并合规协作", scene="community")
    assert r2["contract"] == "NS-IF-002" and r2["decision"] == "allow", r2
    assert r2["fuse_triggered"] is False
    print(f"[2] NS-IF-002 合规判定: decision={r2['decision']} latency={r2['latency_ms']}ms")

    # [3] NS-IF-002 触碰法律负空间 → BLOCK + BV-1 熔断（ID86 绝对熔断）
    r3 = ADAPTER.check_and_fuse(actor="agent-x", action="实施违反 L0 法律底线的行为", scene="community")
    assert r3["decision"] == "block" and r3["fuse_triggered"] is True, r3
    assert r3["nca_refs"]["nsops"], "NS-OPS 侧 NCA 回引缺失（SV-10）"
    print(f"[3] NS-IF-002 法律负空间熔断: decision={r3['decision']} fuse={r3['fuse_triggered']} "
          f"nsops_nca={r3['nca_refs']['nsops']}")

    # [4] NS-IF-003 合规证明：触碰后不可合规（预检 blocked）
    r4 = ADAPTER.compliance_cert(actor="agent-x", action="实施违反 L0 法律底线的行为")
    assert r4["contract"] == "NS-IF-003" and r4["compliant"] is False, r4
    assert r4["precheck"]["blocked"] is True
    print(f"[4] NS-IF-003 违规不可合规: compliant={r4['compliant']} fuse_count={r4['fuse_count']}")

    # [5] NCA 链完整性（SV-7，本会话存证）
    from app.nca_logger import verify_chain
    v = verify_chain()
    assert v["valid"] is True, v
    print(f"[5] NCA 链校验: valid={v['valid']} checked={v['checked']}")

    print("\nM3-1 NS-OPS 真实对接 E2E all passed (5/5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
