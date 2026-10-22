# -*- coding: utf-8 -*-
"""通道对外补齐 C 测试（效用保金；L1SI166-CHANNEL-GAP-001 项 C ＋ 裁定项三之 2／Q-2）。

覆盖：
  C-1  押付正例：登记主体本人押付 → 201；event_no SUD- 前缀；NCA 落链
       （AGENT_CHANNEL_DEPOSIT_PAID）；回执有效额＝Σ押付−Σ没收−Σ退还
  C-2  权限：匿名 401；非本人 403（人类签名权不可绕）
  C-3  fail-closed 入参：零/负额 → 400；缺 mou_ref → 400（计量非凭空）
  C-4  三态处置：frozen（owner 可）／refunded（owner 可）／confiscated
       （founder-only：owner 403、founder 201 且 pool=保险金池）；各落 NCA
  C-5  处置超额（>当前有效保金）→ 400（fail-closed）
  C-6  余额数学：押 10 → 有效 10；冻 4 → 有效仍 10、冻结单列 4；
       退 3 → 有效 7；没收 2 → 有效 5（冻结不减有效额）
  C-7  沙盒准入闸：无保金 → 403 DEPOSIT_REQUIRED（fail-closed 拒入盒）；
       有保金 → 200 过闸（与六步硬序同向叠加、⛔ 不造旁路）
  C-8  配置缺省：阈值未配置 → 503 DEPOSIT_CONFIG_MISSING（⛔ 忘配＝开门）
  C-9  实况端：GET …/deposits 逐笔事件＋有效额＋冻结额＋阈值回显
"""
import pytest
from fastapi.testclient import TestClient

from agent_channel_ops import CONTRACT_VERSION, _REGISTERED_PACKAGE_HASHES_16
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "GapC-2026"
_SEQ = {"n": 0}
_GOOD_HASH = _REGISTERED_PACKAGE_HASHES_16[0]


@pytest.fixture(autouse=True)
def _fresh():
    import api_v1
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()
    yield
    api_v1._register_hits.clear()


def _auth() -> tuple[str, dict]:
    _SEQ["n"] += 1
    name = f"gc{_SEQ['n']:03d}"
    r = client.post("/api/v1/auth/register",
                    json={"username": name, "password": _PW,
                          "agree_contract": True, "contract_version": "V1.0",
                          "anchor_kind": "notifier", "anchor_evidence_ref": "t"})
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/auth/login", json={"username": name, "password": _PW})
    assert r.status_code == 200, r.text[:300]
    with get_session() as s:   # 补锚（等价核验落点，同 gap_b 惯例）
        a = s.get(M.UserAnchor, name)
        a.tier_state = "已补"
        a.verified_at = "2026-10-23T00:00:00Z"
        a.verifier = "test-fixture"
        s.commit()
    return name, {"Authorization": r.json()["data"]["token"]}


def _founder() -> dict:
    """人类裁决（founder 会话）——没收权落点（照抄 b4 造法）。"""
    from datetime import datetime, timezone
    from auth import hash_password
    name = "founder-gap-c"
    now = datetime.now(timezone.utc).isoformat()
    ph, salt, iters = hash_password(f"pw-{name}")
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, name)
        if u is None:
            s.add(M.User(username=name, password_hash=ph, salt=salt,
                         iterations=iters, role="founder", created_at=now))
        else:
            u.role = "founder"
    r = client.post("/api/v1/auth/login", json={"username": name, "password": f"pw-{name}"})
    assert r.status_code == 200, r.text[:300]
    return {"Authorization": r.json()["data"]["token"]}


_REG_SEQ = {"n": 0}


def _register(hdr: dict) -> str:
    """登记（⛔ 不代押保金——C 项测试须自控保金有无，故不用 b2/b3/gap_b 代押版）。"""
    _REG_SEQ["n"] += 1
    tag = f"gc-{_REG_SEQ['n']:03d}"
    r = client.post("/api/v1/agent-channel/register",
                    json={"channel_type": "ANCHOR",
                          "device": f"C路设备-{tag}", "compute": "C路算力-x",
                          "protocol": "C路协议-x", "role": "C路角色-x",
                          "knowledge": "C路知识-x", "permission_ttl": "C路权限时效-x",
                          "root_token_ref": "root-token://gapc/1"}, headers=hdr)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["reg_no"]


def _pay(reg_no: str, hdr: dict, amount: int = 10, mou_ref: str = "mou://gapc/1") -> object:
    return client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                       json={"amount_mou": amount, "mou_ref": mou_ref}, headers=hdr)


def _act(reg_no: str, hdr: dict, action: str, amount: int, note: str = "处置测试") -> object:
    return client.post(f"/api/v1/agent-channel/{reg_no}/deposit-actions",
                       json={"action": action, "amount_mou": amount, "note": note},
                       headers=hdr)


def _to_ns_review_passed(reg_no: str, hdr: dict) -> None:
    """①②③ 走通至沙盒门前（④ 由用例自调，以测保金闸）。"""
    r = client.post("/api/v1/agent-channel/protocol-load",
                    json={"reg_no": reg_no, "contract_version": CONTRACT_VERSION,
                          "package_sha256_16": _GOOD_HASH}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/token",
                    json={"reg_no": reg_no, "action": "issue"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/api/v1/agent-channel/ns-review",
                    json={"reg_no": reg_no, "boundary_ref": "nsfl://gapc/1",
                          "adversarial_set_ref": "nsfl://gapc/adv1",
                          "scene_scope": "scene://gapc/demo"}, headers=hdr)
    assert r.status_code == 200, r.text[:300]


def _sandbox(reg_no: str, hdr: dict, run_ref: str = "run://gapc/0001") -> object:
    return client.post("/api/v1/agent-channel/sandbox",
                       json={"reg_no": reg_no, "sea_elements_ref": "sea://gapc/1",
                             "sandbox_run_ref": run_ref, "result": "passed"},
                       headers=hdr)


# ---------------------------------------------------------------- C-1 押付正例
def test_pay_positive_event_and_nca():
    who, hdr = _auth()
    reg_no = _register(hdr)
    r = _pay(reg_no, hdr, amount=10)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["paid"] is True and d["amount_mou"] == 10
    assert d["effective_mou"] == 10                      # Σ押付−Σ没收−Σ退还
    assert d["event_no"].startswith("SUD-") and d["nca_ref"]
    with get_session() as s:
        row = s.get(M.SiteAgentUtilityDeposit, d["event_no"])
        assert row is not None and row.action == "paid" and row.amount_mou == 10
        assert row.actor == who and row.mou_ref == "mou://gapc/1"
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_DEPOSIT_PAID"


# ---------------------------------------------------------------- C-2 权限
def test_pay_anon_401_and_non_owner_403():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _pay(reg_no, hdr).status_code == 201
    r2 = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                     json={"amount_mou": 3, "mou_ref": "mou://gapc/x"})
    assert r2.status_code == 401
    _, hdr2 = _auth()
    r3 = _pay(reg_no, hdr2, amount=3)
    assert r3.status_code == 403 and "人类签名权" in r3.text


# ---------------------------------------------------------------- C-3 fail-closed 入参
def test_pay_fail_closed_amount_and_mou_ref():
    _, hdr = _auth()
    reg_no = _register(hdr)
    for body in ({"amount_mou": 0, "mou_ref": "mou://gapc/1"},
                 {"amount_mou": -5, "mou_ref": "mou://gapc/1"},
                 {"amount_mou": 5, "mou_ref": "  "},
                 {"amount_mou": 5}):
        r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits", json=body, headers=hdr)
        assert r.status_code == 400, (body, r.text[:300])
    r = client.post(f"/api/v1/agent-channel/{reg_no}/deposits",
                    json={"amount_mou": 5, "mou_ref": "mou://gapc/1",
                          "surprise": 1}, headers=hdr)   # extra=forbid
    assert r.status_code == 422


# ---------------------------------------------------------------- C-4 三态处置
def test_actions_three_states_and_confiscate_founder_only():
    who, hdr = _auth()
    reg_no = _register(hdr)
    assert _pay(reg_no, hdr, amount=10).status_code == 201
    # frozen：登记主体本人可
    r = _act(reg_no, hdr, "frozen", 4)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["action"] == "frozen" and d["effective_mou"] == 10   # 冻结不减有效额
    # refunded：登记主体本人可
    r = _act(reg_no, hdr, "refunded", 2)
    assert r.status_code == 201, r.text[:400]
    assert r.json()["data"]["effective_mou"] == 8
    # confiscated：owner 自操作 → 403（没收权在人类裁决）
    r = _act(reg_no, hdr, "confiscated", 1)
    assert r.status_code == 403
    # confiscated：founder → 201 且入保险金池
    fhdr = _founder()
    r = _act(reg_no, fhdr, "confiscated", 1)
    assert r.status_code == 201, r.text[:400]
    d = r.json()["data"]
    assert d["action"] == "confiscated" and d["effective_mou"] == 7
    with get_session() as s:
        ev = s.get(M.SiteAgentUtilityDeposit, d["event_no"])
        assert ev is not None and ev.pool == "保险金池" and ev.actor != who
        nca = s.get(M.NcaChain, d["nca_ref"])
        assert nca is not None and nca.action == "AGENT_CHANNEL_DEPOSIT_CONFISCATED"


# ---------------------------------------------------------------- C-5 处置超额
def test_action_overdraft_400():
    _, hdr = _auth()
    reg_no = _register(hdr)
    assert _pay(reg_no, hdr, amount=5).status_code == 201
    for action in ("frozen", "refunded"):
        r = _act(reg_no, hdr, action, 6)
        assert r.status_code == 400 and "超额" in r.text
    fhdr = _founder()
    r = _act(reg_no, fhdr, "confiscated", 6)
    assert r.status_code == 400 and "超额" in r.text
    # 非法 action 词 → 400
    r = _act(reg_no, hdr, "paid", 1)
    assert r.status_code == 400


# ---------------------------------------------------------------- C-6 余额数学
def test_balance_math_effective_and_frozen_separate():
    _, hdr = _auth()
    reg_no = _register(hdr)
    _pay(reg_no, hdr, amount=10)
    _pay(reg_no, hdr, amount=5)                       # 两笔押付：Σ=15
    _act(reg_no, hdr, "frozen", 4)                    # 冻结单列
    _act(reg_no, hdr, "refunded", 3)                  # 退 3
    _act(reg_no, _founder(), "confiscated", 2)        # 没收 2 入池
    with get_session() as s:
        from agent_channel_deposit_ops import effective_deposit, frozen_amount
        assert effective_deposit(s, reg_no) == 15 - 3 - 2          # =10
        assert frozen_amount(s, reg_no) == 4                        # 单列不减
    r = client.get(f"/api/v1/agent-channel/{reg_no}/deposits", headers=hdr)
    assert r.status_code == 200, r.text[:400]
    d = r.json()["data"]
    assert d["effective_mou"] == 10 and d["frozen_mou"] == 4
    assert d["required_min_mou"] == 1                             # conftest 阈值
    assert len(d["events"]) == 5                                  # 逐笔事件账


# ---------------------------------------------------------------- C-7 沙盒准入闸
def test_sandbox_gate_deposit_required_then_open():
    _, hdr = _auth()
    reg_no = _register(hdr)
    _to_ns_review_passed(reg_no, hdr)
    # 无保金：fail-closed 拒入盒
    r = _sandbox(reg_no, hdr)
    assert r.status_code == 403 and "DEPOSIT_REQUIRED" in r.text
    # 押付后：同向叠加过闸（六步硬序不动、⛔ 不造旁路）
    assert _pay(reg_no, hdr, amount=5).status_code == 201
    r = _sandbox(reg_no, hdr, run_ref="run://gapc/0002")
    assert r.status_code == 200, r.text[:400]
    # 有效额跌破阈值（全额没收）→ 再申报沙盒即拒（即时 fail-closed）
    _act(reg_no, _founder(), "confiscated", 5)
    r = _sandbox(reg_no, hdr, run_ref="run://gapc/0003")
    assert r.status_code == 403 and "DEPOSIT_REQUIRED" in r.text


# ---------------------------------------------------------------- C-8 配置缺省
def test_sandbox_gate_config_missing_503(monkeypatch):
    monkeypatch.delenv("TDCA_UTILITY_DEPOSIT_MIN_MOU", raising=False)
    _, hdr = _auth()
    reg_no = _register(hdr)
    _pay(reg_no, hdr, amount=5)
    _to_ns_review_passed(reg_no, hdr)
    r = _sandbox(reg_no, hdr)
    assert r.status_code == 503 and "DEPOSIT_CONFIG_MISSING" in r.text
    # 阈值语义：0/非法值同样 ⟹ 闸关（⛔ 忘配＝开门）
    monkeypatch.setenv("TDCA_UTILITY_DEPOSIT_MIN_MOU", "0")
    r = _sandbox(reg_no, hdr)
    assert r.status_code == 503
    monkeypatch.setenv("TDCA_UTILITY_DEPOSIT_MIN_MOU", "abc")
    r = _sandbox(reg_no, hdr)
    assert r.status_code == 503


# ---------------------------------------------------------------- C-9 实况端
def test_deposit_state_endpoint_events_echo():
    _, hdr = _auth()
    reg_no = _register(hdr)
    _pay(reg_no, hdr, amount=7)
    _act(reg_no, hdr, "frozen", 2)
    r = client.get(f"/api/v1/agent-channel/{reg_no}/deposits", headers=hdr)
    assert r.status_code == 200, r.text[:400]
    d = r.json()["data"]
    assert d["reg_no"] == reg_no and d["channel_type"] == "ANCHOR"
    assert d["effective_mou"] == 7 and d["frozen_mou"] == 2
    acts = [e["action"] for e in d["events"]]
    assert acts == ["paid", "frozen"]                             # 逐笔有序
    assert all(e["event_no"].startswith("SUD-") for e in d["events"])
    r2 = client.get(f"/api/v1/agent-channel/{reg_no}/deposits")   # 匿名 → 401
    assert r2.status_code == 401
