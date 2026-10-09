# -*- coding: utf-8 -*-
"""
TDCA-KB 知识库存储层 — 三大白皮书结构化存储（TDCA-KG-001 §4.3）
制度锚定: TDCA-KG-001 §4.3 / §4.4 | ID56
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

职责: 知识单元 CRUD + 场景查询 + KB→KG 联动钩子
NSFL-Declaration:
  - 知识单元写入前校验溯源字段（source 必须为三大白皮书之一）
  - 不写入/伪造未经确认的制度内容
SPDX-License-Identifier: TDCA-Internal
"""

from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from tdca_kb.models.knowledge_unit import KnowledgeUnit

# 合法来源（认知负空间：知识必须溯源至真实白皮书）
VALID_SOURCES = {"制度白皮书", "数学基础白皮书", "经济模型白皮书"}

VALID_STABILITY = {"STABLE", "EVOLVING", "DEPRECATED"}
VALID_MOU_IMPACT = {"HIGH", "MEDIUM", "LOW"}

_MOU_IMPACT_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def impact_order_rank(mou_impact: str) -> int:
    """MOU 影响排序键（降级路径用）"""
    return _MOU_IMPACT_RANK.get(mou_impact, 3)


class KnowledgeBaseStore:
    """
    三大白皮书结构化存储 — TDCA-KG-001 §4.3
    :param session: SQLAlchemy Session（生产为 PG，测试可为 SQLite 内存）
    """

    def __init__(self, session: Session, nca_generator=None):
        self.session = session
        self.nca = nca_generator

    # ---- CRUD ----

    def create_unit(self, unit: KnowledgeUnit) -> str:
        """创建知识单元（校验溯源字段）"""
        self._validate_unit(unit)
        from tdca_kb.db.models import KnowledgeUnitORM
        orm = KnowledgeUnitORM(
            id=unit.id, source=unit.source, chapter=unit.chapter,
            section=unit.section, content_text=unit.content_text,
            formalization=unit.formalization, examples=unit.examples,
            counter_examples=unit.counter_examples, derives=unit.derives,
            contradicts=unit.contradicts, implements=unit.implements,
            tested_by=unit.tested_by, priority=unit.priority,
            stability=unit.stability, ota_version=unit.ota_version,
            last_reviewed=unit.last_reviewed, reviewed_by=unit.reviewed_by,
            human_confirmed=unit.human_confirmed,
            applicable_scenes=unit.applicable_scenes,
            required_for_roles=unit.required_for_roles,
            mou_impact=unit.mou_impact,
        )
        self.session.add(orm)
        self.session.flush()
        self._record_nca("CreateKnowledgeUnit", {"unit_id": unit.id})
        return unit.id

    def get_unit(self, unit_id: str) -> Optional[KnowledgeUnit]:
        """按 ID 读取知识单元"""
        from tdca_kb.db.models import KnowledgeUnitORM
        orm = self.session.get(KnowledgeUnitORM, unit_id)
        self._record_nca("GetKnowledgeUnit", {"unit_id": unit_id},
                         {"found": orm is not None})
        return orm.to_dataclass() if orm else None

    def update_unit(self, unit_id: str, **fields) -> bool:
        """更新知识单元字段"""
        from tdca_kb.db.models import KnowledgeUnitORM
        orm = self.session.get(KnowledgeUnitORM, unit_id)
        if orm is None:
            return False
        allowed = {
            "content_text", "formalization", "examples", "counter_examples",
            "derives", "contradicts", "implements", "tested_by",
            "priority", "stability", "ota_version", "last_reviewed",
            "reviewed_by", "human_confirmed", "applicable_scenes",
            "required_for_roles", "mou_impact",
        }
        for k, v in fields.items():
            if k not in allowed:
                raise ValueError(f"非法更新字段: {k}")
            setattr(orm, k, v)
        self.session.flush()
        self._record_nca("UpdateKnowledgeUnit", {"unit_id": unit_id, "fields": list(fields)})
        return True

    def delete_unit(self, unit_id: str) -> bool:
        """删除知识单元"""
        from tdca_kb.db.models import KnowledgeUnitORM
        orm = self.session.get(KnowledgeUnitORM, unit_id)
        if orm is None:
            return False
        self.session.delete(orm)
        self.session.flush()
        self._record_nca("DeleteKnowledgeUnit", {"unit_id": unit_id})
        return True

    def list_units(self, source: Optional[str] = None,
                   limit: int = 100) -> List[KnowledgeUnit]:
        """列出知识单元（可按来源过滤）"""
        from tdca_kb.db.models import KnowledgeUnitORM
        q = self.session.query(KnowledgeUnitORM)
        if source:
            q = q.filter(KnowledgeUnitORM.source == source)
        rows = q.limit(limit).all()
        self._record_nca("ListKnowledgeUnits",
                         {"source": source, "limit": limit},
                         {"count": len(rows)})
        return [r.to_dataclass() for r in rows]

    # ---- 核心查询模式（TDCA-KG-001 §4.3）----

    def query_by_scene(self, scene_id: str) -> List[KnowledgeUnit]:
        """
        查询某场景适用的全部制度约束 — TDCA-KG-001 §4.3 核心查询模式
        条件: applicable_scenes 包含 scene_id, 非 DEPRECATED, 人工确认
        排序: priority DESC, mou_impact DESC
        """
        from tdca_kb.db.models import KnowledgeUnitORM
        from sqlalchemy import case

        impact_order = case(
            (KnowledgeUnitORM.mou_impact == "HIGH", 0),
            (KnowledgeUnitORM.mou_impact == "MEDIUM", 1),
            else_=2,
        )
        dialect = (self.session.bind.dialect.name
                   if self.session.bind is not None else "sqlite")
        if dialect == "postgresql":
            # 生产 PG：原生 ARRAY ANY 索引加速
            rows = (
                self.session.query(KnowledgeUnitORM)
                .filter(
                    KnowledgeUnitORM.applicable_scenes.any(scene_id),
                    KnowledgeUnitORM.stability != "DEPRECATED",
                    KnowledgeUnitORM.human_confirmed.is_(True),
                )
                .order_by(KnowledgeUnitORM.priority.desc(), impact_order)
                .all()
            )
        else:
            # 测试降级（SQLite）：候选集 Python 过滤后排序，语义与 PG 一致
            rows = (
                self.session.query(KnowledgeUnitORM)
                .filter(
                    KnowledgeUnitORM.stability != "DEPRECATED",
                    KnowledgeUnitORM.human_confirmed.is_(True),
                )
                .all()
            )
            rows = [r for r in rows if scene_id in (r.applicable_scenes or [])]
            rows.sort(key=lambda r: (-r.priority, impact_order_rank(r.mou_impact)))
        self._record_nca("QueryByScene", {"scene_id": scene_id},
                         {"count": len(rows)})
        return [r.to_dataclass() for r in rows]

    # ---- KB→KG 联动 ----

    def sync_to_kg(self, unit: KnowledgeUnit,
                   graph_writer: Optional[Any] = None) -> Optional[str]:
        """
        KB → KG 联动：知识单元变更自动触发图谱节点更新（TDCA-KG-001 §4.4）
        :param graph_writer: 可选的图谱写接口（upsert_node）
        """
        node = unit.to_kg_node()
        if graph_writer is not None:
            return graph_writer.upsert_node(node)
        return None

    # ---- 内部 ----

    def _validate_unit(self, unit: KnowledgeUnit):
        """溯源校验（认知负空间）"""
        if unit.source not in VALID_SOURCES:
            raise ValueError(
                f"[NSFL-TRIGGER] 非法知识来源: {unit.source}，"
                f"必须为 {sorted(VALID_SOURCES)}"
            )
        if unit.stability not in VALID_STABILITY:
            raise ValueError(f"非法 stability: {unit.stability}")
        if unit.mou_impact not in VALID_MOU_IMPACT:
            raise ValueError(f"非法 mou_impact: {unit.mou_impact}")

    def _record_nca(self, op: str, params: Dict, summary: Any = None) -> Optional[str]:
        """记录操作 NCA — ID91"""
        if self.nca is None:
            return None
        if hasattr(self.nca, "record_query"):
            return self.nca.record_query(
                query_type=op, parameters=params, result_summary=summary or {})
        return None
