"""tdca_ecoscan · M2 流水线测试（DCD-ECOSCAN-001 M2 验收 B-1~B-4）

B-1 全链自动化: 候选→诊断→邀请→台账 一跑到底（scanner/diagnoser/inviter/ledger 串接）
B-2 分润细则: 邀请函含 15% + 开源方优先 + 社区基金会（宣言 §三 措辞一致性）
B-3 邀请纪律: 仅 TIER-A / 频率闸 ≤2 周 / 幂等防重复 / 流水线上限
B-4 可追溯: 扫描/邀请全量落 NCA 台账 + 邀请函防篡改摘要
"""
import pytest

from tdca_ecoscan.diagnoser import CandidateDiagnoser, TIER_A, TIER_C
from tdca_ecoscan.inviter import InviteGenerator, WEEKLY_INVITE_LIMIT
from tdca_ecoscan.ledger import EcoLedger
from tdca_ecoscan.pipeline import (
    InvitePipeline,
    PROFIT_SHARE_DEFAULT,
    PROFIT_SHARE_CLAUSES,
)
from tdca_ecoscan.scanner import EcoScanner


def _repo(full="deepseek-ai/harness", stars=33000, lic="MIT",
          desc="everything-is-plugin agent framework with append-only session logs",
          pushed="2026-08-20T00:00:00Z", kw=("agent", "harness")):
    return {"repo_full": full, "stars": stars, "license_spdx": lic,
            "description": desc, "pushed_at": pushed, "keywords": list(kw)}


def _tier_a_repo(full="openai/codex-harness"):
    return _repo(full=full, desc="agent harness plugin adapter audit logs multi-agent")


class TestPipelineFullChain:
    """B-1 全链自动化。"""

    def test_run_end_to_end(self, tmp_path):
        """一跑到底：候选 → 诊断 → 邀请 → 台账。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_repo(full="a/harness"),
                           _repo(full="b/harness")], max_invites=2)
        # 候选全部被诊断
        assert len(result.candidates) >= 1
        # TIER-A 全部受邀
        for p in result.candidates:
            assert p.tier == TIER_A
        assert len(result.invited) == len(result.candidates)
        assert all(l.tier == "A" for l in result.invited)
        # 台账已落账
        assert result.ledger_report["total_records"] >= 1
        assert result.ledger_report["invite_count"] == len(result.invited)

    def test_scan_recorded_in_ledger(self, tmp_path):
        """扫描记录落 NCA 台账（可追溯）。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        pipe.run([_repo(full="a/harness")])
        report = pipe._ledger.weekly_report()
        assert report["scan_count"] >= 1

    def test_invite_recorded_with_nca_ref(self, tmp_path):
        """邀请函含 NCA 存证编号且落账。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="x/harness")])
        assert result.invited[0].nca_ref.startswith("NCA-ECOSCAN-")

    def test_auto_mode_selection(self, tmp_path):
        """自动选轨：可审计+分账 → compound。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="y/harness")])
        assert result.invited[0].mode in ("mount", "compound")


class TestProfitSharing:
    """B-2 分润细则（宣言 §三）。"""

    def test_default_rate_15pct(self):
        """默认分润 = 15%（常量锚点）。"""
        assert PROFIT_SHARE_DEFAULT == 0.15

    def test_letter_contains_15pct(self, tmp_path):
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="z/harness")])
        letter = result.invited[0]
        assert "15%" in letter.body

    def test_letter_contains_priority_and_foundation(self, tmp_path):
        """开源方优先 + 社区基金会版税（措辞一致性）。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="w/harness")])
        missing = InvitePipeline.validate_profit_sharing(result.invited[0])
        assert missing == [], f"分润措辞缺失: {missing}"
        assert all(c in result.invited[0].body for c in PROFIT_SHARE_CLAUSES)

    def test_validate_profit_sharing_missing_detected(self):
        """校验器能检出缺失分润措辞的邀请函。"""
        from tdca_ecoscan.inviter import InviteLetter
        bad = InviteLetter(
            invite_id="INV-BAD", repo_full="x/y", mode="mount", tier="A",
            body="无分润表述", nca_ref="NCA-1", created_at="2026-08-23T00:00:00Z",
            provenance="SIMULATED")
        missing = InvitePipeline.validate_profit_sharing(bad)
        assert "profit_share_15pct" in missing


class TestInviteDiscipline:
    """B-3 邀请纪律。"""

    def test_only_tier_a_invited(self, tmp_path):
        """仅 TIER-A 受邀；C 档跳过并记录原因。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="a/harness"),
                           _repo(full="c/util", desc="simple util", stars=10)])
        assert len(result.invited) == 1
        skipped = [s for s in result.skipped if "c/util" in str(s)]
        assert skipped and "not_invited" in str(skipped[0]["reason"])
        assert "tier_C_not_invited" in str(skipped[0]["reason"]) or "tier_B_not_invited" in str(skipped[0]["reason"])

    def test_pipeline_max_invites(self, tmp_path):
        """流水线上限闸（防批量轰炸）。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        repos = [_tier_a_repo(full=f"r{i}/harness") for i in range(6)]
        result = pipe.run(repos, max_invites=3)
        assert len(result.invited) == 3
        assert any(s["reason"] == "pipeline_max_invites_reached" for s in result.skipped)

    def test_duplicate_repo_skipped(self, tmp_path):
        """同 repo 本次运行幂等去重。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        repos = [_tier_a_repo(full="dup/harness")] * 3
        result = pipe.run(repos)
        # 同一 repo 仅 1 封邀请
        assert len(result.invited) == 1
        assert any(s["reason"] == "duplicate_in_run" for s in result.skipped)

    def test_weekly_frequency_gate(self, tmp_path):
        """台账频率闸：同一 repo 跨运行 ≤2/周（防轰炸）。"""
        pipe1 = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        pipe1.run([_tier_a_repo(full="freq/harness")])
        pipe2 = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        pipe2.run([_tier_a_repo(full="freq/harness")])
        pipe3 = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result3 = pipe3.run([_tier_a_repo(full="freq/harness")])
        # 第 3 次周邀请超限 → 跳过
        assert len(result3.invited) == 0
        assert any("NSFL-TRIGGER" in str(s["reason"]) for s in result3.skipped)

    def test_invite_limit_constant(self):
        assert WEEKLY_INVITE_LIMIT == 2


class TestTraceability:
    """B-4 可追溯。"""

    def test_letter_digest_stable(self):
        """邀请函摘要稳定可比对（防篡改）。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_tier_a_repo(full="dig/harness")])[0]
        p = d.diagnose(t)
        l1 = InviteGenerator().generate(p)
        assert InvitePipeline.letter_digest(l1) == InvitePipeline.letter_digest(l1)
        assert InvitePipeline.letter_digest(l1).startswith("sha256:")

    def test_pipeline_result_dict_serializable(self, tmp_path):
        """结果可 JSON 序列化（接口熵=0）。"""
        import json
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="json/harness")])
        json.dumps(result.to_dict())  # 不抛异常即通过

    def test_ledger_weekly_report_shape(self, tmp_path):
        """台账周报结构完整。"""
        pipe = InvitePipeline(ledger=EcoLedger(target_dir=str(tmp_path)))
        result = pipe.run([_tier_a_repo(full="shape/harness")])
        r = result.ledger_report
        assert set(r) >= {"total_records", "scan_count", "invite_count", "invited_repos"}
