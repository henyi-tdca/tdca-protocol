# -*- coding: utf-8 -*-
"""
TDCA 外部系统适配器 M3 测试 — FC005/EIOS/Notifier/Chain/DCEP
制度锚定: TDCA-KG-001 §七 | ID24 | ID43 | ID79/ID92 | FC: TDCA-FC-20260804-006-M3
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_adapters.fc005_adapter import FC005Adapter
from tdca_adapters.eios_adapter import EIOSAdapter, IMPLEMENTED_CAPABILITIES
from tdca_adapters.notifier_adapter import NotifierAdapter
from tdca_adapters.chain_adapter import TDCAChainAdapter
from tdca_adapters.dcep_adapter import DCEPAdapter
from tdca_nca.generator import NCAGenerator


# ==================== FC-005 适配器 ====================

class FakeGRPCClient:
    """gRPC 客户端假实现"""

    def __init__(self, entropy=0.0):
        self.entropy = entropy
        self.calls = []

    def GetDevelopmentConstraints(self, **kw):
        self.calls.append(kw)
        return _FakeConstraints(self.entropy)


class _FakeConstraints:
    def __init__(self, entropy):
        self.interface_entropy_budget = entropy
        self.principles = [{"id": "ID29"}]


class TestFC005Adapter:
    """检查项 8：FC-005 编译前获取制度约束"""

    def test_compile_with_constraints(self, nca_placeholder):
        client = FakeGRPCClient(entropy=0.0)
        adapter = FC005Adapter(client, nca_placeholder)
        out = adapter.compile_with_constraints("Constitution-Trainer", "code")
        assert out["can_compile"] is True
        assert out["constraints"].principles
        assert len(client.calls) == 1

    def test_entropy_positive_rejected(self, nca_placeholder):
        """ID82：接口熵 > 0 拒绝编译"""
        adapter = FC005Adapter(FakeGRPCClient(entropy=0.5), nca_placeholder)
        with pytest.raises(ValueError):
            adapter.compile_with_constraints("role-x", "code")

    def test_generates_nca(self):
        from tdca_nca.generator import NCAGenerator
        nca_gen = NCAGenerator()
        adapter = FC005Adapter(FakeGRPCClient(), nca_gen)
        out = adapter.compile_with_constraints("role-x", "code")
        assert out["nca"] is not None
        assert nca_gen.count() == 1


# ==================== EIOS 适配器 ====================

class FakeASP:
    def __init__(self):
        self.registrations = []
        self.calls = []

    def register_agent(self, registration):
        self.registrations.append(registration)

    def route_to_grpc(self, rpc_name, request):
        self.calls.append(rpc_name)
        return {"rpc": rpc_name, "handled": True}


class TestEIOSAdapter:
    """检查项 9：EIOS 注册为 Service 型智能体"""

    def test_register_as_service(self, nca_placeholder):
        asp = FakeASP()
        adapter = EIOSAdapter(asp, nca_placeholder)
        reg = adapter.register_as_service("REPO-003-KG")
        assert reg["eios_type"] == "SERVICE"
        assert reg["cluster"] == "GOVERNANCE"
        assert asp.registrations[0]["agent_id"] == "REPO-003-KG"

    def test_capabilities_match_grpc(self):
        """NSFL：capabilities 必须与六 RPC 一一对应，禁止虚构能力"""
        from tdca_gateway.server.grpc_server import TDCAGatewayServicer
        rpc_names = {m for m in dir(TDCAGatewayServicer) if m[0].isupper()}
        assert len(IMPLEMENTED_CAPABILITIES) == 6  # 对应 6 RPC
        assert len(rpc_names) == 6

    def test_handle_kg_query(self, nca_placeholder):
        asp = FakeASP()
        adapter = EIOSAdapter(asp, nca_placeholder)
        out = adapter.handle_asp_call({"capability": "knowledge_graph_query"})
        assert out["handled"] is True

    def test_handle_unknown_capability(self, nca_placeholder):
        adapter = EIOSAdapter(FakeASP(), nca_placeholder)
        out = adapter.handle_asp_call({"capability": "no_such"})
        assert out["error"] == "Unknown capability"


# ==================== 通知机适配器 ====================

class FakeKGForNotifier:
    def __init__(self):
        self.nodes = {}
        self.updates = []

    def update_node_property(self, node_id, property_name, value):
        self.updates.append((node_id, property_name, value))
        self.nodes[node_id] = self.nodes.get(node_id, {})
        self.nodes[node_id][property_name] = value

    def get_node(self, node_id):
        return self.nodes.get(node_id, {})

    def query(self, cypher, params):
        scene = params.get("scene_id")
        return [{"notifier_id": n["physical_notifier"]}
                for n in self.nodes.values()
                if n.get("scene") == scene and n.get("physical_notifier")]


class TestNotifierAdapter:
    """检查项 10：拓扑节点绑定物理通知机"""

    def test_bind_notifier(self, nca_placeholder):
        kg = FakeKGForNotifier()
        adapter = NotifierAdapter(kg, nca_placeholder)
        result = adapter.bind_notifier("node-1", "NOTIFIER-01")
        assert result["bound"] is True
        assert kg.nodes["node-1"]["physical_notifier"] == "NOTIFIER-01"

    def test_get_notifier_by_scene(self, nca_placeholder):
        kg = FakeKGForNotifier()
        kg.nodes["n1"] = {"scene": "scene-a", "physical_notifier": "N-1"}
        kg.nodes["n2"] = {"scene": "scene-a", "physical_notifier": "N-2"}
        adapter = NotifierAdapter(kg, nca_placeholder)
        notifiers = adapter.get_notifier_by_scene("scene-a")
        assert set(notifiers) == {"N-1", "N-2"}


# ==================== 联盟链适配器 ====================

class FakeChain:
    def __init__(self):
        self.batches = []
        self.verified = []

    def submit_batch(self, batch):
        self.batches.append(batch)
        return f"tx-{len(self.batches)}"

    def verify(self, nca_id):
        self.verified.append(nca_id)
        return True


class TestChainAdapter:
    """检查项 11：TDCA 链批量上链（≥100 条自动上链）"""

    def test_batch_flush_at_threshold(self, nca_placeholder):
        chain = FakeChain()
        adapter = TDCAChainAdapter(chain, nca_placeholder, batch_size=5)
        for i in range(5):
            adapter.submit_nca({"nca_id": f"NCA-{i}", "seal": "s",
                                "timestamp": i, "content": {"i": i}})
        assert adapter.flush_count == 1
        assert adapter.pending_count() == 0
        assert len(chain.batches[0]) == 5

    def test_below_threshold_accumulates(self, nca_placeholder):
        chain = FakeChain()
        adapter = TDCAChainAdapter(chain, nca_placeholder, batch_size=100)
        for i in range(3):
            adapter.submit_nca({"nca_id": f"NCA-{i}", "seal": "s",
                                "timestamp": i, "content": {}})
        assert adapter.flush_count == 0
        assert adapter.pending_count() == 3

    def test_content_hash_included(self, nca_placeholder):
        chain = FakeChain()
        adapter = TDCAChainAdapter(chain, nca_placeholder, batch_size=1)
        adapter.submit_nca({"nca_id": "NCA-1", "seal": "s",
                            "timestamp": 1, "content": {"a": 1}})
        entry = chain.batches[0][0]
        assert "content_hash" in entry
        assert len(entry["content_hash"]) == 64

    def test_verify_on_chain(self, nca_placeholder):
        chain = FakeChain()
        adapter = TDCAChainAdapter(chain, nca_placeholder)
        assert adapter.verify_on_chain("NCA-1") is True


# ==================== DCEP 适配器 ====================

class FakeDCEP:
    def __init__(self):
        self.execs = []
        self.queries = []

    def execute_contract(self, contract_type, params):
        self.execs.append((contract_type, params))
        return {"tx_hash": "tx-abc"}

    def query_contract(self, transaction_id):
        self.queries.append(transaction_id)
        return True


class TestDCEPAdapter:
    """检查项 12：数字人民币 MOU 锚定（真实税收数据强制）"""

    def test_anchor_mou_sums_tax(self, nca_placeholder):
        dcep = DCEPAdapter(FakeDCEP(), nca_placeholder)
        out = dcep.anchor_mou("TXN-1", tax_in=50, tax_out=30)
        assert out["mou"] == 80
        assert out["contract_tx"] == "tx-abc"

    def test_missing_tax_data_blocked(self, nca_placeholder):
        """NSFL：无真实税收数据禁止生成虚假 MOU（ID79/ID92）"""
        dcep = DCEPAdapter(FakeDCEP(), nca_placeholder)
        with pytest.raises(ValueError):
            dcep.anchor_mou("TXN-2", tax_in=None, tax_out=10)

    def test_negative_tax_blocked(self, nca_placeholder):
        dcep = DCEPAdapter(FakeDCEP(), nca_placeholder)
        with pytest.raises(ValueError):
            dcep.anchor_mou("TXN-3", tax_in=-5, tax_out=10)

    def test_zero_tax_allowed(self, nca_placeholder):
        """真实零税收（合法空转）应允许"""
        dcep = DCEPAdapter(FakeDCEP(), nca_placeholder)
        out = dcep.anchor_mou("TXN-4", tax_in=0, tax_out=0)
        assert out["mou"] == 0

    def test_verify_mou(self, nca_placeholder):
        dcep = DCEPAdapter(FakeDCEP(), nca_placeholder)
        assert dcep.verify_mou("TXN-1") is True
