"""cog_align · M2 评测场景包测试（DCD-COG-ALIGN-001 §五 M2）

三场景:
  1. 思想病毒防御（认知漂移检测）
  2. 认知漂移监测（时间序列收敛/漂移）
  3. 对齐度分档（高度/中度/低度/不可对齐）
"""
import json

import pytest

from cog_align.api import CogAlignAPIHandler
from cog_align.cli import main as cli_main
from cog_align.scenarios import CogAlignScenarios


def _s(**kw):
    base = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    base.update(kw)
    return base


class TestThoughtVirusDefense:
    """场景 1: 思想病毒防御（认知漂移检测）。"""

    def test_drift_alert_detected(self):
        """认知状态偏离基准且持续增大 → DRIFT_ALERT。"""
        sc = CogAlignScenarios()
        baseline = _s(A=0.5, D=0.5, L=0.5, C=0.5, SC=0.5)
        series = [
            ("t0", _s(A=0.5, SC=0.5)),
            ("t1", _s(A=0.7, SC=0.3)),
            ("t2", _s(A=0.9, SC=0.1)),
        ]
        r = sc.thought_virus_defense("agent-x", series, baseline)
        assert r.verdict == "DRIFT_ALERT"
        assert "人工复核" in r.recommendation
        assert r.scenario == "thought_virus_defense"

    def test_no_drift_when_stable(self):
        """认知状态稳定 → NO_DRIFT。"""
        sc = CogAlignScenarios()
        baseline = _s(A=0.5, SC=0.5)
        series = [
            ("t0", _s(A=0.5, SC=0.5)),
            ("t1", _s(A=0.51, SC=0.49)),
            ("t2", _s(A=0.5, SC=0.5)),
        ]
        r = sc.thought_virus_defense("agent-y", series, baseline)
        assert r.verdict == "NO_DRIFT"

    def test_requires_two_points(self):
        """<2 时点 → 拒绝。"""
        sc = CogAlignScenarios()
        with pytest.raises(ValueError):
            sc.thought_virus_defense("a", [("t0", _s())], _s())

    def test_invalid_state_rejected(self):
        """越界状态 → NSFL-TRIGGER。"""
        sc = CogAlignScenarios()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            sc.thought_virus_defense("a", [("t0", _s()), ("t1", _s(SC=2.0))], _s())

    def test_provenance_label(self):
        """ID92: provenance 标注。"""
        sc = CogAlignScenarios()
        r = sc.thought_virus_defense("a", [("t0", _s()), ("t1", _s())], _s(),
                                     provenance="REAL-API")
        assert r.provenance == "REAL-API"


class TestDriftMonitor:
    """场景 2: 认知漂移监测。"""

    def test_converging_verdict(self):
        """距离递减 → CONVERGING。"""
        sc = CogAlignScenarios()
        series = [
            ("t0", _s(A=0.9, SC=0.9), _s(A=0.1, SC=0.1)),
            ("t1", _s(A=0.6, SC=0.6), _s(A=0.4, SC=0.4)),
            ("t2", _s(A=0.52, SC=0.52), _s(A=0.5, SC=0.5)),
        ]
        r = sc.cognitive_drift_monitor("a", "b", series)
        assert r.verdict == "CONVERGING"
        assert r.detail["final_gap"] > 0

    def test_drift_alert_verdict(self):
        """距离放大 → DRIFT_ALERT（协商协议建议）。"""
        sc = CogAlignScenarios()
        series = [
            ("t0", _s(A=0.52, SC=0.52), _s(A=0.5, SC=0.5)),
            ("t1", _s(A=0.7, SC=0.7), _s(A=0.3, SC=0.3)),
            ("t2", _s(A=0.9, SC=0.9), _s(A=0.1, SC=0.1)),
        ]
        r = sc.cognitive_drift_monitor("a", "b", series)
        assert r.verdict == "DRIFT_ALERT"
        assert "协商协议" in r.recommendation

    def test_stable_verdict(self):
        """距离平稳 → STABLE。"""
        sc = CogAlignScenarios()
        series = [
            ("t0", _s(A=0.5), _s(A=0.5)),
            ("t1", _s(A=0.5), _s(A=0.5)),
            ("t2", _s(A=0.5), _s(A=0.5)),
        ]
        r = sc.cognitive_drift_monitor("a", "b", series)
        assert r.verdict == "STABLE"


class TestAlignmentTiering:
    """场景 3: 对齐度分档。"""

    def test_high_alignment(self):
        """近距离 → 高度对齐。"""
        sc = CogAlignScenarios()
        t = sc.alignment_tiering("a", _s(A=0.9, SC=0.9), "b", _s(A=0.89, SC=0.9))
        assert t.tier_ab == "高度对齐"

    def test_unalignable(self):
        """全维相反 → 不可对齐（d≈0.9，difficulty≈0.407 < 0.45）。"""
        sc = CogAlignScenarios()
        t = sc.alignment_tiering(
            "a", _s(A=0.95, D=0.95, L=0.95, C=0.95, SC=0.95),
            "b", _s(A=0.05, D=0.05, L=0.05, C=0.05, SC=0.05))
        assert t.tier_ab == "不可对齐"

    def test_asymmetric_tiering(self):
        """不对称性产品化: 双向分档不一致（命题 3.10）。"""
        sc = CogAlignScenarios()
        t = sc.alignment_tiering("high", _s(A=0.95, SC=0.95, D=0.95),
                                 "low", _s(A=0.15, SC=0.15, D=0.15))
        assert t.asym_tier is True
        assert t.tier_ab != t.tier_ba

    def test_tier_matrix(self):
        """多主体分档矩阵（SELF 对角 + 分档标注）。"""
        sc = CogAlignScenarios()
        matrix = sc.tier_matrix({"a": _s(A=0.9), "b": _s(A=0.5), "c": _s(A=0.1)})
        assert matrix["a"]["a"] == "SELF"
        assert "对齐" in matrix["a"]["c"]
        assert len(matrix) == 3


class TestScenarioAPIAndCLI:
    """M2 对外接口（API + CLI）。"""

    def test_api_thought_virus(self):
        """API: /scenarios/thought-virus。"""
        from http.server import HTTPServer
        from urllib import request

        CogAlignAPIHandler.service = None  # scenarios 自建 service
        CogAlignAPIHandler.notary = None
        CogAlignAPIHandler.auto_notarize = False
        server = HTTPServer(("127.0.0.1", 0), CogAlignAPIHandler)
        port = server.server_address[1]
        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "subject": "agent-x",
                "baseline_state": _s(),
                "state_series": [["t0", _s()], ["t1", _s(A=0.8, SC=0.2)]],
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/cog-align/scenarios/thought-virus",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert payload["report"]["scenario"] == "thought_virus_defense"
            assert payload["report"]["verdict"] in ("DRIFT_ALERT", "NO_DRIFT")
        finally:
            server.shutdown()

    def test_api_tiering(self):
        """API: /scenarios/tiering（单对）。"""
        from http.server import HTTPServer
        from urllib import request

        CogAlignAPIHandler.service = None
        CogAlignAPIHandler.notary = None
        CogAlignAPIHandler.auto_notarize = False
        server = HTTPServer(("127.0.0.1", 0), CogAlignAPIHandler)
        port = server.server_address[1]
        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "subject_a": "a", "state_a": _s(A=0.9),
                "subject_b": "b", "state_b": _s(A=0.1),
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/cog-align/scenarios/tiering",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert "tier_ab" in payload["report"]
        finally:
            server.shutdown()

    def test_cli_scenario_tiering(self, capsys):
        """CLI: scenario tiering。"""
        rc = cli_main(["scenario", "--scenario", "tiering",
                       "--a", "a", "--state-a", json.dumps(_s(A=0.9)),
                       "--b", "b", "--state-b", json.dumps(_s(A=0.1))])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert "tier_ab" in report

    def test_cli_scenario_unknown(self, capsys):
        """CLI: 未知场景 → NSFL 拒绝。"""
        with pytest.raises(SystemExit):
            cli_main(["scenario", "--scenario", "bogus"])
