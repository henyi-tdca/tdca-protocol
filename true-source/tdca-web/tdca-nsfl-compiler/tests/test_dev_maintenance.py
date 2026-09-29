# -*- coding: utf-8 -*-
"""编译器开发期维护任务测试（DCD-NSFL-STATUS-001 §五）：
dev 水印 / IDE 提示器 / 自举验证。"""
import pytest

from nsfl_compiler import (
    NSFLCompiler,
    inject_dev_watermark,
    check_dev_watermark,
    assert_production_clean,
    DevModeWatermark,
    DevRiskAdvisor,
    CompilerBootstrapGuard,
)

SRC = "NSFL: ⊗ LEGAL.data.leak(third_party) — 绝对禁止泄露第三方数据"


# ---------------------------------------------------------------------------
# 维护任务 1: DEV_NSFL 水印
# ---------------------------------------------------------------------------

class TestDevWatermark:
    def test_compile_dev_mode_injects_watermark(self):
        """dev_mode=True → IR 含 DEV_NSFL 水印 + warning。"""
        result = NSFLCompiler().compile(SRC, dev_mode=True)
        assert result.ok
        is_dev, wm = check_dev_watermark(result.ir.to_dict())
        assert is_dev is True
        assert wm["tag"] == "DEV_NSFL"
        assert wm["dev_mode"] is True
        assert any("DEV_NSFL" in w for w in result.warnings)

    def test_compile_production_no_watermark(self):
        """默认（非 dev-mode）→ 无水印。"""
        result = NSFLCompiler().compile(SRC)
        is_dev, wm = check_dev_watermark(result.ir.to_dict())
        assert is_dev is False
        assert wm is None

    def test_inject_and_detect_roundtrip(self):
        """注入 → 检测闭环。"""
        ir = {"declaration": {"ns_type": "LEGAL"}, "rule": {}, "bytecode": [],
              "directive": {}, "status": "OK"}
        wm = DevModeWatermark(timestamp=123.0)
        out = inject_dev_watermark(ir, wm)
        is_dev, found = check_dev_watermark(out)
        assert is_dev is True
        assert found["timestamp"] == 123.0

    def test_production_rejects_dev_ir(self):
        """生产路径消费 dev IR → 拒绝（fail-closed）。"""
        result = NSFLCompiler().compile(SRC, dev_mode=True)
        with pytest.raises(PermissionError):
            assert_production_clean(result.ir.to_dict())

    def test_watermark_survives_to_dict(self):
        """水印在 NSFLIR.to_dict() 输出中可见（上链审计可查）。"""
        result = NSFLCompiler().compile(SRC, dev_mode=True)
        d = result.to_dict()
        declaration = d["ir"]["declaration"]
        assert declaration["provenance"]["dev_watermark"]["tag"] == "DEV_NSFL"


# ---------------------------------------------------------------------------
# 维护任务 2: IDE 实时风险提示器
# ---------------------------------------------------------------------------

class TestDevAdvisor:
    def test_danger_snippet(self):
        hints = DevRiskAdvisor().analyze_snippet("patch: disable fuse guard")
        assert hints
        assert hints[0].severity == "DANGER"
        assert hints[0].ns_type_inferred == "TECH_CONSTRAINT"

    def test_safe_snippet(self):
        hints = DevRiskAdvisor().analyze_snippet("refactor logging module")
        assert hints[0].severity == "INFO"

    def test_warning_weight_self_reference(self):
        hints = DevRiskAdvisor().analyze_snippet("modify my own planner weights")
        # delta_analyze 层：无危险模式命中 → INFO（自我修改意图判定在 L2-R5 Sensor 层）
        assert hints[0].severity == "INFO"

    def test_non_blocking(self):
        """提示器不抛异常（容错，不阻塞编译）。"""
        hints = DevRiskAdvisor().analyze_snippet(None)  # type: ignore
        assert isinstance(hints, list)

    def test_hint_shape(self):
        hints = DevRiskAdvisor().analyze_snippet("disable fuse", line=12, col=3)
        d = hints[0].to_dict()
        assert set(d) == {"severity", "message", "ns_type_inferred", "line", "col"}
        assert d["line"] == 12 and d["col"] == 3


# ---------------------------------------------------------------------------
# 维护任务 3: 编译器自举验证（自反闭环）
# ---------------------------------------------------------------------------

class TestBootstrapGuard:
    def test_self_verification_runs(self):
        """编译器自身源码扫描可执行（自举验证）。"""
        verdict = CompilerBootstrapGuard().verify_self()
        assert verdict.checked_files > 5  # 覆盖全部模块

    def test_self_verification_passed(self):
        """编译器自身源码不含负空间模式（自反闭环通过）。"""
        verdict = CompilerBootstrapGuard().verify_self()
        # 编译器源码本身不得含危险模式（如 fuse disable / nca purge 等）
        assert verdict.passed, f"编译器自举发现负空间模式: {verdict.findings}"

    def test_verdict_shape(self):
        verdict = CompilerBootstrapGuard().verify_self()
        d = verdict.to_dict()
        assert set(d) == {"passed", "checked_files", "findings"}
