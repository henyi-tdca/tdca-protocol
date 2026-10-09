# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-2 真实 E2E 冒烟——沙盒生命周期 ↔ FlowEngine（FE-IF-001/002）
# 约束矩阵:     FC-SBX-OPS-001 SV-1（α>1.2）/ SV-8
# 先验分布:     交付确认书 M3-2 + flow_adapter.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-2 真实 E2E 冒烟（FE-IF-001/002 全链路：inproc FlowEngine 桥接）。

流程: 创建沙盒 → FE-IF-001 hook → 阶段同步 P0→P1→P2→P3 → FE-IF-002 α>1.2 advance → P4。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.flow_adapter import FlowAdapter  # noqa: E402
from app.models import Sandbox  # noqa: E402

SID = "did:tdca:sandbox:e2e" + "0" * 28  # 合法格式沙盒 ID


def _sbx(alpha: float = 1.25, delta: float = 10.0, fuse: bool = False) -> Sandbox:
    """构造含真实评估记录的沙盒实例（E2E：模拟 Sandbox 数据形态）。"""
    sb = Sandbox(sandbox_id=SID, name="e2e", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={})
    sb.activation_logs = [{"coefficient": alpha, "status": "财政自给性达成"}]
    sb.positive_sum_logs = [{"delta": delta, "fuse": fuse}]
    return sb


def main() -> int:
    adapter = FlowAdapter(mode="inproc")

    # [1] FE-IF-001 hook（P0 启动）
    r = adapter.hook_sandbox(SID, {"type": "sbx_lifecycle"})
    assert r["contract"] == "FE-IF-001" and r["phase"] == "P0", r
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # SV-10 回引
    print(f"[1] FE-IF-001 hook: flow_id={r['flow_id']} phase=P0 NCA={r['nca_refs']['sbx']}")

    # [2] FE-IF-001 状态查询
    st = adapter.status(SID)
    assert st["phase"] == "P0" and st["phase_seq"] == ["P0"], st
    print(f"[2] FE-IF-001 status: phase={st['phase']} seq={st['phase_seq']}")

    # [3] FE-IF-001 阶段同步：沙盒 P0 → FlowEngine P1（映射推进）
    r = adapter.sync_phase(SID, "P0")
    assert r["phase"] == "P1", r
    print("[3] FE-IF-001 sync: 沙盒 P0 → FlowEngine P1")

    # [4] FE-IF-001 阶段同步：沙盒 P1 → FlowEngine P3（逐段穿越）
    r = adapter.sync_phase(SID, "P1")
    assert r["phase"] == "P3", r
    print(f"[4] FE-IF-001 sync: 沙盒 P1 → FlowEngine {r['phase']}")

    # [5] FE-IF-002 α≤1.2 拒绝（SV-1 必要非充分）
    try:
        adapter.activation_signal(SID, _sbx(alpha=1.2))
        raise AssertionError("α=1.2 不应通过（SV-1）")
    except ValueError:
        print("[5] FE-IF-002 SV-1 守卫: α=1.2 拒绝（严格大于）")

    # [6] FE-IF-002 消费真实记录（α>1.2 + 正和过）→ P3→P4
    r = adapter.activation_signal(SID, _sbx(alpha=1.25, delta=10.0))
    assert r["contract"] == "FE-IF-002" and r["alpha"] == 1.25, r
    assert r["phase"] == "P4", r  # P3->P4 穿越成功（sandbox_pass 来自真实评估）
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    print(f"[6] FE-IF-002 advance: α=1.25（真实记录）→ phase={r['phase']}")

    # [7] 台账 + 状态确认
    hooks = adapter.list_hooks()
    assert len(hooks) == 1 and hooks[0]["sandbox_id"] == SID
    final = adapter.status(SID)
    assert final["phase_seq"] == ["P0", "P1", "P2", "P3", "P4"], final
    print(f"[7] 台账: hooks={len(hooks)} 最终 seq={final['phase_seq']}")

    print("\nM3-2 FE-IF E2E all passed (7/7)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
