"""tdca_ecoscan · AutoForker 测试（TDCA-AUTOFORK-001）

C-1 五门判定: 宽松许可过滤 / 契合分级（仅 A/B）
C-2 材料生成: TDCA-Agreement.yaml + README 声明（含模拟态分润 + 上游版权）
C-3 半自动: plan 不执行（待确认）；execute 需 token
C-4 台账: NCA 存证（模拟态账本，凭账本转实际结算）
"""
import pytest

from tdca_ecoscan.forker import AutoForker, PERMISSIVE_LICENSES
from tdca_ecoscan.scanner import EcoScanner


def _repo(full="openai/codex", stars=113851, lic="Apache-2.0",
          desc="Lightweight coding agent with audit logs and plugin system",
          pushed="2026-08-23T00:00:00Z", kw=("agent", "codex")):
    return {"repo_full": full, "stars": stars, "license_spdx": lic,
            "description": desc, "pushed_at": pushed, "keywords": list(kw)}


class TestLicenseGate:
    def test_permissive_licenses(self):
        """仅宽松许可入池（GPL 传染性拒绝）。"""
        assert "MIT" in PERMISSIVE_LICENSES
        assert "Apache-2.0" in PERMISSIVE_LICENSES
        assert "GPL-3.0" not in PERMISSIVE_LICENSES

    def test_reject_copyleft(self):
        f = AutoForker()
        plans = f.plan([_repo(lic="GPL-3.0", full="gpl/project")])
        assert len(plans) == 0

    def test_reject_no_license(self):
        """无 License → scan_static 硬拒（AUDIT-001 ValueError）。"""
        f = AutoForker()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            f.plan([_repo(lic=None)])


class TestTierGate:
    def test_only_ab_planned(self):
        f = AutoForker()
        # 高契合（插件+审计+分账）→ A 档入计划
        plans = f.plan([_repo(full="a/harness")])
        assert len(plans) == 1
        assert plans[0].tier in ("A", "B")

    def test_low_fit_skipped(self):
        f = AutoForker()
        # 无契合信号 → C 档不入计划
        plans = f.plan([_repo(full="c/util", desc="simple utility", stars=10, kw=())])
        assert len(plans) == 0

    def test_max_plans(self):
        f = AutoForker()
        repos = [_repo(full=f"r{i}/h") for i in range(6)]
        plans = f.plan(repos, max_plans=3)
        assert len(plans) == 3


class TestMaterialGen:
    def test_agreement_contains_key_clauses(self):
        f = AutoForker()
        plan = f.plan([_repo(full="openai/codex")])[0]
        assert "upstream" in plan.agreement_yaml
        assert "0.15" in plan.agreement_yaml          # 15% 分润
        assert "simulated" in plan.agreement_yaml      # 模拟态
        assert "no-source-modify" in plan.agreement_yaml  # 不改码红线

    def test_readme_declares_upstream_copyright(self):
        f = AutoForker()
        plan = f.plan([_repo(full="openai/codex")])[0]
        assert "版权归原作者" in plan.readme_snippet
        assert "TDCA 协议层附加版本" in plan.readme_snippet
        assert "未修改任何上游源码" in plan.readme_snippet
        assert "凭账本转实际结算" in plan.readme_snippet  # 模拟态账本转换裁定

    def test_plan_no_execution_by_default(self):
        """半自动：plan 仅生成材料，不执行 fork。"""
        f = AutoForker()
        plans = f.plan([_repo(full="openai/codex")])
        assert len(plans) == 1
        # 无 token 参数——execute 必须显式调用
        assert hasattr(f, "execute")


class TestLedger:
    def test_ledger_simulated_mode(self):
        f = AutoForker()
        plan = f.plan([_repo(full="openai/codex")])[0]
        rec = AutoForker.ledger_record(plan, executed=False)
        assert rec["mode"] == "simulated"
        assert rec["repo_full"] == "openai/codex"
        assert rec["payload_hash"].startswith("sha256:")

    def test_ledger_nca_id(self):
        f = AutoForker()
        plan = f.plan([_repo(full="openai/codex")])[0]
        rec = AutoForker.ledger_record(plan, executed=True)
        assert rec["NCA-ID"].startswith("NCA-ECOSCAN-FORK-")
        assert rec["executed"] is True
