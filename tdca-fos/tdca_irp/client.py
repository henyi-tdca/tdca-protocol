# -*- coding: utf-8 -*-
"""IRP 客户端 SDK 骨架 — 16 智能体经 gRPC 接入七库（AGENT-TASK-008-IMPL）
制度锚定: TypeSystem §5.1/§5.2 | ID24 | ID91 | ID82
"""
import grpc
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tdca_gateway", "proto", "gen"))
import irp_extension_pb2 as pb
import irp_extension_pb2_grpc as stub


class IRPClient:
    """IRP 客户端：cross_query 五步（皈依→七元组→查询→NCA→验证）"""

    def __init__(self, gateway_endpoint, agent_id, nca_generator=None):
        self.channel = grpc.insecure_channel(gateway_endpoint)
        self.gateway = stub.IRPGatewayStub(self.channel)
        self.agent_id = agent_id
        self.nca = nca_generator

    def _config_right(self, how, share=0.0, tax=0):
        return pb.IRPConfigRightCall(
            who=self.agent_id, what="irp", when=0, how=how,
            share=share, cfg="cfg-hash", tax=tax)

    def cross_query(self, target_repo, query, nca_trace=()):
        """步骤: 七元组 → IRPCrossQuery → 网关（皈依+NSFL+查询）→ 返回+NCA"""
        req = pb.IRPQueryRequest(
            agent_id=self.agent_id, target_repo=target_repo, query=query,
            config_right=self._config_right("query"), nca_trace=list(nca_trace))
        return self.gateway.IRPCrossQuery(req)

    def cross_invoke(self, target_repo, operation, payload, nca_trace=()):
        req = pb.IRPInvokeRequest(
            agent_id=self.agent_id, target_repo=target_repo, operation=operation,
            payload=payload, config_right=self._config_right("invoke"),
            nca_trace=list(nca_trace))
        return self.gateway.IRPCrossInvoke(req)

    def cross_verify(self, nca_id, nca_trace=()):
        req = pb.IRPVerifyRequest(agent_id=self.agent_id, nca_id=nca_id,
                                  nca_trace=list(nca_trace))
        return self.gateway.IRPCrossVerify(req)
