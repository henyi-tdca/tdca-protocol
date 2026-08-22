"""value_services · 增值服务包测试（M2 双服务打包统一入口）。"""
import json

import pytest

import value_services
from value_services import main as vs_main


def _s(**kw):
    base = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    base.update(kw)
    return base


class TestValueServicesBundle:
    """双服务打包统一入口。"""

    def test_version(self):
        """包版本 = M2。"""
        assert value_services.VERSION == "2.0.0-M2"

    def test_services_manifest(self):
        """双服务清单。"""
        assert set(value_services.SERVICES.keys()) == {"cog-align", "util-value"}

    def test_unified_cog_align_measure(self, capsys):
        """统一入口 → cog_align measure。"""
        rc = vs_main(["cog-align", "measure",
                      "--a", "a", "--state-a", json.dumps(_s(A=0.9)),
                      "--b", "b", "--state-b", json.dumps(_s(A=0.1))])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "cog_align_pair"

    def test_unified_cog_align_scenario(self, capsys):
        """统一入口 → cog_align scenario（M2 场景包）。"""
        rc = vs_main(["cog-align", "scenario", "--scenario", "tiering",
                      "--a", "a", "--state-a", json.dumps(_s(A=0.9)),
                      "--b", "b", "--state-b", json.dumps(_s(A=0.1))])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert "tier_ab" in report

    def test_unified_util_value_assess(self, capsys):
        """统一入口 → util_value assess。"""
        txs = json.dumps([{"direction": "output", "amount": 100}])
        rc = vs_main(["util-value", "assess", "--asset", "cp", "--tx", txs])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["floor"]["u_observed"] == 100.0

    def test_unified_util_value_entry(self, capsys):
        """统一入口 → util_value entry（M2 入表服务）。"""
        txs = json.dumps([{"direction": "output", "amount": 100}])
        rc = vs_main(["util-value", "entry", "--asset", "cp", "--tx", txs,
                      "--period", "2026-08"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "util_value_entry_report"
        assert report["accounting_entry"]["book_value"] == 100.0

    def test_unified_unknown_cmd_rejected(self):
        """未知服务 → rc 2（非 SystemExit）。"""
        rc = vs_main(["bogus", "measure"])
        assert rc == 2
