# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3 集成联动）
# 目标函数:     M3-1 NS-IF 契约测试——NS-IF-001~003 适配层（传输层 monkeypatch 模拟）
# 约束矩阵:     FC-SBX-OPS-001 SV-8（<1s）/ SV-10（双向存证）+ 接口熵=0
# 先验分布:     NS-OPS test_m3_acceptance（HTTP 模式 monkeypatch）+ nsops_adapter.py
# 配置权边界:   L2；仅测试环境
# 预期分配:     NS-IF 契约断言全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""M3-1 NS-IF-001~003 契约测试（适配层，传输层 monkeypatch 模拟）。

制度锚定: FC-SBX-OPS-001 M3-1 | SPDX-License-Identifier: TDCA-Internal

测试策略（确定性隔离）:
  - monkeypatch nsops_adapter._http_call（不依赖真实 NS-OPS 8123 常驻）
  - 契约断言: NS-IF-001 约束查询 / NS-IF-002 熔断触发（BLOCK→fuse）/ NS-IF-003 合规证明
  - SV-8 延迟断言 / SV-10 双向存证断言（NCA 链）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.nsops_adapter as nsops_adapter  # noqa: E402
from app.nsops_adapter import NSOpsAdapter  # noqa: E402


# ---------------------------------------------------------------- 桩数据

NS_OPS_CONSTRAINTS = [
    {
        "id": "NS-SUBJECT-001", "layer": "subject", "certainty": "high",
        "action": "我不会泄露第三方隐私数据",
    },
    {
        "id": "NS-INST-001", "layer": "institutional", "certainty": "absolute",
        "action": "任何人不能实施违反 L0 法律底线的行为",
    },
]

NS_OPS_JUDGMENT_BLOCK = {
    "decision": "block",
    "reason": "触碰制度负空间（L0 法律底线），绝对熔断（BV-1/NSFL ⊗）",
    "matched_constraints": ["NS-INST-001"],
    "fuse_triggered": True,
    "nca_ref": "TDCA-REASONIX-20260810-015",
}

NS_OPS_JUDGMENT_ALLOW = {
    "decision": "allow",
    "reason": "未触碰负空间，允许执行",
    "matched_constraints": [],
    "fuse_triggered": False,
    "nca_ref": "TDCA-REASONIX-20260810-016",
}

NS_OPS_PRECHECK_BLOCKED = {
    "blocked": True,
    "results": [
        {"declaration_id": "NSFL-LEGAL-001", "scope": "法律负空间",
         "matched_prohibitions": ["不得将知识图谱用于任何违反中国现行法律法规的查询或推理"],
         "blocked": True},
    ],
}

NS_OPS_PRECHECK_PASS = {"blocked": False, "results": []}

NS_OPS_FUSES_ACTIVE = [
    {"fuse_id": "F-1", "rule_id": "NS-OPS-F3-LEGAL", "fuse_type": "LEGAL",
     "state": "ACTIVE", "reason": "法律负空间", "human_escalated": True},
]

NS_OPS_FUSES_EMPTY: list = []


# ---------------------------------------------------------------- helpers

def _adapter() -> NSOpsAdapter:
    return NSOpsAdapter(base_url="http://test-ns-ops:8123")


def _stub_http(responses: list, expected: Optional[list] = None) -> mock.Mock:
    """按序返回预设 (status, json) 的 _http_call 替身；expected 为 (method, path) 断言列表。"""
    seq = iter(responses)
    expected = list(expected or [])
    calls = []

    def fake(method, path, body=None, params=None, base_url="http://test-ns-ops:8123"):
        calls.append((method, path))
        try:
            return next(seq)
        except StopIteration:
            return (200, {})

    f = mock.Mock(side_effect=fake)
    # 记录断言在返回后执行：用 wrapper 校验 method/path（E4 契约面增强）
    def wrapper(method, path, body=None, params=None, base_url="http://test-ns-ops:8123"):
        result = fake(method, path, body=body, params=params, base_url=base_url)
        if expected:
            idx = len(calls) - 1
            exp_method, exp_path = expected[idx] if idx < len(expected) else (None, None)
            assert method == exp_method, f"method 不匹配: {method} != {exp_method}"
            assert path == exp_path, f"path 不匹配: {path} != {exp_path}"
        return result

    f.side_effect = wrapper
    return f


# ---------------------------------------------------------------- NS-IF-001 约束查询

def test_nsif001_query_constraints_ok(monkeypatch):
    """NS-IF-001: 约束查询返回清单 + NCA 双向存证（SV-10）。"""
    monkeypatch.setattr(nsops_adapter, "_http_call", _stub_http([(200, NS_OPS_CONSTRAINTS)]))
    r = _adapter().query_constraints(layer="institutional")
    assert r["contract"] == "NS-IF-001"
    assert r["count"] == 2
    assert r["constraints"][0]["id"] == "NS-SUBJECT-001"
    assert r["latency_ms"] < 1000  # SV-8
    assert r["nca_refs"]["sbx"].startswith("NCA-")  # SV-10 双向存证


def test_nsif001_latency_over_sv8(monkeypatch):
    """NS-IF-001: 延迟 ≥1s 违反 SV-8 → ConnectionError（快系统 ID71）。"""
    with mock.patch("time.monotonic", side_effect=[1000.0, 1002.0]):
        monkeypatch.setattr(nsops_adapter, "_http_call", _stub_http([(200, NS_OPS_CONSTRAINTS)]))
        with pytest.raises(ConnectionError, match="SV-8"):
            _adapter().query_constraints()


def test_nsif001_ns_ops_unreachable(monkeypatch):
    """NS-IF-001: NS-OPS 不可达 → ConnectionError（沙盒准入不可静默放行）。"""
    def boom(method, path, body=None, params=None, base_url="http://test-ns-ops:8123"):
        raise ConnectionError("[NS-IF] NS-OPS 服务不可达")
    monkeypatch.setattr(nsops_adapter, "_http_call", boom)
    with pytest.raises(ConnectionError, match="不可达"):
        _adapter().query_constraints()


# ---------------------------------------------------------------- NS-IF-002 熔断触发

def test_nsif002_block_triggers_fuse(monkeypatch):
    """NS-IF-002: 触碰法律负空间 → decision=block + fuse_triggered=True（ID86 绝对熔断）。"""
    monkeypatch.setattr(nsops_adapter, "_http_call", _stub_http([(200, NS_OPS_JUDGMENT_BLOCK)]))
    r = _adapter().check_and_fuse(actor="agent-x", action="实施违反 L0 法律底线的行为", scene="community")
    assert r["contract"] == "NS-IF-002"
    assert r["decision"] == "block"
    assert r["fuse_triggered"] is True
    assert r["matched_constraints"] == ["NS-INST-001"]
    assert r["nca_refs"]["nsops"] == "TDCA-REASONIX-20260810-015"  # NS-OPS 侧回引
    assert r["nca_refs"]["sbx"].startswith("NCA-")
    assert r["latency_ms"] < 1000


def test_nsif002_allow_no_fuse(monkeypatch):
    """NS-IF-002: 合规行为 → decision=allow + fuse_triggered=False。"""
    monkeypatch.setattr(nsops_adapter, "_http_call", _stub_http([(200, NS_OPS_JUDGMENT_ALLOW)]))
    r = _adapter().check_and_fuse(actor="agent-x", action="提交六要素声明", scene="community")
    assert r["decision"] == "allow"
    assert r["fuse_triggered"] is False


# ---------------------------------------------------------------- NS-IF-003 合规证明

def test_nsif003_non_compliant_when_precheck_blocked(monkeypatch):
    """NS-IF-003: NSFL 预检 blocked → 不可合规（ID86/NSFL 三不可）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_PRECHECK_BLOCKED), (200, NS_OPS_FUSES_ACTIVE), (200, [])]),
    )
    r = _adapter().compliance_cert(actor="agent-x", action="实施违反法律底线的行为")
    assert r["contract"] == "NS-IF-003"
    assert r["compliant"] is False
    assert r["precheck"]["blocked"] is True
    assert r["nca_refs"]["sbx"].startswith("NCA-")


def test_nsif003_compliant_when_clean(monkeypatch):
    """NS-IF-003: 预检通过 + 无活跃熔断 → compliant=True（出盒合规证明）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_PRECHECK_PASS), (200, NS_OPS_FUSES_EMPTY), (200, [])]),
    )
    r = _adapter().compliance_cert(actor="agent-x", action="合规实验行为")
    assert r["compliant"] is True
    assert r["fuse_count"] == 0
    assert r["latency_ms"] < 1000


def test_nsif003_resolved_fuse_not_blocking(monkeypatch):
    """NS-IF-003: 已解决（RESOLVED）熔断不阻断合规（仅活跃熔断阻断）。"""
    resolved = [{"fuse_id": "F-2", "state": "RESOLVED", "rule_id": "NS-OPS-F3-LEGAL"}]
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_PRECHECK_PASS), (200, resolved), (200, [])]),
    )
    r = _adapter().compliance_cert(actor="agent-x", action="整改完成行为")
    assert r["compliant"] is True
    assert r["fuse_count"] == 0  # RESOLVED 不计活跃


# ---------------------------------------------------------------- fail-closed（T1 修复回归）

def test_nsif002_fail_closed_on_503_json(monkeypatch):
    """NS-IF-002: NS-OPS 返回 503 JSON → NSInterfaceError（禁止默认 allow 放行，ID86）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(503, {"detail": "法律负空间基线更新中"})]),
    )
    with pytest.raises(ConnectionError, match="fail-closed"):
        _adapter().check_and_fuse(actor="agent-x", action="实施违反 L0 法律底线的行为", scene="community")


def test_nsif003_fail_closed_on_503_json(monkeypatch):
    """NS-IF-003: 任一查询 503 → NSInterfaceError（禁止误判 compliant=True）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(503, {"detail": "暂不可用"}), (200, []), (200, [])]),
    )
    with pytest.raises(ConnectionError, match="fail-closed"):
        _adapter().compliance_cert(actor="agent-x", action="实施违反法律底线的行为")


def test_nsif001_fail_closed_on_503_json(monkeypatch):
    """NS-IF-001: 约束查询 503 → NSInterfaceError（禁止空清单误判'无约束'）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(503, {"detail": "暂不可用"})]),
    )
    with pytest.raises(ConnectionError, match="fail-closed"):
        _adapter().query_constraints()


# ---------------------------------------------------------------- 契约面增强（E4）

def test_nsif001_method_path_asserted(monkeypatch):
    """NS-IF-001: 桩校验调用端点契约（GET /api/v1/constraints）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_CONSTRAINTS)], expected=[("GET", "/api/v1/constraints")]),
    )
    r = _adapter().query_constraints()
    assert r["count"] == 2


def test_nsif002_method_path_asserted(monkeypatch):
    """NS-IF-002: 桩校验调用端点契约（POST /api/v1/judgments）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_JUDGMENT_BLOCK)], expected=[("POST", "/api/v1/judgments")]),
    )
    r = _adapter().check_and_fuse(actor="agent-x", action="x" * 2, scene="community")
    assert r["fuse_triggered"] is True


def test_nsif003_three_calls_asserted(monkeypatch):
    """NS-IF-003: 三次调用的 method/path 全部契约断言。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http(
            [(200, NS_OPS_PRECHECK_PASS), (200, NS_OPS_FUSES_EMPTY), (200, [])],
            expected=[
                ("GET", "/api/v1/integration/nsfl/declarations"),
                ("GET", "/api/v1/integration/nsfl/fuses"),
                ("GET", "/api/v1/integration/nsfl/history"),
            ],
        ),
    )
    r = _adapter().compliance_cert(actor="agent-x", action="合规行为")
    assert r["compliant"] is True


def test_nsif002_allow_with_conditions(monkeypatch):
    """NS-IF-002: allow_with_conditions 透传（NS-OPS Decision 四值枚举，E3）。"""
    resp = {"decision": "allow_with_conditions", "reason": "接近边界，附加条件执行",
            "matched_constraints": ["NS-SCENE-001"], "fuse_triggered": False, "nca_ref": "TDCA-REASONIX-20260810-020"}
    monkeypatch.setattr(nsops_adapter, "_http_call", _stub_http([(200, resp)]))
    r = _adapter().check_and_fuse(actor="agent-x", action="接近边界的行为", scene="community")
    assert r["decision"] == "allow_with_conditions"
    assert r["fuse_triggered"] is False


# ---------------------------------------------------------------- 路由层（E4/E5）

def test_route_constraints_invalid_layer():
    """路由层: layer 非法 → 422（E5 输入校验）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/nsops/constraints", params={"layer": "bogus"})
    assert r.status_code == 422


def test_route_check_invalid_scene():
    """路由层: scene 非法 → 422（E5 输入校验）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.post("/api/v1/nsops/check", json={"actor": "agent-x", "action": "行为", "scene": "bogus"})
    assert r.status_code == 422


def test_route_compliance_ok(monkeypatch):
    """路由层: NS-IF-003 合规端点 200（桩传输层）。"""
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_PRECHECK_PASS), (200, NS_OPS_FUSES_EMPTY), (200, [])]),
    )
    client = TestClient(app)
    r = client.post("/api/v1/nsops/compliance", json={"actor": "agent-x", "action": "合规行为"})
    assert r.status_code == 200
    assert r.json()["compliant"] is True


def test_nsif002_decision_missing_fail_closed(monkeypatch):
    """#1: NS-OPS 返回 200 但 decision 缺失 → fail-closed（禁止默认 allow 放行，ID86）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, {"fuse_triggered": False})]),
    )
    with pytest.raises(ConnectionError, match="decision"):
        _adapter().check_and_fuse(actor="agent-x", action="行为", scene="community")


def test_nsif003_fuses_structure_break_fail_closed(monkeypatch):
    """#2: fuses 响应非 list → fail-closed（禁止默认空台账判合规，ID86）。"""
    monkeypatch.setattr(
        nsops_adapter, "_http_call",
        _stub_http([(200, NS_OPS_PRECHECK_PASS), (200, {"weird": True}), (200, [])]),
    )
    with pytest.raises(ConnectionError, match="结构异常"):
        _adapter().compliance_cert(actor="agent-x", action="行为")


def test_nsif_fail_closed_generates_error_nca(monkeypatch):
    """#5: fail-closed 异常路径生成 ERROR NCA（C01/SV-7 联动故障可观测）。"""
    from app import nca_logger

    before = len(nca_logger.list_nca())
    def boom(method, path, body=None, params=None, base_url="http://test-ns-ops:8123"):
        raise ConnectionError("[NS-IF] NS-OPS 服务不可达")
    monkeypatch.setattr(nsops_adapter, "_http_call", boom)
    with pytest.raises(ConnectionError):
        _adapter().check_and_fuse(actor="agent-x", action="行为", scene="community")
    after = nca_logger.list_nca()
    assert len(after) == before + 1  # ERROR NCA 已落盘
    assert "FAIL_CLOSED" in after[-1]["operation"]


# ---------------------------------------------------------------- 契约破坏

def test_nsif_contract_break_non_json(monkeypatch):
    """NS-OPS 非 JSON 响应 → ConnectionError（契约破坏显式失败，不静默降级）。"""
    class FakeResp:
        status = 200

        def read(self):
            return b"<html>502 Bad Gateway</html>"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    import urllib.request as _ur
    monkeypatch.setattr(_ur, "urlopen", lambda *a, **k: FakeResp())
    with pytest.raises(ConnectionError, match="非 JSON"):
        nsops_adapter._http_call("GET", "/api/v1/constraints")


def test_nsif_http_error_json(monkeypatch):
    """NS-OPS HTTP 错误但 JSON 响应 → 返回 (code, json)（错误码透传）。"""
    class FakeHTTPError(Exception):
        code = 503

        def read(self):
            return json.dumps({"detail": "法律负空间基线更新中"}).encode("utf-8")

    import urllib.error as _ue
    monkeypatch.setattr(_ue, "HTTPError", FakeHTTPError)
    with mock.patch("urllib.request.urlopen", side_effect=FakeHTTPError()):
        status, body = nsops_adapter._http_call("GET", "/api/v1/constraints")
    assert status == 503
    assert body["detail"] == "法律负空间基线更新中"
