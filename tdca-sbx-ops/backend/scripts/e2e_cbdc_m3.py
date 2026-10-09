# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-5 真实 E2E 冒烟——数字人民币 MOU 锚定（CB-IF-001 模拟过渡）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7 / SV-8 + ID79/ID92
# 先验分布:     交付确认书 M3-5 + cbdc_anchor.py
# 配置权边界:   L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""M3-5 真实 E2E 冒烟（CB-IF-001：inproc MOU 锚定管线桥接，tdca-fos 只读）。

流程: 负税收拒绝（NSFL）→ MOU 锚定（simulated 显式标记 + ID79）→ 状态查询 → NCA 链。
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from app.cbdc_anchor import CbdcAnchor  # noqa: E402

SID = "did:tdca:sandbox:e5" + "0" * 29


def main() -> int:
    adapter = CbdcAnchor()

    # [1] CB-IF-001 负税收拒绝（NSFL 无数据/负值禁止伪造 MOU）
    try:
        adapter.anchor(SID, tax_in=-1, tax_out=50)
        raise AssertionError("负税收不应通过（NSFL）")
    except ValueError:
        print("[1] CB-IF-001 NSFL 守卫: 负税收拒绝（禁止伪造 MOU）")

    # [2] CB-IF-001 MOU 锚定（simulated 显式标记 + ID79 MOU=和）
    r = adapter.anchor(SID, tax_in=120, tax_out=80)
    assert r["contract"] == "CB-IF-001" and r["mou"] == 200, r  # ID79
    assert r["verified"] is True and r["simulated"] is True, r  # ID92
    assert r["source"] == "SIMULATED-TAX-AUTHORITY"
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    print(f"[2] CB-IF-001 锚定: mou=200 verified={r['verified']} simulated={r['simulated']} "
          f"NCA={r['nca_refs']['sbx']}")

    # [3] CB-IF-001b 状态查询（沙盒 mou_logs）
    from app import store as st
    from app.models import Sandbox
    sid = st.new_sandbox_id()
    sb = Sandbox(sandbox_id=sid, name="e2e", initiator_did="did:tdca:INNOVATOR-001",
                 initiator_role="innovator", six_elements={})
    st.save_sandbox(sb)
    r2 = adapter.anchor(sid, tax_in=100, tax_out=50)
    sb2 = st.load_sandbox(sid)
    sb2.mou_logs = [{"transaction_id": r2["transaction_id"], "mou": r2["mou"],
                     "verified": r2["verified"], "simulated": r2["simulated"]}]
    st.save_sandbox(sb2)
    st3 = adapter.mou_status(sid)
    assert st3["mou"] == 150 and st3["verified"] is True
    print(f"[3] CB-IF-001b 状态: mou={st3['mou']} count={st3['count']}")

    # [4] NCA 链
    from app.nca_logger import verify_chain
    v = verify_chain()
    assert v["valid"] is True, v
    print(f"[4] NCA 链校验: valid={v['valid']} checked={v['checked']}")

    print("\nM3-5 CB-IF E2E all passed (4/4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
