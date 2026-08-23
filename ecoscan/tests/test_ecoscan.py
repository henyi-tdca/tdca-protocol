"""tdca_ecoscan · M1 测试（DCD-ECOSCAN-001 验收 A-1~A-5）

A-1 雷达扫描: 关键词/活跃过滤正确
A-2 候选诊断: 制度契合度评估正确（License 合规前置）
A-3 合规内置: 不触碰非公开仓/非 OSI 许可（AUDIT-001）
A-4 邀请纪律: 频率限制 + 台账防重复（≤2 条/周/目标）
A-5 测试: ≥15 用例全绿（M1）
"""
import pytest

from tdca_ecoscan.diagnoser import TIER_A, TIER_B, TIER_C, CandidateDiagnoser
from tdca_ecoscan.inviter import WEEKLY_INVITE_LIMIT, InviteGenerator
from tdca_ecoscan.ledger import EcoLedger
from tdca_ecoscan.scanner import EcoScanner, ScanTarget


def _repo(full="deepseek-ai/harness", stars=33000, lic="MIT",
          desc="everything-is-plugin agent framework with append-only session logs",
          pushed="2026-08-20T00:00:00Z", kw=("agent", "harness")):
    return {"repo_full": full, "stars": stars, "license_spdx": lic,
            "description": desc, "pushed_at": pushed, "keywords": list(kw)}


class TestScanner:
    """A-1 雷达扫描。"""

    def test_scan_static_ok(self):
        s = EcoScanner()
        targets = s.scan_static([_repo()])
        assert len(targets) == 1
        assert targets[0].license_spdx == "MIT"

    def test_scan_rejects_no_license(self):
        """无 License → AUDIT-001 拒绝（A-3）。"""
        s = EcoScanner()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            s.scan_static([_repo(lic=None)])

    def test_rejects_non_osi_license(self):
        """非 OSI 许可（如 Proprietary）→ 拒绝。"""
        s = EcoScanner()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            s.scan_static([_repo(lic="Proprietary")])

    def test_recent_active(self):
        s = EcoScanner()
        t = s.scan_static([_repo(pushed="2026-08-20T00:00:00Z")])[0]
        assert s.is_recent(t, days=30) is True

    def test_recent_stale(self):
        s = EcoScanner()
        t = s.scan_static([_repo(pushed="2026-01-01T00:00:00Z")])[0]
        assert s.is_recent(t, days=30) is False

    def test_recent_no_timestamp(self):
        s = EcoScanner()
        t = s.scan_static([_repo(pushed=None)])[0]
        assert s.is_recent(t) is False


class TestDiagnoser:
    """A-2 候选诊断。"""

    def test_tier_a_high_fit(self):
        """DSH 类（插件+审计+分账）→ TIER-A。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo()])[0]
        p = d.diagnose(t)
        assert p.tier == TIER_A
        assert p.license_compliant is True
        assert p.fit_score >= 0.75

    def test_tier_c_no_signal(self):
        """无契合信号 → TIER-C。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(desc="simple utility library", kw=())])[0]
        p = d.diagnose(t)
        assert p.tier == TIER_C

    def test_tier_c_bad_license(self):
        """License 不合规 → TIER-C + fit 0（A-3）。"""
        d = CandidateDiagnoser()
        # 通过诊断器（非 scan_static 硬拒）验证合规前置
        t = ScanTarget(repo_full="x/y", stars=10, license_spdx="UNKNOWN",
                       pushed_at=None, description="agent log", keywords=[],
                       url="https://github.com/x/y")
        p = d.diagnose(t)
        assert p.tier == TIER_C
        assert p.fit_score == 0.0
        assert p.license_compliant is False

    def test_tier_b_medium(self):
        """部分信号 → TIER-B。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(desc="agent workflow engine", kw=("agent", "orchestrator"))])[0]
        p = d.diagnose(t)
        assert p.tier in (TIER_B, TIER_A)  # 至少 B

    def test_route_groups(self):
        """批量路由三档分组。"""
        d = CandidateDiagnoser()
        s = EcoScanner()
        targets = s.scan_static([
            _repo(full="a/harness", desc="agent framework plugin logs"),
            _repo(full="b/util", desc="simple util", stars=10),
        ])
        routed = d.route(targets)
        assert set(routed.keys()) == {TIER_A, TIER_B, TIER_C}

    def test_star_bonus(self):
        """高星加分。"""
        d = CandidateDiagnoser()
        # 用非目标优先级仓库（避免白名单加分封顶干扰）
        t1 = EcoScanner().scan_static([_repo(full="plain/util", desc="agent plugin", stars=100)])[0]
        t2 = EcoScanner().scan_static([_repo(full="plain/util", desc="agent plugin", stars=5000)])[0]
        assert d.diagnose(t2).fit_score > d.diagnose(t1).fit_score

    def test_float_boundary_no_misjudge(self):
        """浮点边界修正：0.35+0.1 不得误判为 C（应 ≥ B）。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(full="x/harness", desc="plugin", stars=2000, kw=("harness",))])[0]
        p = d.diagnose(t)
        assert p.tier != TIER_C

    def test_target_priority_dsh_upgraded_to_a(self):
        """目标优先级（宣言 §六）：deepseek harness 身份命中 → 定向加分 → TIER-A。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([
            {"repo_full": "deepseek-ai/deepseek-harness", "stars": 185601,
             "license_spdx": "MIT", "description": "DeepSeek Harness: Everything is a Plugin.",
             "pushed_at": "2026-08-20T00:00:00Z", "keywords": ["deepseek harness"]}])[0]
        p = d.diagnose(t)
        assert p.tier == TIER_A
        assert p.fit_score >= 0.75

    def test_target_priority_not_generalized(self):
        """目标优先级加分不泛化：非 deepseek/codex 的 harness 不受定向加分。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(full="other/harness", desc="plugin", stars=2000, kw=("harness",))])[0]
        p = d.diagnose(t)
        # 无定向加分：0.35+0.1=0.45 → B（非 A）
        assert p.tier in (TIER_B, TIER_C)


class TestInviter:
    """A-4 邀请纪律。"""

    def test_generate_mount(self):
        """挂载话术生成（TIER-A）。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo(desc="agent plugin adapter")])[0]
        p = d.diagnose(t)
        letter = InviteGenerator().generate(p, mode="mount")
        assert letter.mode == "mount"
        assert "不改变您的任何代码" in letter.body
        assert letter.nca_ref.startswith("NCA-ECOSCAN-")

    def test_generate_compound(self):
        """化合话术生成。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(desc="agent framework append-only audit logs multi-agent")])[0]
        p = d.diagnose(t)
        assert p.tier == TIER_A
        letter = InviteGenerator().generate(p, mode="compound")
        assert letter.mode == "compound"
        assert "化合" in letter.body

    def test_auto_mode_selection(self):
        """自动选轨：可审计+分账 → compound。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static(
            [_repo(desc="agent framework append-only session logs multi-agent")])[0]
        p = d.diagnose(t)
        assert p.tier == TIER_A
        letter = InviteGenerator().generate(p)
        assert letter.mode == "compound"

    def test_tier_b_rejected(self):
        """TIER-B/C 不发出邀请（礼貌纪律）。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo(desc="agent workflow", kw=("agent",))])[0]
        p = d.diagnose(t)
        if p.tier != TIER_A:
            with pytest.raises(ValueError, match="NSFL-TRIGGER"):
                InviteGenerator().generate(p)

    def test_dynamic_profit_sharing_in_body(self):
        """邀请函含动态分润 15% 表述（宣言 §三）。"""
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo(desc="agent plugin adapter")])[0]
        p = d.diagnose(t)
        letter = InviteGenerator().generate(p, mode="mount")
        assert "15%" in letter.body
        assert "开源授权规定" in letter.body
        assert "社区基金会" in letter.body


class TestLedger:
    """A-4 台账防重复/频率。"""

    def test_record_scan(self, tmp_path):
        ledger = EcoLedger(target_dir=str(tmp_path))
        rec = ledger.record_scan([_repo()])
        assert rec["NCA-ID"].startswith("NCA-ECOSCAN-")
        assert rec["Operation-Type"] == "EcoScan-scan"

    def test_invite_frequency_limit(self, tmp_path):
        """周邀请 ≤2/目标（防轰炸）。"""
        ledger = EcoLedger(target_dir=str(tmp_path))
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo(full="dsh/harness")])[0]
        p = d.diagnose(t)
        gen = InviteGenerator()
        assert p.tier == TIER_A
        ledger.record_invite(gen.generate(p, "mount"))
        ledger.record_invite(gen.generate(p, "mount"))
        # 第 3 次超限 → NSFL 拒绝
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            ledger.record_invite(gen.generate(p, "mount"))

    def test_weekly_report(self, tmp_path):
        ledger = EcoLedger(target_dir=str(tmp_path))
        d = CandidateDiagnoser()
        t = EcoScanner().scan_static([_repo(full="a/harness"), _repo(full="b/harness")])[0]
        p = d.diagnose(t)
        ledger.record_scan([_repo()])
        if p.tier == TIER_A:
            ledger.record_invite(InviteGenerator().generate(p, "mount"))
        report = ledger.weekly_report()
        assert report["total_records"] >= 1
        assert "invite_count" in report

    def test_invite_limit_constant(self):
        assert WEEKLY_INVITE_LIMIT == 2
