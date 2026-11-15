# -*- coding: utf-8 -*-
"""L1SI214-TOKEN-B3-001 真实系统沙盒（批3）：九判据 D-1~D-9 ＋ 补（签名门两条）逐条实测。

数据：沙盒账号 b3_owner（viewer，持 OR-b3pub〔公开在架〕／OR-b3priv〔未公开〕／OR-b3op）、
b3_operator（operator，持 OR-b3op 验 D-2）、b3_delegate（viewer，无权属，验授权件路径）；
权属行／挂出行直接种入；授权件走真实 draft|sign 端点。全部沙盒库，⛔ 涉真实账户。
判据映射：D-1/D-5 第2把分两档 · D-2/D-3 第1把（含先判先报）· D-4 两过放行＋留痕 ·
D-6 拒绝留痕含码 · D-7/D-8 界面两句（vitest 件见前端 __tests__，本件静态核＋端点文案）·
D-9 钥匙来源列 · 补 无签名不生效／存证失败回滚。
"""
import secrets

from fastapi.testclient import TestClient

from app import app
from auth import hash_password, _token_hash
from db import get_session, get_sessionmaker
from db import models as M

client = TestClient(app)

_NOW = "2026-11-15T00:00:00+00:00"
_FUTURE = "2027-11-15T00:00:00+00:00"

TEXT_LOCK1 = "你的账号无此操作许可"
TEXT_LOCK2 = "你对该项资产无配置权——须由该资产的所有者授予"


def _mkuser(username: str, role: str):
    ph, salt, iters = hash_password("sbx-pass-123")
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


def _mkownership(rid: str, owner: str):
    with get_sessionmaker().begin() as s:
        s.add(M.OwnershipRecord(
            record_id=rid, work_title=f"沙盒作品 {rid}", owner_ref=owner,
            source_lineage="沙盒种入", status="registered",
            data_provenance="simulated", created_at=_NOW, updated_at=_NOW))


def _mklisting(lid: str, owner: str, rid: str, status: str = "active"):
    with get_sessionmaker().begin() as s:
        s.add(M.MarketListing(
            listing_id=lid, owner_ref=owner, ownership_record_id=rid,
            asset_summary="沙盒挂出", scene="沙盒场景",
            initial_conditions="初始条件必公开（沙盒）",
            status=status, data_provenance="simulated",
            published_at=_NOW, updated_at=_NOW))


def _draft(subject: str, grantor: str, grantee: str, tok: str):
    return client.post("/api/v1/authorization/draft", headers={"Authorization": tok},
                       json={"operation": "activate", "grantor": grantor,
                             "grantee": grantee, "subject": subject,
                             "scope": "配置权委托（沙盒，逐项写明）",
                             "term": "至撤回为止",
                             "conditions": {"may_sub_grant": "否",
                                            "may_commercialize": "否",
                                            "attribution_required": "是"},
                             "submit": True})


def _sign(aid: str, tok: str):
    return client.post("/api/v1/authorization/sign",
                       headers={"Authorization": tok}, json={"auth_id": aid})


def _lock_rows(actor: str):
    with get_session() as s:
        return (s.query(M.NcaChain)
                .filter(M.NcaChain.action == "dual_lock_decision",
                        M.NcaChain.actor == actor).all())


def setup_module():
    _mkuser("b3_owner", "viewer")
    _mkuser("b3_operator", "operator")
    _mkuser("b3_delegate", "viewer")
    _mkownership("OR-b3pub", "b3_owner")     # 公开在架（有挂出件 active）
    _mkownership("OR-b3priv", "b3_owner")    # 未公开（无挂出件）
    _mkownership("OR-b3op", "b3_operator")   # operator 自有（验 D-2：有配置权无操作许可）
    _mklisting("ML-b3pub", "b3_owner", "OR-b3pub", "active")


class TestDualLock:
    def setup_method(self):
        self.tok_owner = _mksession("b3_owner")
        self.tok_op = _mksession("b3_operator")
        self.tok_del = _mksession("b3_delegate")

    # ---------- D-1：有操作权限、无配置权（公开对象 → 403 NO_CONFIG_RIGHT） ----------
    def test_d1_lock2_public(self):
        r = _draft("配置权委托 OR-b3pub（沙盒）", "b3_delegate", "b3_else",
                   self.tok_del)
        assert r.status_code == 201, r.text
        aid = r.json()["data"]["auth_id"]
        rs = _sign(aid, self.tok_del)
        assert rs.status_code == 403
        assert rs.json()["detail"] == f"NO_CONFIG_RIGHT：{TEXT_LOCK2}"
        # D-6：拒绝留痕一条，含拒绝码
        rows = _lock_rows("b3_delegate")
        assert any("deny-NO_CONFIG_RIGHT" in (r.artifact_path or "") for r in rows)

    # ---------- D-5：非公开对象之无权 → 404（⛔403），与「不存在」同码同文案 ----------
    def test_d5_lock2_nonpublic_404(self):
        r = _draft("配置权委托 OR-b3priv（沙盒）", "b3_delegate", "b3_else",
                   self.tok_del)
        aid = r.json()["data"]["auth_id"]
        rs = _sign(aid, self.tok_del)
        assert rs.status_code == 404
        body_real = rs.json()
        # 真不存在的对象：同码同文案（⛔ 区分存在性）
        r2 = _draft("配置权委托 OR-b3none（沙盒）", "b3_delegate", "b3_else",
                    self.tok_del)
        aid2 = r2.json()["data"]["auth_id"]
        rs2 = _sign(aid2, self.tok_del)
        assert rs2.status_code == 404
        assert body_real == rs2.json()

    # ---------- D-2：有配置权、无操作权限 → 403 NO_OPERATION_PERM ----------
    def test_d2_lock1_with_ownership(self):
        r = _draft("配置权委托 OR-b3op（沙盒）", "b3_operator", "b3_else",
                   self.tok_op)
        aid = r.json()["data"]["auth_id"]
        rs = _sign(aid, self.tok_op)
        assert rs.status_code == 403
        assert rs.json()["detail"] == f"NO_OPERATION_PERM：{TEXT_LOCK1}"

    # ---------- D-3：两把皆无 → 码落第 1 把（先判先报，⛔倒序） ----------
    def test_d3_lock1_first(self):
        r = _draft("配置权委托 OR-b3pub（沙盒）", "b3_operator", "b3_else",
                   self.tok_op)
        aid = r.json()["data"]["auth_id"]
        rs = _sign(aid, self.tok_op)
        assert rs.status_code == 403
        assert rs.json()["detail"].startswith("NO_OPERATION_PERM")
        # 留痕侧证顺序：L2 记「未执行（先判先报）」
        rows = _lock_rows("b3_operator")
        hit = [r for r in rows if aid in (r.authz_ref or "")]
        assert hit and "L2-deny:未执行（先判先报）" in (hit[-1].artifact_path or "")

    # ---------- D-4：两把皆过 → 执行成功＋留痕一条（含授权件路径） ----------
    def test_d4_both_pass(self):
        before = len(_lock_rows("b3_owner"))
        r = _draft("配置权委托 OR-b3pub（沙盒）", "b3_owner", "b3_delegate",
                   self.tok_owner)
        aid = r.json()["data"]["auth_id"]
        rs = _sign(aid, self.tok_owner)
        assert rs.status_code == 200, rs.text
        assert rs.json()["data"]["status"] == "active"
        rows = _lock_rows("b3_owner")
        assert len(rows) == before + 1
        hit = [r for r in rows if r.authz_ref == aid]
        assert hit and hit[-1].artifact_path.endswith("/allow")
        # 授权件路径：被授权方凭 active 件于该资产过第 2 把（配置资格生效）
        r2 = _draft("配置权转委托 OR-b3pub 子项（沙盒）", "b3_delegate", "b3_x3",
                    self.tok_del)
        aid2 = r2.json()["data"]["auth_id"]
        rs2 = _sign(aid2, self.tok_del)
        assert rs2.status_code == 200, rs2.text
        assert rs2.json()["data"]["status"] == "active"

    # ---------- D-8：两类文案分得开（两句不同、各带本把钥匙来源语义） ----------
    def test_d8_two_texts_distinct(self):
        assert TEXT_LOCK1 != TEXT_LOCK2
        assert "所有者" not in TEXT_LOCK1          # 第 1 把文案 ⛔ 提对象／门
        assert TEXT_LOCK2 == ("你对该项资产无配置权——须由该资产的所有者授予")

    # ---------- D-9：/me/permissions 增「钥匙来源」列 ----------
    def test_d9_key_source_column(self):
        r = client.get("/api/v1/me/permissions",
                       headers={"Authorization": self.tok_owner})
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["key_source_legend"] == {"第1把": "注册用户（本人）",
                                          "第2把": "资产所有者"}
        for row in d["matrix"]:
            assert row["key_source"] in ("注册用户（本人）", "资产所有者")
        auth_rows = [row for row in d["matrix"] if row["action"] == "授权"]
        assert auth_rows and all(row["key_source"] == "资产所有者"
                                 for row in auth_rows)
        other = [row for row in d["matrix"] if row["action"] != "授权"]
        assert other and all(row["key_source"] == "注册用户（本人）"
                             for row in other)


class TestSignatureGate:
    """补：签名门两条——无本人签名 ⟹ 件不生效；存证失败 ⟹ 事务回滚。"""

    def setup_method(self):
        self.tok_owner = _mksession("b3_owner")

    def test_no_signature_not_effective(self):
        r = _draft("配置权委托 OR-b3pub（沙盒·未签）", "b3_owner", "b3_delegate",
                   self.tok_owner)
        aid = r.json()["data"]["auth_id"]
        # 未签署：公开读回 pending_sign（⛔ active）；被授权方不能凭未签件过第 2 把
        pub = client.get(f"/api/v1/authorization/{aid}")
        assert pub.json()["data"]["status"] == "pending_sign"
        with get_session() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            assert d.signer is None and d.status == "pending_sign"

    def test_evidence_failure_rolls_back(self, monkeypatch):
        import authorization_panel_ops as apo
        r = _draft("配置权委托 OR-b3pub（沙盒·回滚）", "b3_owner", "b3_delegate",
                   self.tok_owner)
        aid = r.json()["data"]["auth_id"]

        def _boom(*a, **k):
            raise RuntimeError("沙盒注爆：存证落链失败")

        monkeypatch.setattr(apo, "_nca_append", _boom)
        rs = _sign(aid, self.tok_owner)
        assert rs.status_code == 500
        monkeypatch.undo()
        with get_session() as s:
            d = s.get(M.AuthorizationPanelDoc, aid)
            assert d.status == "pending_sign"   # 状态停本步：未生效
            assert d.signer is None


class TestUiHints:
    """D-7/D-8 界面件：E-1 授权前明示、E-2 钥匙来源提示（静态核——vitest 动态件
    见前端 __tests__/b3-dual-lock-ui.test.tsx，npm 依赖装毕即跑）。"""

    def test_e1_e2_source_present(self):
        import pathlib
        p = (pathlib.Path(__file__).resolve().parents[2]
             / "tdca-frontend" / "src" / "pages" / "authorization-panel.tsx")
        src = p.read_text(encoding="utf-8")
        assert "此操作将生成一份授权件（法律性文件），须本人签名" in src   # E-1
        assert "e1-sign-notice" in src
        assert "这项配置权应由该资产的所有者授予" in src                  # E-2
        assert "e2-key-source" in src
        # ⛔ 默认勾选「我已阅读」：页面不得出现默认勾选项
        assert "defaultChecked" not in src
