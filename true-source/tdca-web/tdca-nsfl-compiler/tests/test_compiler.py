# -*- coding: utf-8 -*-
"""编译器 M1 单元测试：C1 词法/语法/语义 + C2 ⊗⊘⊙ + C3 schema + C4 IR。"""
import pytest

from nsfl_compiler import (
    NSFLCompiler,
    CompileStatus,
    NSFLLexer,
    NSFLParser,
    NSFLTokenType,
    NSFLSyntaxError,
    SemanticAnalyzer,
    NSFLOperatorSemantics,
    SchemaValidator,
    SchemaValidationError,
)
from nsfl_compiler.operators import FuseLevel, FuseTier, NS_Operator
from nsfl_compiler.schema import NSFLRule


# ---------------------------------------------------------------------------
# C1 词法
# ---------------------------------------------------------------------------

class TestLexer:
    def test_basic_tokens(self):
        toks = NSFLLexer("NSFL: ⊗ data.leak(third_party)").tokenize()
        types = [t.type for t in toks]
        assert types == [
            NSFLTokenType.NSFL, NSFLTokenType.COLON, NSFLTokenType.OPERATOR,
            NSFLTokenType.IDENT, NSFLTokenType.DOT, NSFLTokenType.IDENT,
            NSFLTokenType.LPAREN, NSFLTokenType.IDENT, NSFLTokenType.RPAREN,
            NSFLTokenType.EOF,
        ]

    def test_all_operators(self):
        for op in "⊗⊘⊙":
            toks = NSFLLexer(f"NSFL: {op} x.y").tokenize()
            assert toks[2].type == NSFLTokenType.OPERATOR
            assert toks[2].value == op

    def test_note_stripping(self):
        toks = NSFLLexer("NSFL: ⊗ x.y — 绝对禁止泄露").tokenize()
        assert toks[-2].type == NSFLTokenType.NOTE
        assert toks[-2].value == "绝对禁止泄露"

    def test_number_and_pipe(self):
        toks = NSFLLexer("NSFL: ⊘ TRANSACTION_LIMIT.transfer | max:100 @L2").tokenize()
        types = [t.type for t in toks]
        # 词法层独立 token：max / : / 100（组合在 parser 层完成）
        assert NSFLTokenType.NUMBER in types
        vals = [t.value for t in toks]
        assert "max" in vals and "100" in vals
        assert NSFLTokenType.PIPE in types and NSFLTokenType.AT in types

    def test_string_arg(self):
        toks = NSFLLexer("NSFL: ⊙ x.y('cn') | cross_border@suspend").tokenize()
        assert any(t.type == NSFLTokenType.STRING and t.value == "cn" for t in toks)

    def test_unexpected_char(self):
        with pytest.raises(NSFLSyntaxError):
            NSFLLexer("NSFL: ⊗ x.y $bad").tokenize()

    def test_unclosed_string(self):
        with pytest.raises(NSFLSyntaxError):
            NSFLLexer("NSFL: ⊗ x.y('abc)").tokenize()

    def test_position_tracking(self):
        toks = NSFLLexer("NSFL:\n  ⊗ x.y").tokenize()
        op = next(t for t in toks if t.type == NSFLTokenType.OPERATOR)
        assert op.line == 2


# ---------------------------------------------------------------------------
# C1 语法（Parser）
# ---------------------------------------------------------------------------

class TestParser:
    def test_parse_forbid(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.data.leak(third_party) — 法律禁止").parse()
        assert decl.operator == "⊗"
        assert decl.ns_type == "LEGAL"
        assert decl.action == "data.leak"
        assert decl.args == ["third_party"]
        assert decl.note == "法律禁止"
        assert decl.operator_name == "FORBID"

    def test_parse_limit(self):
        decl = NSFLParser("NSFL: ⊘ TRANSACTION_LIMIT.transfer | max:100 @L2").parse()
        assert decl.operator == "⊘"
        assert decl.ns_type == "TRANSACTION_LIMIT"
        assert decl.parameter == "max:100"
        assert decl.layer == "L2"

    def test_parse_scene(self):
        decl = NSFLParser("NSFL: ⊙ DATA_CROSS_BORDER.transfer | cn:teardown").parse()
        assert decl.operator_name == "SCENE"
        assert decl.parameter == "cn:teardown"

    def test_parse_action_segments(self):
        decl = NSFLParser("NSFL: ⊗ ETHICAL.a.b.c").parse()
        assert decl.action == "a.b.c"

    def test_parse_missing_operator(self):
        with pytest.raises(NSFLSyntaxError):
            NSFLParser("NSFL: x.y").parse()

    def test_parse_missing_nsfl_keyword(self):
        with pytest.raises(NSFLSyntaxError):
            NSFLParser("⊗ x.y").parse()

    def test_parse_trailing_tokens(self):
        with pytest.raises(NSFLSyntaxError):
            NSFLParser("NSFL: ⊗ x.y extra").parse()


# ---------------------------------------------------------------------------
# C1 语义（Semantic）
# ---------------------------------------------------------------------------

class TestSemantic:
    def test_unknown_ns_type(self):
        decl = NSFLParser("NSFL: ⊗ NOPE.x.y").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert not res.ok
        assert res.issues[0].code == "NS-001"

    def test_legal_only_forbid(self):
        decl = NSFLParser("NSFL: ⊘ LEGAL.x.y | max:5").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert not res.ok
        assert any(i.code == "NS-002" for i in res.issues)

    def test_layer_mismatch(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.x.y @L2").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert any(i.code == "NS-003" for i in res.issues)

    def test_forbid_with_parameter(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.x.y | max:5").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert any(i.code == "NS-004" for i in res.issues)

    def test_limit_requires_parameter(self):
        decl = NSFLParser("NSFL: ⊘ TRANSACTION_LIMIT.transfer").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert any(i.code == "NS-005" for i in res.issues)

    def test_ok_declaration(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.data.leak — 法律禁止").parse()
        res = SemanticAnalyzer().analyze(decl)
        assert res.ok
        assert res.inferred_layer == "L0"


# ---------------------------------------------------------------------------
# C2 ⊗⊘⊙ 运算符执行语义（A-3 全覆盖）
# ---------------------------------------------------------------------------

class TestOperatorSemantics:
    @pytest.mark.parametrize("ns_type,level,tier", [
        ("LEGAL", FuseLevel.PERMANENT_BAN, FuseTier.ATOMIC),
        ("DATA_CROSS_BORDER", FuseLevel.TEARDOWN, FuseTier.HARD),
        ("TRANSACTION_LIMIT", FuseLevel.TEARDOWN, FuseTier.HARD),
        ("SENSITIVE_CONTENT", FuseLevel.TEARDOWN, FuseTier.HARD),
        ("TECH_CONSTRAINT", FuseLevel.TEARDOWN, FuseTier.HARD),
        ("ETHICAL", FuseLevel.SUSPEND, FuseTier.SOFT),
        ("EMOTIONAL", FuseLevel.SUSPEND, FuseTier.SOFT),
        ("BELIEF", FuseLevel.SUSPEND, FuseTier.SOFT),
    ])
    def test_forbid_all_types(self, ns_type, level, tier):
        d = NSFLOperatorSemantics.resolve(ns_type, "⊗")
        assert d.operator == NS_Operator.FORBID
        assert d.fuse_level == level
        assert d.tier == tier
        assert d.alt_path is None  # 绝对禁止一律无 alt_path

    def test_forbid_legal_no_alt_path(self):
        d = NSFLOperatorSemantics.resolve("LEGAL", "⊗")
        assert d.alt_path is None
        assert d.fuse_level == FuseLevel.PERMANENT_BAN

    def test_limit_max(self):
        d = NSFLOperatorSemantics.resolve("TRANSACTION_LIMIT", "⊘", "max:100")
        assert d.operator == NS_Operator.LIMIT_MAX
        assert d.parameter == "100"

    def test_limit_min(self):
        d = NSFLOperatorSemantics.resolve("TRANSACTION_LIMIT", "⊘", "min:0")
        assert d.operator == NS_Operator.LIMIT_MIN

    def test_limit_eq(self):
        d = NSFLOperatorSemantics.resolve("TECH_CONSTRAINT", "⊘", "eq:5")
        assert d.operator == NS_Operator.LIMIT_EQ

    def test_limit_default_max(self):
        d = NSFLOperatorSemantics.resolve("TRANSACTION_LIMIT", "⊘", "100")
        assert d.operator == NS_Operator.LIMIT_MAX

    def test_limit_bad_prefix(self):
        with pytest.raises(ValueError):
            NSFLOperatorSemantics.resolve("TRANSACTION_LIMIT", "⊘", "foo:1")

    def test_scene_domain_only(self):
        d = NSFLOperatorSemantics.resolve("DATA_CROSS_BORDER", "⊙", "cn")
        assert d.operator == NS_Operator.RESTRICT_TIER
        assert d.domain == "cn"
        assert d.fuse_level == FuseLevel.SUSPEND  # 默认档

    def test_scene_domain_tier(self):
        d = NSFLOperatorSemantics.resolve("DATA_CROSS_BORDER", "⊙", "cn:teardown")
        assert d.fuse_level == FuseLevel.TEARDOWN
        assert d.domain == "cn"

    def test_scene_bad_tier(self):
        with pytest.raises(ValueError):
            NSFLOperatorSemantics.resolve("DATA_CROSS_BORDER", "⊙", "cn@nuke")

    def test_unknown_operator(self):
        with pytest.raises(ValueError):
            NSFLOperatorSemantics.resolve("LEGAL", "?")


# ---------------------------------------------------------------------------
# C3 schema 校验
# ---------------------------------------------------------------------------

class TestSchemaValidator:
    def test_legal_rule(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.data.leak — 法律禁止").parse()
        rule = SchemaValidator().validate(decl)
        assert isinstance(rule, NSFLRule)
        assert rule.operator == NS_Operator.FORBID
        assert rule.severity == "HIGH"
        assert rule.layer == "L0"
        assert rule.enabled is True
        assert rule.alt_path is None

    def test_rule_id_injection_rejected(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.x.y — note").parse()
        with pytest.raises(SchemaValidationError) as ei:
            SchemaValidator().validate(decl, rule_id="bad id; DROP TABLE")
        assert ei.value.code == "NS-006"

    def test_legal_operator_restricted(self):
        # ⊘ 用于 LEGAL → 语义层已拒（NS-002），validate 抛错
        decl = NSFLParser("NSFL: ⊘ LEGAL.x.y | max:5").parse()
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate(decl)

    def test_limit_decimal_rejects_negative(self):
        decl = NSFLParser("NSFL: ⊘ TRANSACTION_LIMIT.transfer | max:-5").parse()
        with pytest.raises(SchemaValidationError) as ei:
            SchemaValidator().validate(decl)
        assert ei.value.code == "NS-009"

    def test_restrict_tier_validation(self):
        decl = NSFLParser("NSFL: ⊙ DATA_CROSS_BORDER.x | cn:observe").parse()
        rule = SchemaValidator().validate(decl)
        assert rule.parameter == "OBSERVE"

    def test_restrict_tier_bad_value(self):
        decl = NSFLParser("NSFL: ⊙ DATA_CROSS_BORDER.x | cn:nuke").parse()
        with pytest.raises(SchemaValidationError) as ei:
            SchemaValidator().validate(decl)
        assert ei.value.code == "NS-008"

    def test_layer_mismatch_rejected(self):
        decl = NSFLParser("NSFL: ⊗ LEGAL.x.y @L2 — note").parse()
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate(decl)


class TestInstitutionalBottomLines:
    """制度底线双保险分支（NS-011~NS-014，直接触发 _validate_institutional）。"""

    def _rule(self, ns_type="LEGAL", operator=NS_Operator.FORBID, severity="HIGH",
              layer="L0", alt_path=None, enabled=True) -> NSFLRule:
        return NSFLRule(
            rule_id="NSFL-TEST-001", ns_type=ns_type, operator=operator,
            parameter=None, severity=severity, layer=layer,
            alt_path=alt_path, enabled=enabled,
        )

    def test_legal_severity_not_high(self):
        # NS-011: fuse_type==LEGAL → severity 恒 HIGH
        v = SchemaValidator()
        with pytest.raises(SchemaValidationError) as ei:
            v._validate_institutional(self._rule(severity="LOW"), "LEGAL", "LEGAL")
        assert ei.value.code == "NS-011"

    def test_legal_alt_path_injected(self):
        # NS-012: fuse_type==LEGAL → alt_path 恒 None（ID86 绝对熔断）
        v = SchemaValidator()
        with pytest.raises(SchemaValidationError) as ei:
            v._validate_institutional(self._rule(alt_path="escape"), "LEGAL", "LEGAL")
        assert ei.value.code == "NS-012"

    def test_legal_enabled_flipped(self):
        # NS-013: fuse_type==LEGAL → enabled 恒 True（防 OTA 软重置）
        v = SchemaValidator()
        with pytest.raises(SchemaValidationError) as ei:
            v._validate_institutional(self._rule(enabled=False), "LEGAL", "LEGAL")
        assert ei.value.code == "NS-013"

    def test_severity_escalation_rejected(self):
        # NS-014: severity > severity_max 越级拒绝（L2 场景型不得 HIGH）
        v = SchemaValidator()
        with pytest.raises(SchemaValidationError) as ei:
            v._validate_institutional(
                self._rule(ns_type="TRANSACTION_LIMIT", severity="HIGH", layer="L2"),
                "TECHNICAL", "TRANSACTION_LIMIT",
            )
        assert ei.value.code == "NS-014"

    def test_legal_passes_bottom_lines(self):
        # 合法 LEGAL 规则通过全部底线
        v = SchemaValidator()
        v._validate_institutional(self._rule(), "LEGAL", "LEGAL")  # 不抛异常


# ---------------------------------------------------------------------------
# C4 IR / 字节码 + 主流水线
# ---------------------------------------------------------------------------

class TestIRAndCompiler:
    def test_compile_ok(self):
        result = NSFLCompiler().compile("NSFL: ⊗ LEGAL.data.leak(third_party) — 绝对禁止泄露第三方数据")
        assert result.ok
        assert result.status == CompileStatus.OK
        ir = result.ir
        assert ir.rule["fuse_type"] == "LEGAL"
        assert ir.rule["operator"] == "FORBID"
        assert ir.directive["fuse_level"] == "PERMANENT_BAN"
        assert any(b.opcode == "NSFL_DECL" for b in ir.bytecode)

    def test_compile_partial_without_note(self):
        result = NSFLCompiler().compile("NSFL: ⊗ LEGAL.x.y")
        assert result.ok
        assert result.status == CompileStatus.PARTIAL
        assert result.warnings

    def test_compile_failed_unknown_type(self):
        result = NSFLCompiler().compile("NSFL: ⊗ NOPE.x.y")
        assert not result.ok
        assert result.status == CompileStatus.FAILED
        assert result.errors

    def test_compile_deterministic(self):
        src = "NSFL: ⊗ LEGAL.data.leak(third_party) — 法律禁止"
        a = NSFLCompiler().compile(src).ir.to_dict()
        b = NSFLCompiler().compile(src).ir.to_dict()
        assert a == b  # 确定性输出（BV-3 可验证）

    def test_to_dict_shape(self):
        result = NSFLCompiler().compile("NSFL: ⊗ LEGAL.x.y — note")
        d = result.to_dict()
        assert set(d) == {"ok", "status", "ir", "errors", "warnings", "duration_ms"}
        assert d["status"] == "OK"

    def test_compile_action_code_compat(self):
        compiler = NSFLCompiler()
        out = compiler.compile_action_code("subject", "我不会泄露第三方隐私数据", "high")
        assert out["action_code"].startswith("NSFL: ⊗ subject.")
        assert out["compile_status"] in ("OK", "PARTIAL")

    def test_compile_action_code_institutional(self):
        out = NSFLCompiler().compile_action_code("institutional", "禁止伪造贡献记录", "high")
        assert out["action_code"].startswith("NSFL: ⊗ institutional.")
        assert out["compile_status"] == "OK"

    def test_perf_single_declaration(self):
        """A-2: 单条声明 <100ms（P95<200ms）。"""
        compiler = NSFLCompiler()
        src = "NSFL: ⊗ LEGAL.data.leak(third_party) — 绝对禁止泄露第三方数据"
        times = []
        for _ in range(50):
            result = compiler.compile(src)
            assert result.ok
            times.append(result.duration_ms)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 200
        assert max(times) < 200
