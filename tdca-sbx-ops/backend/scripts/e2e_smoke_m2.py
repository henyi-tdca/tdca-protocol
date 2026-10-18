# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M2 三位一体与正和验证）
# 目标函数:     真实 HTTP E2E 冒烟（M2 全链路：F2/F4/F5/F6）
# 约束矩阵:     FC-SBX-OPS-001 SV-1~7
# 先验分布:     交付报告 M2
# 配置权边界:    L2 层；仅验证脚本
# 预期分配:     全链路断言；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
# -*- coding: utf-8 -*-
"""SBX-OPS M2 真实 HTTP E2E 冒烟。

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
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    six = {"目标函数": "M2冒烟", "约束矩阵": "SV-1~7", "先验分布": "任务书",
           "配置权边界": "L2", "预期分配": "冒烟", "审计轨迹": "NCA"}
    status, sb = req("POST", "/sandboxes", {"name": "M2冒烟沙盒", "initiator_did": "did:tdca:INNOVATOR-001",
                                            "initiator_role": "innovator", "six_elements": six})
    assert status == 201, (status, sb)
    sid = sb["sandbox_id"]
    print(f"[1] 创建沙盒: 201 phase={sb['phase']}")

    # F2 三位一体
    trinity = [
        {"role": "innovator", "did": "did:tdca:INNOVATOR-001", "contribution": {"value": 30.0, "type": "ip"}, "reservation_utility": 5.0},
        {"role": "investor", "did": "did:tdca:INVESTOR-001", "contribution": {"value": 50.0, "type": "capital"}, "reservation_utility": 8.0},
        {"role": "government", "did": "did:tdca:GOV-001", "contribution": {"value": 20.0, "type": "pcr"}, "reservation_utility": 2.0},
    ]
    status, sb = req("POST", f"/sandboxes/{sid}/trinity", {"profiles": trinity})
    assert status == 200 and set(sb["trinity"]["profiles"]) == {"innovator", "investor", "government"}, (status, sb)
    print("[2] 三位一体配置: 200 三方已注册")

    status, sb = req("POST", f"/sandboxes/{sid}/trinity/shapley", {})
    weights = sb["trinity"]["shapley_weights"]
    assert status == 200 and abs(sum(weights.values()) - 145.0) < 1e-6, (status, weights)
    assert sb["trinity"]["shapley_properties"]["efficiency"] is True
    print(f"[3] Shapley 分配: 200 Σφ={sum(weights.values())} 效率性=True")

    # F4 S-Right + PUCR
    status, sb = req("POST", f"/sandboxes/{sid}/srights", {"scene": "社区协作", "holder_did": "did:tdca:INNOVATOR-001"})
    assert status == 200 and sb["s_rights"][0]["gradient"] == "L0"
    print("[4] S-Right 分配: 200 gradient=L0")

    status, sb = req("POST", f"/sandboxes/{sid}/pucr", {"amount": 50000.0, "data_nature": "simulated"})
    assert status == 200 and sb["pucr"]["amount"] == 50000.0
    print("[5] PUCR 预售（SV-2）: 200 amount=50000")

    # 进入实验期（F6/F5 须 P0）
    status, sb = req("POST", f"/sandboxes/{sid}/start", {})
    assert status == 200 and sb["phase"] == "P0"
    print("[5b] 进入实验: 200 phase=P0")

    # F6 正和验证
    status, sb = req("POST", f"/sandboxes/{sid}/positive-sum",
                     {"coalition_utility": 300.0, "independent_utilities": [80.0, 90.0, 50.0]})
    assert status == 200 and sb["positive_sum_logs"][-1]["is_positive_sum"] is True
    print("[6] 正和验证（F6）: 200 delta=80.0 S_synergy>0")

    # F5 化合（ENG-003 + 正和门槛，surplus 服务端取正和记录）
    status, sb = req("POST", f"/sandboxes/{sid}/chem/combine", {
        "assets": ["IP", "knowledge", "scene_weight"],
        "conditions": {"indivisible": True, "emergent": True, "nonlinear": False},
        "justification": "组合产生涌现价值",
    })
    assert status == 200 and sb["reactions"][0]["chem_type"] == "CHEM-001", (status, sb)
    assert sb["reactions"][0]["utility_surplus"] == 80.0  # 绑定正和验证 delta
    assert len(sb["eng003_log"]) == 1
    print("[7] 正向化合（CHEM-001 + ENG-003）: 200 surplus=80（绑定正和验证）")

    # 未正和验证直接化合拒绝（surplus 不可自报）
    status, sb2 = req("POST", "/sandboxes", {"name": "M2冒烟B", "initiator_did": "did:tdca:INNOVATOR-001",
                                              "initiator_role": "innovator", "six_elements": six})
    sid2 = sb2["sandbox_id"]
    req("POST", f"/sandboxes/{sid2}/start", {})
    status, detail = req("POST", f"/sandboxes/{sid2}/chem/combine", {
        "assets": ["IP"], "conditions": {"indivisible": True, "emergent": True, "nonlinear": True},
        "justification": "x",
    })
    assert status == 422 and "正和验证" in detail["detail"], (status, detail)
    print("[8] 未正和化合拒绝: 422（surplus 不可自报）")

    # NCA 链校验 + 反应轨迹
    status, v = req("GET", "/nca/verify")
    assert status == 200 and v["valid"] is True, (status, v)
    status, rx = req("GET", f"/sandboxes/{sid}/chem/reactions")
    assert status == 200 and len(rx["reactions"]) == 1
    print(f"[9] NCA 链校验: valid=True checked={v['checked']} · 反应轨迹 1 条")

    print("\nM2 E2E smoke all passed (9/9)")


if __name__ == "__main__":
    sys.exit(main())
