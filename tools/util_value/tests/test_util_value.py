"""util_value · 效用价值评估引擎测试套件（DCD-UTIL-VALUE-001 M1 验收 A-1~A-6）

验收项映射:
  A-1 效用下限: U_observed=Σ(销项+进项)（对照 TDCA-UTILITY-OBSERVABLE-001）
  A-2 五阶分层: 分层评估输出正确（权重可配）
  A-3 入表报告: 结构化评估报告（地板值/分层/依据/存证）
  A-4 口径约束: MOU 地板语义（不输出主观估值）
  A-5 ≥15 用例全绿（含地板/分层/边界/空流 fail-closed）
  A-6 回归（toolchain 全套——外部 pytest 执行）
"""
import json
import threading

import pytest

from util_value.api import UtilValueAPIHandler
from util_value.cli import main as cli_main
from util_value.engine import UtilValueService
from util_value.notary import UtilValueNotary
from util_value.report import build_assessment_report


def _tx(direction, amount, tier=None):
    d = {"direction": direction, "amount": amount}
    if tier is not None:
        d["tier"] = tier
    return d


class TestObservableFloor:
    """A-1 效用下限。"""

    def test_floor_output_only(self):
        """纯销项: U_observed = Σ销项。"""
        svc = UtilValueService()
        floor = svc.observable_floor("asset-1", [
            _tx("output", 100), _tx("output", 50),
        ])
        assert floor.u_observed == 150.0
        assert floor.output_total == 150.0
        assert floor.input_total == 0.0
        assert floor.tx_count == 2

    def test_floor_input_only(self):
        """纯进项: U_observed = Σ进项。"""
        svc = UtilValueService()
        floor = svc.observable_floor("asset-2", [
            _tx("input", 30), _tx("input", 20),
        ])
        assert floor.u_observed == 50.0

    def test_floor_bidirectional_sum(self):
        """双向计量: U_observed = Σ销项 + Σ进项（双向显示性偏好）。"""
        svc = UtilValueService()
        floor = svc.observable_floor("asset-3", [
            _tx("output", 100), _tx("output", 40),
            _tx("input", 30), _tx("input", 10),
        ])
        assert floor.u_observed == 180.0
        assert floor.output_total == 140.0
        assert floor.input_total == 40.0

    def test_floor_empty_fail_closed(self):
        """空流 fail-closed: U_observed = 0（合法地板，禁止无锚估值）。"""
        svc = UtilValueService()
        floor = svc.observable_floor("asset-empty", [])
        assert floor.u_observed == 0.0
        assert floor.tx_count == 0

    def test_floor_invalid_direction(self):
        """非法方向 → NSFL-TRIGGER 拒绝。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.observable_floor("a", [{"direction": "sideways", "amount": 10}])

    def test_floor_invalid_amount(self):
        """负金额/非数值 → 拒绝。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.observable_floor("a", [_tx("output", -5)])
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.observable_floor("a", [{"direction": "output", "amount": "x"}])

    def test_floor_not_a_list(self):
        """非列表交易流 → 拒绝。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.observable_floor("a", "not-a-list")

    def test_floor_provenance_label(self):
        """ID92: provenance 标注默认 SIMULATED，可显式 REAL。"""
        svc = UtilValueService()
        assert svc.observable_floor("a", [_tx("output", 1)]).provenance == "SIMULATED"
        f = svc.observable_floor("a", [_tx("output", 1)], provenance="REAL-TAX-CHAIN")
        assert f.provenance == "REAL-TAX-CHAIN"


class TestTierAssessment:
    """A-2 五阶分层。"""

    def test_tier_all_five_present(self):
        """五阶全输出（IP/知识/交换/场景/认知 NCA）。"""
        svc = UtilValueService()
        txs = [
            _tx("output", 100, tier="ip"),
            _tx("output", 50, tier="knowledge"),
            _tx("output", 25, tier="exchange"),
            _tx("output", 15, tier="scenario"),
            _tx("output", 10, tier="cognitive_nca"),
        ]
        tiers = svc.tier_assessment("asset-t", txs)
        assert set(tiers.tiers.keys()) == {
            "ip", "knowledge", "exchange", "scenario", "cognitive_nca"}
        assert tiers.tiers["ip"]["amount"] == 100.0
        assert tiers.tiers["cognitive_nca"]["amount"] == 10.0

    def test_tier_weighted_total_equals_floor(self):
        """分层汇总 = U_observed（不新增估值，地板语义）。"""
        svc = UtilValueService()
        txs = [
            _tx("output", 100, tier="ip"),
            _tx("input", 50, tier="knowledge"),
        ]
        tiers = svc.tier_assessment("asset-w", txs)
        floor = svc.observable_floor("asset-w", txs)
        assert tiers.weighted_total == floor.u_observed == 150.0

    def test_tier_shares_sum_to_one(self):
        """分层构成占比之和 = 1。"""
        svc = UtilValueService()
        txs = [
            _tx("output", 60, tier="ip"),
            _tx("output", 40, tier="exchange"),
        ]
        tiers = svc.tier_assessment("asset-s", txs)
        shares = sum(t["share"] for t in tiers.tiers.values())
        assert abs(shares - 1.0) < 1e-9

    def test_tier_weights_configurable(self):
        """权重可配（自定义权重归一化）。"""
        svc = UtilValueService(tier_weights={"ip": 5.0, "knowledge": 3.0})
        txs = [_tx("output", 10, tier="ip")]
        tiers = svc.tier_assessment("asset-c", txs)
        # 未配置层权重 0，已配置层归一化
        assert tiers.weights["ip"] == pytest.approx(5.0 / 8.0)
        assert tiers.weights["knowledge"] == pytest.approx(3.0 / 8.0)

    def test_tier_default_classification(self):
        """缺省分层: 销项→exchange，进项→knowledge。"""
        svc = UtilValueService()
        txs = [_tx("output", 30), _tx("input", 20)]
        tiers = svc.tier_assessment("asset-d", txs)
        assert tiers.tiers["exchange"]["amount"] == 30.0
        assert tiers.tiers["knowledge"]["amount"] == 20.0

    def test_tier_invalid_label(self):
        """非法分层标签 → 拒绝。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.tier_assessment("a", [_tx("output", 10, tier="bogus")])


class TestSafetyCheck:
    """估值安全熔断（文献 §3.3 底线思维）。"""

    def test_safe_ratio(self):
        """proposed ≤ 2.7×U_observed → SAFE。"""
        svc = UtilValueService()
        s = svc.safety_check(200.0, 100.0)
        assert s.status == "SAFE"

    def test_warning_ratio(self):
        """2.7 < proposed ≤ 3×U_observed → WARNING（需证据链）。"""
        svc = UtilValueService()
        s = svc.safety_check(280.0, 100.0)
        assert s.status == "WARNING"

    def test_circuit_breaker(self):
        """proposed > 3×U_observed → 强制锚定 U_observed×1.5。"""
        svc = UtilValueService()
        s = svc.safety_check(400.0, 100.0)
        assert s.status == "CIRCUIT_BREAKER"
        assert "1.5" in s.action
        assert "150" in s.action

    def test_zero_floor_no_anchor(self):
        """U_observed=0 → 任何正估值熔断（无锚定价禁止）。"""
        svc = UtilValueService()
        s = svc.safety_check(100.0, 0.0)
        assert s.status == "CIRCUIT_BREAKER"
        assert svc.safety_check(0.0, 0.0).status == "SAFE"

    def test_invalid_valuation_rejected(self):
        """负估值 → 拒绝。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.safety_check(-1.0, 100.0)


class TestReportAndSevenElements:
    """A-3/A-4 报告与七要素。"""

    def test_assessment_report_structure(self):
        """A-3 入表报告: 地板+分层+依据+报告类型。"""
        svc = UtilValueService()
        txs = [_tx("output", 100, tier="ip")]
        floor = svc.observable_floor("a", txs)
        tiers = svc.tier_assessment("a", txs)
        report = build_assessment_report(floor, tiers=tiers, report_id="R-UTIL-1")
        assert report["report_type"] == "util_value_assessment"
        assert report["basis"] == "TDCA-UTILITY-OBSERVABLE-001"
        assert report["floor"]["u_observed"] == 100.0
        json.dumps(report)  # 可序列化

    def test_report_floor_semantics_no_valuation(self):
        """A-4 MOU 地板语义: 报告含解释字段（地板非天花板），无主观估值字段。"""
        svc = UtilValueService()
        floor = svc.observable_floor("a", [_tx("output", 100)])
        report = build_assessment_report(floor, report_id="R-UTIL-2")
        assert "interpretation" in report["floor"]
        assert "可观测下限" in report["floor"]["interpretation"]
        assert "非主观估值" in report["floor"]["interpretation"]

    def test_seven_element_decomposition(self):
        """NS-007 函数七要素分解（ID68）。"""
        svc = UtilValueService()
        meta = {
            "objective": "版权资产入表计量",
            "constraint": "只输出可观测下限",
            "prior": "TDCA-UTILITY-OBSERVABLE-001",
            "config_boundary": "只读交易流水",
            "distribution": "入表报告+存证",
            "audit": "NCA 存证哈希",
            "negative_space": "不输出主观估值",
        }
        dec = svc.seven_element_decomposition("a", meta)
        assert dec["schema"] == "NS-007-FUNCTION-7ELEM-001"
        assert dec["elements"]["7_negative_space"] == "不输出主观估值"

    def test_seven_element_missing_required(self):
        """七要素缺项 → 拒绝（发布即契约完整性）。"""
        svc = UtilValueService()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.seven_element_decomposition("a", {"objective": "x"})


class TestNotary:
    """A-4 存证。"""

    def test_notary_records_nca(self, tmp_path):
        """评估自动落 NCA + MOU 地板语义标注。"""
        notary = UtilValueNotary(target_dir=str(tmp_path))
        rec = notary.record({"report_id": "R", "provenance": "SIMULATED"})
        assert rec["NCA-ID"].startswith("NCA-UTILVALUE-")
        assert rec["MOU-Anchor"]["Floor-Semantics"] == "地板非天花板——只输出可观测下限（MEMO-006-Audit）"
        import os
        assert os.path.exists(rec["_path"])


class TestAPIAndCLI:
    """A-3 API/CLI 端点。"""

    def test_api_assess_endpoint(self):
        """API: POST /api/v1/util-value/assess。"""
        from http.server import HTTPServer
        from urllib import request

        UtilValueAPIHandler.service = UtilValueService()
        UtilValueAPIHandler.notary = None
        UtilValueAPIHandler.auto_notarize = False
        server = HTTPServer(("127.0.0.1", 0), UtilValueAPIHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "asset_id": "api-asset",
                "transactions": [_tx("output", 100), _tx("input", 40)],
                "proposed_valuation": 500.0,
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/util-value/assess",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert payload["report"]["floor"]["u_observed"] == 140.0
            assert payload["report"]["safety"]["status"] == "CIRCUIT_BREAKER"
        finally:
            server.shutdown()

    def test_api_invalid_body_400(self):
        """API: 非法 JSON → 400。"""
        from http.server import HTTPServer
        from urllib import request
        from urllib.error import HTTPError

        UtilValueAPIHandler.service = UtilValueService()
        UtilValueAPIHandler.notary = None
        UtilValueAPIHandler.auto_notarize = False
        server = HTTPServer(("127.0.0.1", 0), UtilValueAPIHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/util-value/assess",
                data=b"not-json", headers={"Content-Type": "application/json"})
            with pytest.raises(HTTPError) as exc:
                request.urlopen(req, timeout=5)
            assert exc.value.code == 400
        finally:
            server.shutdown()

    def test_cli_assess(self, capsys):
        """CLI: util_value assess。"""
        txs = json.dumps([_tx("output", 100), _tx("input", 40)])
        rc = cli_main(["assess", "--asset", "cli-asset", "--tx", txs,
                       "--proposed", "500"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["floor"]["u_observed"] == 140.0
        assert report["safety"]["status"] == "CIRCUIT_BREAKER"

    def test_cli_assess_empty_flow(self, capsys):
        """CLI: 空交易流 fail-closed 地板 0。"""
        rc = cli_main(["assess", "--asset", "empty", "--tx", "[]"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["floor"]["u_observed"] == 0.0
