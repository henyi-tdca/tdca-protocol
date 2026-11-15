# -*- coding: utf-8 -*-
"""L1SI214-CONSOLE-A2-001 件二测试：任免私域管理员端点（B-1~B-3 判据逐条实测）。

端点：POST /api/v1/me/privilege-admin/appoint|revoke。
数据全部沙盒（sbx_pa_*），⛔ 涉真实账户；nca_chain 读断言只查本测试写入的 action 集合。
"""
import hashlib
import secrets

from fastapi.testclient import TestClient

from app import app
from auth import hash_password, _token_hash
from db import get_session, get_sessionmaker
from db import models as M
from dual_lock import lock2_config_right

client = TestClient(app)

_NOW = "2026-11-15T00:00:00+00:00"
_FUTURE = "2027-11-15T00:00:00+00:00"
_PW = "sbx-pass-123"

OWNER = "sbx_pa_owner"
OTHER = "sbx_pa_other"
ADMIN = "sbx_pa_admin"
AGENT = "sbx_pa_agent"
ASSET_OWNER = "OR-sbx-pa-owner-001"
ASSET_OTHER = "OR-sbx-pa-other-001"
ASSET_NONE = "OR-sbx-pa-ghost-001"


def _mkuser(username: str, role: str, external: bool = False):
    ph, salt, iters = hash_password(_PW)
    with get_sessionmaker().begin() as s:
        s.add(M.User(username=username, password_hash=ph, salt=salt,
                     iterations=iters, role=role, created_at=_NOW,
                     data_provenance="simulated"))
        if external:
            s.add(M.UserIdentity(
                username=username, identity_type="external",
                agent_card_json="{}", owner_auth="AR-sbx-pa-1",
                created_at=_NOW, updated_at=_NOW,
                data_provenance="simulated"))


def _mkasset(record_id: str, owner: str, status: str = "registered"):
    with get_sessionmaker().begin() as s:
        s.add(M.OwnershipRecord(
            record_id=record_id, work_title="sbx 权属（任免端点测试）",
            owner_ref=owner, jurisdiction_branch="unspecified",
            source_lineage="sbx", status=status,
            created_at=_NOW, updated_at=_NOW, data_provenance="simulated"))


def _mksession(username: str) -> str:
    tok = "TDCA-SES-" + secrets.token_urlsafe(32)
    with get_sessionmaker().begin() as s:
        s.add(M.AuthSession(token_hash=_token_hash(tok), username=username,
                            expires_at=_FUTURE, revoked=0, created_at=_NOW,
                            data_provenance="simulated"))
    return tok


def _masked(username: str) -> str:
    return hashlib.sha256(username.encode("utf-8")).hexdigest()[:12]


def _nca_rows(*actions):
    with get_session() as s:
        return (s.query(M.NcaChain).filter(M.NcaChain.action.in_(actions))
                .order_by(M.NcaChain.ts).all())


def _active_doc(me: str, appointee: str, asset_ref: str):
    with get_session() as s:
        for d in (s.query(M.AuthorizationPanelDoc)
                  .filter(M.AuthorizationPanelDoc.status == "active",
                          M.AuthorizationPanelDoc.drafter == me,
                          M.AuthorizationPanelDoc.grantee == appointee)
                  .all()):
            if asset_ref in (d.subject or ""):
                return d
    return None


def setup_module():
    _mkuser(OWNER, "operator")
    _mkuser(OTHER, "viewer")
    _mkuser(ADMIN, "viewer")
    _mkuser(AGENT, "viewer", external=True)
    _mkasset(ASSET_OWNER, OWNER)
    _mkasset(ASSET_OTHER, OTHER)


class TestTwoLocks:
    def setup_method(self):
        self.tok_owner = _mksession(OWNER)
        self.tok_other = _mksession(OTHER)
        self.tok_agent = _mksession(AGENT)

    # 未登录 401（上游 fail-closed）
    def test_unauthenticated_401(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        json={"asset_ref": ASSET_OWNER, "appointee": ADMIN})
        assert r.status_code == 401

    # 第 1 把锁 · 智能体（external 身份）代任免 ⟹ 拒 403
    def test_agent_refused_403(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_agent},
                        json={"asset_ref": ASSET_OWNER, "appointee": ADMIN})
        assert r.status_code == 403

    # 第 1 把锁 · on_behalf 非空（代签代填红线）⟹ 拒 403
    def test_on_behalf_refused_403(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": ASSET_OWNER, "appointee": ADMIN,
                              "on_behalf": "some-agent"})
        assert r.status_code == 403

    # 第 2 把锁 · 他人私域 ⟹ 404 同码
    def test_other_domain_404(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": ASSET_OTHER, "appointee": ADMIN})
        assert r.status_code == 404
        # 与他人令牌 404 同码（不泄露存在性）
        r2 = client.post("/api/v1/me/privilege-admin/appoint",
                         headers={"Authorization": self.tok_owner},
                         json={"asset_ref": ASSET_NONE, "appointee": ADMIN})
        assert r2.status_code == 404

    # 第 2 把锁 · 已注销权属 ⟹ 404 同码
    def test_cancelled_domain_404(self):
        cancelled = "OR-sbx-pa-cancel-001"
        _mkasset(cancelled, OWNER, status="cancelled")
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": cancelled, "appointee": ADMIN})
        assert r.status_code == 404

    # 形态非法 asset_ref ⟹ 404 同码
    def test_bad_asset_shape_404(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": "XX-nope", "appointee": ADMIN})
        assert r.status_code == 404

    # 带查询参数 ⟹ 404（/me 族口径）
    def test_query_params_404(self):
        r = client.post(f"/api/v1/me/privilege-admin/appoint?user={ADMIN}",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": ASSET_OWNER, "appointee": ADMIN})
        assert r.status_code == 404


class TestAppointRevokeLifecycle:
    def setup_method(self):
        self.tok_owner = _mksession(OWNER)
        self.appointee = f"sbx_pa_m{secrets.token_hex(3)}"
        _mkuser(self.appointee, "viewer")

    def _body(self):
        return {"asset_ref": ASSET_OWNER, "appointee": self.appointee}

    # B-1 任命可执行：自己域内任命成功，对方确获资格（域内授权关系在册 active，
    #   且经在役 dual_lock 第 2 把锁口径实证——配置权判定通过）
    def test_b1_appoint_grants_qualification(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json=self._body())
        assert r.status_code == 201
        d = r.json()["data"]
        assert d["status"] == "active" and d["auth_id"].startswith("AP-")
        doc = _active_doc(OWNER, self.appointee, ASSET_OWNER)
        assert doc is not None and doc.nca_seq     # 资格在册＋存证在册
        # 实证：在役第 2 把锁口径——被任命者对该资产获配置权
        ok, why = lock2_config_right(self.appointee, ASSET_OWNER)
        assert ok, why

    # 重复任命 ⟹ 409（不叠件）
    def test_duplicate_appoint_409(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner}, json=self._body())
        assert r.status_code == 409

    # 被任命者不存在 ⟹ 404 同码
    def test_appointee_missing_404(self):
        r = client.post("/api/v1/me/privilege-admin/appoint",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": ASSET_OWNER,
                              "appointee": "sbx_pa_ghost_user"})
        assert r.status_code == 404

    # B-2 任命留痕：一条 user_privilege_admin_change，五要素齐、⛔ 含值
    def test_b2_appoint_audit_trail(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        rows = [r for r in _nca_rows("user_privilege_admin_change")
                if r.actor == OWNER and r.subject_ref == _masked(self.appointee)]
        assert len(rows) >= 1
        rec = rows[-1]
        assert rec.artifact_path == f"auth://me/privilege-admin/{OWNER}/appoint/ok"
        assert rec.ts and rec.data_provenance == "real"
        raw = str(rec.__dict__)
        for secret in (self.tok_owner, _token_hash(self.tok_owner)):
            assert secret not in raw, "凭据串入审计行"

    # B-1 撤销可执行：对方确失资格（在役第 2 把锁口径回拒）
    def test_b1_revoke_removes_qualification(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        r = client.post("/api/v1/me/privilege-admin/revoke",
                        headers={"Authorization": self.tok_owner}, json=self._body())
        assert r.status_code == 200 and r.json()["data"]["status"] == "revoked"
        assert _active_doc(OWNER, self.appointee, ASSET_OWNER) is None
        ok, _why = lock2_config_right(self.appointee, ASSET_OWNER)
        assert not ok

    # B-2 撤销留痕：末段 failed 之外为 revoke/ok，字段齐
    def test_b2_revoke_audit_trail(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        client.post("/api/v1/me/privilege-admin/revoke",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        rows = [r for r in _nca_rows("user_privilege_admin_change")
                if r.actor == OWNER and r.subject_ref == _masked(self.appointee)]
        assert len(rows) >= 2
        rec = rows[-1]
        assert rec.artifact_path == f"auth://me/privilege-admin/{OWNER}/revoke/ok"
        assert rec.ts

    # 未任命过即撤销 ⟹ 404 同码
    def test_revoke_without_appointment_404(self):
        r = client.post("/api/v1/me/privilege-admin/revoke",
                        headers={"Authorization": self.tok_owner}, json=self._body())
        assert r.status_code == 404

    # 撤销后重复撤销 ⟹ 404 同码
    def test_double_revoke_404(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        client.post("/api/v1/me/privilege-admin/revoke",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        r = client.post("/api/v1/me/privilege-admin/revoke",
                        headers={"Authorization": self.tok_owner}, json=self._body())
        assert r.status_code == 404

    # 撤销他人私域的任命 ⟹ 404 同码（第 2 把锁先行）
    def test_revoke_other_domain_404(self):
        client.post("/api/v1/me/privilege-admin/appoint",
                    headers={"Authorization": self.tok_owner}, json=self._body())
        r = client.post("/api/v1/me/privilege-admin/revoke",
                        headers={"Authorization": self.tok_owner},
                        json={"asset_ref": ASSET_OTHER, "appointee": self.appointee})
        assert r.status_code == 404
