# -*- coding: utf-8 -*-
"""L1SI214-TOKEN-B2-001 真实系统沙盒（批2）：六判据 S-1~S-6 逐条实测。

A 项 DELETE /me/tokens/{id}：只删自己／即失效／写审计／不泄露（404 同码）／幂等／软删。
B 项两类留痕：改密（成功＋失败各一条）与私域管理员任免（样例一条），⛔ 含值。
数据全部沙盒（sbx_*），⛔ 涉真实账户；nca_chain 读断言只查本测试写入的 action 集合。
"""
import re
import secrets

from fastapi.testclient import TestClient

from app import app
from auth import hash_password, _token_hash
from db import get_session, get_sessionmaker
from db import models as M
from me_audit import audit_privilege_admin_change

client = TestClient(app)

_NOW = "2026-11-15T00:00:00+00:00"
_FUTURE = "2027-11-15T00:00:00+00:00"
_PW = "sbx-pass-123"


def _mkuser(username: str, role: str):
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        s.add(M.User(username=username, password_hash=ph, salt=salt,
                     iterations=iters, role=role, created_at=_NOW,
                     data_provenance="simulated"))


def _mksession(username: str) -> str:
    tok = "TDCA-SES-" + secrets.token_urlsafe(32)
    with get_sessionmaker().begin() as s:
        s.add(M.AuthSession(token_hash=_token_hash(tok), username=username,
                            expires_at=_FUTURE, revoked=0, created_at=_NOW,
                            data_provenance="simulated"))
    return tok


def _masked(tok: str) -> str:
    return _token_hash(tok)[:4] + "****"


def _nca_rows(*actions):
    with get_session() as s:
        return (s.query(M.NcaChain).filter(M.NcaChain.action.in_(actions))
                .order_by(M.NcaChain.ts).all())


def setup_module():
    for u, r in (("s2_a", "operator"), ("s2_b", "viewer")):
        _mkuser(u, r)


class TestRevokeCriteria:
    def setup_method(self):
        self.tok_a = _mksession("s2_a")
        self.tok_a2 = _mksession("s2_a")
        self.tok_b = _mksession("s2_b")
        self.mid_a = _masked(self.tok_a)
        self.mid_b = _masked(self.tok_b)

    # S-1 只删自己：删自己成；删他人（B 的 id）404
    def test_s1_only_self(self):
        r = client.delete(f"/api/v1/me/tokens/{self.mid_a}",
                          headers={"Authorization": self.tok_a})
        assert r.status_code == 200 and r.json()["data"]["result"] == "revoked"
        r2 = client.delete(f"/api/v1/me/tokens/{self.mid_b}",
                           headers={"Authorization": self.tok_a2})
        assert r2.status_code == 404
        # B 的令牌并未被吊销（行仍 active）
        with get_session() as s:
            row = s.get(M.AuthSession, _token_hash(self.tok_b))
            assert row.revoked == 0

    # S-2 即失效：被吊销令牌再请求 me 端点 ⟹ 401
    def test_s2_immediate_invalid(self):
        client.delete(f"/api/v1/me/tokens/{self.mid_a}",
                      headers={"Authorization": self.tok_a})
        for url in ("/api/v1/me/tokens", "/api/v1/me/permissions"):
            r = client.get(url, headers={"Authorization": self.tok_a})
            assert r.status_code == 401, f"{url} 应 401 实得 {r.status_code}"

    # S-3 写审计：每次吊销一条，五要素齐、⛔ 含值
    def test_s3_audit_trail(self):
        client.delete(f"/api/v1/me/tokens/{self.mid_a}",
                      headers={"Authorization": self.tok_a})
        rows = _nca_rows("user_token_revoke")
        mine = [r for r in rows if r.actor == "s2_a" and self.mid_a in (r.artifact_path or "")]
        assert len(mine) == 1
        rec = mine[-1]
        assert rec.actor == "s2_a"                          # 操作者
        assert f"auth://me/tokens/{self.mid_a}/revoked" == rec.artifact_path  # 脱敏 id＋结果
        assert rec.ts                                       # 时点
        raw = str(rec.__dict__)
        for secret in (self.tok_a, self.tok_b, _token_hash(self.tok_a)):
            assert secret not in raw, "凭据串入审计行"

    # S-4 不泄露：删他人 404，与不存在同码；成功码不混用
    def test_s4_no_existence_leak(self):
        assert client.delete(
            f"/api/v1/me/tokens/{self.mid_b}",
            headers={"Authorization": self.tok_a}).status_code == 404
        assert client.delete(
            "/api/v1/me/tokens/zzzz****",
            headers={"Authorization": self.tok_a}).status_code == 404
        assert client.delete(
            "/api/v1/me/tokens/deadbeef****",
            headers={"Authorization": self.tok_a}).status_code == 404
        # 带 user 类参数亦 404（⛔ 接受参数）
        assert client.delete(
            f"/api/v1/me/tokens/{self.mid_a}?user=s2_b",
            headers={"Authorization": self.tok_a}).status_code == 404

    # S-5 幂等：连删两次均成功且状态一致
    def test_s5_idempotent(self):
        r1 = client.delete(f"/api/v1/me/tokens/{self.mid_a}",
                           headers={"Authorization": self.tok_a})
        r2 = client.delete(f"/api/v1/me/tokens/{self.mid_a}",
                           headers={"Authorization": self.tok_a2})  # A 另一枚会话执行
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["data"]["result"] == "revoked"
        assert r2.json()["data"]["result"] == "already_revoked"
        with get_session() as s:
            row = s.get(M.AuthSession, _token_hash(self.tok_a))
            assert row.revoked == 1                          # 状态不回跳
        # 且未登录/他人无法借幂等接口探测
        assert client.delete(
            f"/api/v1/me/tokens/{self.mid_a}").status_code == 401

    # S-6 两类留痕齐：改密（成＋败）与任免各一条，字段齐、⛔ 含值
    def test_s6_two_trails(self):
        # 改密失败（旧密错误）——先跑，成功路径会吊销本人其它会话
        rf = client.post("/api/v1/me/password",
                         headers={"Authorization": self.tok_a},
                         json={"old_password": "wrong-old-000", "new_password": "new-pass-789"})
        assert rf.status_code == 400
        # 改密成功（本人，旧密正确；用 tok_a2，成功后 tok_a 已被吊销不再用）
        rs = client.post("/api/v1/me/password",
                         headers={"Authorization": self.tok_a2},
                         json={"old_password": _PW, "new_password": "new-pass-456"})
        assert rs.status_code == 200
        # 任免样例（沙盒内造一条）
        audit_privilege_admin_change("s2_a", "s2_agent1", "appoint", "ok")
        rows = _nca_rows("user_password_change", "user_password_change_failed",
                         "user_privilege_admin_change")
        acts = [r.action for r in rows if r.actor == "s2_a"]
        assert "user_password_change" in acts
        assert "user_password_change_failed" in acts
        pwc = [r for r in rows if r.action == "user_password_change" and r.actor == "s2_a"]
        assert pwc and pwc[-1].artifact_path.endswith("/ok")
        pwf = [r for r in rows if r.action == "user_password_change_failed" and r.actor == "s2_a"]
        assert pwf and pwf[-1].artifact_path.endswith("/failed")
        pad = [r for r in rows if r.action == "user_privilege_admin_change" and r.actor == "s2_a"]
        assert pad and pad[-1].subject_ref and pad[-1].ts
        assert pad[-1].artifact_path == "auth://me/privilege-admin/s2_a/appoint/ok"
        # ⛔ 含值：审计行全文不得含密码/哈希/凭据
        for r in rows:
            raw = str(r.__dict__)
            for banned in (_PW, "new-pass-456", "new-pass-789", "wrong-old-000",
                           self.tok_a, self.tok_a2, _token_hash(self.tok_a)):
                assert banned not in raw, f"凭据入审计: {r.action}"
        # 留痕是审计面：/me/permissions 输出里 ⛔ 出现审计行内容
        perms = client.get("/api/v1/me/permissions",
                           headers={"Authorization": self.tok_a2}).text
        assert "user_password_change" not in perms
        assert "nca_chain" not in perms


class TestSoftDelete:
    def test_row_kept_and_listed_revoked(self):
        tok = _mksession("s2_b")
        mid = _masked(tok)
        client.delete(f"/api/v1/me/tokens/{mid}",
                      headers={"Authorization": tok})
        with get_session() as s:
            row = s.get(M.AuthSession, _token_hash(tok))
            assert row is not None and row.revoked == 1   # 软删：行在
        # 换一枚会话看清单：status=revoked 如实可见
        tok_b2 = _mksession("s2_b")
        d = client.get("/api/v1/me/tokens",
                       headers={"Authorization": tok_b2}).json()["data"]
        st = [t["status"] for t in d["tokens"] if t["id"] == mid]
        assert st == ["revoked"]
