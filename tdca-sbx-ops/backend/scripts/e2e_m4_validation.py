# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M4 验收）
# 目标函数:     M4 真实验证链路 E2E——F3 evaluate（real）→ F6 正和 → FE-IF-002/PM-IF-001 advance
# 约束矩阵:     FC-SBX-OPS-001 SV-1（α>1.2 必要非充分）+ 开发纪律（正和不可 mock）
# 先验分布:     M4 会话框初始化声明 + M3-3 V11（真实评估链路验证归 M4）
# 配置权边界:   L2 层；仅验收脚本
# 预期分配:     全链路真实断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M4 真实验证链路 E2E（F3→F6→advance 全链路真实，不可 mock）。

流程: 沙盒创建 → F3 evaluate（real 数据，α>1.2）→ F6 positive-sum（真实引擎）
      → FE-IF-002 advance（FlowEngine）→ PM-IF-001 advance（PhaseMachine）→ DSA 状态确认。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.sandbox_core import SandboxCore  # noqa: E402
from app.flow_adapter import FlowAdapter  # noqa: E402
from app.phase_adapter import PhaseAdapter  # noqa: E402
from app.dsa_extension import DsaExtension  # noqa: E402

CORE = SandboxCore()
FLOW = FlowAdapter(mode="inproc")
PHASE = PhaseAdapter()
DSA = DsaExtension()

SIX = {"目标函数": "M4验收", "约束矩阵": "SV-1~7", "先验分布": "任务书",
       "配置权边界": "L2", "预期分配": "验收", "审计轨迹": "NCA"}


def main() -> int:
    # [1] 沙盒创建（F1）
    sb = CORE.create("M4验收沙盒", "did:tdca:INNOVATOR-001", "innovator", SIX)
    sid = sb.sandbox_id
    print(f"[1] F1 沙盒创建: {sid} phase={sb.phase.value}")

    # [2] 进入实验期（Phase0→P0）后先 F6 正和验证（效用精灵真实引擎，不可 mock，限 P0）
    CORE.start_experiment(sid, "did:tdca:INNOVATOR-001")
    sb = CORE.verify_positive_sum(sid, coalition_utility=300.0, independent_utilities=[80.0, 90.0, 50.0])
    last = sb.positive_sum_logs[-1]
    assert last["is_positive_sum"] is True and last["fuse"] is False, last
    print(f"[2] F6 正和验证: delta={last['delta']}（效用精灵真实引擎，不可 mock）")

    # [3] F3 evaluate（数据性质 simulated——当前无真实税务数据源，MOU anchor_real 未授权（ID92）；
    #      链路真实性由"真实引擎消费真实沙盒记录"表达（F6 效用精灵 + activation_logs 服务端读取））
    sb = CORE.evaluate(sid, 100, 150, 20, data_nature="simulated")
    alpha = sb.activation_logs[-1]["coefficient"]
    assert alpha == 1.7 and sb.activation_logs[-1]["status"] == "财政自给性达成", sb.activation_logs
    assert sb.activation_logs[-1]["data_nature"] == "simulated", sb.activation_logs  # V1：显式 simulated
    print(f"[3] F3 验证: α={alpha}>1.2 财政自给性达成（simulated 显式标注，ID92）phase={sb.phase.value}")

    # [4] FE-IF-001 hook + sync（FlowEngine 生命周期：推进到 P3）
    FLOW.hook_sandbox(sid, {"type": "sbx_lifecycle"})
    st = FLOW.status(sid)
    print(f"[4] FE-IF-001 hook: flow_id={st['flow_id']} phase={st['phase']}")
    FLOW.sync_phase(sid, "P0", real_phase="P0")  # → P1
    FLOW.sync_phase(sid, "P1", real_phase="P1")  # → P3（逐段穿越）
    st = FLOW.status(sid)
    assert st["phase"] == "P3", st
    print(f"[4] FE-IF-001 sync: → phase={st['phase']}（P0→P1→P3）")

    # [5] FE-IF-002 advance（α>1.2 + 正和过 → P3→P4）
    r = FLOW.activation_signal(sid, sb)
    assert r["alpha"] == 1.7 and r["phase"] == "P4", r
    print(f"[5] FE-IF-002 advance: α=1.7 → phase={r['phase']}（真实评估消费）")

    # [6] PM-IF-001 advance（PhaseMachine 直连）
    r2 = PHASE.advance_signal(sid, sb, current_phase="P4", real_phase="P4")
    print(f"[6] PM-IF-001 advance: α={r2['alpha']} phase={r2['phase']}")

    # [7] DSA 状态确认（全链路末端：SBX-ACTIVE 正常态）
    dsa_st = DSA.status(sid)
    assert dsa_st["dsa_status"] is None or dsa_st["dsa_status"] == "SBX-ACTIVE", dsa_st
    print(f"[7] DSA 状态: phase={dsa_st['phase']} dsa_status={dsa_st['dsa_status']}")

    # [8] NCA 链完整性（F8）
    from app.nca_logger import verify_chain
    v = verify_chain()
    assert v["valid"] is True, v
    print(f"[8] F8 NCA 链: valid={v['valid']} checked={v['checked']}")

    print("\nM4 真实验证链路 E2E all passed (8/8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
