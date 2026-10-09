"""pi_nca · Pi M1 测试（DCD-PI-COMPOUND-001 验收 A-1~A-6）

A-1 编译适配: MIT 层构建协议 → TDCA 制度语义正确映射
A-2 存证转换: 构建轨迹 → NCA 六要素正确
A-3 Fair Source 隔离: 化合零触碰 Fair Source 核心层（风险管控）
A-4 不碰核心: Pi 核心零修改
A-5 测试: ≥16 用例全绿（M1a 10 + M1b 6）
A-6 回归: 既有基线不破
"""
import json

import pytest

from pi_nca.cli import main as cli_main
from pi_nca.compiler import FAIR_SOURCE_LAYER, MIT_LAYER, PiCompiler


def _spec(spec_id="agent-1", with_fair=False):
    steps = [
        {"step_id": "s1", "layer": "mit", "action": "configure"},
        {"step_id": "s2", "layer": "mit", "action": "install"},
        {"step_id": "s3", "layer": "mit", "action": "test"},
    ]
    if with_fair:
        steps.append({"step_id": "s4", "layer": FAIR_SOURCE_LAYER, "action": "invoke"})
    return {"spec_id": spec_id, "steps": steps}


class TestParse:
    """解析。"""

    def test_parse_valid(self):
        compiler = PiCompiler()
        data = compiler.parse_agent_spec(json.dumps(_spec()))
        assert len(data["steps"]) == 3

    def test_parse_empty_rejected(self):
        compiler = PiCompiler()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            compiler.parse_agent_spec("")

    def test_parse_missing_steps(self):
        compiler = PiCompiler()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            compiler.parse_agent_spec(json.dumps({"spec_id": "x"}))


class TestFairSourceGuard:
    """A-3 Fair Source 隔离。"""

    def test_all_mit_allowed(self):
        """全 MIT 层 → 可化合（无拦截）。"""
        compiler = PiCompiler()
        guard = compiler.fair_source_guard(_spec())
        assert guard.blocked is False
        assert guard.allowed_steps == 3

    def test_fair_source_blocked(self):
        """Fair Source 层步骤 → 拦截。"""
        compiler = PiCompiler()
        guard = compiler.fair_source_guard(_spec(with_fair=True))
        assert guard.blocked is True
        assert guard.blocked_steps == ["s4"]
        assert "许可证边界" in guard.message

    def test_compile_blocked_by_fair_source(self):
        """编译时遇 Fair Source → NSFL-TRIGGER 拒绝（硬约束）。"""
        compiler = PiCompiler()
        with pytest.raises(ValueError, match="Fair Source"):
            compiler.compile_to_tdca(_spec(with_fair=True))

    def test_layer_constants(self):
        """层常量定义。"""
        assert MIT_LAYER == "mit"
        assert FAIR_SOURCE_LAYER == "fair-source"


class TestCompile:
    """A-1 编译适配（Compile 非蒸馏）。"""

    def test_compile_maps_semantics(self):
        """构建动作 → TDCA 制度语义。"""
        compiler = PiCompiler()
        steps = compiler.compile_to_tdca(_spec())
        assert steps[0].tdca_semantics == "配置权边界声明（L2 配置权市场层）"
        assert steps[2].tdca_semantics == "验收门禁（六要素校验）"

    def test_compile_all_mit_layer(self):
        """编译结果全部标注 MIT 层。"""
        compiler = PiCompiler()
        steps = compiler.compile_to_tdca(_spec())
        assert all(s.layer == MIT_LAYER for s in steps)

    def test_compile_deterministic(self):
        """同规格 → 同语义（可复核）。"""
        compiler = PiCompiler()
        s1 = compiler.compile_to_tdca(_spec())
        s2 = compiler.compile_to_tdca(_spec())
        assert [s.to_dict() for s in s1] == [s.to_dict() for s in s2]

    def test_custom_action_mapping(self):
        """未映射动作 → 通用语义。"""
        compiler = PiCompiler()
        spec = {"steps": [{"step_id": "s1", "layer": "mit", "action": "weird"}]}
        steps = compiler.compile_to_tdca(spec)
        assert steps[0].tdca_semantics == "制度语义映射: weird"


class TestNcaStamping:
    """A-2 存证转换。"""

    def test_ncas_generated(self):
        """构建轨迹 → NCA 存证（每次编译步骤落链）。"""
        compiler = PiCompiler()
        steps = compiler.compile_to_tdca(_spec())
        ncas = compiler.build_compile_ncas(steps)
        assert len(ncas) == 3
        assert ncas[0]["Operation-Type"] == "Agent-Compile"

    def test_nca_id_prefix(self):
        """NCA-ID 前缀。"""
        compiler = PiCompiler()
        ncas = compiler.build_compile_ncas(compiler.compile_to_tdca(_spec()))
        assert ncas[0]["NCA-ID"].startswith("NCA-PI-")

    def test_nca_layer_annotation(self):
        """NCA 标注 MIT 层（Fair Source 隔离可审计）。"""
        compiler = PiCompiler()
        ncas = compiler.build_compile_ncas(compiler.compile_to_tdca(_spec()))
        assert all(n["Layer"] == MIT_LAYER for n in ncas)

    def test_nca_provenance(self):
        """ID92: provenance 标注。"""
        compiler = PiCompiler(provenance="REAL-API")
        ncas = compiler.build_compile_ncas(compiler.compile_to_tdca(_spec()))
        assert ncas[0]["Provenance"] == "REAL-API"


class TestCLIAndConstraints:
    """M1c + A-4 不碰核心。"""

    def test_cli_compile(self, capsys):
        """CLI: compile。"""
        rc = cli_main(["compile", "--spec", json.dumps(_spec())])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["guard"]["blocked"] is False
        assert len(result["steps"]) == 3

    def test_cli_guard_blocked(self, capsys):
        """CLI: guard 检测 Fair Source 拦截。"""
        rc = cli_main(["guard", "--spec", json.dumps(_spec(with_fair=True))])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["blocked"] is True

    def test_cli_compile_fair_rejected(self):
        """CLI: 含 Fair Source 编译 → NSFL-TRIGGER 拒绝。"""
        with pytest.raises(ValueError, match="Fair Source"):
            cli_main(["compile", "--spec", json.dumps(_spec(with_fair=True))])

    def test_no_core_modification(self):
        """不碰核心：独立实现（无 import Pi 核心）。"""
        import inspect
        import pi_nca.compiler as mod
        src = inspect.getsource(mod)
        assert "import earendil" not in src
