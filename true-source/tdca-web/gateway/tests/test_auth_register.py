# -*- coding: utf-8 -*-
"""M4-REGISTER 注册端点测试（GSEQ-0663）。

验收映射：① 注册成功 200 可登录 → test_register_success_200_auto_session
          ② 重复 username 409 → test_register_duplicate_409
          ③ 弱密码/非法 username 拒绝 → test_register_weak_password_400 / test_register_bad_username_400
          ④ 密码哈希落库非明文 → test_register_password_not_plaintext
          ⑤ 注册动作落 NCA 存证 → test_register_nca_chain_appended
          ⑥ 限流（每 IP 每小时 ≤N）→ test_register_rate_limit_429
          ⑦ 鉴权启用下注册豁免（否则无法注册）→ test_register_exempt_under_auth_on
"""
import os

import pytest
from fastapi.testclient import TestClient

import api_v1
from app import app
from auth import SESSION_PREFIX
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "Reg-pass-2026"      # 测试口令（仅测试库，非真实凭据）


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """每用例清空限流计数（TestClient 共享来源 IP）。"""
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


def _reg(username: str, password: str = _PW, **kw):
    body = {"username": username, "password": password,
            "agree_contract": True, "contract_version": "V1.0"}
    body.update(kw)
    return client.post("/api/v1/auth/register", json=body)


def _drop_user(username: str):
    with get_sessionmaker().begin() as s:
        u = s.get(M.User, username)
        if u is not None:
            s.delete(u)


class _auth_on:
    def __enter__(self):
        os.environ["TDCA_GATEWAY_AUTH"] = "1"
    def __exit__(self, *a):
        os.environ.pop("TDCA_GATEWAY_AUTH", None)


def test_register_success_200_auto_session():
    _drop_user("reg-ok-1")
    r = _reg("reg-ok-1")
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["username"] == "reg-ok-1"
    assert d["role"] == "viewer"                       # 默认只读角色
    assert d["token"].startswith(SESSION_PREFIX)       # 注册即签发 2h 会话
    assert d["nca_id"].startswith("NCA-WEB-")          # 存证号随响应返回
    assert r.json()["data_nature"] == "real"
    # 会话立即可用
    me = client.get("/api/v1/auth/me", headers={"Authorization": d["token"]})
    assert me.status_code == 200 and me.json()["data"]["username"] == "reg-ok-1"
    # 注册后可走正常登录
    login = client.post("/api/v1/auth/login",
                        json={"username": "reg-ok-1", "password": _PW})
    assert login.status_code == 200
    _drop_user("reg-ok-1")


def test_register_duplicate_409():
    _drop_user("reg-dup-1")
    assert _reg("reg-dup-1").status_code == 200
    r = _reg("reg-dup-1")
    assert r.status_code == 409
    _drop_user("reg-dup-1")


def test_register_duplicate_409_no_side_effects():
    """D-1（GSEQ-0678）：重复注册 409「用户名已存在」且零副产物——不落缔约 NCA、不创建会话（响应无 token）。"""
    _drop_user("reg-dup-2")
    assert _reg("reg-dup-2").status_code == 200
    with get_session() as s:
        chain_before = s.query(M.NcaChain).count()
    r = _reg("reg-dup-2")
    assert r.status_code == 409
    body = r.json()
    assert body["detail"] == "用户名已存在"              # 错误语义不变（L1SI153 段一：仅增设 code 字段）
    assert body.get("code") == "TDCA-E-STATE-STATE-002"  # 重复注册归簇 STATE-002，无会话/存证字段
    assert "token" not in body and "chain" not in body
    with get_session() as s:
        assert s.query(M.NcaChain).count() == chain_before  # 409 不落缔约存证
    _drop_user("reg-dup-2")


def test_register_weak_password_400():
    for bad in ("short1", "onlyletters", "12345678", ""):
        r = _reg("reg-weak-1", bad)
        assert r.status_code == 400, (bad, r.text)
        with get_session() as s:
            assert s.get(M.User, "reg-weak-1") is None   # 拒绝即不落库


def test_register_bad_username_400():
    for bad in ("ab", "has space", "含中文", "semi;colon", "a" * 33):
        r = _reg(bad)
        assert r.status_code == 400, (bad, r.text)
    api_v1._register_hits.clear()   # 前 5 次已达限流阈值，清零后再验空串（限流另有专项用例）
    assert _reg("").status_code == 400


def test_register_password_not_plaintext():
    _drop_user("reg-hash-1")
    assert _reg("reg-hash-1").status_code == 200
    with get_session() as s:
        u = s.get(M.User, "reg-hash-1")
        assert u is not None
        assert u.password_hash != _PW
        assert len(u.password_hash) == 64                # PBKDF2-SHA256 hex
        assert u.salt and u.iterations >= 120000
        assert u.role == "viewer"
    _drop_user("reg-hash-1")


def test_register_nca_chain_appended():
    _drop_user("reg-nca-1")
    with get_session() as s:
        before = s.query(M.NcaChain).count()
    r = _reg("reg-nca-1")
    assert r.status_code == 200
    nca_id = r.json()["data"]["nca_id"]
    # L1SI145-ANCHOR-B2-001：注册现落两条存证——缔约＋锚段（未选锚者亦落锚段，如实记名级·待补）
    with get_session() as s:
        assert s.query(M.NcaChain).count() == before + 2
        row = s.get(M.NcaChain, nca_id)   # ts 秒级精度下同秒多行，按返回存证号主键直查（确定性）
        assert row is not None
        assert row.action == "user_register_contract"
        assert row.actor == "reg-nca-1"
        assert row.prev_nca                              # 链式衔接非空
        assert "TDCA-REGISTER-CONTRACT-001/V1.0" in row.artifact_path  # 缔约落链含协议版本
        assert "zh:ee33e2c8" in row.artifact_path and "en:7018e356" in row.artifact_path  # 双版本哈希
        # 锚段存证：默认未选 → kind none／记名级／待补；锚行 nca_ref 回填同一存证号
        arow = s.get(M.NcaChain, r.json()["data"]["anchor"]["nca_ref"])
        assert arow is not None and arow.action == "user_anchor_select"
        assert "anchor://kind:none/tier:记名级/state:待补" in arow.artifact_path
        uarow = s.get(M.UserAnchor, "reg-nca-1")
        assert uarow is not None and uarow.anchor_kind is None
        assert uarow.anchor_tier == "记名级" and uarow.tier_state == "待补"
        assert uarow.nca_ref == arow.nca_id
    _drop_user("reg-nca-1")


def test_register_rate_limit_429():
    cap = api_v1._REGISTER_MAX
    for i in range(cap):
        r = _reg(f"reg-rl-{i}")
        assert r.status_code == 200, (i, r.text)
    r = _reg("reg-rl-overflow")
    assert r.status_code == 429
    for i in range(cap):
        _drop_user(f"reg-rl-{i}")


def test_register_exempt_under_auth_on():
    """鉴权启用（B-4 fail-closed）下注册仍可达——否则新用户无法入场。"""
    _drop_user("reg-exempt-1")
    with _auth_on():
        r = _reg("reg-exempt-1")
        assert r.status_code == 200, r.text
    _drop_user("reg-exempt-1")


def test_register_contract_consent_required():
    """注册即缔约 fail-closed：未同意/版本不符 → 400 且不落库。"""
    _drop_user("reg-noconsent-1")
    r = client.post("/api/v1/auth/register",
                    json={"username": "reg-noconsent-1", "password": _PW})
    assert r.status_code == 400                          # 缺 agree_contract
    r = _reg("reg-noconsent-1", agree_contract=False)
    assert r.status_code == 400                          # 显式不同意
    api_v1._register_hits.clear()
    r = _reg("reg-noconsent-1", contract_version="V0.9")
    assert r.status_code == 400                          # 旧版协议蒙混拒绝
    with get_session() as s:
        assert s.get(M.User, "reg-noconsent-1") is None


def test_register_contract_fields_in_response():
    """缔约回执：版本 + 三件套哈希 + 同意时间戳随响应返回。"""
    _drop_user("reg-contract-1")
    r = _reg("reg-contract-1")
    assert r.status_code == 200
    c = r.json()["data"]["contract"]
    assert c["contract_id"] == "TDCA-REGISTER-CONTRACT-001"
    assert c["version"] == "V1.0"
    assert c["zh_sha256"].startswith("ee33e2c8")
    assert c["en_sha256"].startswith("7018e356")
    assert c["machine_sha256"].startswith("f7648624")
    assert c["consent_ts"]                               # 服务端同意时间戳非空
    _drop_user("reg-contract-1")


def test_register_rate_limit_per_real_ip():
    """nginx 单跳前置下按 X-Real-IP 分桶：A 打满不影响 B（否则代理后全站共享 5 次/小时）。"""
    cap = api_v1._REGISTER_MAX
    for i in range(cap):
        r = client.post("/api/v1/auth/register",
                        json={"username": f"reg-ipa-{i}", "password": _PW, "agree_contract": True, "contract_version": "V1.0"},
                        headers={"X-Real-IP": "10.0.0.1"})
        assert r.status_code == 200, (i, r.text)
    r = client.post("/api/v1/auth/register",
                    json={"username": "reg-ipa-x", "password": _PW, "agree_contract": True, "contract_version": "V1.0"},
                    headers={"X-Real-IP": "10.0.0.1"})
    assert r.status_code == 429
    r = client.post("/api/v1/auth/register",
                    json={"username": "reg-ipb-0", "password": _PW, "agree_contract": True, "contract_version": "V1.0"},
                    headers={"X-Real-IP": "10.0.0.2"})
    assert r.status_code == 200          # 另一真实 IP 独立配额
    for i in range(cap):
        _drop_user(f"reg-ipa-{i}")
    _drop_user("reg-ipb-0")


def test_register_nca_visible_in_me_dashboard():
    """REGISTER-002 缺口⑤（GSEQ-0671）：/me/dashboard 暴露本人最近注册缔约存证号。"""
    _drop_user("reg-me-1")
    r = _reg("reg-me-1")
    assert r.status_code == 200, r.text
    nca_id = r.json()["data"]["nca_id"]
    tok = r.json()["data"]["token"]
    me = client.get("/api/v1/me/dashboard", headers={"Authorization": tok})
    assert me.status_code == 200, me.text[:200]
    assert me.json()["data"]["session"]["last_register_nca_id"] == nca_id
    _drop_user("reg-me-1")
