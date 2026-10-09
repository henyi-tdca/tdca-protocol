# -*- coding: utf-8 -*-
"""
TDCA 通知机适配器 — 拓扑维度子图绑定物理节点（M3）
制度锚定: TDCA-KG-001 §2.2 TopologyNode / §七 | TDCA-ENV-001 | ID91 NCA
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

物理锚定从概念变为图节点（拓扑维度子图）。
NSFL-Declaration:
  - 通知机绑定仅写 TopologyNode.physical_notifier 属性，不修改其他维度
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Any


class NotifierAdapter:
    """
    通知机适配器 — 拓扑维度子图绑定物理节点
    """

    def __init__(self, kg_engine, nca_generator):
        self.kg = kg_engine
        self.nca = nca_generator

    def bind_notifier(self, node_id: str, notifier_id: str) -> Dict:
        """
        将拓扑节点绑定到物理通知机
        """
        # 更新图数据库
        if hasattr(self.kg, "update_node_property"):
            self.kg.update_node_property(
                node_id=node_id,
                property_name="physical_notifier",
                value=notifier_id,
            )

        # 验证绑定
        node = self.kg.get_node(node_id) if hasattr(self.kg, "get_node") else None
        bound = (node or {}).get("physical_notifier") == notifier_id

        if self.nca is not None and hasattr(self.nca, "generate"):
            self.nca.generate(
                type="TECHNICAL", layer=2,
                content={
                    "adapter": "NOTIFIER",
                    "action": "bind_notifier",
                    "node_id": node_id,
                    "notifier_id": notifier_id,
                },
            )

        return {"node_id": node_id, "notifier_id": notifier_id, "bound": bound}

    def get_notifier_by_scene(self, scene_id: str) -> List[str]:
        """
        查询某场景下的全部通知机
        """
        if hasattr(self.kg, "query"):
            rows = self.kg.query(
                """
                MATCH (s:Scene {scene_id: $scene_id})<-[:BOUND_TO]-(n:TopologyNode)
                RETURN n.physical_notifier AS notifier_id
                """,
                {"scene_id": scene_id},
            )
            return [r.get("notifier_id") for r in rows if r.get("notifier_id")]
        return []
