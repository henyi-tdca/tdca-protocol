# -*- coding: utf-8 -*-
"""编译器 M3 集成验收测试（DCD-NSFL-M3 集成里程碑）。

范围（立项方案 M3 原义）: C1-C6 全通过 + 与既有基座集成验证——
  1. 编译器 C1-C6 全链路（M1+M2 回归）
  2. 与 D-2 schema 集成（C3 NS_Rule 结构对齐，消费方无回归）
  3. 与 NS-OPS compile_action_code 兼容（A-7 存量契约）
  4. 与 Runtime L2-R5 Sensor 集成（C6 Δ-Analysis ⊗ 双检查——ICD 共享接口）
  5. 自举闭环（编译器自身 NSFL 检查）
"""
import pytest

from nsfl_compiler import (
    NSFLCompiler,
    CompileStatus,
    SSCPCompiler,
    SelfModificationAnalyzer,
    CompilerBootstrapGuard,
)


# ---------------------------------------------------------------------------
# 1. C1-C6 全链路回归（M1+M2 功能面）
# ---------------------------------------------------------------------------

class TestFullChain:
    def test_c1_c4_compile_full(self):
        """C1-C4: 词法→语法→语义→schema→IR 全通。"""
        c = NSFLCompiler()
        for src in (
            "NSFL: ⊗ LEGAL.data.leak — 法律禁止",
            "NSFL: ⊘ TRANSACTION_LIMIT.transfer | max:100000 @L2 — 转账上限",
            "NSFL: ⊙ DATA_CROSS_BORDER.export | cn:teardown — 跨境熔断",
        ):
            res = c.compile(src)
            assert res.ok, res.errors
            assert res.status == CompileStatus.OK

    def test_c5_sscp_contract(self):
        """C5: SSCP 进化锁契约生成 + LEGAL 底线。"""
        res = SSCPCompiler().compile(
            "LLOCK S_agent_cog WITH threshold=0.9 LOCK_ACTION=FREEZE HUF=true NS_TYPE=LEGAL")
        assert res.ok
        assert res.contract.fuse_directive["fuse_level"] == "PERMANENT_BAN"

    def test_c6_delta_analysis(self):
        """C6: Δ-Analysis 危险模式推导 + ⊗ 注入。"""
        res = SelfModificationAnalyzer().delta_analyze(
            {"S_agent_cog": {}},
            {"type": "CODE_MODIFICATION", "delta_c": "purge nca audit trail"})
        assert res.verdict == "BLOCKED"
        assert res.ns_type_inferred == "LEGAL"
        assert res.fuse_directive["fuse_level"] == "PERMANENT_BAN"


# ---------------------------------------------------------------------------
# 2. 与 D-2 schema 集成（C3 消费方对齐，NS_Rule 结构无回归）
# ---------------------------------------------------------------------------

class TestD2SchemaIntegration:
    def test_ir_rule_matches_d2_ns_rule_shape(self):
        """编译器 NS_Rule 输出与 D-2 schema NS_Rule 结构兼容（消费方零转换）。"""
        res = NSFLCompiler().compile(
            "NSFL: ⊗ LEGAL.data.leak — 法律禁止")
        rule = res.ir.rule
        # D-2 NS_Rule 关键字段（rule_id/ns_type/operator/parameter/severity/layer/alt_path/enabled）
        for field in ("rule_id", "ns_type", "fuse_type", "operator",
                      "parameter", "severity", "layer", "alt_path", "enabled"):
            assert field in rule, f"IR rule 缺 D-2 字段: {field}"
        # LEGAL 语义对齐（fuse_type/severity/alt_path）
        assert rule["fuse_type"] == "LEGAL"
        assert rule["severity"] == "HIGH"
        assert rule["alt_path"] is None

    def test_legal_rule_d2_validate_rules(self):
        """D-2 VALIDATE_RULES 底线（LEGAL 五约束）在编译侧成立。"""
        res = NSFLCompiler().compile("NSFL: ⊗ LEGAL.x.y — note")
        rule = res.ir.rule
        assert rule["operator"] == "FORBID"      # LEGAL 仅 FORBID
        assert rule["severity"] == "HIGH"        # severity 恒 HIGH
        assert rule["alt_path"] is None          # alt_path 恒 None
        assert rule["enabled"] is True           # enabled 恒 True


# ---------------------------------------------------------------------------
# 3. 与 NS-OPS compile_action_code 兼容（A-7 存量契约）
# ---------------------------------------------------------------------------

class TestNSOpsCompat:
    def test_compile_action_code_contract(self):
        """对齐 tdca-ns-ops NSFLApi.compile_action_code 契约（A-7）。"""
        out = NSFLCompiler().compile_action_code("subject", "我不会泄露第三方隐私数据", "high")
        assert out["action_code"].startswith("NSFL: ⊗ subject.")
        assert out["compile_status"] in ("OK", "PARTIAL")
        assert "blocked_for_ambiguity" in out
        assert "message" in out

    def test_compile_action_code_institutional_legal(self):
        """institutional 层映射 LEGAL（存量语料兼容）。"""
        out = NSFLCompiler().compile_action_code("institutional", "禁止伪造贡献记录", "high")
        assert out["compile_status"] == "OK"

    def test_compile_action_code_ambiguous_flag(self):
        """无语义注释声明 → PARTIAL + blocked_for_ambiguity 联动（对齐契约）。"""
        out = NSFLCompiler().compile_action_code("scene", "削弱社区主题意义", "medium")
        assert out["compile_status"] in ("OK", "PARTIAL")
        # 契约: blocked_for_ambiguity 与 PARTIAL 联动
        assert out["blocked_for_ambiguity"] == (out["compile_status"] == "PARTIAL")


# ---------------------------------------------------------------------------
# 4. 与 Runtime L2-R5 Sensor 集成（C6 ⊗ 双检查——ICD §3.3 共享接口）
# ---------------------------------------------------------------------------

class TestRuntimeSensorIntegration:
    def test_shared_delta_analysis_interface(self):
        """ICD §3.3: 编译器 C6 与 Runtime L2-R5 Sensor 同一 Δ 输入同一判定。"""
        from ns_runtime import NSBoundarySensor
        delta = {"type": "CODE_MODIFICATION", "delta_c": "disable fuse guard",
                 "subject": "S_agent_cog-001"}
        state = {"S_agent_cog": {"id": "S_agent_cog-001"}}
        c6 = SelfModificationAnalyzer().delta_analyze(state, delta)
        sensor = NSBoundarySensor()
        sr = sensor.analyze(state, delta)
        # 共享接口语义一致（ns_type 推导相同；Sensor 聚合为 BLOCKED）
        assert c6.ns_type_inferred == sr.ns_type_inferred
        assert sr.verdict == "BLOCKED"
        assert sr.mapped_fuse == "HARD"

    def test_compiler_to_sensor_contract_feed(self):
        """编译器 IR 可注入 Sensor 审计链（端到端数据流）。"""
        from ns_runtime import NSBoundarySensor
        c = NSFLCompiler()
        res = c.compile("NSFL: ⊗ LEGAL.data.leak — 绝对禁止")
        assert res.ok
        # Sensor 对编译期声明的行为做运行时判定（双检查闭合）
        sensor = NSBoundarySensor()
        sr = sensor.analyze(
            {"S_agent_cog": {"id": "S_agent_cog-001"}},
            {"type": "CODE_MODIFICATION",
             "delta_c": f"execute {res.ir.rule['rule_id']}",
             "subject": "S_agent_cog-001"})
        assert sr.verdict in ("SAFE", "WARNING", "BLOCKED", "CRYOGENIC")
        assert sr.nca_ref.startswith("NCA-SENSOR")


# ---------------------------------------------------------------------------
# 5. 自举闭环（编译器自身 NSFL 检查）
# ---------------------------------------------------------------------------

class TestBootstrapClosed:
    def test_compiler_bootstrap_pass(self):
        """编译器自身源码通过 NSFL 检查（自反闭环）。"""
        verdict = CompilerBootstrapGuard().verify_self()
        assert verdict.passed, f"自举失败: {verdict.findings}"
        assert verdict.checked_files >= 5


# ---------------------------------------------------------------------------
# 6. 编译器 M3 全量回归（A-2 时延基线）
# ---------------------------------------------------------------------------

class TestM3Perf:
    def test_full_chain_latency(self):
        """M1-M2 全链路编译 <200ms（M2 阈值）。"""
        import time
        c = NSFLCompiler()
        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            c.compile("NSFL: ⊗ LEGAL.data.leak — 绝对禁止泄露")
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        assert times[int(len(times) * 0.95)] < 200
