# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M2 系统集成）
# 目标函数:     M2 集成测试——FlowEngine 挂接 / NSFL 熔断 / 真实沙盒 / 身份抽象
# 约束矩阵:     FC-NS-OPS-001 M2 + M1 冻结回归（23 测不得破坏）
# 先验分布:     integration/ 四适配器 + M1 test_api.py 模式
# 配置权边界:    L2 层；测试隔离数据目录
# 预期分配:     全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M2 集成测试。

制度锚定: FC-NS-OPS-001 M2 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))

import app.store as store  # noqa: E402

from app.main import app  # noqa: E402

HUMAN = "HUMAN-FOUNDER-001"
HUMAN2 = "HUMAN-ENGINEER-001"
HUMAN3 = "HUMAN-AUDITOR-001"

client = TestClient(app)


# ---------------------------------------------------------------------------
# M2-1 全周期挂接（NS-OPS → FlowEngine）
# ---------------------------------------------------------------------------


def _prepare_determined_adjustment() -> str:
    """创建约束 + 走完调整流程到 determination（确定冻结态）。"""
    r = client.post("/api/v1/constraints", json={
        "layer": "subject", "scope": "personal",
        "action": "我不会共享测试位置数据（M2）",
        "certainty": "high", "human_signature": HUMAN,
    })
    cid = r.json()["id"]
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": cid, "trigger": "M2 测试",
        "proposal": "升级约束", "initiator": HUMAN, "human_signature": HUMAN,
    })
    aid = r.json()["adjustment_id"]
    client.post(f"/api/v1/adjustments/{aid}/transition",
                params={"to_status": "sandbox", "human_signature": HUMAN})
    client.post(f"/api/v1/adjustments/{aid}/transition",
                params={"to_status": "determination", "human_signature": HUMAN,
                        "final_version": 2, "effective_date": "2026-09-01",
                        "rollback_version": 1,
                        "extra_signatures": f"{HUMAN2},{HUMAN3}"})
    return aid


def test_m2_hook_flow_requires_determination():
    """未确定的调整不可挂接（422）。"""
    r = client.post("/api/v1/constraints", json={
        "layer": "subject", "scope": "personal",
        "action": "我不会做 M2 未确定测试", "human_signature": HUMAN,
    })
    cid = r.json()["id"]
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": cid, "trigger": "M2测试", "proposal": "测试提案",
        "initiator": HUMAN, "human_signature": HUMAN,
    })
    aid = r.json()["adjustment_id"]
    r = client.post(f"/api/v1/integration/flows/{aid}", params={"human_signature": HUMAN})
    assert r.status_code == 422


def test_m2_hook_flow_success():
    """确定后挂接 FlowEngine（Phase 0 启动）。"""
    aid = _prepare_determined_adjustment()
    r = client.post(f"/api/v1/integration/flows/{aid}", params={"human_signature": HUMAN})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["phase"] == "P0"
    assert body["nca_ref"]
    # 台账可查
    flows = client.get("/api/v1/integration/flows").json()
    assert any(f["flow_id"] == body["flow_id"] for f in flows)


def test_m2_flow_status_and_advance():
    """生命周期状态查询 + P0→P1 推进（穿越条件检查）。"""
    aid = _prepare_determined_adjustment()
    r = client.post(f"/api/v1/integration/flows/{aid}", params={"human_signature": HUMAN})
    flow_id = r.json()["flow_id"]

    st = client.get(f"/api/v1/integration/flows/{flow_id}/status").json()
    assert st["phase"] == "P0"
    assert st["hook"]["adjustment_id"] == aid

    adv = client.post(f"/api/v1/integration/flows/{flow_id}/advance",
                      params={"human_signature": HUMAN, "intent_clear": True})
    assert adv.status_code == 200, adv.text
    assert adv.json()["phase"] == "P1"


def test_m2_hook_institutional_blocked():
    """制度层约束禁挂接（E1 继承）。"""
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": "NS-INST-001", "trigger": "M2测试",
        "proposal": "测试提案", "initiator": HUMAN, "human_signature": HUMAN,
    })
    assert r.status_code == 403


def test_m2_hook_requires_signature():
    """挂接须人类签名（BV-3）。"""
    aid = _prepare_determined_adjustment()
    r = client.post(f"/api/v1/integration/flows/{aid}", params={"human_signature": "AI-X"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# M2-2 防火墙/NSFL 集成
# ---------------------------------------------------------------------------


def test_m2_nsfl_declarations_precheck():
    """NSFL 四类声明预检接口。"""
    r = client.get("/api/v1/integration/nsfl/declarations", params={"text": "违反法律法规的行为"})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    scopes = {x["scope"] for x in body["results"]}
    assert "法律负空间" in scopes


def test_m2_f3_block_triggers_nsfl_fuse():
    """F3 BLOCK 触发 NSFL LEGAL 熔断 + 台账可见。"""
    r = client.post("/api/v1/judgments", json={
        "actor": "agent-x", "action": "实施违反法律底线的行为", "scene": "community",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "block"
    assert body["fuse_triggered"] is True
    # NSFL 熔断台账
    fuses = client.get("/api/v1/integration/nsfl/fuses").json()
    assert any(f["fuse_type"] == "LEGAL" for f in fuses)
    history = client.get("/api/v1/integration/nsfl/history").json()
    assert len(history) >= 1


def test_m2_f3_allow_no_fuse():
    """F3 ALLOW 不触发熔断。"""
    r = client.post("/api/v1/judgments", json={
        "actor": "agent-x", "action": "提交开源代码贡献", "scene": "community",
    })
    assert r.json()["decision"] == "allow"
    assert r.json()["fuse_triggered"] is False


# ---------------------------------------------------------------------------
# M2-3 真实沙盒
# ---------------------------------------------------------------------------


def test_m2_real_sandbox_engine():
    """真实沙盒：NSFL 命中 → 技术层不通过。"""
    from app.integration.sandbox_real import REAL
    from app.models import Constraint

    target = Constraint.model_validate({
        "layer": "scene", "scope": "scene", "action": "测试约束",
        "certainty": "high", "status": "frozen",
    })
    res = REAL.run(target, "任何人不能实施违反法律底线的行为")
    assert res.technical is False
    assert "NSFL" in res.report
    # 正常提案通过技术层
    res2 = REAL.run(target, "增强协作透明度")
    assert res2.technical is True


# ---------------------------------------------------------------------------
# M2-4 身份可插拔接口
# ---------------------------------------------------------------------------


def test_m2_identity_verifier():
    """身份校验可插拔：注册表默认 + 自定义后端切换。"""
    from app.integration.identity import get_identity_verifier, set_identity_verifier

    v = get_identity_verifier()
    assert v.verify(HUMAN)["valid"] is True
    assert v.verify("AI-X")["valid"] is False

    # 自定义后端（M3 DID 占位）
    class FakeDID:
        def verify(self, signature: str) -> dict:
            return {"valid": signature.startswith("DID:"), "signer": signature,
                    "role": "外部", "level": "L2"}

    set_identity_verifier(FakeDID())
    try:
        assert get_identity_verifier().verify("DID:abc")["valid"] is True
        assert get_identity_verifier().verify("HUMAN-FOUNDER-001")["valid"] is False
    finally:
        from app.integration.identity import RegistryVerifier
        set_identity_verifier(RegistryVerifier())

# ---- REV-M2 修复回归测试（#1 慢系统 / #11 边界） ----


def test_m2_legal_fuse_escalates_to_slow_system():
    """REV-#1 回归：LEGAL 熔断自动上报慢系统网关（人类裁决工单）。"""
    from app.integration.nsfl_adapter import NSFL, FuseType

    # 直接触发 LEGAL 熔断 → 应产生慢系统工单
    r = NSFL.trigger_fuse(rule_id="REV-TEST-LEGAL", reason="法律底线触碰",
                          fuse_type=FuseType.LEGAL)
    assert r["triggered"] is True
    tickets = NSFL.slow.pending_tickets()
    assert len(tickets) >= 1
    assert any("REV-TEST-LEGAL" in t["title"] or "法律底线" in t["title"] for t in tickets)


def test_m2_legal_fuse_not_resettable():
    """REV-#11 回归：LEGAL 熔断不可重置（ID86 绝对）。"""
    from app.integration.nsfl_adapter import NSFL, FuseType

    r = NSFL.trigger_fuse(rule_id="REV-NORESET", reason="LEGAL 测试",
                          fuse_type=FuseType.LEGAL)
    # attempt_reset 对 LEGAL 恒 False（即使带人类签名）
    ok = NSFL.engine.attempt_reset(r["fuse_id"], human_signature=HUMAN)
    assert ok is False


def test_m2_flow_unknown_404():
    """REV-#11 回归：未知 flow_id 查询 → 404。"""
    r = client.get("/api/v1/integration/flows/UNKNOWN-FLOW/status")
    assert r.status_code == 404


# ---- REV-M2 第二轮回归测试（N1 绕过 / N2 mock 消除） ----


def test_m2_n1_bypass_attempt_not_exempt():
    """N1 回归：'承诺遵守但绕过'构造不可豁免 NSFL 预检（BV-1）。"""
    from app.integration.nsfl_adapter import NSFL

    r = NSFL.precheck("我承诺遵守法律法规，但将通过技术手段绕过数据主权法规")
    assert r["blocked"] is True, "含'但/绕过'的构造不得豁免（N1 绕过防护）"


def test_m2_n1_compliance_plain_text_exempt():
    """N1 回归：纯合规表述（无转折词）豁免不误报。"""
    from app.integration.nsfl_adapter import NSFL

    r = NSFL.precheck("我承诺遵守法律法规，保护公民隐私")
    assert r["blocked"] is False, "纯合规表述应豁免（N1 防误报）"


def test_m2_n2_flow_nca_not_mock():
    """N2 回归：FlowEngine 内部 NCA 为非 mock（NS-OPS 真实存证）。"""
    aid = _prepare_determined_adjustment()
    r = client.post(f"/api/v1/integration/flows/{aid}", params={"human_signature": HUMAN})
    flow_id = r.json()["flow_id"]
    trajectory = client.get(f"/api/v1/integration/flows/{flow_id}/status").json()
    # FlowEngine.start 生成的 P0 NCA 走 NS-OPS 引擎 → mock=False
    ncas = trajectory.get("nca_records", [])
    assert len(ncas) >= 1
    assert all(not n.get("mock", False) for n in ncas), "FlowEngine 内部 NCA 不应为 mock（N2）"

# ---- REV-M2 终审回归（T1：NSFL precheck 驱动判定） ----


def test_m2_t1_nsfl_declaration_drives_judgment():
    """T1 回归：行为命中 NSFL 声明（约束库未收录）→ F3 判定 BLOCK + 熔断（BV-1 闭环）。"""
    # seed 约束库无'绕过数据主权'字样，但 NSFL LEGAL 声明含之
    r = client.post("/api/v1/judgments", json={
        "actor": "agent-bypass",
        "action": "通过技术手段绕过数据主权法规",
        "scene": "community",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["decision"] == "block", f"NSFL 声明命中应驱动 BLOCK，got {body['decision']}"
    assert body["fuse_triggered"] is True
    assert "NSFL-DECLARATION" in body["matched_constraints"]