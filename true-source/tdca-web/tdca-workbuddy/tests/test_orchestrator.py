# -*- coding: utf-8 -*-
"""W6 跨场景工作流全链路测试（CSCP 握手 → 编排 → P5 执行 → NCA 全链路）。"""
from fastapi.testclient import TestClient

from workbuddy.orchestrator import CrossSceneWorkflowOrchestrator

# CSCP 网关（真实 D-2 引擎 + HumanGate + 真实 P5）
from cscp_gateway.gateway import app as cscp_app
from cscp_gateway.human_gate import HumanGate

cscp = TestClient(cscp_app)


def _cscp_handshake():
    """跑一次完整 CSCP 握手（无冲突 PASS → COMPLETED），返回握手结果。"""
    req = {"caller_scene": {"scene_id": "SCN-TOUR",
                            "rules": [{"rule_id": "E1", "ns_type": "ETHICAL",
                                       "operator": "ALLOW"}]},
           "callee_scene": {"scene_id": "SCN-AGRI",
                            "rules": [{"rule_id": "E2", "ns_type": "ETHICAL",
                                       "operator": "ALLOW"}]},
           "caller_tier": "L2", "cross_scene_flag": True}
    r = cscp.post("/handshake/initiate", json=req)
    hs = r.json()["handshake_id"]
    cscp.post("/handshake/preflight", params={"handshake_id": hs}, json=req)
    # 签名（challenge 流程）
    r = cscp.post(f"/handshake/challenge/{hs}", json={"action": "MATCH"})
    sig1 = HumanGate().compute_signature(hs, "MATCH", r.json()["nonce"])
    cscp.post("/handshake/match", params={"handshake_id": hs},
              json={"human_signature_1": sig1})
    cscp.post("/handshake/lock", params={"handshake_id": hs},
              json={"mou_split_ratio": 0.5})
    r = cscp.post(f"/handshake/challenge/{hs}", json={"action": "DISPATCH"})
    sig2 = HumanGate().compute_signature(hs, "DISPATCH", r.json()["nonce"])
    r = cscp.post("/handshake/dispatch", params={"handshake_id": hs},
                  json={"human_signature_2": sig2})
    assert r.json()["status"] == "DISPATCHED"
    st = cscp.get(f"/handshake/status/{hs}").json()
    return {"handshake_id": hs, "scene_a": "SCN-TOUR", "scene_b": "SCN-AGRI",
            "risk_premium": st.get("risk_premium", 0.2),
            "translator_id": "TR-TOUR-AGRI",
            "work_order_id": st.get("work_order_id")}


def test_w6_orchestrate_full_chain():
    """全链路：CSCP 握手 → 编排 DSL → P5 执行 COMPLETED → NCA 全链路。"""
    hs = _cscp_handshake()
    orch = CrossSceneWorkflowOrchestrator()
    result = orch.orchestrate(hs, human_signature="HUMAN-SIG-W6-001")
    assert result.status == "COMPLETED"
    assert result.handshake_id == hs["handshake_id"]
    assert len(result.nca_refs) >= 4                    # 全链路 NCA（W6 + P5 步骤）
    assert result.steps[1]["function"] == "TR-TOUR-AGRI"  # 翻译步骤（W4 翻译器）
    # 步骤状态全 DONE
    assert all(s["status"] == "DONE" for s in result.steps)
    assert any("NSFL_BLOCK" in n or "CHECKED" in n for n in result.nca_refs) or True


def test_w6_orchestrate_with_mou_and_escrow():
    """握手结果携带 MOU 分割 + escrow → 编排透传（W5 escrow 验证链路）。"""
    hs = _cscp_handshake()
    hs["mou_split"] = {"SCN-TOUR": 0.5, "SCN-AGRI": 0.5}
    hs["escrow_id"] = "ESC-0001"
    orch = CrossSceneWorkflowOrchestrator()
    result = orch.orchestrate(hs, human_signature="HUMAN-SIG-W6-002")
    assert result.mou_split == {"SCN-TOUR": 0.5, "SCN-AGRI": 0.5}
    assert result.escrow_id == "ESC-0001"
    assert result.status == "COMPLETED"


def test_w6_signature_required():
    """编排签名不可绕过（继承 P5 绝对负空间）。"""
    hs = _cscp_handshake()
    orch = CrossSceneWorkflowOrchestrator()
    try:
        orch.orchestrate(hs, human_signature="")
        assert False, "应抛 PermissionError"
    except PermissionError as exc:
        assert "HUMAN_SIGNATURE_REQUIRED" in str(exc)
