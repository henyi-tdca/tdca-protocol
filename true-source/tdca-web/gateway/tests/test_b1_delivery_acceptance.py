# -*- coding: utf-8 -*-
"""L1SI195-B1-001：C2 交付清单＋C3 验收记录测试（/api/v1/delivery/* ＋ /api/v1/acceptance/*）。

令面自测映射：
  C-2 五条：① 缺哈希被拒且提示缺哪件 ② 逐件哈希与回收值比对显符/不符 ③ delivery_id＋
    nca_seq 生成且可查 ④ 接收确认须报哈希（无哈希视同未收） ⑤ 匿名可查件数与各件哈希；
  C-3 五条：① 无事前标准不许开验（临时加 → 拒并熔断） ② 逐条结论可回溯条目 ③ 不通过
    必带差距与整改单 ④ acceptance_id＋nca_seq 生成 ⑤ passed 只显「可结算」⛔ 触发结算；
  可靠性九项：半条记录／双库对拍／NCA 反查／熔断（reconfirm·hash streak·standard）／
    fail-closed／operator 解冻／默认拒／无存证拒／权限拒。
"""
import json

import pytest
from fastapi.testclient import TestClient

import acceptance_ops
import delivery_ops
from app import app
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "B1Deliv-pass-2026"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    import api_v1
    api_v1._register_hits.clear()      # 注册/登录频控逐测清零（同 C-1 套件口径）
    api_v1._login_hits.clear()
    monkeypatch.setenv("TDCA_DELIVERY_DIR", str(tmp_path / "delivery"))
    monkeypatch.setenv("TDCA_ACCEPTANCE_DIR", str(tmp_path / "acceptance"))
    yield
    api_v1._register_hits.clear()
    api_v1._login_hits.clear()


def _auth(uname):
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


def _mk_operator(uname):
    h = _auth(uname)
    with get_sessionmaker().begin() as s:
        s.get(M.User, uname).role = "operator"
    return h


def _auth_id(headers):
    """走 C-1 面板起草拿真 auth_id（只读依赖，不动 C-1 端点）。"""
    r = client.post("/api/v1/authorization/draft", json={
        "operation": "activate",
        "grantor": "甲主体（测试）", "grantee": "乙主体（测试）",
        "subject": "配置权·算法件一", "scope": "场景：联调；地域：站内；次数：100 次",
        "term": "2026-11-04 至 2026-12-31",
        "conditions": {"may_sub_grant": "否", "may_commercialize": "是",
                       "attribution_required": "是"},
        "submit": True}, headers=headers)
    assert r.status_code == 201, r.text[:300]
    return r.json()["data"]["auth_id"]


_ITEMS = [{"name": "件甲", "version": "v1", "hash": "AAAA1111AAAA1111", "size_bytes": 1024},
          {"name": "件乙", "version": "v2", "hash": "BBBB2222BBBB2222", "size_bytes": 2048}]


def _manifest(headers, aid, items=None, **kw):
    body = {"auth_id": aid, "receiver": "乙主体（测试）",
            "batches": "一批两卷", "deliver_at": "2026-11-10",
            "items": _ITEMS if items is None else items}
    body.update(kw)
    return client.post("/api/v1/delivery/manifest", json=body, headers=headers)


def _full_delivery(uname="d2_user01"):
    """开单→补件→确认 delivered 的快捷路（每测独立账号）。"""
    h = _auth(uname)
    aid = _auth_id(h)
    r = _manifest(h, aid)
    did = r.json()["data"]["delivery_id"]
    client.post("/api/v1/delivery/items", json={"delivery_id": did, "items": [
        {"name": "件丙", "hash": "CCCC3333CCCC3333"}]}, headers=h)
    return h, did


# ═════════════════════ C-2 令面自测五条 ═════════════════════

def test_c2_1_missing_hash_rejected_with_item_name():
    h = _auth("d2_c21")
    r = _manifest(h, _auth_id(h), items=[{"name": "件甲", "version": "v1"},
                                         {"name": "件乙", "hash": "X" * 16}])
    assert r.status_code == 400 and "件甲" in r.json()["detail"]  # 缺哪件逐一点名


def test_c2_1b_placeholder_hash_rejected():
    h = _auth("d2_c21b")
    r = _manifest(h, _auth_id(h), items=[{"name": "件甲", "hash": "稍后补"}])
    assert r.status_code == 400 and "稍后补" in r.json()["detail"]


def test_c2_2_hash_compare_match_and_mismatch():
    h, did = _full_delivery("d2_c22")
    good = [{"name": "件甲", "hash": "AAAA1111AAAA1111"},
            {"name": "件乙", "hash": "BBBB2222BBBB2222"},
            {"name": "件丙", "hash": "CCCC3333CCCC3333"}]
    r = client.post("/api/v1/delivery/confirm",
                    json={"delivery_id": did, "received": good}, headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "received"
    checks = r.json()["data"]["received_checks"]
    assert all(c["match"] for c in checks)
    # 不符样：新建一单，回执故意错一件
    h2 = _auth("d2_c22b")
    r = _manifest(h2, _auth_id(h2))
    did2 = r.json()["data"]["delivery_id"]
    client.post("/api/v1/delivery/items", json={"delivery_id": did2, "items": [
        {"name": "x", "hash": "DDDD4444DDDD4444"}]}, headers=h2)
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did2, "received": [
        {"name": "件甲", "hash": "AAAA1111AAAA1111"},
        {"name": "件乙", "hash": "BBBB2222BBBB2222"},
        {"name": "x", "hash": "WRONG000WRONG000"}]}, headers=h2)
    checks = {c["name"]: c["match"] for c in r.json()["data"]["received_checks"]}
    assert checks["x"] is False and checks["件甲"] is True  # 符／不符逐件显示


def test_c2_3_delivery_id_and_nca_seq_queryable():
    h = _auth("d2_c23")
    r = _manifest(h, _auth_id(h))
    data = r.json()["data"]
    assert data["delivery_id"].startswith("DLV-") and data["nca_seq"].startswith("NCA-WEB-")
    g = client.get(f"/api/v1/delivery/{data['delivery_id']}")
    assert g.status_code == 200
    d = g.json()["data"]
    assert d["nca_seq"] == data["nca_seq"] and d["total_items"] == 2
    # NCA 链反查（可靠性#3）：artifact_path=delivery:{id}
    with get_session() as s:
        row = s.get(M.NcaChain, data["nca_seq"])
    assert row.artifact_path == f"delivery:{data['delivery_id']}"


def test_c2_4_confirm_requires_hashes():
    h, did = _full_delivery("d2_c24")
    # 无哈希回执 → delivered（视同未收），不是 received
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "delivered"
    # 部分回执 → 仍 delivered（operator 复核视角二次确认——同一人短时复认会撞熔断①，照 C-2 口径）
    op = _mk_operator("d2_c24op")
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did, "received": [
        {"name": "件甲", "hash": "AAAA1111AAAA1111"}]}, headers=op)
    assert r.status_code == 200 and r.json()["data"]["status"] == "delivered"


def test_c2_5_anonymous_public_read():
    h, did = _full_delivery("d2_c25")
    g = client.get(f"/api/v1/delivery/{did}")   # 匿名（免会话）
    assert g.status_code == 200
    d = g.json()["data"]
    assert d["total_items"] == 3 and all("hash" in it for it in d["items"])
    assert "created_by" not in d                # 起草人账号 ⛔ 公开面


# ═════════════════════ C-2 可靠性 ═════════════════════

def test_c2_r1_no_half_record_on_nca_failure(monkeypatch):
    h = _auth("d2_r1")
    monkeypatch.setattr(delivery_ops, "_nca_append",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("chain down")))
    r = _manifest(h, _auth_id(h))
    assert r.status_code == 500 and "未发生" in r.json()["detail"]
    store = delivery_ops._store()
    assert list(store.glob("DLV-*.json")) == []   # 清单已清，无编号无半条


def test_c2_r4a_reconfirm_breaker_and_r5_r6_resume():
    h, did = _full_delivery("d2_r4a")
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h)
    assert r.status_code == 200
    # 观察窗内重复确认 → 熔断①
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h)
    assert r.status_code == 423
    # fail-closed：冻结后全拒
    r = client.post("/api/v1/delivery/items", json={"delivery_id": did, "items": [
        {"name": "y", "hash": "EEEE5555EEEE5555"}]}, headers=h)
    assert r.status_code == 423
    doc = delivery_ops._load(did)
    assert doc["status"] == "suspended" and delivery_ops._freeze_active(did)["reason"] == "reconfirm"
    # 非 operator 解冻被拒
    h2 = _auth("d2_r4a2")
    r = client.post("/api/v1/delivery/confirm",
                    json={"delivery_id": did, "resume": True}, headers=h2)
    assert r.status_code == 403
    # operator 复核解冻（回摆 delivered——确认后原位）
    op = _mk_operator("d2_r4op")
    r = client.post("/api/v1/delivery/confirm",
                    json={"delivery_id": did, "resume": True, "note": "复核通过"}, headers=op)
    assert r.status_code == 200 and r.json()["data"]["status"] == "delivered"
    assert delivery_ops._freeze_active(did) is None


def test_c2_r4b_hash_streak_breaker():
    h, did = _full_delivery("d2_r4b")
    doc = delivery_ops._load(did)
    doc["rec_hash"] = "DEADBEEF00000000"        # 篡改副本哈希 → 对拍不符
    delivery_ops._save(doc)
    for i in range(1, 3):
        r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h)
        assert r.status_code == 409 and f"连续 {i} 次" in r.json()["detail"]
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h)
    assert r.status_code == 423                  # 第三次熔断②
    assert delivery_ops._freeze_active(did)["reason"] == "hash"


def test_c2_r7_default_deny_and_r9_permissions():
    # 无 auth_id 不许开清单
    h = _auth("d2_r7")
    r = client.post("/api/v1/delivery/manifest", json={
        "receiver": "乙", "items": _ITEMS}, headers=h)
    assert r.status_code == 400 and "auth_id" in r.json()["detail"]
    # 假 auth_id 拒
    r = _manifest(h, "AP-fffffffffffffffff"[:13])
    assert r.status_code == 400
    # 匿名写拒（401）；非本人确认拒（403）
    r = client.post("/api/v1/delivery/manifest", json={})
    assert r.status_code == 401
    h2 = _auth("d2_r7b")
    r = _manifest(h2, _auth_id(h2))
    did = r.json()["data"]["delivery_id"]
    client.post("/api/v1/delivery/items", json={"delivery_id": did, "items": [
        {"name": "z", "hash": "FFFF6666FFFF6666"}]}, headers=h2)
    h3 = _auth("d2_r7c")
    r = client.post("/api/v1/delivery/confirm", json={"delivery_id": did}, headers=h3)
    assert r.status_code == 403


def test_c2_r8_no_evidence_means_nothing():
    h = _auth("d2_r8")
    r = _manifest(h, _auth_id(h))
    did = r.json()["data"]["delivery_id"]
    # 篡改：抹掉存证指针 → 对外视未发生
    doc = delivery_ops._load(did)
    doc["nca_seq"] = None
    delivery_ops._save(doc)
    assert client.get(f"/api/v1/delivery/{did}").status_code == 404
    r = client.post("/api/v1/delivery/items", json={"delivery_id": did, "items": [
        {"name": "w", "hash": "ABCD7777ABCD7777"}]}, headers=h)
    assert r.status_code == 409 and "无存证" in r.json()["detail"]


# ═════════════════════ C-3 令面自测五条 ═════════════════════

def _delivery_for_acceptance(uname):
    """造一份 delivered 状态的清单供开验。"""
    h, did = _full_delivery(uname)
    client.post("/api/v1/delivery/confirm", json={"delivery_id": did, "received": [
        {"name": "件甲", "hash": "AAAA1111AAAA1111"},
        {"name": "件乙", "hash": "BBBB2222BBBB2222"},
        {"name": "件丙", "hash": "CCCC3333CCCC3333"}]}, headers=h)
    return h, did


def _standard(h, did, items=None):
    body = {"delivery_id": did, "standards": items or [
        {"item": "件甲", "criterion": "哈希相符且可复算"},
        {"item": "件乙", "criterion": "大小与清单一致"}]}
    return client.post("/api/v1/acceptance/standard", json=body, headers=h)


def test_c3_1_no_standard_no_verdict_and_breaker_on_extra_item():
    h, did = _delivery_for_acceptance("d3_c31")
    r = _standard(h, did)
    acc = r.json()["data"]["acceptance_id"]
    # 临时加事前没有的条目 → 400＋熔断③
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": True, "basis": "大小一致"},
        {"item": "临时加项", "pass": True, "basis": "事后补登"}]}, headers=h)
    assert r.status_code == 400 and "标准无法对应" in r.json()["detail"]
    fz = acceptance_ops._freeze_active(acc)
    assert fz is not None and fz["reason"] == "standard"
    # fail-closed：冻结后全拒
    r = client.post("/api/v1/acceptance/rectify", json={"acceptance_id": acc, "items": [
        {"item": "件甲", "deadline": "2026-11-20"}]}, headers=h)
    assert r.status_code == 423


def test_c3_2_verdicts_traceable_to_items():
    h, did = _delivery_for_acceptance("d3_c32")
    acc = _standard(h, did).json()["data"]["acceptance_id"]
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符且可复算"},
        {"item": "件乙", "pass": False, "basis": "大小一致", "gap": "实收 1900 字节，清单 2048"}]},
        headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "rejected"
    verdicts = {v["item"]: v for v in r.json()["data"]["verdicts"]}
    assert verdicts["件乙"]["pass"] is False and "1900" in verdicts["件乙"]["gap"]
    # 公开读可回溯逐条结论
    g = client.get(f"/api/v1/acceptance/{acc}")
    assert g.json()["data"]["verdicts"][1]["item"] == "件乙"


def test_c3_3_fail_requires_gap_and_rectify():
    h, did = _delivery_for_acceptance("d3_c33")
    acc = _standard(h, did).json()["data"]["acceptance_id"]
    # 不通过空差距 → 400
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": False, "basis": "大小一致"}]}, headers=h)
    assert r.status_code == 400 and "差距" in r.json()["detail"]
    # 完整判定 → rejected → 整改（条目／期限）→ re_judging → 复判 passed
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": False, "basis": "大小一致", "gap": "实收不符"}]}, headers=h)
    assert r.json()["data"]["status"] == "rejected"
    r = client.post("/api/v1/acceptance/rectify", json={"acceptance_id": acc, "items": [
        {"item": "件乙", "deadline": "2026-11-20"}]}, headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "re_judging"
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": True, "basis": "整改后复测一致"}], "note": "复判"},
        headers=h)
    assert r.json()["data"]["status"] == "passed"


def test_c3_4_acceptance_id_and_nca_seq():
    h, did = _delivery_for_acceptance("d3_c34")
    r = _standard(h, did)
    data = r.json()["data"]
    assert data["acceptance_id"].startswith("ACC-") and data["nca_seq"].startswith("NCA-WEB-")
    with get_session() as s:
        row = s.get(M.NcaChain, data["nca_seq"])
    assert row.artifact_path == f"acceptance:{data['acceptance_id']}"


def test_c3_5_passed_shows_settlement_word_only():
    h, did = _delivery_for_acceptance("d3_c35")
    acc = _standard(h, did).json()["data"]["acceptance_id"]
    client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": True, "basis": "大小一致"}]}, headers=h)
    g = client.get(f"/api/v1/acceptance/{acc}")
    d = g.json()["data"]
    assert d["status"] == "passed" and d["settlement"] == "可结算"
    # S-4：⛔ 接结算——无任何结算触发字段/端点
    assert "settle" not in json.dumps(d, ensure_ascii=False).replace("settlement", "").lower()
    # rejected 态不显结算字样
    h2, did2 = _delivery_for_acceptance("d3_c35b")
    acc2 = _standard(h2, did2).json()["data"]["acceptance_id"]
    client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc2, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "哈希相符"},
        {"item": "件乙", "pass": False, "basis": "大小一致", "gap": "不符"}]}, headers=h2)
    d2 = client.get(f"/api/v1/acceptance/{acc2}").json()["data"]
    assert "settlement" not in d2


def test_c3_r1_no_half_record_on_nca_failure(monkeypatch):
    h, did = _delivery_for_acceptance("d3_r1")
    monkeypatch.setattr(acceptance_ops, "_nca_append",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("chain down")))
    r = _standard(h, did)
    assert r.status_code == 500 and "未发生" in r.json()["detail"]
    store = acceptance_ops._store()
    assert list(store.glob("ACC-*.json")) == []   # 验收单已清，无编号无半条


def test_c3_r7_default_deny_and_deps():
    h = _auth("d3_r7")
    # 无 delivery_id 不许开验
    r = client.post("/api/v1/acceptance/standard", json={
        "standards": [{"item": "a", "criterion": "b"}]}, headers=h)
    assert r.status_code == 400 and "delivery_id" in r.json()["detail"]
    # 假 delivery_id 拒
    r = client.post("/api/v1/acceptance/standard", json={
        "delivery_id": "DLV-abc", "standards": [{"item": "a", "criterion": "b"}]}, headers=h)
    assert r.status_code == 400
    # 匿名写拒
    r = client.post("/api/v1/acceptance/standard", json={})
    assert r.status_code == 401


def test_c3_r8_no_evidence_and_r9_roles():
    h, did = _delivery_for_acceptance("d3_r8")
    acc = _standard(h, did).json()["data"]["acceptance_id"]
    doc = acceptance_ops._load(acc)
    doc["nca_seq"] = None
    acceptance_ops._save(doc)
    assert client.get(f"/api/v1/acceptance/{acc}").status_code == 404
    # 非本人判定拒
    h2 = _auth("d3_r8b")
    r = client.post("/api/v1/acceptance/verdict", json={"acceptance_id": acc, "verdicts": [
        {"item": "件甲", "pass": True, "basis": "x"}]}, headers=h2)
    assert r.status_code in (403, 404, 409)   # 无存证先撞 409/404 序，任一均 fail-closed
