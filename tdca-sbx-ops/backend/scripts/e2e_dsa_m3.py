# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-6 真实 E2E 冒烟——DSA 状态机扩展（SBX-SUSPENDED/BANNED，SV-9）
# 约束矩阵:     FC-SBX-OPS-001 SV-9 + DSA-001（回退三档）
# 先验分布:     会话框规范-S0-M3-6-初始化声明-20260810.md + dsa_extension.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-6 真实 E2E 冒烟（DSA 扩展字段先行：SV-9 熔断落地 + 回退三档）。

流程: MINOR 熔断→SUSPENDED（SV-9）→resume→MODERATE 需人类裁决→SEVERE→BANNED 不可逆。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.dsa_extension import (  # noqa: E402
    DsaExtension, BREAK_LEVEL_MINOR, BREAK_LEVEL_MODERATE, BREAK_LEVEL_SEVERE,
    DSA_ACTIVE, DSA_SUSPENDED, DSA_BANNED,
)


def _mk_sandbox() -> str:
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="e2e", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={})
    st.save_sandbox(sb)
    return sid


def main() -> int:
    adapter = DsaExtension()

    # [1] MINOR 熔断 → SBX-SUSPENDED（SV-9 100ms 达标）
    sid = _mk_sandbox()
    r = adapter.suspend(sid, "轻微越界", BREAK_LEVEL_MINOR)
    assert r["dsa_status"] == DSA_SUSPENDED, r
    assert r["sv9_compliant"] is True, r
    print(f"[1] MINOR 熔断: dsa_status={r['dsa_status']} sv9={r['sv9_compliant']} "
          f"latency={r['latency_ms']}ms NCA={r['nca_refs']['sbx']}")

    # [2] MINOR resume → SBX-ACTIVE（限期重整后）
    r2 = adapter.resume(sid)
    assert r2["dsa_status"] == DSA_ACTIVE, r2
    print(f"[2] MINOR resume: dsa_status={r2['dsa_status']}（限期重整后恢复）")

    # [3] MODERATE 恢复须人类裁决
    sid2 = _mk_sandbox()
    adapter.suspend(sid2, "中度越界", BREAK_LEVEL_MODERATE)
    try:
        adapter.resume(sid2)
        raise AssertionError("MODERATE 无人类裁决不应恢复")
    except ValueError:
        print("[3] MODERATE 守卫: 无人类裁决拒绝恢复（DSA-001 §3.4）")
    r3 = adapter.resume(sid2, human_approval="did:tdca:HUMAN-FOUNDER-001")
    assert r3["dsa_status"] == DSA_ACTIVE
    print(f"[3] MODERATE resume（人类裁决）: dsa_status={r3['dsa_status']}")

    # [4] SEVERE → SBX-BANNED 永久休眠（不可逆，I-5 人类签批）
    sid3 = _mk_sandbox()
    r4 = adapter.ban(sid3, "触及法律负空间", human_signatory="did:tdca:HUMAN-FOUNDER-001")
    assert r4["dsa_status"] == DSA_BANNED and r4["break_level"] == BREAK_LEVEL_SEVERE, r4
    print(f"[4] SEVERE 永久休眠: dsa_status={r4['dsa_status']} break_level={r4['break_level']}")

    # [5] BANNED 不可逆 + 状态查询 + NCA 链
    try:
        adapter.resume(sid3)
        raise AssertionError("BANNED 不应可恢复")
    except ValueError:
        print("[5] BANNED 不可逆守卫: 恢复拒绝（永久休眠）")
    st = adapter.status(sid3)
    assert st["dsa_status"] == DSA_BANNED
    from app.nca_logger import verify_chain
    v = verify_chain()
    assert v["valid"] is True, v
    print(f"[5] 状态确认: dsa_status={st['dsa_status']} · NCA 链 valid={v['valid']} checked={v['checked']}")

    print("\nM3-6 DSA E2E all passed (5/5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
