"""util_value · M2 入表服务化测试（DCD-UTIL-VALUE-001 §五 M2）

三件套:
  1. 入表报告模板（对接会计口径）
  2. 版权链存证上链（模拟通道）
  3. 对外服务接口（API entry + CLI entry）
"""
import json

import pytest

from util_value.accounting import (
    ACCOUNT_INTANGIBLE,
    ACCOUNT_RD,
    ENTRY_CAPITALIZE,
    ENTRY_EXPENSE,
    UtilValueAccounting,
)
from util_value.api import UtilValueAPIHandler
from util_value.cli import main as cli_main


def _tx(direction, amount, tier=None):
    d = {"direction": direction, "amount": amount}
    if tier is not None:
        d["tier"] = tier
    return d


class TestAccountingEntry:
    """1. 会计入表建议（对接会计口径）。"""

    def test_capitalize_with_floor(self):
        """U_observed > 0 → 资本化入表（无形资产科目，入账=地板）。"""
        acct = UtilValueAccounting()
        e = acct.accounting_entry("CP-1", [_tx("output", 100), _tx("input", 40)],
                                  period="2026-08")
        assert e.entry_type == ENTRY_CAPITALIZE
        assert e.account == ACCOUNT_INTANGIBLE
        assert e.book_value == 140.0          # 入账 = U_observed（地板）
        assert "非主观估值" in e.to_dict()["note"]

    def test_expense_when_no_floor(self):
        """U_observed = 0 → 费用化（禁止无锚资本化，fail-closed）。"""
        acct = UtilValueAccounting()
        e = acct.accounting_entry("CP-empty", [], period="2026-08")
        assert e.entry_type == ENTRY_EXPENSE
        assert e.book_value == 0.0

    def test_custom_account(self):
        """自定义科目（在建工程）。"""
        acct = UtilValueAccounting()
        e = acct.accounting_entry("CP-2", [_tx("output", 50)],
                                  period="2026-08", account="在建工程-版权资产")
        assert e.account == "在建工程-版权资产"

    def test_period_recorded(self):
        """会计期间记录。"""
        acct = UtilValueAccounting()
        e = acct.accounting_entry("CP-3", [_tx("output", 10)], period="2026-09")
        assert e.period == "2026-09"

    def test_book_value_is_floor_not_valuation(self):
        """MOU 地板语义: 入账金额 = 地板，非估值（可审计可复核）。"""
        acct = UtilValueAccounting()
        e = acct.accounting_entry("CP-4", [_tx("output", 100), _tx("input", 100)],
                                  period="2026-08")
        assert e.book_value == 200.0
        assert e.basis.startswith("TDCA-UTILITY-OBSERVABLE-001")


class TestCopyrightChain:
    """2. 版权链存证上链（模拟通道）。"""

    def test_chain_record_generated(self):
        """存证记录生成（record_hash 非空，模拟上链状态）。"""
        acct = UtilValueAccounting()
        r = acct.copyright_chain_record("CP-5", [_tx("output", 100)])
        assert len(r.record_hash) == 64          # SHA-256 hex
        assert r.chain_status == "SIMULATED_ONCHAIN"
        assert "SIM" in r.chain_id

    def test_chain_hash_deterministic(self):
        """同输入 → 同哈希（可复核）。"""
        acct = UtilValueAccounting()
        txs = [_tx("output", 100), _tx("input", 40)]
        r1 = acct.copyright_chain_record("CP-6", txs)
        r2 = acct.copyright_chain_record("CP-6", txs)
        assert r1.record_hash == r2.record_hash

    def test_chain_hash_changes_with_tx(self):
        """不同交易流 → 不同哈希。"""
        acct = UtilValueAccounting()
        r1 = acct.copyright_chain_record("CP-7", [_tx("output", 100)])
        r2 = acct.copyright_chain_record("CP-7", [_tx("output", 200)])
        assert r1.record_hash != r2.record_hash

    def test_chain_provenance(self):
        """ID92: provenance 标注。"""
        acct = UtilValueAccounting()
        r = acct.copyright_chain_record("CP-8", [_tx("output", 1)],
                                        provenance="REAL-JUDICIAL-CHAIN")
        assert r.provenance == "REAL-JUDICIAL-CHAIN"


class TestFullEntryReport:
    """3. M2 完整入表报告。"""

    def test_full_report_structure(self):
        """完整报告: 地板+分层+会计+版权链。"""
        acct = UtilValueAccounting()
        report = acct.full_entry_report(
            "CP-9", [_tx("output", 120, tier="ip"), _tx("input", 50, tier="knowledge")],
            period="2026-08")
        assert report["report_type"] == "util_value_entry_report"
        assert report["schema_version"] == "2.0"
        assert report["floor"]["u_observed"] == 170.0
        assert report["accounting_entry"]["entry_type"] == ENTRY_CAPITALIZE
        assert report["copyright_chain"]["chain_status"] == "SIMULATED_ONCHAIN"
        json.dumps(report)  # 可序列化

    def test_full_report_with_safety(self):
        """含拟议估值 → 安全熔断检查并入报告。"""
        acct = UtilValueAccounting()
        report = acct.full_entry_report(
            "CP-10", [_tx("output", 100)], period="2026-08",
            proposed_valuation=1000.0)
        assert report["safety"]["status"] == "CIRCUIT_BREAKER"
        assert "1.5" in report["safety"]["action"]

    def test_full_report_with_seven_elements(self):
        """含七要素元数据 → 分解并入报告。"""
        acct = UtilValueAccounting()
        report = acct.full_entry_report(
            "CP-11", [_tx("output", 100)], period="2026-08",
            seven_elements_meta={
                "objective": "版权入表", "constraint": "地板语义",
                "prior": "UTILITY-OBSERVABLE", "config_boundary": "只读",
                "distribution": "入表报告", "audit": "NCA",
            })
        assert report["seven_elements"]["schema"] == "NS-007-FUNCTION-7ELEM-001"

    def test_full_report_empty_fail_closed(self):
        """空交易流 → 费用化（fail-closed）。"""
        acct = UtilValueAccounting()
        report = acct.full_entry_report("CP-empty", [], period="2026-08")
        assert report["accounting_entry"]["entry_type"] == ENTRY_EXPENSE
        assert report["accounting_entry"]["book_value"] == 0.0


class TestEntryAPIAndCLI:
    """3. 对外服务接口。"""

    def test_api_entry_endpoint(self):
        """API: POST /api/v1/util-value/entry。"""
        from http.server import HTTPServer
        from urllib import request

        UtilValueAPIHandler.service = None
        UtilValueAPIHandler.notary = None
        UtilValueAPIHandler.auto_notarize = False
        server = HTTPServer(("127.0.0.1", 0), UtilValueAPIHandler)
        port = server.server_address[1]
        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "asset_id": "api-cp", "period": "2026-08",
                "transactions": [_tx("output", 100), _tx("input", 40)],
                "proposed_valuation": 900.0,
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/util-value/entry",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert payload["report"]["report_type"] == "util_value_entry_report"
            assert payload["report"]["floor"]["u_observed"] == 140.0
            assert payload["report"]["safety"]["status"] == "CIRCUIT_BREAKER"
        finally:
            server.shutdown()

    def test_cli_entry(self, capsys):
        """CLI: util_value entry。"""
        txs = json.dumps([_tx("output", 100), _tx("input", 40)])
        rc = cli_main(["entry", "--asset", "cli-cp", "--tx", txs,
                       "--period", "2026-08", "--proposed", "900"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "util_value_entry_report"
        assert report["accounting_entry"]["book_value"] == 140.0

    def test_cli_entry_empty(self, capsys):
        """CLI: entry 空流 → 费用化。"""
        rc = cli_main(["entry", "--asset", "empty", "--tx", "[]"])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["accounting_entry"]["entry_type"] == ENTRY_EXPENSE
