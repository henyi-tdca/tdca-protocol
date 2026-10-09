"""maka_nca · Maka M1 测试（DCD-MAKA-COMPOUND-001 验收 A-1~A-6）

A-1 格式转换: Event Log（model/tool_call/tool_result/termination）→ NCA 六要素
A-2 哈希链: append-only → 审计轨迹哈希链连续
A-3 正和验证: UtilityGenie 正和性评估
A-4 不碰核心: 转换器独立包（BIDIR-001，不修改 Maka 核心）
A-5 测试: ≥20 用例全绿（M1a 12 + M1b 8）
A-6 回归: 既有基线不破
"""
import json

import pytest

from maka_nca.cli import main as cli_main
from maka_nca.converter import EVENT_TO_OP_TYPE, MakaNcaConverter
from maka_nca.validator import PositiveSumValidator


def _event(etype, **kw):
    ev = {"type": etype, "agent": "agent-x", "provenance": "SIMULATED"}
    ev.update(kw)
    return ev


def _sample_log():
    return [
        _event("model", call_id="c1", content="start"),
        _event("tool_call", call_id="c2", tool="search", status="success"),
        _event("tool_result", call_id="c3", success=True, result="found"),
        _event("model", call_id="c4", content="analyze"),
        _event("termination", call_id="c5", reason="complete"),
    ]


class TestParse:
    """M1a 解析。"""

    def test_parse_jsonl(self):
        raw = "\n".join(json.dumps(e) for e in _sample_log())
        conv = MakaNcaConverter()
        events = conv.parse_event_log(raw)
        assert len(events) == 5

    def test_parse_json_array(self):
        raw = json.dumps(_sample_log())
        conv = MakaNcaConverter()
        events = conv.parse_event_log(raw)
        assert len(events) == 5

    def test_parse_empty_rejected(self):
        conv = MakaNcaConverter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            conv.parse_event_log("")

    def test_parse_invalid_type_rejected(self):
        conv = MakaNcaConverter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            conv.parse_event_log(json.dumps([{"type": "bogus"}]))


class TestConversion:
    """M1a 格式转换（A-1）。"""

    def test_event_type_mapping(self):
        """四类事件 → 正确 Operation-Type。"""
        assert EVENT_TO_OP_TYPE["model"] == "Agent-Inference"
        assert EVENT_TO_OP_TYPE["tool_call"] == "Tool-Invoke"
        assert EVENT_TO_OP_TYPE["tool_result"] == "Tool-Result"
        assert EVENT_TO_OP_TYPE["termination"] == "Agent-Termination"

    def test_to_nca_record(self):
        """单事件 → NCA 记录（六要素字段齐全）。"""
        conv = MakaNcaConverter()
        rec = conv.to_nca_record(_event("tool_call", call_id="c9"), seq=9)
        d = rec.to_dict()
        assert d["NCA-ID"].startswith("NCA-MAKA-")
        assert d["Operation-Type"] == "Tool-Invoke"
        assert d["Provenance"] == "SIMULATED"
        assert d["Source-Event"]["type"] == "tool_call"

    def test_record_hash_nonempty(self):
        """记录哈希非空（SHA-256）。"""
        conv = MakaNcaConverter()
        rec = conv.to_nca_record(_event("model"), seq=1)
        assert len(rec.record_hash) == 64

    def test_hash_changes_with_event(self):
        """不同事件 → 不同哈希。"""
        conv = MakaNcaConverter()
        r1 = conv.to_nca_record(_event("model", content="a"), seq=1)
        r2 = conv.to_nca_record(_event("model", content="b"), seq=1)
        assert r1.record_hash != r2.record_hash


class TestAuditChain:
    """M1a 哈希链（A-2）。"""

    def test_chain_prev_hash_linked(self):
        """审计链：每记录 prev_hash 指向前一记录。"""
        conv = MakaNcaConverter()
        chain = conv.build_audit_chain(_sample_log())
        assert len(chain) == 5
        assert chain[0].prev_hash is None
        assert chain[1].prev_hash == chain[0].record_hash

    def test_chain_integrity_verified(self):
        """链完整性验证通过。"""
        conv = MakaNcaConverter()
        chain = conv.build_audit_chain(_sample_log())
        assert conv.verify_chain(chain) is True

    def test_chain_tamper_detected(self):
        """篡改中间记录 → 链验证失败（append-only 不可篡改）。"""
        conv = MakaNcaConverter()
        chain = conv.build_audit_chain(_sample_log())
        # 篡改第 2 条记录的哈希（模拟）
        from dataclasses import replace
        tampered = replace(chain[1], record_hash="0" * 64)
        assert conv.verify_chain([chain[0], tampered] + chain[2:]) is False

    def test_chain_deterministic_hashes(self):
        """同输入序列 → 同链（可复核）。"""
        conv = MakaNcaConverter()
        c1 = conv.build_audit_chain(_sample_log())
        c2 = conv.build_audit_chain(_sample_log())
        assert [r.record_hash for r in c1] == [r.record_hash for r in c2]


class TestPositiveSum:
    """M1b 正和验证（A-3）。"""

    def test_positive_sum(self):
        """高成功占比 → POSITIVE_SUM。"""
        log = [_event("tool_call", status="success"),
               _event("tool_result", success=True),
               _event("tool_call", status="success"),
               _event("tool_result", success=True)]
        v = PositiveSumValidator().validate(log)
        assert v.verdict == "POSITIVE_SUM"
        assert v.positive_sum is True

    def test_negative_sum(self):
        """低成功占比 → NEGATIVE_SUM（停机制定建议）。"""
        log = [_event("tool_call", status="success"),
               _event("tool_result", success=True),
               _event("tool_call", status="failed"),
               _event("tool_result", success=False),
               _event("tool_call", status="failed"),
               _event("tool_result", success=False)]
        v = PositiveSumValidator().validate(log)
        assert v.verdict == "NEGATIVE_SUM"
        assert "停机制定" in v.recommendation

    def test_no_calls(self):
        """无工具调用 → NO_CALLS。"""
        log = [_event("model")]
        v = PositiveSumValidator().validate(log)
        assert v.verdict == "NO_CALLS"

    def test_empty_rejected(self):
        """空事件 → 拒绝。"""
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            PositiveSumValidator().validate([])

    def test_custom_threshold(self):
        """自定义阈值。"""
        log = [_event("tool_call", status="success"),
               _event("tool_result", success=True),
               _event("tool_call", status="failed"),
               _event("tool_result", success=False)]
        v = PositiveSumValidator(threshold=0.4).validate(log)
        assert v.positive_sum is True  # 0.5 >= 0.4

    def test_ratio_calculation(self):
        """成功占比计算正确。"""
        log = [_event("tool_call", status="success"),
               _event("tool_result", success=True),
               _event("tool_call", status="failed"),
               _event("tool_result", success=True)]
        v = PositiveSumValidator().validate(log)
        assert v.total_calls == 4
        assert v.successful_calls == 3
        assert v.failed_calls == 1
        assert v.success_ratio == pytest.approx(0.75)


class TestEndToEnd:
    """M1c 端到端（A-4 不碰核心）。"""

    def test_endtoend_integration(self):
        """转换 + 正和验证一体化。"""
        conv = MakaNcaConverter()
        events = conv.parse_event_log(json.dumps(_sample_log()))
        chain = conv.build_audit_chain(events)
        verdict = PositiveSumValidator().validate(events)
        assert conv.verify_chain(chain) is True
        assert verdict.verdict in ("POSITIVE_SUM", "NO_CALLS")

    def test_cli_convert(self, capsys):
        """CLI: convert 输出审计链。"""
        raw = json.dumps(_sample_log())
        rc = cli_main(["convert", "--log", raw])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["chain_integrity"] is True
        assert len(result["records"]) == 5

    def test_cli_validate(self, capsys):
        """CLI: validate 输出正和判定。"""
        raw = json.dumps(_sample_log())
        rc = cli_main(["validate", "--log", raw, "--session", "s1"])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert "verdict" in result

    def test_cli_endtoend(self, capsys):
        """CLI: endtoend 全链。"""
        raw = json.dumps(_sample_log())
        rc = cli_main(["endtoend", "--log", raw])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["chain_integrity"] is True
        assert "positive_sum" in result

    def test_no_core_modification(self):
        """不碰核心：转换器独立于 Maka——无 import 外部核心。"""
        import inspect
        import maka_nca.converter as conv_mod
        src = inspect.getsource(conv_mod)
        # 独立实现，不依赖任何 Maka 核心模块
        assert "import maka" not in src
