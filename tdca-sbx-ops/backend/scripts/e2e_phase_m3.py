# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-3 真实 E2E 冒烟——激活系数达标→PhaseMachine 阶段推进（PM-IF-001）
# 约束矩阵:     FC-SBX-OPS-001 SV-1（α>1.2 必要非充分）/ SV-8
# 先验分布:     交付确认书 M3-3 + phase_adapter.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-3 真实 E2E 冒烟（PM-IF-001：inproc PhaseMachine 桥接）。

流程: α≤1.2 拒绝（SV-1）→ α>1.2 P3→P4 穿越 → 条件查询 → 状态集合。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.phase_adapter import PhaseAdapter  # noqa: E402

SID = "did:tdca:sandbox:e3" + "0" * 29


def _sbx(alpha: float, delta: float = 10.0, fuse: bool = False):
    class S:
        pass
    s = S()
    s.activation_logs = [{"coefficient": alpha, "status": "财政自给性达成"}]
    s.positive_sum_logs = [{"delta": delta, "fuse": fuse}]
    return s


def main() -> int:
    adapter = PhaseAdapter()

    # [1] PM-IF-001 α≤1.2 拒绝（SV-1 必要非充分）
    try:
        adapter.advance_signal(SID, _sbx(alpha=1.2), current_phase="P3")
        raise AssertionError("α=1.2 不应通过（SV-1）")
    except ValueError:
        print("[1] PM-IF-001 SV-1 守卫: α=1.2 拒绝（必要非充分）")

    # [2] PM-IF-001 α>1.2 + 正和过 → P3→P4 穿越
    r = adapter.advance_signal(SID, _sbx(alpha=1.25, delta=10.0), current_phase="P3")
    assert r["contract"] == "PM-IF-001" and r["alpha"] == 1.25, r
    assert r["phase"] == "P4" and r["fuse"] is None, r
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    print(f"[2] PM-IF-001 advance: α=1.25 P3→P4 穿越成功 NCA={r['nca_refs']['sbx']}")

    # [3] PM-IF-001 正和 fuse 拒绝
    try:
        adapter.advance_signal(SID, _sbx(alpha=1.4, fuse=True), current_phase="P3")
        raise AssertionError("正和 fuse 不应通过")
    except ValueError:
        print("[3] PM-IF-001 正和守卫: fuse 拒绝推进（消费真实 positive_sum_logs）")

    # [4] PM-IF-001b 穿越条件查询
    c = adapter.conditions("P3", "P4")
    assert "sandbox_pass" in c["conditions"] and "positive_sum" in c["conditions"], c
    print(f"[4] PM-IF-001b conditions(P3→P4): {c['conditions']}")

    # [5] 状态集合
    states = adapter.state_table()
    assert "P0" in states and "P8" in states and "COMPLETED" in states
    print(f"[5] 状态集合: {len(states)} 状态（9 Phase + 终态）")

    print("\nM3-3 PM-IF E2E all passed (5/5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
