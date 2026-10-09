# -*- coding: utf-8 -*-
"""
TDCA-Gateway gRPC 服务完整实现 — DevCluster → Governance Cluster
制度锚定: TDCA-KG-001 §3.4 / §5.2 | ID38 破例识别 | ID82 接口熵 | ID91 NCA
版本: V1.0 | 状态: M2-CODED | FC: TDCA-FC-20260804-006-M2

六 RPC 全部实现，每个 RPC 调用生成 NCA。
依赖注入：graph_engine / kb_store / tp_reasoner / nca_generator / nsfl_engine。
NSFL-Declaration:
  - 破例识别触发时返回 PERMISSION_DENIED 并触发熔断
  - 接口熵 > 0 时返回 FAILED_PRECONDITION
  - 所有响应必须携带 NCA 引用（ID91）
SPDX-License-Identifier: TDCA-Internal
"""

from concurrent import futures
from typing import Optional, Any

import grpc

from tdca_gateway.proto import (
    dev_governance_pb2,
    dev_governance_pb2_grpc,
)

try:
    import google.protobuf  # noqa: F401
    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False


class TDCAGatewayServicer(dev_governance_pb2_grpc.TDCAKnowledgeGraphServicer):
    """
    DevCluster → Governance Cluster gRPC 服务完整实现
    所有 RPC 调用必须生成 NCA
    """

    def __init__(self, graph_engine, kb_store, tp_reasoner, nca_generator,
                 nsfl_engine=None):
        self.graph = graph_engine
        self.kb = kb_store
        self.tp = tp_reasoner
        self.nca = nca_generator
        self.nsfl = nsfl_engine
        self.version = "TDCA-FC-20260804-006-M2"

    # ---- NCA 工具 ----

    def _make_nca(self, query_type: str,
                  params: dict) -> dev_governance_pb2.NCAReference:
        """统一 NCA 生成"""
        nca = self.nca.generate(
            type="COGNITIVE", layer=1,
            content={"query": query_type, "params": params},
        )
        return dev_governance_pb2.NCAReference(
            nca_id=nca.nca_id,
            seal=nca.seal,
            mou_contribution=nca.mou_contribution,
        )

    def _deny(self, context: grpc.ServicerContext, code, details,
              query_type: str, params: dict):
        """生成拒绝响应（携带 NCA）"""
        context.set_code(code)
        context.set_details(details)
        try:
            nca_ref = self._make_nca(query_type, params)
        except Exception:
            nca_ref = dev_governance_pb2.NCAReference()
        return dev_governance_pb2.TDCAResponse(nca=nca_ref, version=self.version)

    # ---- RPC 1: 获取开发约束 ----

    def GetDevelopmentConstraints(self, request: Any, context: Any) -> Any:
        """TDCA-KG-001 §3.4 核心接口 — 获取开发约束"""
        # 1. 查询图数据库
        constraints = self.graph.get_development_constraints(
            target_role_id=request.target_role_id,
            target_cluster=request.target_cluster,
            developer_model=request.developer_model,
            scene_id=request.scene_id,
        )
        constraint_set = constraints.get("constraint_set", {})

        # 2. 执行破例识别预检（ID38）
        pseudo_check = self.tp.execute("ExceptionDetection", {
            "principle_id": "ID29",
            "draft_text": request.target_role_id,
        })
        if pseudo_check.triggered:
            if self.nsfl is not None:
                self.nsfl.trigger(
                    rule_id="ID38-PRE-CHECK", severity=3,
                    reason=pseudo_check.alert.get("reason", ""),
                    alt_path=pseudo_check.alert.get("alt_path", "人工审查"),
                    nca_ref=pseudo_check.nca_reference,
                )
            return self._deny(
                context, grpc.StatusCode.PERMISSION_DENIED,
                f"破例识别触发: {pseudo_check.alert.get('reason', '')}",
                "GetDevelopmentConstraints",
                {"role": request.target_role_id},
            )

        # 3. 接口熵验证（ID82）
        total_entropy = constraint_set.get("total_interface_entropy", 0) or 0
        if total_entropy > 0:
            entropy_check = self.tp.execute("InterfaceEntropyZero", {
                "code_module_id": f"module-{request.target_role_id}",
                "compiler": request.developer_model,
                "calculated_entropy": total_entropy,
            })
            if entropy_check.triggered:
                return self._deny(
                    context, grpc.StatusCode.FAILED_PRECONDITION,
                    "接口熵 > 0，违反 TDCA-PRINCIPLE-INTERFACE-ENTROPY-001",
                    "GetDevelopmentConstraints",
                    {"role": request.target_role_id},
                )

        # 4. 构建响应
        principles = [
            dev_governance_pb2.Principle(
                id=p["id"], name=p["name"], priority=p["priority"],
                formalization=p.get("formalization", ""),
            )
            for p in constraint_set.get("required_principles_as_objects", [])
        ]
        articles = [
            dev_governance_pb2.Constitution(
                article=c.get("article", 0), title=c.get("title", ""),
                text=c.get("text", ""),
                enforcement_level=c.get("enforcement_level", "HARD"),
            )
            for c in constraint_set.get("required_constitutions_as_objects", [])
        ]
        nsfl_rules = [
            dev_governance_pb2.NSFLRule(
                id=r.get("id", ""), type=r.get("type", ""),
                pattern=r.get("pattern", ""), level=r.get("level", "HARD"),
            )
            for r in constraint_set.get("required_nsfl_rules_as_objects", [])
        ]

        response = dev_governance_pb2.ConstraintSet(
            interface_entropy_budget=0.0,
            human_signature_required=any(p.priority == 5 for p in principles),
            principles=principles,
            articles=articles,
            nsfl_rules=nsfl_rules,
        )

        return dev_governance_pb2.TDCAResponse(
            constraint_set=response,
            nca=self._make_nca("GetDevelopmentConstraints", {
                "role": request.target_role_id,
                "model": request.developer_model,
            }),
            version=self.version,
        )

    # ---- RPC 2: 制度原理依赖链 ----

    def GetPrincipleDependencyChain(self, request: Any, context: Any) -> Any:
        """查询制度原理依赖链"""
        chain = self.graph.get_dependency_chain(request.principle_id) \
            if hasattr(self.graph, "get_dependency_chain") else []
        principles = [
            dev_governance_pb2.Principle(
                id=p.get("id", ""), name=p.get("name", ""),
                priority=p.get("priority", 0),
                formalization=p.get("formalization", ""),
            )
            for p in (chain if isinstance(chain, list) else [])
        ]
        return dev_governance_pb2.TDCAResponse(
            dependency_chain=dev_governance_pb2.DependencyChain(
                chain=principles, depth=len(principles)),
            nca=self._make_nca("GetPrincipleDependencyChain",
                               {"id": request.principle_id}),
            version=self.version,
        )

    # ---- RPC 3: NSFL 影响查询 ----

    def GetNSFLImpact(self, request: Any, context: Any) -> Any:
        """查询负空间规则对某场景的影响"""
        rules = self.graph.get_nsfl_for_scene(request.scene_id) \
            if hasattr(self.graph, "get_nsfl_for_scene") else []
        applicable = [
            dev_governance_pb2.NSFLRule(
                id=r.get("id", ""), type=r.get("type", ""),
                pattern=r.get("pattern", ""), level=r.get("level", "HARD"),
            )
            for r in (rules if isinstance(rules, list) else [])
        ]
        blocked = any(r.level == "HARD" for r in applicable)
        alt_path = "" if not blocked else "发起宪法修正案流程（慢系统）"
        return dev_governance_pb2.TDCAResponse(
            nsfl_impact=dev_governance_pb2.NSFLImpactReport(
                applicable_rules=applicable, blocked=blocked, alt_path=alt_path),
            nca=self._make_nca("GetNSFLImpact", {"scene": request.scene_id}),
            version=self.version,
        )

    # ---- RPC 4: 函数语料六要素完整性 ----

    def VerifyFunctionSpecCompleteness(self, request: Any, context: Any) -> Any:
        """验证函数语料六要素完整性 — ID68"""
        result = self.graph.verify_function_spec_completeness(request.role_id)
        checks = {
            "has_objective": result.get("has_objective", False),
            "has_constraints": result.get("has_constraints", False),
            "has_prior": result.get("has_prior", False),
            "has_config_right": result.get("has_config_right", False),
            "has_allocation": result.get("has_allocation", False),
            "has_audit_trail": result.get("has_audit_trail", False),
        }
        return dev_governance_pb2.TDCAResponse(
            completeness=dev_governance_pb2.CompletenessReport(
                has_objective=checks["has_objective"],
                has_constraints=checks["has_constraints"],
                has_prior=checks["has_prior"],
                has_config_right=checks["has_config_right"],
                has_allocation=checks["has_allocation"],
                has_audit_trail=checks["has_audit_trail"],
                complete=all(checks.values()),
            ),
            nca=self._make_nca("VerifyFunctionSpecCompleteness",
                               {"role": request.role_id}),
            version=self.version,
        )

    # ---- RPC 5: MRCR 兼容性 ----

    def CheckMRCRCompatibility(self, request: Any, context: Any) -> Any:
        """MRCR 兼容性检查 — ID54"""
        isolated = self.graph.check_mrcr_isolation(
            request.agent_id, list(request.scene_ids))
        violations = [] if isolated else [f"agent:{request.agent_id} 场景未隔离"]
        return dev_governance_pb2.TDCAResponse(
            mrcr=dev_governance_pb2.MRCRReport(
                isolated=isolated, violations=violations),
            nca=self._make_nca("CheckMRCRCompatibility",
                               {"agent": request.agent_id}),
            version=self.version,
        )

    # ---- RPC 6: 图版本差异 ----

    def GetGraphVersionDiff(self, request: Any, context: Any) -> Any:
        """图版本差异查询 — OTA 支持"""
        diff = self.graph.get_version_diff(
            request.from_version, request.to_version) \
            if hasattr(self.graph, "get_version_diff") else []
        return dev_governance_pb2.TDCAResponse(
            version_diff=dev_governance_pb2.VersionDiff(
                changed_nodes=diff if isinstance(diff, list) else []),
            nca=self._make_nca("GetGraphVersionDiff", {
                "from": request.from_version, "to": request.to_version}),
            version=self.version,
        )


def serve(graph_engine: Any, kb_store: Any, tp_reasoner: Any, nca_generator: Any,
          nsfl_engine: Any = None, port: int = 50051) -> Optional[grpc.Server]:
    """启动 gRPC 服务"""
    if not PROTO_AVAILABLE:
        return None
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = TDCAGatewayServicer(
        graph_engine, kb_store, tp_reasoner, nca_generator, nsfl_engine)
    dev_governance_pb2_grpc.add_TDCAKnowledgeGraphServicer_to_server(
        servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server
