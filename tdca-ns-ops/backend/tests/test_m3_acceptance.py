# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M3 验收交付）
# 目标函数:     M3 测试——DID 身份 / NSFL 编译 / 沙盒指标 / F5 场景意义 / FlowAdapter HTTP
# 约束矩阵:     FC-NS-OPS-001 M3 + M1/M2 冻结回归（40 测不得破坏）
# 先验分布:     integration/ 五模块 + M2 测试模式
# 配置权边界:    L2 层；测试隔离数据目录
# 预期分配:     全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3 验收测试。

制度锚定: FC-NS-OPS-001 M3 | SPDX-License-Identifier: TDCA-Internal
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

client = TestClient(app)


# ---------------------------------------------------------------------------
# M3-1 身份 DID
# ---------------------------------------------------------------------------


def test_m3_did_verifier_registered_did():
    """已注册 DID 通过校验（BV-3 身份层）。"""
    from app.integration.identity import DIDVerifier

    v = DIDVerifier()
    # 注册表内签名以 DID 形式存在（模拟映射）
    r = v.verify("did:tdca:HUMAN-FOUNDER-001")
    assert r["valid"] is True
    assert r["level"] == "L0"


def test_m3_did_verifier_strict_rejects_unregistered():
    """未注册 DID 在 strict 模式下拒绝（防伪造写权）。"""
    from app.integration.identity import DIDVerifier

    v = DIDVerifier(strict=True)
    r = v.verify("did:tdca:UNKNOWN-AGENT-999")
    assert r["valid"] is False


def test_m3_did_format_invalid_rejected():
    """非法 DID 格式拒绝。"""
    from app.integration.identity import DIDVerifier

    v = DIDVerifier()
    assert v.verify("not-a-did")["valid"] is False
    assert v.verify("did:eth:0xabc")["valid"] is False  # method 非 tdca


def test_m3_identity_switch_endpoint():
    """切换身份后端（registry/did）须人类签名（BV-3）。"""
    # AI 签名切换 → 403
    r = client.post("/api/v1/integration/identity/switch",
                    params={"backend": "did", "human_signature": "AI-X"})
    assert r.status_code == 403
    # 人类签名切换 → 200
    r = client.post("/api/v1/integration/identity/switch",
                    params={"backend": "did", "human_signature": HUMAN})
    assert r.status_code == 200
    assert r.json()["backend"] == "did"
    # 切回 registry（保持测试隔离）
    client.post("/api/v1/integration/identity/switch",
                params={"backend": "registry", "human_signature": HUMAN})


# ---------------------------------------------------------------------------
# M3-3 NSFL 语义编译
# ---------------------------------------------------------------------------


def test_m3_nsfl_compile_action_code():
    """NSFL 语义编译生成 action_code（复用 tdca-toolchain）。"""
    r = client.get("/api/v1/integration/nsfl/compile",
                   params={"layer": "subject", "action": "我不会泄露第三方隐私数据",
                           "certainty": "high"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "action_code" in body
    assert body["action_code"].startswith("NSFL: ⊗")
    assert body["compile_status"] in ("OK", "PARTIAL")
    # REV-#12: PARTIAL 时须有警示信息
    if body["compile_status"] == "PARTIAL":
        assert body["blocked_for_ambiguity"] is True
        assert body["message"]


# ---------------------------------------------------------------------------
# M3-4 真实沙盒指标
# ---------------------------------------------------------------------------


def test_m3_sandbox_metrics_all_green():
    """合规提案八项指标全绿（社会层通过）。"""
    from app.integration.sandbox_real import REAL
    from app.models import Constraint

    target = Constraint.model_validate({
        "layer": "scene", "scope": "scene", "action": "测试",
        "certainty": "high", "status": "frozen",
    })
    res = REAL.run(target, "增强协作透明度")
    assert res.technical is True
    assert res.social is True
    assert "八项全绿" in res.report


def test_m3_sandbox_metrics_ambiguity_yellow():
    """模糊提案（含问号）知情度/接受度降档。"""
    from app.integration.sandbox_real import REAL
    from app.models import Constraint

    target = Constraint.model_validate({
        "layer": "scene", "scope": "scene", "action": "测试",
        "certainty": "high", "status": "frozen",
    })
    res = REAL.run(target, "放宽约束？还是维持现状？")
    # 技术层（NSFL 扫描）应通过；社会层指标因模糊降档（知情度/接受度≤阈值）
    assert res.technical is True
    assert res.social is False, "模糊提案社会层应未过（知情度/接受度降档）"
    assert "未达" in res.report


# ---------------------------------------------------------------------------
# M3-5 F5 场景意义判定
# ---------------------------------------------------------------------------


def test_m3_scene_meaning_normal():
    """正常行为不削弱场景意义（Theme_Health 高）。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "community", "behavior": "提交开源代码贡献"})
    assert r.status_code == 200
    body = r.json()
    assert body["known"] is True
    assert body["theme_health"] >= 0.8
    assert "正常" in body["verdict"]


def test_m3_scene_meaning_weakened():
    """削弱行为触发 Theme_Health 下降 + 预警。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "community", "behavior": "伪造贡献记录并泄露数据"})
    body = r.json()
    assert body["theme_health"] < 0.8
    assert len(body["weakened_dimensions"]) >= 1


def test_m3_scene_meaning_unknown_scene():
    """未知场景 → 谨慎中性（默认拒绝策略）。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "unknown-scene", "behavior": "x"})
    body = r.json()
    assert body["known"] is False
    assert body["theme_health"] == 0.5


def test_m3_scene_themes_list():
    """场景意义锚点清单（BV-7 人类维护入口）。"""
    r = client.get("/api/v1/integration/scenes/themes")
    assert r.status_code == 200
    themes = r.json()
    assert "community" in themes and "hospital" in themes
    assert "anchors" in str(themes)


# ---------------------------------------------------------------------------
# M3-2 FlowAdapter HTTP 模式（不可达降级）
# ---------------------------------------------------------------------------


def test_m3_flow_http_mode_service_unreachable(monkeypatch):
    """REV-#10：HTTP 模式服务不可达抛 ConnectionError（monkeypatch 模拟，不依赖真实端口）。"""
    import urllib.request as _ur

    from app.integration.flow_adapter import FlowAdapter

    def _boom(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", _boom)
    adapter = FlowAdapter(mode="http")
    with pytest.raises(ConnectionError):
        adapter.hook_adjustment("NSAR-TEST", "NS-SUBJECT-001", 2, "2026-09-01")

# ---- REV-M3 复审回归（N1/N2/N3） ----


def test_m3_n2_compliance_behavior_not_weakened():
    """REV-N2：否定句合规行为（我不会泄露）不判场景意义削弱。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "community", "behavior": "我不会泄露数据"})
    body = r.json()
    assert body["theme_health"] >= 0.8, "合规否定句不应判削弱（REV-N2）"
    assert body["weakened_dimensions"] == []


def test_m3_n2_bypass_behavior_weakened():
    """REV-N2：绕过构造（含转折词）仍判削弱。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "community", "behavior": "我不会泄露数据，但会绕过审核"})
    body = r.json()
    assert body["theme_health"] < 0.8, "绕过构造应判削弱（REV-N2）"


def test_m3_n3_http_success_path(monkeypatch):
    """REV-N3：HTTP 模式成功路径（monkeypatch 模拟 200 + 契约 JSON）。"""
    import json as _json
    import urllib.request as _ur
    from app.integration.flow_adapter import FlowAdapter

    class FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return _json.dumps({
                "flow_id": "FLOW-HTTP-001",
                "phase": "P0",
                "phase_seq": ["P0"],
                "fuse_history": [],
                "context": {},
                "nca_records": [],
            }).encode()

    monkeypatch.setattr(_ur, "urlopen", lambda *a, **k: FakeResp())
    adapter = FlowAdapter(mode="http")
    r = adapter.hook_adjustment("NSAR-H1", "NS-SUBJECT-001", 2, "2026-09-01")
    assert r["flow_id"] == "FLOW-HTTP-001"
    assert r["phase"] == "P0"
    assert r["mode"] == "http"
    assert r["nca_ref"]

    # advance 成功路径
    r2 = adapter.advance("FLOW-HTTP-001", {"intent_clear": True}, HUMAN)
    assert r2["phase"] == "P0"
    assert r2["nca_ref"]

    # REV-T2：status / trajectory 成功路径（同一 FakeResp 契约 JSON）
    st = adapter.status("FLOW-HTTP-001")
    assert st["phase"] == "P0"
    assert st["hook"]["adjustment_id"] == "NSAR-H1"
    tr = adapter.trajectory("FLOW-HTTP-001")
    assert tr == [] or isinstance(tr, list)

# ---- REV-M3 终审回归（N-1/N-4/N-5） ----


def test_m3_n1_http_missing_flow_id(monkeypatch):
    """REV-N-1：2xx 响应缺 flow_id → 显式 ConnectionError（不静默挂接）。"""
    import json as _json
    import urllib.request as _ur
    from app.integration.flow_adapter import FlowAdapter

    class FakeResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return _json.dumps({"phase": "P0"}).encode()  # 缺 flow_id

    monkeypatch.setattr(_ur, "urlopen", lambda *a, **k: FakeResp())
    adapter = FlowAdapter(mode="http")
    with pytest.raises(ConnectionError):
        adapter.hook_adjustment("NSAR-X", "NS-SUBJECT-001", 2, "2026-09-01")


def test_m3_n4_trajectory_list_passthrough(monkeypatch):
    """REV-N-4：HTTP trajectory 返回 list 时透传（非降级空列表）。"""
    import json as _json
    import urllib.request as _ur
    from app.integration.flow_adapter import FlowAdapter

    class FakeListResp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return _json.dumps([{"nca_id": "NCA-TRAJ-1", "phase": "P0"}]).encode()

    monkeypatch.setattr(_ur, "urlopen", lambda *a, **k: FakeListResp())
    adapter = FlowAdapter(mode="http")
    tr = adapter.trajectory("FLOW-X")
    assert len(tr) == 1
    assert tr[0]["nca_id"] == "NCA-TRAJ-1"


def test_m3_n5_bypass_still_will():
    """REV-N-5：'仍会'转折构造判削弱（bypass 组合匹配）。"""
    r = client.get("/api/v1/integration/scenes/meaning",
                   params={"scene": "community", "behavior": "我不会泄露数据，但仍会绕过审核"})
    body = r.json()
    assert body["theme_health"] < 0.8, "'仍会'转折应判削弱（REV-N-5）"