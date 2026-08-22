"""util_value · 评估服务 API（M1 服务化 HTTP 端点，零依赖标准库）。

  POST /api/v1/util-value/assess      入表评估（地板+分层+安全）
  GET  /api/v1/util-value/health      健康检查
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlparse

from .engine import UtilValueService
from .notary import UtilValueNotary
from .report import build_assessment_report
from .accounting import UtilValueAccounting


class UtilValueAPIHandler(BaseHTTPRequestHandler):
    service: UtilValueService = None
    notary: Optional[UtilValueNotary] = None
    auto_notarize: bool = True

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/v1/util-value/health":
            self._send_json(200, {"status": "ok", "service": "util_value"})
        else:
            self._send_json(404, {"error": "not found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid json body"})
            return
        try:
            if path == "/api/v1/util-value/assess":
                result = self._handle_assess(body)
            elif path == "/api/v1/util-value/entry":
                result = self._handle_entry(body)
            else:
                self._send_json(404, {"error": "not found", "path": path})
                return
        except (ValueError, KeyError, TypeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return
        if self.auto_notarize and self.notary is not None:
            self.notary.record(result["report"], operation_type="UtilValueAssess")
        self._send_json(200, result)

    def _handle_assess(self, body: dict) -> dict:
        svc = self.service
        asset_id = body["asset_id"]
        txs = body.get("transactions", [])
        floor = svc.observable_floor(asset_id, txs, provenance=body.get("provenance"))
        tiers = svc.tier_assessment(asset_id, txs, provenance=body.get("provenance"))
        safety = None
        if body.get("proposed_valuation") is not None:
            safety = svc.safety_check(body["proposed_valuation"], floor.u_observed)
        seven = None
        if body.get("seven_elements_meta"):
            seven = svc.seven_element_decomposition(asset_id, body["seven_elements_meta"])
        report = build_assessment_report(
            floor, tiers=tiers, safety=safety, seven_elements=seven,
            report_id=body.get("report_id") or f"util-value-{asset_id}",
        )
        return {"report": report}

    def _handle_entry(self, body: dict) -> dict:
        acct = UtilValueAccounting(self.service)
        report = acct.full_entry_report(
            asset_id=body["asset_id"],
            transactions=body.get("transactions", []),
            period=body.get("period", "2026-08"),
            proposed_valuation=body.get("proposed_valuation"),
            account=body.get("account"),
            seven_elements_meta=body.get("seven_elements_meta"),
            provenance=body.get("provenance", "SIMULATED"),
        )
        return {"report": report}

    def _send_json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        pass


def create_server(port: int = 8124, host: str = "127.0.0.1",
                  notary_dir: Optional[str] = None,
                  auto_notarize: bool = True) -> HTTPServer:
    UtilValueAPIHandler.service = UtilValueService()
    UtilValueAPIHandler.notary = UtilValueNotary(target_dir=notary_dir)
    UtilValueAPIHandler.auto_notarize = auto_notarize
    return HTTPServer((host, port), UtilValueAPIHandler)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8124
    server = create_server(port=port)
    print(f"util_value API 服务已启动: http://127.0.0.1:{port}/api/v1/util-value/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
