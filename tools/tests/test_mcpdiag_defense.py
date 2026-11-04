# FC-ID: DCD-MCP-BRIDGE-001 | L1SI196-MCPDIAG-001 批1防御断言集（A11）
"""MCPDIAG-001 批1：ns_types 非对象同型防御断言（trispace.py 两判 + server.py 越界段）。

V6 单测：四型坏卡（缺键 / null / "not-a-dict" / []）直调 judge_operator_coverage 与
judge_absolute_negative_space，一律返 tuple、零 raise（改前 null/str/list 三型 AttributeError）。
V1-V4 端到端：四型坏卡各走一次完整写路（无害实参），断言 CODE_JUDGMENT_FAIL、
四判读数照出（J1/J2 FAIL 在 detail）、链长与链末哈希前后不变、无新存证件、
无熔断日志、状态机未登记（零消耗拒绝）。
V5 回归：令面合格卡四判全过、出 NSFL-CERT、升 SBX-ACTIVE（判据语义与闭集未动）。

⛔本文件不触碰批2（agent_card_fingerprint ＋ Audit-Trail 两步）；⛔不部署。
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
from mcp_bridge.server import BridgeServer  # noqa: E402
from mcp_bridge import trispace  # noqa: E402


def _j(obj):
    return json.dumps(obj, ensure_ascii=False)


def _card(**over):
    card = {"identity_type": "external", "data_provenance": "simulated",
            "ns_types": {"absolute": ["发币", "公售"],
                         "scene_limited": ["跨境数据"],
                         "approval_required": ["对外缔约"]},
            "forbidden_operators": ["发币"],
            "declared_fields": ["text"]}
    card.update(over)
    return card


def _bad_card(shape):
    """四型坏卡：ns_types 缺键 / null / "not-a-dict" / []。
    其余字段令面最小集——⊗操作符在、声明字段在，坏只坏在 ns_types 形状。"""
    card = {"forbidden_operators": ["发币"], "declared_fields": ["text"]}
    if shape != "missing":
        card["ns_types"] = {"null": None, "str": "not-a-dict", "list": []}[shape]
    return card


_BAD_SHAPES = ["missing", "null", "str", "list"]


@pytest.fixture()
def srv(tmp_path):
    return BridgeServer(tmp_path / "evidence", caller="test-client")


def _call(srv, name, args, rid=1):
    return srv.handle_line(_j({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                               "params": {"name": name, "arguments": args}}))


def _nca_files(ev):
    return list(Path(ev).glob("NCA-MCP-*.yaml"))


# ============ V6 单测：两判函数四型坏卡零 raise ============

@pytest.mark.parametrize("shape", _BAD_SHAPES)
def test_v6_j2_bad_ns_types_returns_tuple(shape):
    """J2 直调：四型坏卡一律返 (bool, str) tuple，零 raise。"""
    out = trispace.judge_operator_coverage(_bad_card(shape))
    assert isinstance(out, tuple) and len(out) == 2
    assert isinstance(out[0], bool) and isinstance(out[1], str)


@pytest.mark.parametrize("shape", _BAD_SHAPES)
def test_v6_j3_bad_ns_types_returns_tuple(shape):
    """J3 直调：四型坏卡一律返 (bool, str) tuple，零 raise。"""
    out = trispace.judge_absolute_negative_space(_bad_card(shape), "hello", [])
    assert isinstance(out, tuple) and len(out) == 2
    assert isinstance(out[0], bool) and isinstance(out[1], str)


# ============ V1-V4 端到端：完整写路，判读照出，零消耗 ============

@pytest.mark.parametrize("shape", _BAD_SHAPES)
def test_v1_v4_e2e_bad_ns_types_judgment_fail_zero_consumption(srv, shape):
    """坏卡走完整写路：CODE_JUDGMENT_FAIL，四判读数照出，
    链长与链末哈希前后不变，无新件/无熔断日志/坏卡未入状态机（零消耗）。
    起手先落一笔合格写，使链末号读数非平凡（链长 1、有真哈希可比）。"""
    ok = _call(srv, "tdca:echo", {"text": "baseline", "agent_card": _card()})
    assert "error" not in ok
    card = _bad_card(shape)
    chain_before = srv.wm.chain()
    nca_before = len(_nca_files(srv.wm.dir))
    head_before = srv.wm.chain()[0] if srv.wm.chain() else None  # 链首=最旧件
    r = _call(srv, "tdca:echo", {"text": "hello", "agent_card": card})
    assert r["error"]["code"] == trispace.CODE_JUDGMENT_FAIL
    msg = r["error"]["message"]
    assert "J1_NS-Type完整性" in msg          # 覆盖为空/非对象 → J1 FAIL 读数照出
    assert "J2_⊗覆盖度" in msg                # ⊗操作符全部 orphan → J2 FAIL 读数照出
    assert "J3_法律负空间绝对化" in msg and "J4_最小化合" in msg
    chain_after = srv.wm.chain()
    assert len(chain_after) == len(chain_before)              # 链长不变（两读数相等）
    assert chain_after[-1]["Hash"] == chain_before[-1]["Hash"]  # 链末号不变
    assert head_before is not None and chain_after[0]["Hash"] == head_before["Hash"]
    assert len(_nca_files(srv.wm.dir)) == nca_before          # 无新存证件
    assert not (Path(srv.wm.dir) / ".nsfl-fuse.log").exists()  # 无熔断日志
    assert srv.state.agent(trispace.card_fingerprint(card)) is None  # 坏卡未升 SBX 未入状态机


# ============ V5 回归：合格卡全路不变 ============

def test_v5_valid_card_full_path_unchanged(srv):
    """令面合格卡：四判全 PASS、出 NSFL-CERT、落 SBX-ACTIVE、存证件带 space_id/status。"""
    card = _card()
    r = _call(srv, "tdca:echo", {"text": "hi", "agent_card": card})
    assert "error" not in r
    body = r["result"]["content"][0]["text"]
    assert "NSFL-CERT" in body and "space_id=SBX status=SBX-ACTIVE" in body
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    assert doc["space_id"] == "SBX" and doc["status"] == "SBX-ACTIVE"
    assert doc["chain_ref"] == trispace.CHAIN_REF
    st = srv.state.agent(trispace.card_fingerprint(card))
    assert st["status"] == "SBX-ACTIVE" and st["cert"]["cert_id"].startswith("NSFL-CERT")
