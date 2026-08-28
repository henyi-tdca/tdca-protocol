"""tdca_ecoscan · 评论模式 M1 测试（TDCA-HANDOFF-KIMI-ECOSCAN-COMMENT-M1-001）

C-1 ECOACT fail-closed: 七字段缺一即拒（无存证不发送）
C-2 频率闸: 评论与邀请共享 ≤2 条/周/目标触达预算
C-3 话术: 三段式结构 + 500 字左右（200~700 强制）
C-4 发送纪律: 无 token 拒绝 / 发送失败不上台账 / 台账回填五要素
"""
import pytest

from tdca_ecoscan.commenter import (
    COMMENT_MAX_LEN, COMMENT_MIN_LEN, ECOACT_REQUIRED_FIELDS,
    CommentComposer, Commenter,
)
from tdca_ecoscan.inviter import InviteGenerator
from tdca_ecoscan.ledger import EcoLedger
from tdca_ecoscan.diagnoser import CandidateProfile, TIER_A
from tdca_ecoscan.scanner import ScanTarget


def _ledger(tmp_path):
    return EcoLedger(target_dir=str(tmp_path / "nca"), operator="test")


def _ecoact(repo="openai/codex", **kw):
    base = {
        "repo_full": repo, "mode": "comment", "license_spdx": "Apache-2.0",
        "invite_nca_ref": "NCA-ECOSCAN-20260828-INV-TEST",
        "response_status": "pending",
        "profit_sharing": "15% 模拟态 NCA 记账",
        "compliance": "只赋能不改码/无强制诱导/跨境外汇流程注明",
    }
    base.update(kw)
    return base


def _sender_ok(url="https://github.com/openai/codex/issues/1#issuecomment-1"):
    def send(repo_full, issue_n, body, token):
        return {"html_url": url, "id": 1}
    return send


def _sender_fail(*_a, **_kw):
    raise RuntimeError("评论发送失败 HTTP 403")


def _diag(n=210):
    return ("贵项目在身份互操作机制上做得非常扎实，设计思路与我们的观察结论一致。"
            "不过从制度层视角看存在真问题：协作的可信交付与结算环节缺少可验证的确权与熔断机制，"
            "信任停留在技术执行层，出问题后责任链与追溯成本都在上升。")[:n]


class TestEcoactFailClosed:
    def test_full_ecoact_pass(self, tmp_path):
        """七字段齐备 → 放行发送。"""
        c = Commenter(_ledger(tmp_path), sender=_sender_ok())
        rec = c.post("openai/codex", 1, CommentComposer().compose("openai/codex", _diag()),
                     _ecoact(), token="t")
        assert rec.url and rec.repo_full == "openai/codex"

    @pytest.mark.parametrize("field", ECOACT_REQUIRED_FIELDS)
    def test_missing_each_field_rejected(self, tmp_path, field):
        """七字段逐一缺失 → 全部 fail-closed（无存证不发送）。"""
        eco = _ecoact()
        eco[field] = ""
        c = Commenter(_ledger(tmp_path), sender=_sender_ok())
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            c.post("openai/codex", 1, "x" * 300, eco, token="t")

    def test_no_ecoact_no_send(self, tmp_path):
        """存证缺失时 sender 零调用。"""
        called = []
        c = Commenter(_ledger(tmp_path),
                      sender=lambda *a: called.append(a) or {"html_url": "x"})
        with pytest.raises(ValueError):
            c.post("openai/codex", 1, "x" * 300, {}, token="t")
        assert called == []


class TestRateGate:
    def test_comment_counts_as_touch(self, tmp_path):
        """已有 2 条评论触达 → 第 3 条拒绝。"""
        lg = _ledger(tmp_path)
        c = Commenter(lg, sender=_sender_ok())
        body = CommentComposer().compose("openai/codex", _diag())
        c.post("openai/codex", 1, body, _ecoact(), token="t")
        c.post("openai/codex", 2, body, _ecoact(), token="t")
        with pytest.raises(ValueError, match="频率超限"):
            c.post("openai/codex", 3, body, _ecoact(), token="t")

    def test_invites_share_touch_budget(self, tmp_path):
        """邀请计入同一触达预算（2 邀请后评论被拒）。"""
        lg = _ledger(tmp_path)
        gen = InviteGenerator()
        target = ScanTarget(repo_full="openai/codex", stars=1000,
                            license_spdx="Apache-2.0", pushed_at="2026-08-01T00:00:00Z",
                            description="agent audit", keywords=["agent"], url="")
        profile = CandidateProfile(
            target=target, non_invasive=True, auditable=True, settlement_pain=True,
            license_compliant=True, fit_score=0.9, tier=TIER_A, rationale="t")
        lg.record_invite(gen.generate(profile, mode="mount"))
        lg.record_invite(gen.generate(profile, mode="mount"))
        c = Commenter(lg, sender=_sender_ok())
        with pytest.raises(ValueError, match="频率超限"):
            c.post("openai/codex", 1, CommentComposer().compose("openai/codex", _diag()),
                   _ecoact(), token="t")

    def test_one_touch_allows_second(self, tmp_path):
        """1 条触达 → 第 2 条放行。"""
        lg = _ledger(tmp_path)
        c = Commenter(lg, sender=_sender_ok())
        body = CommentComposer().compose("openai/codex", _diag())
        c.post("openai/codex", 1, body, _ecoact(), token="t")
        rec = c.post("openai/codex", 2, body, _ecoact(), token="t")
        assert rec.comment_id

    def test_other_repo_unaffected(self, tmp_path):
        """频率闸按目标隔离。"""
        lg = _ledger(tmp_path)
        c = Commenter(lg, sender=_sender_ok())
        body = CommentComposer().compose("a/b", _diag())
        c.post("a/b", 1, body, _ecoact(repo="a/b"), token="t")
        c.post("a/b", 2, body, _ecoact(repo="a/b"), token="t")
        rec = c.post("c/d", 1, CommentComposer().compose("c/d", _diag()),
                     _ecoact(repo="c/d"), token="t")
        assert rec.repo_full == "c/d"


class TestComposer:
    def test_three_sections_present(self):
        body = CommentComposer().compose("openai/codex", _diag())
        assert "【诊断】" in body and "【TDCA 解法】" in body and "【交流邀请】" in body

    def test_over_700_rejected(self):
        with pytest.raises(ValueError, match="超长"):
            CommentComposer().compose("openai/codex", _diag() + "长" * 500)

    def test_too_short_rejected(self):
        with pytest.raises(ValueError, match="过短"):
            CommentComposer().compose("openai/codex", "亮点不错。")

    def test_empty_diagnosis_rejected(self):
        with pytest.raises(ValueError, match="增量价值"):
            CommentComposer().compose("openai/codex", "  ")

    def test_default_length_in_range(self):
        body = CommentComposer().compose("openai/codex", _diag())
        assert COMMENT_MIN_LEN <= len(body) <= COMMENT_MAX_LEN


class TestSendDiscipline:
    def test_no_token_rejected(self, tmp_path):
        c = Commenter(_ledger(tmp_path), sender=_sender_ok())
        with pytest.raises(ValueError, match="token"):
            c.post("openai/codex", 1, "x" * 300, _ecoact(), token=None)

    def test_send_failure_no_ledger(self, tmp_path):
        """发送失败 → 不上台账（fail-closed）。"""
        lg = _ledger(tmp_path)
        c = Commenter(lg, sender=_sender_fail)
        with pytest.raises(RuntimeError):
            c.post("openai/codex", 1, "x" * 300, _ecoact(), token="t")
        assert lg.weekly_report()["comment_count"] == 0

    def test_ledger_fields_complete(self, tmp_path):
        """台账回填五要素：repo_full/issue_n/url/时间/response_status。"""
        lg = _ledger(tmp_path)
        c = Commenter(lg, sender=_sender_ok())
        rec = c.post("openai/codex", 7, CommentComposer().compose("openai/codex", _diag()),
                     _ecoact(), token="t")
        assert rec.repo_full == "openai/codex" and rec.issue_n == 7
        assert rec.url and rec.created_at and rec.response_status == "pending"
        report = lg.weekly_report()
        assert report["comment_count"] == 1
        assert "openai/codex" in report["commented_repos"]
