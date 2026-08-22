"""cog_align · 认知对齐评测服务测试套件（DCD-COG-ALIGN-001 M1 验收 A-1~A-6）

验收项映射:
  A-1 单对评测（不对称距离+优势方+双向难度，对照命题 3.10）
  A-2 多主体矩阵（N×N + 势差排序）
  A-3 报告生成（机器可读结构化）
  A-4 存证（自动 NCA 落链，provenance 标注）
  A-5 ≥15 用例全绿（含不对称性/势差/边界）
  A-6 回归（toolchain 全套——外部 pytest 执行）
"""
import json
import math
import threading

import pytest

from cog_align.api import CogAlignAPIHandler, create_server
from cog_align.cli import main as cli_main
from cog_align.engine import CogAlignService
from cog_align.notary import CogAlignNotary
from cog_align.report import (
    build_convergence_report,
    build_multi_report,
    build_pair_report,
    summarize_negotiation,
)


def _s(**kw):
    base = {"A": 0.5, "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
    base.update(kw)
    return base


class TestPairMeasure:
    """A-1 单对评测。"""

    def test_asymmetry_proposition_3_10(self):
        """命题 3.10: 高认知理解低认知容易（d 短），反之困难（d 长）。"""
        svc = CogAlignService()
        high = _s(A=0.95, D=0.95, L=0.9, C=0.9, SC=0.95)
        low = _s(A=0.2, D=0.2, L=0.2, C=0.2, SC=0.2)
        m = svc.measure("high", high, "low", low)
        assert m.asymmetric is True
        assert m.d_ab < m.d_ba          # high 理解 low 距离短
        assert m.difficulty_ab > m.difficulty_ba
        assert m.dominant_side == "high"

    def test_symmetric_states_no_asymmetry(self):
        """相同状态 → 对称（d_ab == d_ba），无优势方。"""
        svc = CogAlignService()
        s = _s(A=0.7, D=0.7, L=0.7, C=0.7, SC=0.7)
        m = svc.measure("a", s, "b", s)
        assert m.asymmetric is False
        assert m.d_ab == m.d_ba == 0.0
        assert m.dominant_side is None

    def test_negotiation_threshold_phase2(self):
        """NIA-MACM PHASE-2: distance > 阈值 → 协商触发。"""
        svc = CogAlignService()
        far_a = _s(A=0.9, D=0.9, L=0.9, C=0.9, SC=0.9)
        far_b = _s(A=0.05, D=0.05, L=0.05, C=0.05, SC=0.05)
        assert svc.measure("a", far_a, "b", far_b).negotiation_required is True

    def test_close_states_no_negotiation(self):
        """近距离 → 不触发协商。"""
        svc = CogAlignService()
        a = _s(A=0.6, D=0.6)
        b = _s(A=0.62, D=0.61)
        assert svc.measure("a", a, "b", b).negotiation_required is False

    def test_difficulty_alignment_definition_3_37(self):
        """定义 3.37: difficulty = exp(−d)，∈ (0,1]。"""
        svc = CogAlignService()
        a = _s(A=0.8, D=0.8, L=0.8, C=0.8, SC=0.8)
        b = _s(A=0.1, D=0.1, L=0.1, C=0.1, SC=0.1)
        m = svc.measure("a", a, "b", b)
        assert math.isclose(m.difficulty_ab, math.exp(-m.d_ab), rel_tol=1e-9)
        assert 0.0 < m.difficulty_ab <= 1.0
        assert 0.0 < m.difficulty_ba <= 1.0

    def test_fuzzy_direction_enhancement(self):
        """模糊置信度增强（FUZZY_CONFIDENCE）: 贴近 → HIGH。"""
        svc = CogAlignService()
        a = _s(A=0.9, D=0.9, L=0.9, C=0.9, SC=0.9)
        b = _s(A=0.88, D=0.89, L=0.9, C=0.91, SC=0.9)
        m = svc.measure("a", a, "b", b)
        assert m.fuzzy_direction in ("HIGH", "MEDIUM", "NO_DIFFERENCE")
        assert 0.0 <= m.fuzzy_nearness <= 1.0

    def test_provenance_labeling_id92(self):
        """ID92: provenance 标注默认 SIMULATED，可显式 REAL。"""
        svc = CogAlignService()
        a = _s(); b = _s(A=0.1)
        assert svc.measure("a", a, "b", b).provenance == "SIMULATED"
        m = svc.measure("a", a, "b", b, provenance="REAL-API-TEST")
        assert m.provenance == "REAL-API-TEST"

    def test_invalid_state_out_of_range(self):
        """负空间预检: 维度越界 [0,1] → NSFL-TRIGGER 拒绝。"""
        svc = CogAlignService()
        bad = _s(SC=1.5)
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.measure("a", bad, "b", _s())

    def test_invalid_state_non_numeric(self):
        """非数值维度 → 拒绝。"""
        svc = CogAlignService()
        bad = {"A": "x", "D": 0.5, "L": 0.5, "C": 0.5, "SC": 0.5}
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            svc.measure("a", bad, "b", _s())


class TestMultiSubject:
    """A-2 多主体矩阵。"""

    def test_nxn_matrix_and_self_zero(self):
        """N×N 距离矩阵 + 自身距离 0。"""
        svc = CogAlignService()
        states = {"s1": _s(A=0.9), "s2": _s(A=0.5), "s3": _s(A=0.1)}
        m = svc.evaluate_event("e1", states)
        assert set(m.subjects) == {"s1", "s2", "s3"}
        assert m.distance_matrix["s1"]["s1"] == 0.0
        assert m.distance_matrix["s2"]["s3"] >= 0.0

    def test_asymmetry_ratio_bounds(self):
        """不对称比率 ∈ [0,1]。"""
        svc = CogAlignService()
        states = {"s1": _s(A=0.9, SC=0.9), "s2": _s(A=0.5, SC=0.5), "s3": _s(A=0.1, SC=0.1)}
        m = svc.evaluate_event("e2", states)
        assert 0.0 <= m.asymmetry_ratio <= 1.0

    def test_power_ranking_desc(self):
        """势差分析: 认知水平降序排序。"""
        svc = CogAlignService()
        states = {"high": _s(A=0.95, SC=0.95), "mid": _s(A=0.5, SC=0.5), "low": _s(A=0.05, SC=0.05)}
        m = svc.evaluate_event("e3", states)
        levels = [r["cognitive_level"] for r in m.power_ranking]
        assert levels == sorted(levels, reverse=True)
        assert m.power_ranking[0]["subject"] == "high"

    def test_fuzzy_clusters_present(self):
        """模糊聚类（λ 截集）输出。"""
        svc = CogAlignService()
        states = {"a": _s(A=0.9, SC=0.9), "b": _s(A=0.88, SC=0.9), "c": _s(A=0.1, SC=0.1)}
        m = svc.evaluate_event("e4", states)
        assert isinstance(m.fuzzy_clusters, list)

    def test_validate_self_consistency(self):
        """自证: 对齐难度 ∈ (0,1]（复用基座 validate 语义）。"""
        svc = CogAlignService()
        states = {"a": _s(A=0.9), "b": _s(A=0.2)}
        m = svc.evaluate_event("e5", states)
        for a in m.subjects:
            for b in m.subjects:
                assert 0.0 < m.alignment_difficulties[a][b] <= 1.0


class TestReportAndNotary:
    """A-3/A-4 报告与存证。"""

    def test_pair_report_machine_readable(self):
        """A-3 单对报告: 机器可读 JSON 结构。"""
        svc = CogAlignService()
        m = svc.measure("a", _s(A=0.9), "b", _s(A=0.1))
        r = build_pair_report(m, "R-001", event="evt")
        assert r["report_type"] == "cog_align_pair"
        assert r["report_id"] == "R-001"
        json.dumps(r)  # 可序列化

    def test_multi_report_machine_readable(self):
        """A-3 多主体报告。"""
        svc = CogAlignService()
        m = svc.evaluate_event("evt", {"a": _s(A=0.9), "b": _s(A=0.1)})
        r = build_multi_report(m, "R-002")
        assert r["report_type"] == "cog_align_multi"
        json.dumps(r)

    def test_negotiation_summary(self):
        """协商触发建议汇总（NIA-MACM PHASE-2 对接）。"""
        svc = CogAlignService()
        m1 = svc.measure("a", _s(A=0.9, SC=0.9), "b", _s(A=0.05, SC=0.05))
        m2 = svc.measure("c", _s(A=0.6), "d", _s(A=0.61))
        summary = summarize_negotiation({"a-b": m1, "c-d": m2})
        assert [s["pair"] for s in summary] == ["a-b"]

    def test_notary_records_nca(self, tmp_path):
        """A-4 存证: 自动落 NCA 文件 + provenance 标注。"""
        notary = CogAlignNotary(target_dir=str(tmp_path))
        rec = notary.record({"report_id": "R-X", "provenance": "SIMULATED"})
        assert rec["NCA-ID"].startswith("NCA-COGALIGN-")
        assert rec["Provenance"] == "SIMULATED"
        import os
        assert os.path.exists(rec["_path"])

    def test_notary_sequential_ids(self, tmp_path):
        """存证序号递增（同日多笔）。"""
        notary = CogAlignNotary(target_dir=str(tmp_path))
        r1 = notary.record({"provenance": "SIMULATED"})
        r2 = notary.record({"provenance": "SIMULATED"})
        assert r1["NCA-ID"] != r2["NCA-ID"]


class TestAPIAndCLI:
    """A-3 API/CLI 端点。"""

    def test_api_measure_endpoint(self):
        """API: POST /api/v1/cog-align/measure。"""
        svc = CogAlignService()
        CogAlignAPIHandler.service = svc
        CogAlignAPIHandler.notary = None
        CogAlignAPIHandler.auto_notarize = False
        from http.server import HTTPServer
        from urllib import request

        server = HTTPServer(("127.0.0.1", 0), CogAlignAPIHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "subject_a": "agent-a", "state_a": _s(A=0.9, SC=0.9),
                "subject_b": "agent-b", "state_b": _s(A=0.1, SC=0.1),
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/cog-align/measure",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert payload["report"]["report_type"] == "cog_align_pair"
            assert payload["report"]["asymmetric"] is True
        finally:
            server.shutdown()

    def test_api_event_endpoint(self):
        """API: POST /api/v1/cog-align/event。"""
        svc = CogAlignService()
        CogAlignAPIHandler.service = svc
        CogAlignAPIHandler.notary = None
        CogAlignAPIHandler.auto_notarize = False
        from http.server import HTTPServer
        from urllib import request

        server = HTTPServer(("127.0.0.1", 0), CogAlignAPIHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            body = json.dumps({
                "event": "e-api", "cognitive_states": {"a": _s(A=0.9), "b": _s(A=0.1)},
            }).encode()
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/cog-align/event",
                data=body, headers={"Content-Type": "application/json"})
            with request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            assert payload["report"]["report_type"] == "cog_align_multi"
            assert payload["report"]["subjects"] == ["a", "b"]
        finally:
            server.shutdown()

    def test_api_invalid_body_400(self):
        """API: 非法 JSON → 400。"""
        svc = CogAlignService()
        CogAlignAPIHandler.service = svc
        CogAlignAPIHandler.notary = None
        CogAlignAPIHandler.auto_notarize = False
        from http.server import HTTPServer
        from urllib import request
        from urllib.error import HTTPError

        server = HTTPServer(("127.0.0.1", 0), CogAlignAPIHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = request.Request(
                f"http://127.0.0.1:{port}/api/v1/cog-align/measure",
                data=b"not-json", headers={"Content-Type": "application/json"})
            with pytest.raises(HTTPError) as exc:
                request.urlopen(req, timeout=5)
            assert exc.value.code == 400
        finally:
            server.shutdown()

    def test_cli_measure(self, capsys):
        """CLI: cog_align measure 输出 JSON 报告。"""
        rc = cli_main(["measure", "--a", "a", "--state-a", json.dumps(_s(A=0.9)),
                       "--b", "b", "--state-b", json.dumps(_s(A=0.1))])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "cog_align_pair"

    def test_cli_event(self, capsys):
        """CLI: cog_align event 多主体。"""
        states = json.dumps({"a": _s(A=0.9), "b": _s(A=0.1)})
        rc = cli_main(["event", "--event", "e-cli", "--states", states])
        out = capsys.readouterr().out
        assert rc == 0
        report = json.loads(out)
        assert report["report_type"] == "cog_align_multi"


class TestConvergence:
    """收敛轨迹（认知漂移监测）。"""

    def test_converging_series(self):
        """距离递减序列 → converging。"""
        svc = CogAlignService()
        series = [
            ("t0", _s(A=0.9, SC=0.9), _s(A=0.1, SC=0.1)),
            ("t1", _s(A=0.6, SC=0.6), _s(A=0.4, SC=0.4)),
            ("t2", _s(A=0.52, SC=0.52), _s(A=0.5, SC=0.5)),
        ]
        t = svc.convergence("a", "b", series)
        assert t.converging is True
        assert t.drift_alert is False
        assert len(t.trace) == 3

    def test_drift_alert(self):
        """距离放大序列 → drift_alert。"""
        svc = CogAlignService()
        series = [
            ("t0", _s(A=0.52, SC=0.52), _s(A=0.5, SC=0.5)),
            ("t1", _s(A=0.7, SC=0.7), _s(A=0.3, SC=0.3)),
            ("t2", _s(A=0.9, SC=0.9), _s(A=0.1, SC=0.1)),
        ]
        t = svc.convergence("a", "b", series)
        assert t.converging is False
        assert t.drift_alert is True

    def test_insufficient_points_rejected(self):
        """<2 时点 → 拒绝。"""
        svc = CogAlignService()
        with pytest.raises(ValueError):
            svc.convergence("a", "b", [("t0", _s(), _s())])
