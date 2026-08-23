"""端到端演示：Python 发起 → Go 核心校验 → NCA 落链 → 熔断判定（融入方案 I-4）。

流程:
  1. Python 构造 AgentCard（模拟智能体申请准入）
  2. Go enforce 校验（PASS 才继续）
  3. Go nca 链追加（事实存证）
  4. Go nsfl 熔断判定（正常信号 WARN 不阻断；恶意信号 BLOCK/FUSED）
  5. 输出全链 JSON（接口熵=0，可被 Kimi 推送仓库后复现）

数据性质: SIMULATED（ID92）——演示数据，不构成真实配置权执行。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tdca_core_go import TdcadBridge


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe = os.path.join(root, "tdcad.exe")
    b = TdcadBridge(tdcad_path=exe if os.path.exists(exe) else None)

    print("=" * 60)
    print("TDCA Core Go 端到端（I-4）— Python 发起 → Go 核心执行")
    print("数据性质: SIMULATED（ID92）")
    print("=" * 60)

    # 1. 准入校验（enforce）
    card = {
        "agent_id": "NM-DEMO-001",
        "protocol_version": "3.1.2",
        "scene_id": "scene-phy-notification",
        "role": "NM-Operator",
        "allowed_calls": ["verify", "record"],
        "nsfl_boundary": ["no-key-export", "no-tamper"],
    }
    res = b.enforce_check(card)
    print(f"\n[1] enforce check: {res['status']} ({res['reason']})")
    if res["status"] != "PASS":
        print("准入未通过——终止")
        return 1

    # 2. NCA 落链（事实存证）
    record = {
        "nca_id": "NCA-E2E-DEMO-001",
        "type": "fact",
        "hash": "",
        "ts": "2026-08-23T00:00:00Z",
        "signer": "TDCA-PUBKEY-DEMO-01",
        "payload_ref": "FactHash_demo_1",
        "prev_hash": "sha256:genesis",
        "nsfl": {"version": "V0.2", "triggered": False},
    }
    nca_res = b.nca_append(record)
    print(f"[2] nca append: {nca_res['status']} (head={nca_res['head'][:20]}...)")

    # 3. 熔断判定（正常信号）
    warn = b.nsfl_eval("demo-trigger-1", "suspicious-pattern")
    print(f"[3] nsfl eval (normal): {warn['action']['status']} — blocked={warn['blocked']}")

    # 4. 熔断判定（恶意信号——破坏性）
    fuse = b.nsfl_eval("demo-trigger-2", "nsfl-bypass-attempt")
    print(f"[4] nsfl eval (malicious): {fuse['action']['status']} "
          f"— irreversible={fuse['action']['irreversible']}")

    # 5. 汇总
    summary = {
        "e2e": "PASS",
        "enforce": res,
        "nca": nca_res,
        "nsfl_warn": warn["action"]["status"],
        "nsfl_fuse": fuse["action"]["status"],
        "note": "Python→Go 全链打通；接口熵=0；数据 SIMULATED（ID92）",
    }
    print("\n" + "=" * 60)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
