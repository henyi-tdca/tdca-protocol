# -*- coding: utf-8 -*-
"""AUDIT-ANCHOR-001 断言集（≥6 条，逐条可机验）。

断言语义（输入 → 期望 → 实测）：
  A-1 规范序列化：规格 §2.3 示例逐字节复现（键序/分隔符/转义）；
  A-2 前缀域分离：叶子 0x00／内部 0x01／日锚 0x02 缺一即不合规；
  A-3 Merkle 奇数复制与叶子序：3 叶根＝node(node(0,1),node(2,2))，输入乱序同根；
  A-4 日锚链与缺日：none 日双 null 不入链，后日 prev 承上一 anchored 日；
  A-5 排除项物理隔离：nca_watermark/data_nature/note/库内 id/内部编号 ⛔ 入规范化；
  A-6 更正状态机：新版行成、旧版原样、链保持完整、锚值必变；
  A-7 分页真生效：limit/cursor 全遍历无重无漏、非法 limit/cursor fail-closed；
  A-8 取值规范化：amount 十进制 2 位、拒千分位/科学计数法/浮点，ts 6 位补零转 UTC。
"""
import base64
import hashlib
import json

import pytest

from db import get_session, get_sessionmaker
from db import models as M
import ledger_anchor_ops as LA


def _ensure_anchor_routes():
    """anchors* 在测试面显式挂载（等同置旗 TDCA_AUDIT_ANCHOR_INTERNAL=1 之实例）。"""
    from app import app
    paths = {getattr(r, "path", "") for r in app.routes}
    if "/api/v1/audit/anchors" not in paths:
        app.include_router(LA.router)
    return app


_NOW = "2026-08-21T00:00:00Z"


def _add_event(eid, ts, amount=100):
    with get_sessionmaker().begin() as s:
        s.add(M.TaxEvent(event_id=eid, type="dispatch_tax", agent_id="AGENT-A",
                         call_id="CALL-A", amount=amount, ts=ts,
                         data_provenance="simulated"))


def _clean(prefix):
    with get_sessionmaker().begin() as s:
        for r in s.query(M.TaxEvent).all():
            if r.event_id.startswith(prefix):
                s.delete(r)
        for r in s.query(M.AuditDayAnchor).all():
            if r.date.startswith("2026-08-2"):
                s.delete(r)
        for r in s.query(M.AuditBatchAnchor).all():
            if r.date.startswith("2026-08-2"):
                s.delete(r)


# ---------------------------------------------------------------------------
# A-1 规范序列化
# ---------------------------------------------------------------------------

def test_a1_canonical_serialization_matches_spec_example():
    ev = {"event_id": "EVT-...", "type": "transaction_fee",
          "ts": "2026-08-20T15:50:20.486926Z", "amount": "15.00", "currency": "CNY"}
    got = LA.canonical_json_bytes(LA.canonical_event(ev)).decode("utf-8")
    expect = ('{"amount":"15.00","currency":"CNY","event_id":"EVT-...",'
              '"ts":"2026-08-20T15:50:20.486926Z","type":"transaction_fee"}')
    assert got == expect
    # 转义：引号与控制字符按 RFC 8785；非 ASCII 原样（⛔ \\uXXXX 逃逸）
    ev2 = {"event_id": "EVT-\"引\"", "type": "t\nx", "ts": ev["ts"],
           "amount": "0.05", "currency": ""}
    got2 = LA.canonical_json_bytes(LA.canonical_event(ev2)).decode("utf-8")
    assert "\\n" in got2 and '\\"' in got2 and "引" in got2


# ---------------------------------------------------------------------------
# A-2 前缀域分离
# ---------------------------------------------------------------------------

def test_a2_prefix_domain_separation():
    ev = {"event_id": "EVT-P", "type": "t", "ts": "2026-08-20T00:00:00Z",
          "amount": "1.00", "currency": "CNY"}
    canon = LA.canonical_json_bytes(LA.canonical_event(ev))
    leaf = LA.leaf_digest(ev)
    assert leaf == hashlib.sha256(b"\x00" + canon).digest()
    assert leaf != hashlib.sha256(canon).digest()          # ⛔ 省前缀
    l, r = LA.leaf_digest({**ev, "event_id": "EVT-L"}), LA.leaf_digest({**ev, "event_id": "EVT-R"})
    node = LA.merkle_root([("EVT-L", l), ("EVT-R", r)])
    assert node == hashlib.sha256(b"\x01" + l + r).digest()
    assert node != hashlib.sha256(l + r).digest()
    da = LA.day_anchor_digest("2026-08-20", "", [("B2026-08-20", node, 2)])
    assert da != hashlib.sha256(LA.canonical_json_bytes(
        LA.day_header("2026-08-20", "", [("B2026-08-20", node, 2)]))).digest()


# ---------------------------------------------------------------------------
# A-3 Merkle 奇数复制与叶子序
# ---------------------------------------------------------------------------

def _mk(eid):
    return LA.leaf_digest({"event_id": eid, "type": "t", "ts": "2026-08-20T00:00:00Z",
                           "amount": "1.00", "currency": ""})

def test_a3_merkle_odd_dup_and_order():
    l0, l1, l2 = _mk("EVT-0"), _mk("EVT-1"), _mk("EVT-2")
    h = lambda a, b: hashlib.sha256(b"\x01" + a + b).digest()
    expect = h(h(l0, l1), h(l2, l2))
    got = LA.merkle_root([("EVT-2", l2), ("EVT-0", l0), ("EVT-1", l1)])   # 乱序入
    assert got == expect
    assert LA.merkle_root([("EVT-0", l0), ("EVT-1", l1)]) != expect       # 复制生效


# ---------------------------------------------------------------------------
# A-4 日锚链与缺日
# ---------------------------------------------------------------------------

def test_a4_chain_and_none_day():
    try:
        _add_event("EVT-A4-1", "2026-08-21T01:00:00Z")
        _add_event("EVT-A4-2", "2026-08-23T01:00:00Z")
        _add_event("EVT-A4-3", "2026-08-23T02:00:00Z")
        with get_session() as s:
            d1 = LA.publish_day(s, "2026-08-21", _NOW); s.commit()
            d2 = LA.publish_day(s, "2026-08-22", _NOW); s.commit()
            d3 = LA.publish_day(s, "2026-08-23", _NOW); s.commit()
        assert d1["status"] == "anchored" and d1["prev_day_anchor"] == ""      # 首日空串
        assert d2["status"] == "none" and d2["day_anchor"] is None \
            and d2["prev_day_anchor"] is None                                  # 缺日双 null
        assert d3["status"] == "anchored" and d3["prev_day_anchor"] == d1["day_anchor"]
        with get_session() as s:
            assert LA.verify_chain(s) == []
    finally:
        _clean("EVT-A4-")


# ---------------------------------------------------------------------------
# A-5 排除项物理隔离
# ---------------------------------------------------------------------------

def test_a5_excluded_fields_never_canonicalized():
    full = {"event_id": "EVT-X", "type": "t", "ts": "2026-08-20T00:00:00Z",
            "amount": "2.00", "currency": "CNY",
            "nca_watermark": "sha256:aaaa", "data_nature": "mixed", "note": "GSEQ-1234",
            "id": 7, "internal_no": "NCA-20260820"}
    bare = {k: full[k] for k in ("event_id", "type", "ts", "amount", "currency")}
    c_full, c_bare = LA.canonical_event(full), LA.canonical_event(bare)
    assert set(c_full) == {"amount", "currency", "event_id", "ts", "type"}
    assert c_full == c_bare
    assert LA.canonical_json_bytes(c_full) == LA.canonical_json_bytes(c_bare)


# ---------------------------------------------------------------------------
# A-6 更正状态机
# ---------------------------------------------------------------------------

def test_a6_correction_state_machine():
    try:
        _add_event("EVT-A6-1", "2026-08-21T05:00:00Z")
        with get_session() as s:
            v1 = LA.publish_day(s, "2026-08-21", _NOW); s.commit()
        _add_event("EVT-A6-2", "2026-08-21T06:00:00Z")     # 同日增事件 ⟹ 锚必变
        with get_sessionmaker().begin() as s:
            out = LA.correct_day(s, "2026-08-21", _NOW)
        assert out[0]["version"] == 2 and out[0]["status"] == "anchored"
        assert out[0]["day_anchor"] != v1["day_anchor"]
        with get_session() as s:
            old = s.get(M.AuditDayAnchor, ("2026-08-21", 1))
            new = s.get(M.AuditDayAnchor, ("2026-08-21", 2))
            assert old is not None and old.day_anchor == v1["day_anchor"]   # 旧版原样
            assert new is not None and new.day_anchor == out[0]["day_anchor"]
            assert LA.verify_chain(s) == []
        with pytest.raises(ValueError):
            with get_session() as s:
                LA.correct_day(s, "2026-08-25", _NOW)   # 未发布日 ⛔ 更正（须走正常发布）
    finally:
        _clean("EVT-A6-")


# ---------------------------------------------------------------------------
# A-7 分页真生效（接口面）
# ---------------------------------------------------------------------------

def test_a7_pagination_real():
    app = _ensure_anchor_routes()
    from fastapi.testclient import TestClient
    c = TestClient(app)
    try:
        for i in range(5):
            _add_event(f"EVT-A7-{i}", f"2026-08-24T0{i}:00:00Z", amount=100 * (i + 1))
        seen, cursor, pages = [], "", 0
        while True:
            r = c.get("/api/v1/audit/ledger-public", params={"limit": 2, "cursor": cursor})
            assert r.status_code == 200
            body = r.json()["data"]
            pages += 1
            assert len(body["events"]) <= 2                       # limit 真生效
            for e in body["events"]:
                if e["event_id"].startswith("EVT-A7-"):
                    seen.append(e["event_id"])
            cursor = body["next_cursor"]
            if not cursor:
                break
            raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
            assert set(json.loads(raw)) == {"ts", "event_id"}       # 不透明复合位标
        assert pages == -(-r.json()["data"]["total"] // 2)          # 全库分页（含种子件），页数随 total
        assert sorted(seen) == [f"EVT-A7-{i}" for i in range(5)]
        assert len(set(seen)) == 5                                  # 无重无漏
        assert r.json()["data"]["total"] >= 5                       # total 与游标无关
        assert c.get("/api/v1/audit/ledger-public?limit=0").status_code == 400
        assert c.get("/api/v1/audit/ledger-public?limit=501").status_code == 400
        assert c.get("/api/v1/audit/ledger-public?cursor=!!not-base64!!").status_code == 400
    finally:
        _clean("EVT-A7-")


# ---------------------------------------------------------------------------
# A-8 取值规范化
# ---------------------------------------------------------------------------

def test_a8_value_normalization():
    assert LA.normalize_amount("15") == "15.00"
    assert LA.normalize_amount("15.00") == "15.00"
    assert LA.normalize_amount("-5") == "-5.00"
    assert LA.normalize_amount("-0.05") == "-0.05"
    assert LA.normalize_ts("2026-08-20T15:50:20Z") == "2026-08-20T15:50:20.000000Z"
    assert LA.normalize_ts("2026-08-21T00:30:00+08:00") == "2026-08-20T16:30:00.000000Z"
    for bad in ("1,500.00", "1e2", "0.001"):
        with pytest.raises(ValueError):
            LA.normalize_amount(bad)
    with pytest.raises(ValueError):
        LA.normalize_amount(0.5)                                  # ⛔ 浮点入参
    assert LA.day_of("2026-08-20T16:30:00Z") == "2026-08-21"      # +08 日界跨日
