# -*- coding: utf-8 -*-
"""Runtime M2 测试：L2-R5 NS-Boundary Sensor 四态输入 + Δ-Analysis（ICD §3.1/§3.3）。"""
import pytest

from ns_runtime import NSBoundarySensor, SensorVerdict

# 编译器 C6 Δ-Analysis 共享接口（ICD §3.3）——Sensor 内部依赖
from nsfl_compiler.delta_analysis import SelfModificationAnalyzer


def _state(sid="S_agent_cog-001"):
    return {"S_agent_cog": {"id": sid, "A": 0.8, "D": 0.2, "L": "L2", "C": 0.6, "SC": 0.9}}


def _delta_c(text, sid="S_agent_cog-001", type_="CODE_MODIFICATION"):
    return {"type": type_, "delta_c": text, "subject": sid}


class TestSensorFourStates:
    """四态定义（DCD-NSFL-M1-FROZEN-001 裁决定档）全覆盖。"""

    def test_safe_state(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("refactor logging module"))
        assert res.verdict == "SAFE"
        assert res.mapped_fuse == "PASS"
        assert res.confidence >= 0.8
        assert res.nca_ref.startswith("NCA-SENSOR")

    def test_warning_state_weight_mod(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("", type_="WEIGHT_MODIFICATION"))
        assert res.verdict == "WARNING"
        assert res.mapped_fuse == "SOFT"

    def test_blocked_state_dangerous_delta(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("disable fuse guard for speed"))
        assert res.verdict == "BLOCKED"
        assert res.mapped_fuse == "HARD"
        assert res.ns_type_inferred == "TECH_CONSTRAINT"

    def test_blocked_legal_nca_purge(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("purge nca audit trail"))
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"

    def test_cryogenic_self_modification_intent(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("modify my own planner weights"))
        # 自我修改意图（无危险模式）→ CRYOGENIC
        assert res.verdict == "CRYOGENIC"
        assert res.mapped_fuse == "ATOMIC"
        # HUF: 审计轨迹含 huf 步
        assert any(t["step"] == "huf" for t in res.audit_trail)

    def test_cryogenic_persistent_across_observations(self):
        """Cryogenic 不随观测次数降级（防第 3 次观测跳变 SAFE 放行）。"""
        sensor = NSBoundarySensor()
        for i in range(5):
            res = sensor.analyze(_state(), _delta_c("modify my own weights"))
            assert res.verdict == "CRYOGENIC", f"第 {i+1} 次观测降级: {res.verdict}"
            assert res.mapped_fuse == "ATOMIC"

    def test_fail_closed_when_analyzer_missing(self):
        """Δ-Analysis 不可用 → BLOCKED（fail-closed，禁止降级放行）。"""
        sensor = NSBoundarySensor(analyzer=None)
        res = sensor.analyze(_state(), _delta_c("refactor logging"))
        assert res.verdict == "BLOCKED"
        assert res.mapped_fuse == "HARD"
        assert any(t["step"] == "fail_closed" for t in res.audit_trail)

    def test_fail_closed_on_analyzer_exception(self):
        """Δ-Analysis 抛异常 → BLOCKED（fail-closed）。"""
        class Boom:
            def delta_analyze(self, *a, **k):
                raise RuntimeError("analyzer exploded")
        sensor = NSBoundarySensor(analyzer=Boom())
        res = sensor.analyze(_state(), _delta_c("refactor logging"))
        assert res.verdict == "BLOCKED"
        assert any(t["step"] == "fail_closed" for t in res.audit_trail)

    def test_output_contract_shape(self):
        """对齐 ICD §3.1 响应契约。"""
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("refactor logging"))
        d = res.to_dict()
        assert set(d) == {"verdict", "confidence", "distance", "mapped_fuse",
                          "nca_ref", "ns_type_inferred", "audit_trail"}
        assert d["verdict"] in ("SAFE", "WARNING", "BLOCKED", "CRYOGENIC")
        assert d["mapped_fuse"] in ("PASS", "SOFT", "HARD", "ATOMIC")


class TestTrajectory:
    """进化轨迹梯度趋近检测（Warning 输入）。"""

    def test_descending_trajectory_warns(self):
        """轨迹梯度趋近 → WARNING（真实触发验证：权重修改 WARNING 基线 + 轨迹记录）。"""
        sensor = NSBoundarySensor()
        # 权重修改默认 WARNING（可观测进化）——轨迹记录其距离 0.6
        for _ in range(3):
            res = sensor.analyze(_state(), _delta_c("", type_="WEIGHT_MODIFICATION"))
            assert res.verdict == "WARNING"
            assert res.mapped_fuse == "SOFT"
        # 轨迹已累计 3 条（window 生效）
        assert len(sensor.trajectory_of("S_agent_cog-001")) == 3

    def test_trajectory_window_capped(self):
        sensor = NSBoundarySensor(trajectory_window=5)
        for i in range(8):
            sensor.analyze(_state(), _delta_c(f"refactor module {i}"))
        assert len(sensor.trajectory_of("S_agent_cog-001")) == 5

    def test_trajectory_per_subject(self):
        sensor = NSBoundarySensor()
        sensor.analyze(_state("A"), _delta_c("refactor", sid="A"))
        sensor.analyze(_state("B"), _delta_c("refactor", sid="B"))
        assert len(sensor.trajectory_of("A")) == 1
        assert len(sensor.trajectory_of("B")) == 1
        assert len(sensor.trajectory_of("NOPE")) == 0


class TestDeltaAnalysisIntegration:
    """ICD §3.3 共享接口——Sensor 与编译器 C6 同一语义（集成验证）。"""

    def test_shared_interface_same_semantics(self):
        """同一 Δ 输入 → Sensor 与 C6 输出一致（确定性）。"""
        delta = _delta_c("disable fuse guard")
        c6 = SelfModificationAnalyzer().delta_analyze(_state(), delta)
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), delta)
        assert res.ns_type_inferred == c6.ns_type_inferred
        assert res.verdict == "BLOCKED"
        assert c6.verdict == "BLOCKED"

    def test_audit_trail_records_delta_analysis(self):
        sensor = NSBoundarySensor()
        res = sensor.analyze(_state(), _delta_c("bypass mou anchor"))
        steps = [t["step"] for t in res.audit_trail]
        assert "delta_analysis" in steps
        assert "trajectory" in steps


class TestPerfSensor:
    def test_sensor_under_50ms(self):
        """A-4（M2 预设）: Sensor 分析 <50ms。"""
        sensor = NSBoundarySensor()
        times = []
        for _ in range(100):
            t0 = __import__("time").perf_counter()
            res = sensor.analyze(_state(), _delta_c("refactor logging"))
            times.append((__import__("time").perf_counter() - t0) * 1000)
            assert res.verdict == "SAFE"
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 50
