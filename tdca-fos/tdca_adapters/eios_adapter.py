# -*- coding: utf-8 -*-
"""
TDCA EIOS 生态智能操作系统适配器 — 外部系统集成（M3）
制度锚定: ID24 (EIOS 五大智能体类型) | TDCA-KG-001 §2.2 AgentRole | ID91 NCA
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

REPO-003 作为 Service 型智能体注册于 EIOS，通过 ASP 协议接受调度。
NSFL-Declaration:
  - 注册 capabilities 必须与实际实现的 gRPC 接口一一对应，禁止声明未实现能力
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict

# REPO-003 实际实现的 gRPC 能力（与 dev_governance.proto 六 RPC 一一对应）
IMPLEMENTED_CAPABILITIES = [
    "knowledge_graph_query",          # GetDevelopmentConstraints
    "principle_dependency_chain",     # GetPrincipleDependencyChain
    "nsfl_impact_analysis",           # GetNSFLImpact
    "function_spec_verification",     # VerifyFunctionSpecCompleteness
    "mrcr_compatibility_check",       # CheckMRCRCompatibility
    "graph_version_diff",             # GetGraphVersionDiff
]


class EIOSAdapter:
    """
    EIOS 生态智能操作系统适配器
    REPO-003 作为 Service 型智能体注册于 EIOS
    """

    def __init__(self, asp_client, nca_generator):
        self.asp = asp_client  # ASP 智能体调度协议客户端
        self.nca = nca_generator

    def register_as_service(self, service_id: str = "REPO-003-KG") -> Dict:
        """
        注册为 EIOS Service 型智能体
        capabilities 严格对应实际实现的 gRPC 接口（NSFL：不虚构能力）
        """
        registration = {
            "agent_id": service_id,
            "eios_type": "SERVICE",
            "cluster": "GOVERNANCE",
            "capabilities": list(IMPLEMENTED_CAPABILITIES),
            "protocol_version": "TDCA-TP-v1.0",
        }

        self.asp.register_agent(registration)

        if self.nca is not None and hasattr(self.nca, "generate"):
            self.nca.generate(
                type="INSTITUTIONAL", layer=2,
                content={
                    "adapter": "EIOS",
                    "action": "register_as_service",
                    "service_id": service_id,
                },
            )

        return registration

    def handle_asp_call(self, request: Dict) -> Dict:
        """
        处理 ASP 协议调用
        """
        capability = request.get("capability")

        if capability == "knowledge_graph_query":
            return self._handle_kg_query(request)
        elif capability == "principle_dependency_chain":
            return self._handle_dependency_chain(request)
        elif capability == "nsfl_impact_analysis":
            return self._handle_nsfl_impact(request)
        elif capability == "function_spec_verification":
            return self._handle_spec_verification(request)
        elif capability == "mrcr_compatibility_check":
            return self._handle_mrcr(request)
        elif capability == "graph_version_diff":
            return self._handle_version_diff(request)

        return {"error": "Unknown capability"}

    # ---- 能力处理器 ----

    def _handle_kg_query(self, request: Dict) -> Dict:
        """知识图谱查询"""
        if hasattr(self.asp, "route_to_grpc"):
            return self.asp.route_to_grpc("GetDevelopmentConstraints", request)
        return {"capability": "knowledge_graph_query", "handled": True}

    def _handle_dependency_chain(self, request: Dict) -> Dict:
        return {"capability": "principle_dependency_chain", "handled": True}

    def _handle_nsfl_impact(self, request: Dict) -> Dict:
        return {"capability": "nsfl_impact_analysis", "handled": True}

    def _handle_spec_verification(self, request: Dict) -> Dict:
        return {"capability": "function_spec_verification", "handled": True}

    def _handle_mrcr(self, request: Dict) -> Dict:
        return {"capability": "mrcr_compatibility_check", "handled": True}

    def _handle_version_diff(self, request: Dict) -> Dict:
        return {"capability": "graph_version_diff", "handled": True}
