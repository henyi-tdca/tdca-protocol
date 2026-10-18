# -*- coding: utf-8 -*-
"""
TDCA-Gateway gRPC 六 RPC 集成测试 — M2
制度锚定: TDCA-KG-001 §3.4/§5.2 | ID38/ID82/ID91 | FC: TDCA-FC-20260804-006-M2
SPDX-License-Identifier: TDCA-Internal
"""

import pytest

from tdca_gateway.proto import dev_governance_pb2
from tdca_gateway.server.grpc_server import TDCAGatewayServicer
from tdca_nca.generator import NCAGenerator
from tdca_nsfl.fuse_engine import NSFLEngine
from tdca_tp.engine.inference_engine import TDCATPReasoner


class FakeGraph:
    """图引擎假实现"""

    def __init__(self):
        self.constraints = {
            "constraint_set": {
                "required_principles": ["ID29"],
                "total_interface_entropy": 0,
            },
            "interface_entropy": 0.0,
        }

    def get_development_constraints(self, **kw):
        return self.constraints

    def verify_function_spec_completeness(self, role_id):
        return {"has_objective": True, "has_constraints": True, "has_prior": True,
                "has_config_right": True, "has_allocation": True, "has_audit_trail": True}

    def check_mrcr_isolation(self, agent_id, scene_ids):
        return True

    def get_dependency_chain(self, pid):
        return [{"id": pid, "name": "n", "priority": 5, "formalization": "f"}]

    def get_principle_priority(self, principle_id):
        return 5 if principle_id == "ID29" else 0

    def get_principle_name(self, principle_id):
        return "制度基座具有不可还原的第一性"

    def get_nsfl_for_scene(self, scene_id):
        return [{"id": "NSFL-LEGAL-001", "type": "LEGAL", "pattern": "⊗",
                 "level": "HARD"}]

    def get_version_diff(self, frm, to):
        return ["node-1", "node-2"]


class FakeContext:
    def __init__(self):
        self.code = None
        self.details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


@pytest.fixture
def servicer():
    graph = FakeGraph()
    nca = NCAGenerator()
    nsfl = NSFLEngine(nca_generator=nca)
    tp = TDCATPReasoner(graph_engine=graph, nca_generator=nca, nsfl_engine=nsfl)
    return TDCAGatewayServicer(graph, None, tp, nca, nsfl)


class TestGetDevelopmentConstraints:
    """RPC 1：获取开发约束"""

    def test_ok_response(self, servicer):
        req = dev_governance_pb2.ConstraintQuery(
            target_role_id="Constitution-Trainer",
            target_cluster="GOVERNANCE",
            developer_model="DeepSeek-V4",
            scene_id="scene-1",
        )
        resp = servicer.GetDevelopmentConstraints(req, FakeContext())
        assert resp.version == "TDCA-FC-20260804-006-M2"
        assert resp.constraint_set.interface_entropy_budget == 0.0
        assert resp.nca.nca_id.startswith("NCA-")

    def test_pseudo_innovation_denied(self, servicer):
        """ID38：破例识别触发 → PERMISSION_DENIED"""
        req = dev_governance_pb2.ConstraintQuery(
            target_role_id="绕过 ID29 的例外通道",
            target_cluster="GOVERNANCE",
            developer_model="DeepSeek-V4",
            scene_id="scene-1",
        )
        ctx = FakeContext()
        resp = servicer.GetDevelopmentConstraints(req, ctx)
        assert ctx.code.name == "PERMISSION_DENIED"
        assert resp.nca.nca_id.startswith("NCA-")  # 拒绝也携带 NCA

    def test_entropy_violation_precondition(self, servicer):
        """ID82：接口熵 > 0 → FAILED_PRECONDITION"""
        servicer.graph.constraints["constraint_set"]["total_interface_entropy"] = 0.5
        req = dev_governance_pb2.ConstraintQuery(
            target_role_id="正常角色", target_cluster="GOVERNANCE",
            developer_model="DeepSeek-V4", scene_id="scene-1",
        )
        ctx = FakeContext()
        servicer.GetDevelopmentConstraints(req, ctx)
        assert ctx.code.name == "FAILED_PRECONDITION"


class TestOtherRPCs:
    """RPC 2-6"""

    def test_get_principle_dependency_chain(self, servicer):
        req = dev_governance_pb2.PrincipleQuery(principle_id="ID29")
        resp = servicer.GetPrincipleDependencyChain(req, FakeContext())
        assert resp.dependency_chain.depth == 1
        assert resp.dependency_chain.chain[0].id == "ID29"
        assert resp.nca.nca_id.startswith("NCA-")

    def test_get_nsfl_impact(self, servicer):
        req = dev_governance_pb2.NSFLImpactQuery(scene_id="scene-1")
        resp = servicer.GetNSFLImpact(req, FakeContext())
        assert resp.nsfl_impact.blocked is True
        assert resp.nsfl_impact.applicable_rules[0].id == "NSFL-LEGAL-001"

    def test_verify_spec_completeness(self, servicer):
        req = dev_governance_pb2.FunctionSpecQuery(role_id="role-1")
        resp = servicer.VerifyFunctionSpecCompleteness(req, FakeContext())
        assert resp.completeness.complete is True
        assert resp.completeness.has_objective is True

    def test_check_mrcr_compatibility(self, servicer):
        req = dev_governance_pb2.MRCRQuery(agent_id="a1", scene_ids=["s1", "s2"])
        resp = servicer.CheckMRCRCompatibility(req, FakeContext())
        assert resp.mrcr.isolated is True
        assert resp.mrcr.violations == []

    def test_get_graph_version_diff(self, servicer):
        req = dev_governance_pb2.VersionQuery(from_version="v1.0.0",
                                              to_version="v1.1.0")
        resp = servicer.GetGraphVersionDiff(req, FakeContext())
        assert len(resp.version_diff.changed_nodes) == 2

    def test_all_rpcs_generate_nca(self, servicer):
        """每个 RPC 都生成 NCA（ID91）"""
        before = servicer.nca.count()
        servicer.GetPrincipleDependencyChain(
            dev_governance_pb2.PrincipleQuery(principle_id="ID29"), FakeContext())
        servicer.GetNSFLImpact(
            dev_governance_pb2.NSFLImpactQuery(scene_id="s"), FakeContext())
        servicer.VerifyFunctionSpecCompleteness(
            dev_governance_pb2.FunctionSpecQuery(role_id="r"), FakeContext())
        servicer.CheckMRCRCompatibility(
            dev_governance_pb2.MRCRQuery(agent_id="a"), FakeContext())
        servicer.GetGraphVersionDiff(
            dev_governance_pb2.VersionQuery(from_version="a", to_version="b"),
            FakeContext())
        assert servicer.nca.count() >= before + 5
