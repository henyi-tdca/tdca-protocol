# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     真实 HTTP E2E 冒烟验证（对齐 NS-OPS 交付验证模式）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7
# 先验分布:     交付报告 M1
# 配置权边界:    L2 层；仅验证脚本
# 预期分配:     9 步全生命周期断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""SBX-OPS M1 真实 HTTP E2E 冒烟（对齐 NS-OPS 交付验证模式）。

用法: 先 `uvicorn app.main:app --port 8000` 启动服务，再运行本脚本。
"""
import json
import os
import sys
import urllib.request

BASE = os.environ.get("SBX_OPS_BASE", "http://127.0.0.1:8000")
API = BASE + "/api/v1"


def req(method, path, body=None):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    # 1. 健康
    with urllib.request.urlopen(BASE + "/", timeout=5) as r:
        h = json.loads(r.read().decode())
    assert h["status"] == "ok", h
    print(f"[1] 健康检查: ok (stage={h['stage']})")

    # 2. 创建（六要素）
    six = {"目标函数": "E2E冒烟", "约束矩阵": "SV-1~7", "先验分布": "任务书",
           "配置权边界": "L2", "预期分配": "冒烟", "审计轨迹": "NCA"}
    status, sb = req("POST", "/sandboxes", {"name": "E2E冒烟沙盒", "initiator_did": "did:tdca:INNOVATOR-001",
                                            "initiator_role": "innovator", "six_elements": six})
    assert status == 201, (status, sb)
    sid = sb["sandbox_id"]
    print(f"[2] 创建沙盒: 201 phase={sb['phase']} nca={len(sb['nca_ids'])}")

    # 3. 配置 PUCR（SV-2）
    status, sb = req("POST", f"/sandboxes/{sid}/configure", {"pucr": {"amount": 10000}})
    assert status == 200, (status, sb)
    print(f"[3] 配置 PUCR: 200 amount={sb['pucr']['amount']}")

    # 4. 开始实验 Phase0→P0
    status, sb = req("POST", f"/sandboxes/{sid}/start", {})
    assert status == 200 and sb["phase"] == "P0", (status, sb)
    print("[4] 开始实验: 200 phase=P0")

    # 5. 运行迭代（ENG-003 日志）
    status, sb = req("POST", f"/sandboxes/{sid}/run", {"iteration": {"metric": "users", "value": 100}})
    assert status == 200 and len(sb["eng003_log"]) == 1, (status, sb)
    print("[5] 运行迭代: 200 eng003_log=1")

    # 6. 评估（F3，α>1.2）
    status, sb = req("POST", f"/sandboxes/{sid}/evaluate", {"pcr_input": 100, "tax_revenue": 150, "employment_ss": 20})
    assert status == 200 and sb["phase"] == "P1", (status, sb)
    act = sb["activation_logs"][-1]
    assert act["coefficient"] == 1.7 and act["status"] == "财政自给性达成", act
    print(f"[6] 评估: 200 phase=P1 α={act['coefficient']} status={act['status']}")

    # 7. 出盒（SV-1 + SV-6 三方签名 + 人类签批）
    sig = [{"role": "innovator", "did": "did:tdca:INNOVATOR-001", "signature": "s1"},
           {"role": "investor", "did": "did:tdca:INVESTOR-001", "signature": "s2"},
           {"role": "government", "did": "did:tdca:GOV-001", "signature": "s3"}]
    status, sb = req("POST", f"/sandboxes/{sid}/exit", {"signatures": sig, "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
    assert status == 200 and sb["phase"] == "Exit", (status, sb)
    print(f"[7] 出盒: 200 phase=Exit（SV-1 α>1.2 + SV-6 三方签名）")

    # 8. NCA 链校验（F8）
    status, v = req("GET", "/nca/verify")
    assert status == 200 and v["valid"] is True and v["checked"] >= 3, (status, v)
    print(f"[8] NCA 链校验: valid={v['valid']} checked={v['checked']}")

    # 9. SV-1 拦截：α≤1.2 出盒被拒
    status, sb = req("POST", "/sandboxes", {"name": "低效沙盒", "initiator_did": "did:tdca:INNOVATOR-001",
                                            "initiator_role": "innovator", "six_elements": six})
    sid2 = sb["sandbox_id"]
    req("POST", f"/sandboxes/{sid2}/start", {})
    req("POST", f"/sandboxes/{sid2}/evaluate", {"pcr_input": 100, "tax_revenue": 100, "employment_ss": 0})
    status, detail = req("POST", f"/sandboxes/{sid2}/exit", {"signatures": sig, "human_signatory": "did:tdca:HUMAN-FOUNDER-001"})
    assert status == 422 and "SV-1" in detail["detail"], (status, detail)
    print("[9] SV-1 拦截: 422 拒绝（α=1.0 出盒）")

    print("\nE2E smoke all passed (9/9)")


if __name__ == "__main__":
    sys.exit(main())
