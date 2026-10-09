# -*- coding: utf-8 -*-
"""
TDCA FC-005 知识图谱编译器适配器 — 外部系统集成（M3）
制度锚定: TDCA-KG-001 §七 (与 FC-005 衔接) | ID82 接口熵 | ID91 NCA
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

FC-005 作为上游客户端，调用 REPO-003 获取制度约束后编译。
NSFL-Declaration:
  - 编译前必须验证接口熵=0（ID82），否则拒绝编译
  - 不绕过 REPO-003 的制度约束查询
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict


class FC005Adapter:
    """
    FC-005 知识图谱编译器适配器
    FC-005 作为上游客户端，调用 REPO-003 获取制度约束
    """

    def __init__(self, grpc_client, nca_generator):
        self.client = grpc_client  # gRPC 客户端（GetDevelopmentConstraints 接口）
        self.nca = nca_generator

    def compile_with_constraints(self, target_role_id: str,
                                 source_code: str,
                                 developer_model: str = "DeepSeek-V4") -> Dict:
        """
        FC-005 编译前获取制度约束
        """
        # 调用 REPO-003 gRPC 服务
        constraints = self.client.GetDevelopmentConstraints(
            target_role_id=target_role_id,
            target_cluster="GOVERNANCE",
            developer_model=developer_model,
            scene_id="fc005_compile",
        )

        # 验证接口熵（ID82）
        entropy = getattr(constraints, "interface_entropy_budget", 0)
        if entropy > 0:
            raise ValueError("FC-005 编译产物接口熵 > 0，拒绝编译")

        # 生成编译 NCA
        nca = None
        if self.nca is not None and hasattr(self.nca, "generate"):
            nca = self.nca.generate(
                type="TECHNICAL", layer=2,
                content={
                    "adapter": "FC005",
                    "action": "compile_with_constraints",
                    "target_role": target_role_id,
                    "constraints_count": len(getattr(constraints, "principles", [])),
                },
            )

        return {
            "constraints": constraints,
            "nca": nca,
            "can_compile": True,
        }
