# FC-ID: DCD-MCP-BRIDGE-001 | TRISPACE-001 断言集 + 对抗集（A10，覆盖令面五项必测）
"""断言集＋对抗集：匿名写拒／无 CERT 不升 SBX／同号重投语义／越界降级／触法封禁。

零消耗口径校验：拒否路径（无卡/被禁/被停/超限/四判未过）一律
⟹ 无新 NCA 件、trispace-state.json 不增殖、熔断日志不写。
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


@pytest.fixture()
def srv(tmp_path):
    return BridgeServer(tmp_path / "evidence", caller="test-client")


def _call(srv, name, args, rid=1):
    return srv.handle_line(_j({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                               "params": {"name": name, "arguments": args}}))


def _nca_files(ev):
    return list(Path(ev).glob("NCA-MCP-*.yaml"))


def _zero_consumption(ev_dir):
    return (not _nca_files(ev_dir)
            and not (Path(ev_dir) / ".nsfl-fuse.log").exists())


# ============ 断言集（正向） ============

def test_anonymous_reads_open(srv):
    """A1/R-2：匿名（无卡）三读可达——各一条读数。"""
    for i, (name, args) in enumerate([("nca:chain", {}), ("tdca:core", {}),
                                      ("nca:get", {"nca_id": "NOPE"})]):
        r = _call(srv, name, args, rid=i)
        assert "error" not in r, f"{name} 匿名被拒: {r}"
    r = _call(srv, "nca:get", {"nca_id": "NOPE"})
    assert "存证不存在" in r["result"]["content"][0]["text"]


def test_card_write_full_path(srv):
    """A2/A3/A4/A5 正向：持卡 → 四判全过 → 出 CERT → 落 SBX，件带 space_id/status。"""
    r = _call(srv, "tdca:echo", {"text": "hi", "agent_card": _card()})
    assert "error" not in r
    body = r["result"]["content"][0]["text"]
    assert "NSFL-CERT" in body and "space_id=SBX status=SBX-ACTIVE" in body
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    assert doc["space_id"] == "SBX" and doc["status"] == "SBX-ACTIVE"
    assert doc["Post-State"]["Path"].startswith("sbx:")
    assert doc["chain_ref"] == trispace.CHAIN_REF
    st = srv.state.agent(trispace.card_fingerprint(_card()))
    assert st["status"] == "SBX-ACTIVE" and st["cert"]["cert_id"].startswith("NSFL-CERT")


def test_cert_fields_and_validity(srv):
    """R-4：CERT 字段与有效期样例（默认 24h，可配）。"""
    _call(srv, "tdca:echo", {"text": "x", "agent_card": _card()})
    cert = srv.state.agent(trispace.card_fingerprint(_card()))["cert"]
    for k in ("cert_id", "subject", "basis", "judgments", "issued_at",
              "expires_at", "space_id", "status_on_issue"):
        assert k in cert, f"CERT 缺字段 {k}"
    assert cert["judgments"] == {"J1_NS-Type完整性": True, "J2_⊗覆盖度": True,
                                 "J3_法律负空间绝对化": True, "J4_最小化合": True}
    from datetime import datetime
    assert cert["expires_at"] > cert["issued_at"]


def test_chain_declaration_registered(srv):
    """A8/R-9：分链登记件在卷，relation 写明独立于主账。"""
    p = Path(srv.wm.dir) / "CHAIN-DECLARATION.yaml"
    assert p.is_file()
    body = p.read_text(encoding="utf-8")
    assert "chain_ref: TDCA-MCP-CHAIN-001" in body
    assert "分链登记" in body and "NCA-REGISTRY" in body


def test_chain_continuity_across_spaces(srv, tmp_path):
    """A8：跨空间同链 prev_nca 连续（SBX 件哈希链不回退）。"""
    for i in range(2):
        _call(srv, "tdca:echo", {"text": f"c{i}", "agent_card": _card()})
    chain = srv.wm.chain()
    assert len(chain) == 2 and len({c["Hash"] for c in chain}) == 2
    assert all(c["space_id"] == "SBX" for c in chain)


def test_promote_gate_parameterized(srv):
    """A6：出盒闸参数化占位——α 未置（采值未定）⟹ gate=HELD，⛔自拟映射。"""
    _call(srv, "tdca:echo", {"text": "p", "agent_card": _card()})
    g = srv.state.promote_gate(trispace.card_fingerprint(_card()), srv.config)
    assert g["gate"] == "HELD" and g["alpha"] is None
    assert g["alpha_threshold"] == 1.2 and g["human_signature_required"] is False


def test_operator_neutral_value(srv):
    """A9/R-10：Operator 中性值 anonymous（caller 直传，无强制身份采集）。"""
    r = _call(srv, "tdca:echo", {"text": "op", "agent_card": _card()})
    assert "anonymous" not in json.dumps(r, ensure_ascii=False)  # 桥不擅自命名
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    assert doc["Operator"] == "test-client"  # 由调用方载体决定，仓内 shim 取 anonymous


# ============ 对抗集 ============

def test_adversarial_anonymous_write_rejected_zero_consumption(srv, tmp_path):
    """A10-①/R-3：匿名写拒，码文案稳定，零消耗（无件/无状态/无熔断日志）。"""
    r = _call(srv, "tdca:echo", {"text": "no card here"})
    assert r["error"]["code"] == trispace.CODE_NO_CARD
    assert "AGENT_CARD_REQUIRED" in r["error"]["message"]
    assert "零消耗" in r["error"]["message"]
    assert _zero_consumption(srv.wm.dir)
    assert not (Path(srv.wm.dir) / "trispace-state.json").exists()


def test_adversarial_no_cert_no_sbx(srv):
    """A10-②：四判未过（J1 缺档）⟹ 无 CERT、状态留 NS-PENDING、零消耗。"""
    bad = _card()
    del bad["ns_types"]["approval_required"]           # J1 缺档
    r = _call(srv, "tdca:echo", {"text": "x", "agent_card": bad})
    assert r["error"]["code"] == trispace.CODE_JUDGMENT_FAIL
    assert "J1_NS-Type完整性" in r["error"]["message"]
    fp = trispace.card_fingerprint(bad)
    assert srv.state.agent(fp) is None                 # 未升 SBX
    assert _zero_consumption(srv.wm.dir)


def test_adversarial_j2_orphan_operator(srv):
    """J2：⊗操作符未归入三档 ⟹ FAIL（覆盖度缺口）。"""
    bad = _card(forbidden_operators=["发币", "洗钱通道"])
    r = _call(srv, "tdca:echo", {"text": "x", "agent_card": bad})
    assert r["error"]["code"] == trispace.CODE_JUDGMENT_FAIL
    assert "J2_⊗覆盖度" in r["error"]["message"] and "洗钱通道" in r["error"]["message"]


def test_adversarial_j3_exemption_language(srv):
    """J3a：absolute 档含豁免语 ⟹ 负空间被相对化，FAIL。"""
    bad = _card()
    bad["ns_types"]["absolute"] = ["发币（可审批豁免）"]
    r = _call(srv, "tdca:echo", {"text": "x", "agent_card": bad})
    assert r["error"]["code"] == trispace.CODE_JUDGMENT_FAIL
    assert "J3_法律负空间绝对化" in r["error"]["message"]


def test_adversarial_j4_overdesign(srv):
    """J4：实参含未声明字段 ⟹ 过度设计 FAIL。"""
    r = _call(srv, "tdca:echo",
              {"text": "x", "undeclared_payload": {"a": 1}, "agent_card": _card()})
    assert r["error"]["code"] == trispace.CODE_JUDGMENT_FAIL
    assert "J4_最小化合" in r["error"]["message"] and "undeclared_payload" in r["error"]["message"]


def test_adversarial_ban_on_legal_negative_space(srv):
    """A10-⑤/R-7：触法律负空间 ⟹ SBX-BANNED + 熔断 NCA；读路不受影响的。"""
    r = _call(srv, "tdca:echo", {"text": "我们计划发币募资", "agent_card": _card()})
    assert r["result"]["isError"] is True
    assert "SBX-BANNED" in r["result"]["content"][0]["text"]
    fp = trispace.card_fingerprint(_card())
    assert srv.state.agent(fp)["status"] == trispace.ST_SBX_BANNED
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[0].read_text(encoding="utf-8"))
    assert doc["Operation-Type"] == "FuseReject" and doc["status"] == "SBX-BANNED"
    assert doc["space_id"] == "SBX"
    # 封禁后写路拒（零消耗不再落件），读路仍开
    n = len(_nca_files(srv.wm.dir))
    r2 = _call(srv, "tdca:echo", {"text": "again", "agent_card": _card()})
    assert r2["error"]["code"] == trispace.CODE_BANNED
    assert len(_nca_files(srv.wm.dir)) == n
    r3 = _call(srv, "nca:chain", {})
    assert "error" not in r3


def test_adversarial_suspend_on_boundary_cross(srv):
    """A10-④/R-7：越界（实参触及 scene_limited 档）⟹ 拒 + SBX-SUSPENDED + 熔断 NCA + 限期重整。"""
    _call(srv, "tdca:echo", {"text": "first ok", "agent_card": _card()})
    r = _call(srv, "tdca:echo", {"text": "涉及跨境数据流转", "agent_card": _card()})
    assert r["result"]["isError"] is True
    assert "SBX-SUSPENDED" in r["result"]["content"][0]["text"]
    fp = trispace.card_fingerprint(_card())
    a = srv.state.agent(fp)
    assert a["status"] == "SBX-SUSPENDED" and a["suspended_until"]
    doc = yaml.safe_load(_nca_files(srv.wm.dir)[-1].read_text(encoding="utf-8"))
    assert doc["Operation-Type"] == "FuseReject" and doc["status"] == "SBX-SUSPENDED"
    # 停手期内写拒
    r2 = _call(srv, "tdca:echo", {"text": "more", "agent_card": _card()})
    assert r2["error"]["code"] == trispace.CODE_SUSPENDED


def test_adversarial_same_cert_redrive_semantics(srv):
    """A10-③：同号重投语义——同卡再投是正常业务写（每次落新件、链连续、
    状态保持 SBX-ACTIVE，不重复出号扰动状态机）。"""
    fp = trispace.card_fingerprint(_card())
    for i in range(2):
        r = _call(srv, "tdca:echo", {"text": f"redrive {i}", "agent_card": _card()})
        assert "error" not in r
    files = _nca_files(srv.wm.dir)
    assert len(files) == 2
    ids = {yaml.safe_load(p.read_text(encoding="utf-8"))["NCA-ID"] for p in files}
    assert len(ids) == 2                                   # 同号重投 = 两件独立存证
    a = srv.state.agent(fp)
    assert a["status"] == "SBX-ACTIVE" and a["writes"] == 2  # 写计数幂等累计
    chain = srv.wm.chain()
    assert len(chain) == 2 and len({c["Hash"] for c in chain}) == 2


def test_adversarial_rate_limit_zero_consumption(srv, tmp_path, monkeypatch):
    """R-6：限流参数可配——per=1 时第二写即拒且零消耗。"""
    monkeypatch.setenv("TDCA_TRISPACE_RATE_PER_MIN", "1")
    srv.config = trispace.load_config()
    srv.limiter = trispace.RateLimiter(srv.config)
    _call(srv, "tdca:echo", {"text": "one", "agent_card": _card()})
    r = _call(srv, "tdca:echo", {"text": "two", "agent_card": _card()})
    assert r["error"]["code"] == trispace.CODE_RATE_LIMITED
    assert len(_nca_files(srv.wm.dir)) == 1     # 被拒那次零消耗


def test_adversarial_bad_card_shape_zero_consumption(srv):
    """A2：卡非对象/超 4KB ⟹ 视同未持卡，零消耗。"""
    r = _call(srv, "tdca:echo", {"text": "x", "agent_card": "not-a-dict"})
    assert r["error"]["code"] == trispace.CODE_NO_CARD
    big = _card()
    big["padding"] = "x" * 5000
    r = _call(srv, "tdca:echo", {"text": "x", "agent_card": big})
    assert r["error"]["code"] == trispace.CODE_NO_CARD
    assert _zero_consumption(srv.wm.dir)


def test_adversarial_suspension_expiry_restores(srv, monkeypatch):
    """A7 回退：限期重整届满 ⟹ 状态机自动回 SBX-ACTIVE（⛔改链数据）。"""
    monkeypatch.setenv("TDCA_TRISPACE_SUSPEND_HOURS", "0")
    srv.config = trispace.load_config()
    _call(srv, "tdca:echo", {"text": "涉及跨境数据", "agent_card": _card()})
    fp = trispace.card_fingerprint(_card())
    assert srv.state.agent(fp)["status"] == "SBX-SUSPENDED"
    r = _call(srv, "tdca:echo", {"text": "retry", "agent_card": _card()})
    # 0 小时限期：下一写即视为重整届满，恢复 SBX-ACTIVE 走完整四判
    assert srv.state.agent(fp)["status"] == "SBX-ACTIVE"
    assert "error" not in r
