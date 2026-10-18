"""cog_align · 评测服务 API（M1 服务化 HTTP 端点）

零依赖实现（标准库 http.server，对齐 ID31 最简机制）:
  POST /api/v1/cog-align/measure     单对不对称评测
  POST /api/v1/cog-align/event       多主体矩阵评测
  GET  /api/v1/cog-align/health      健康检查
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional
from urllib.parse import urlparse

from .engine import CogAlignService
from .notary import CogAlignNotary
from .report import build_pair_report, build_multi_report
from .scenarios import CogAlignScenarios


class CogAlignAPIHandler(BaseHTTPRequestHandler):
    """cog_align HTTP API handler（无状态，构造时注入 service/notary）。"""

    service: CogAlignService = None
    notary: Optional[CogAlignNotary] = None
    auto_notarize: bool = True

    # ---- 路由 ----

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/v1/cog-align/health":
            self._send_json(200, {"status": "ok", "service": "cog_align"})
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
            if path == "/api/v1/cog-align/measure":
                result = self._handle_measure(body)
            elif path == "/api/v1/cog-align/event":
                result = self._handle_event(body)
            elif path == "/api/v1/cog-align/scenarios/thought-virus":
                result = self._handle_thought_virus(body)
            elif path == "/api/v1/cog-align/scenarios/drift-monitor":
                result = self._handle_drift_monitor(body)
            elif path == "/api/v1/cog-align/scenarios/tiering":
                result = self._handle_tiering(body)
            else:
                self._send_json(404, {"error": "not found", "path": path})
                return
        except (ValueError, KeyError, TypeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return

        if self.auto_notarize and self.notary is not None:
            self.notary.record(result["report"], operation_type="CogAlignMeasure")
        self._send_json(200, result)

    # ---- 业务 ----

    def _handle_measure(self, body: dict) -> dict:
        svc = self.service
        a_id = body["subject_a"]
        b_id = body["subject_b"]
        measure = svc.measure(a_id, body["state_a"], b_id, body["state_b"],
                              provenance=body.get("provenance"))
        report_id = body.get("report_id") or f"cog-align-{a_id}-{b_id}"
        return {"report": build_pair_report(measure, report_id)}

    def _handle_event(self, body: dict) -> dict:
        svc = self.service
        measure = svc.evaluate_event(body["event"], body["cognitive_states"],
                                     provenance=body.get("provenance"))
        report_id = body.get("report_id") or f"cog-align-event-{body['event']}"
        return {"report": build_multi_report(measure, report_id)}

    def _handle_thought_virus(self, body: dict) -> dict:
        scenarios = CogAlignScenarios(self.service)
        result = scenarios.thought_virus_defense(
            subject=body["subject"],
            state_series=[tuple(x) for x in body["state_series"]],
            baseline_state=body["baseline_state"],
            provenance=body.get("provenance", "SIMULATED"),
        )
        return {"report": result.to_dict()}

    def _handle_drift_monitor(self, body: dict) -> dict:
        scenarios = CogAlignScenarios(self.service)
        result = scenarios.cognitive_drift_monitor(
            subject_a=body["subject_a"],
            subject_b=body["subject_b"],
            state_series=[tuple(x) for x in body["state_series"]],
            provenance=body.get("provenance", "SIMULATED"),
        )
        return {"report": result.to_dict()}

    def _handle_tiering(self, body: dict) -> dict:
        scenarios = CogAlignScenarios(self.service)
        if "cognitive_states" in body:
            matrix = scenarios.tier_matrix(
                body["cognitive_states"],
                provenance=body.get("provenance", "SIMULATED"),
            )
            return {"report": {"scenario": "alignment_tier_matrix",
                               "matrix": matrix,
                               "provenance": body.get("provenance", "SIMULATED")}}
        tier = scenarios.alignment_tiering(
            body["subject_a"], body["state_a"],
            body["subject_b"], body["state_b"],
            provenance=body.get("provenance", "SIMULATED"),
        )
        return {"report": tier.to_dict()}

    # ---- 工具 ----

    def _send_json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        # 静默访问日志（保持输出干净）
        pass


def create_server(port: int = 8123, host: str = "127.0.0.1",
                  notary_dir: Optional[str] = None,
                  auto_notarize: bool = True) -> HTTPServer:
    """创建 cog_align 评测服务（零依赖 HTTP 服务）。"""
    CogAlignAPIHandler.service = CogAlignService()
    CogAlignAPIHandler.notary = CogAlignNotary(target_dir=notary_dir)
    CogAlignAPIHandler.auto_notarize = auto_notarize
    return HTTPServer((host, port), CogAlignAPIHandler)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    server = create_server(port=port)
    print(f"cog_align API 服务已启动: http://127.0.0.1:{port}/api/v1/cog-align/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
