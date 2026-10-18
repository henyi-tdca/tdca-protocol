# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-4 真实 E2E 冒烟——效用精灵深度对接（GE-IF-001 实时回调 + 001b 快路径）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 / SV-8
# 先验分布:     交付确认书 M3-4 + genie_callback.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-4 真实 E2E 冒烟（GE-IF-001/001b：inproc 效用精灵桥接，ID24 只读）。

流程: GE-IF-001 正和实时回调 → GE-IF-001b 快路径 → NSFL 熔断 → SV-8 延迟。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.genie_callback import GenieCallback, GenieLinkError  # noqa: E402

SID = "did:tdca:sandbox:e4" + "0" * 29


def _participants(n: int = 3) -> list:
    return [{"agent_id": f"agent-{i}", "capability": 1.0} for i in range(n)]


def _obj_fns(n: int = 3, factor: float = 1.2) -> list:
    """目标函数公式描述（REST 可序列化）。"""
    return [{"type": "linear", "factor": factor} for _ in range(n)]


def main() -> int:
    adapter = GenieCallback()

    # [1] GE-IF-001 正和实时回调（solver 完整求解）
    r = adapter.evaluate(SID, _participants(), _obj_fns(),
                         [2.0] * 3, time_budget=3.0)
    assert r["contract"] == "GE-IF-001" and r["is_positive_sum"] is True, r
    assert r["fuse"] is False and r["nca_refs"]["sbx"].startswith("NCA-")
    print(f"[1] GE-IF-001 实时回调: delta={r['delta']} fuse={r['fuse']} NCA={r['nca_refs']['sbx']}")

    # [2] GE-IF-001b 快路径（S_synergy > 0）
    r2 = adapter.check(SID, coalition_utility=300.0, independent_utilities=[80.0, 90.0, 50.0])
    assert r2["contract"] == "GE-IF-001b" and r2["is_positive_sum"] is True, r2
    assert r2["delta"] == 80.0
    print(f"[2] GE-IF-001b 快路径: delta={r2['delta']} index={r2['positive_sum_index']}")

    # [3] GE-IF-001 NSFL 触碰 → fuse（ID86 熔断语义）
    r3 = adapter.evaluate(SID, _participants(), _obj_fns(),
                          [2.0] * 3, nsfl_boundaries=["autonomous_repair"], time_budget=3.0)
    assert r3["touched_nsfl"] is True and r3["fuse"] is True, r3
    print(f"[3] GE-IF-001 NSFL 熔断: touched_nsfl={r3['touched_nsfl']} fuse={r3['fuse']}")

    # [4] 非正和 → fail-closed（效用精灵 validate 熔断）
    try:
        adapter.evaluate(SID, _participants(), _obj_fns(factor=0.0),
                         [100.0] * 3, time_budget=1.0)
        raise AssertionError("非正和不应通过")
    except GenieLinkError:
        print("[4] GE-IF-001 非正和 fail-closed: GenieLinkError（效用精灵 validate 熔断）")

    # [5] SV-8 延迟 + NCA 链
    assert r["latency_ms"] < 1000, r
    from app.nca_logger import verify_chain
    v = verify_chain()
    assert v["valid"] is True, v
    print(f"[5] SV-8 延迟 {r['latency_ms']}ms < 1s · NCA 链 valid={v['valid']} checked={v['checked']}")

    print("\nM3-4 GE-IF E2E all passed (5/5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
