"""paperclip_nca · Paperclip M1 测试（DCD-PAPERCLIP-COMPOUND-001 验收 A-1~A-5）

A-1 协议编译: 编排协议 → 协作语义正确映射（ID21）
A-2 存证转换: 编排日志 → NCA 六要素正确
A-3 不碰核心: Paperclip 核心零修改
A-4 测试: ≥16 用例全绿（M1a 10 + M1b 6）
A-5 回归: 既有基线不破
"""
import json

import pytest

from paperclip_nca.adapter import PaperclipAdapter
from paperclip_nca.cli import main as cli_main


def _orch(orch_id="orch-1"):
    return {
        "orchestration_id": orch_id,
        "tasks": [
            {"task_id": "t1", "agent": "agent-a", "action": "analyze",
             "status": "success", "depends_on": []},
            {"task_id": "t2", "agent": "agent-b", "action": "search",
             "status": "success", "depends_on": ["t1"]},
            {"task_id": "t3", "agent": "agent-a", "action": "summarize",
             "status": "scheduled", "depends_on": ["t1", "t2"]},
        ],
    }


def _cyclic_orch():
    return {
        "orchestration_id": "orch-cyc",
        "tasks": [
            {"task_id": "t1", "agent": "a", "depends_on": ["t2"]},
            {"task_id": "t2", "agent": "b", "depends_on": ["t1"]},
        ],
    }


class TestParse:
    """解析。"""

    def test_parse_valid(self):
        adapter = PaperclipAdapter()
        data = adapter.parse_orchestration(json.dumps(_orch()))
        assert len(data["tasks"]) == 3

    def test_parse_empty_rejected(self):
        adapter = PaperclipAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_orchestration("")

    def test_parse_missing_tasks_rejected(self):
        adapter = PaperclipAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_orchestration(json.dumps({"agents": []}))

    def test_parse_task_missing_fields(self):
        adapter = PaperclipAdapter()
        with pytest.raises(ValueError, match="NSFL-TRIGGER"):
            adapter.parse_orchestration(json.dumps({"tasks": [{"task_id": "t1"}]}))


class TestCompile:
    """A-1 协议编译（ID21 协作即调用）。"""

    def test_compile_maps_collab(self):
        """编排任务 → 协作语义调用（agent/depends_on/action）。"""
        adapter = PaperclipAdapter()
        calls = adapter.compile_to_collab(_orch())
        assert len(calls) == 3
        assert calls[0].agent == "agent-a"
        assert calls[2].depends_on == ["t1", "t2"]

    def test_compile_call_hash(self):
        """协作调用哈希（SHA-256，可复核）。"""
        adapter = PaperclipAdapter()
        calls = adapter.compile_to_collab(_orch())
        assert all(len(c.call_hash) == 64 for c in calls)

    def test_compile_deterministic(self):
        """同编排 → 同哈希。"""
        adapter = PaperclipAdapter()
        c1 = adapter.compile_to_collab(_orch())
        c2 = adapter.compile_to_collab(_orch())
        assert [c.call_hash for c in c1] == [c.call_hash for c in c2]

    def test_dependency_mapping(self):
        """依赖边正确映射（编排边 → depends_on）。"""
        adapter = PaperclipAdapter()
        calls = adapter.compile_to_collab(_orch())
        by_id = {c.task_id: c for c in calls}
        assert by_id["t2"].depends_on == ["t1"]
        assert by_id["t1"].depends_on == []

    def test_acyclic_detection(self):
        """DAG 校验：无环编排 → acyclic true。"""
        adapter = PaperclipAdapter()
        s = adapter.orchestration_summary(_orch())
        assert s["acyclic"] is True

    def test_cyclic_detection(self):
        """环检测：有环编排 → acyclic false。"""
        adapter = PaperclipAdapter()
        s = adapter.orchestration_summary(_cyclic_orch())
        assert s["acyclic"] is False

    def test_summary_structure(self):
        """摘要：agents/tasks/依赖数。"""
        adapter = PaperclipAdapter()
        s = adapter.orchestration_summary(_orch())
        assert s["agents"] == ["agent-a", "agent-b"]
        assert s["task_count"] == 3
        assert s["dependency_count"] == 3


class TestNcaStamping:
    """A-2 存证转换。"""

    def test_nca_records_generated(self):
        """协作调用 → NCA 存证（每次调用落链）。"""
        adapter = PaperclipAdapter()
        calls = adapter.compile_to_collab(_orch())
        ncas = adapter.build_collab_ncas(calls)
        assert len(ncas) == 3
        assert ncas[0].operation_type == "Collab-Invoke"

    def test_nca_id_prefix(self):
        """NCA-ID 前缀正确。"""
        adapter = PaperclipAdapter()
        ncas = adapter.build_collab_ncas(adapter.compile_to_collab(_orch()))
        assert ncas[0].nca_id.startswith("NCA-PAPERCLIP-")

    def test_nca_provenance(self):
        """ID92: provenance 标注。"""
        adapter = PaperclipAdapter(provenance="REAL-API")
        ncas = adapter.build_collab_ncas(adapter.compile_to_collab(_orch()))
        assert ncas[0].provenance == "REAL-API"

    def test_nca_serializable(self):
        """NCA 可序列化（机器可读）。"""
        adapter = PaperclipAdapter()
        ncas = adapter.build_collab_ncas(adapter.compile_to_collab(_orch()))
        json.dumps([n.to_dict() for n in ncas])


class TestCLIAndConstraints:
    """M1c + A-3 不碰核心。"""

    def test_cli_compile(self, capsys):
        """CLI: compile 输出协作语义 + NCA。"""
        rc = cli_main(["compile", "--orch", json.dumps(_orch())])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert len(result["collab_calls"]) == 3
        assert len(result["nca_records"]) == 3

    def test_cli_summary(self, capsys):
        """CLI: summary 输出结构摘要。"""
        rc = cli_main(["summary", "--orch", json.dumps(_orch())])
        out = capsys.readouterr().out
        assert rc == 0
        result = json.loads(out)
        assert result["acyclic"] is True

    def test_no_core_modification(self):
        """不碰核心：适配器独立实现（无 import Paperclip 核心）。"""
        import inspect
        import paperclip_nca.adapter as mod
        src = inspect.getsource(mod)
        assert "import paperclipai" not in src
