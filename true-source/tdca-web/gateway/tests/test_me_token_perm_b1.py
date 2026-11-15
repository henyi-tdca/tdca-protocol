# -*- coding: utf-8 -*-
"""L1SI214-TOKEN-B1-001 真实系统沙盒（批1）：六判据 S-1~S-6 逐条实测。

数据：沙盒账号 sbx_a（operator）／sbx_b（viewer）／sbx_empty（viewer 无令牌路径单测）；
会话行直接种入（单会话制不改表、不跑登录面）；全部沙盒库，⛔ 涉真实账户。
判据映射：S-1 只本人／S-2 值不回显／S-3 越权查他人 404／S-4 依据齐全／S-5 取值四选／S-6 未登录 401。
"""
import hashlib
import json
import re
import secrets

from fastapi.testclient import TestClient

from app import app
from auth import hash_password, _token_hash
from db import get_session, get_sessionmaker
from db import models as M
from me_ops import _tokens_payload
from perm_table import ALLOW_VALUES, build_permissions

client = TestClient(app)

_NOW = "2026-11-15T00:00:00+00:00"
_FUTURE = "2027-11-15T00:00:00+00:00"
_PAST = "2025-11-15T00:00:00+00:00"


def _mkuser(username: str, role: str):
    ph, salt, iters = hash_password("sbx-pass-123")
    with get_sessionmaker().begin() as s:
        s.add(M.User(username=username, password_hash=ph, salt=salt,
                     iterations=iters, role=role, created_at=_NOW,
                     data_provenance="simulated"))


def _mksession(username: str, expires: str = _FUTURE, revoked: int = 0) -> str:
    """种会话行，返回裸令牌（测试内使用；⛔ 出测试件）。"""
    tok = "TDCA-SES-" + secrets.token_urlsafe(32)
    with get_sessionmaker().begin() as s:
        s.add(M.AuthSession(token_hash=_token_hash(tok), username=username,
                            expires_at=expires, revoked=revoked, created_at=_NOW,
                            data_provenance="simulated"))
    return tok


def setup_module():
    _mkuser("sbx_a", "operator")
    _mkuser("sbx_b", "viewer")
    _mkuser("sbx_empty", "viewer")
    _mkuser("sbx_founder", "founder")


class TestSixCriteria:
    def setup_method(self):
        # A 名下三枚：active×1 / revoked×1 / expired×1；B 名下一枚 active
        self.tok_a_active = _mksession("sbx_a")
        self.tok_a_revoked = _mksession("sbx_a", revoked=1)
        self.tok_a_expired = _mksession("sbx_a", expires=_PAST)
        self.tok_b = _mksession("sbx_b")
        self.hash_b = _token_hash(self.tok_b)

    # ---------- S-1 只返回本人 ----------
    def test_s1_only_self(self):
        r = client.get("/api/v1/me/tokens",
                       headers={"Authorization": self.tok_a_active})
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["scope"] == "self"
        assert d["count"] == 3                      # A 名下三枚全在
        statuses = sorted(t["status"] for t in d["tokens"])
        assert statuses == ["active", "expired", "revoked"]
        # B 的令牌一条也不混入：B 的哈希前 4 不得出现在 A 的清单里
        ids = [t["id"] for t in d["tokens"]]
        assert self.hash_b[:4] + "****" not in ids
        # B 自看只见到 B 自己的一枚
        rb = client.get("/api/v1/me/tokens",
                        headers={"Authorization": self.tok_b})
        assert rb.status_code == 200 and rb.json()["data"]["count"] == 1
        assert rb.json()["data"]["tokens"][0]["id"] == self.hash_b[:4] + "****"

    # ---------- S-2 令牌值不回显 ----------
    def test_s2_no_credential_echo(self):
        r = client.get("/api/v1/me/tokens",
                       headers={"Authorization": self.tok_a_active})
        raw = r.text
        for secret in (self.tok_a_active, self.tok_a_revoked, self.tok_a_expired,
                       self.tok_b,
                       _token_hash(self.tok_a_active), _token_hash(self.tok_b)):
            assert secret not in raw, "凭据串出现在响应中"
        # 人工＋脚本双查：除 id 脱敏位（4hex+****）外不得有可复原凭据形态
        d = r.json()["data"]
        assert all(re.fullmatch(r"[0-9a-f]{4}\*{4}", t["id"]) for t in d["tokens"])
        assert "tokens" in d and isinstance(d["tokens"], list)

    # ---------- S-3 越权查他人 → 404 ----------
    def test_s3_cross_user_404(self):
        for url in ("/api/v1/me/tokens?user=sbx_b",
                    "/api/v1/me/permissions?username=sbx_b",
                    "/api/v1/me/tokens?owner=sbx_b&scope=all"):
            r = client.get(url, headers={"Authorization": self.tok_a_active})
            assert r.status_code == 404, f"{url} 应 404 实得 {r.status_code}"
        # 路径形态越权亦无路由（404）
        assert client.get("/api/v1/me/tokens/sbx_b",
                          headers={"Authorization": self.tok_a_active}).status_code == 404

    # ---------- S-4 依据齐全 ----------
    def test_s4_basis_complete(self):
        for role, tok in (("operator", self.tok_a_active), ("viewer", self.tok_b)):
            r = client.get("/api/v1/me/permissions",
                           headers={"Authorization": tok})
            assert r.status_code == 200
            m = r.json()["data"]["matrix"]
            assert len(m) > 0
            for item in m:
                assert item["basis"].strip(), f"{role} 有空 basis: {item}"
                assert item["basis"] != "见文档"

    # ---------- S-5 取值合规（且四种值都真实出现） ----------
    def test_s5_allow_vocabulary(self):
        seen = set()
        for tok in (self.tok_a_active, self.tok_b):
            r = client.get("/api/v1/me/permissions",
                           headers={"Authorization": tok})
            for item in r.json()["data"]["matrix"]:
                assert item["allow"] in ALLOW_VALUES, item["allow"]
                seen.add(item["allow"])
        assert {"yes", "no", "yes-require-signature", "na"} <= seen, seen

    # ---------- S-6 未登录 → 401 ----------
    def test_s6_anonymous_401(self):
        for url in ("/api/v1/me/tokens", "/api/v1/me/permissions"):
            r = client.get(url)
            assert r.status_code == 401, f"{url} 未登录应 401 实得 {r.status_code}"
            assert r.json().get("detail"), "⛔ 空数组冒充成功"
        # CRT 通道也不可进我的面（我的面仅本人会话）
        r = client.get("/api/v1/me/tokens",
                       headers={"Authorization": "TDCA-CRT-whatever"})
        assert r.status_code == 401


class TestShape:
    def test_field_set_exact(self):
        tok = _mksession("sbx_a")
        d = client.get("/api/v1/me/tokens",
                       headers={"Authorization": tok}).json()["data"]
        assert set(d["tokens"][-1]) == {"id", "kind", "issued_at", "expires_at",
                                        "last_used_at", "status", "bound_agents",
                                        "note"}
        assert d["tokens"][-1]["kind"] == "session"
        assert d["tokens"][-1]["bound_agents"] == []

    def test_empty_tokens(self):
        # 单会话制下「持有有效会话却无令牌行」运行时不可达；空路径按构建层直测
        p = _tokens_payload("sbx_empty")
        assert p == {"tokens": [], "count": 0, "scope": "self"}

    def test_permissions_shape(self):
        tok = _mksession("sbx_founder")
        d = client.get("/api/v1/me/permissions",
                       headers={"Authorization": tok}).json()["data"]
        assert set(d) >= {"role", "scopes", "matrix", "note", "scope"}
        assert d["role"] == "founder" and d["scope"] == "self"
        ons = {i["on"] for i in d["matrix"]}
        assert ons == {"制度层", "我的面"}   # 表B/表C 无治理侧列 → 按表生成不补行
        for i in d["matrix"]:
            assert set(i) == {"action", "on", "allow", "basis", "key_source"}  # B3 E-3 增「钥匙来源」列（令面 mandated，形态随批演进）
