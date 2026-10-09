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
        """包版本 = 3.0.0-M1（merchant_loop 并入）。"""
        assert value_services.VERSION == "3.0.0-M1"

    def test_services_manifest(self):
        """三服务清单（merchant_loop 并入）。"""
        assert set(value_services.SERVICES.keys()) == {"cog-align", "util-value", "merchant-loop"}

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

    def test_unified_merchant_loop_publish(self, capsys, tmp_path):
        """统一入口 → merchant-loop publish（第三服务并入）。"""
        import yaml as _y
        cfg = {
            "benefit_id": "B-VS-1", "merchant_id": "M-VS-1",
            "discount": {"rate": 0.10}, "rebate": {"rate": 0.03},
            "valid_from": "2026-09-01", "valid_until": "2026-12-31",
            "stores": ["S-1"], "scene_type": "retail",
            "objective": "o", "constraint": "c", "prior": "p",
            "config_boundary": "b", "distribution": "d", "audit": "a",
        }
        cfg_path = tmp_path / "benefit.yaml"
        cfg_path.write_text(_y.safe_dump(cfg), encoding="utf-8")
        rc = vs_main(["merchant-loop", "publish", "--config", str(cfg_path)])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["benefit_id"] == "B-VS-1"
        assert report["schema"] == "TDCA-MERCHANT-LOOP-BENEFIT-001"

    def test_unified_merchant_loop_roi(self, capsys):
        """统一入口 → merchant-loop roi-report。"""
        rc = vs_main(["merchant-loop", "roi-report",
                      "--benefit-id", "B-1", "--merchant-id", "M-1",
                      "--budget", "10000", "--audience", "2000"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "merchant_loop_roi"
        assert report["no_asset_appreciation"] is True

    def test_unified_unknown_cmd_rejected(self):
        """未知服务 → rc 2（非 SystemExit）。"""
        rc = vs_main(["bogus", "measure"])
        assert rc == 2
