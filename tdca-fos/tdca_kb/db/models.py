# -*- coding: utf-8 -*-
"""
TDCA-KB PostgreSQL 表结构 — SQLAlchemy ORM（TDCA-KG-001 §4.3）
制度锚定: TDCA-KG-001 §4.2 / §4.3 | ID56
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

覆盖 KnowledgeUnit 全部字段：
  内容层 / 关系层 / 元数据层 / 应用层
NSFL-Declaration:
  - 表结构仅定义存储形态，不承载任何制度语义裁决
  - 知识单元内容必须溯源至真实白皮书
SPDX-License-Identifier: TDCA-Internal
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime,
    ForeignKey, func, Index, JSON,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 测试兼容：SQLite 无 ARRAY，回退到 JSON（生产保持 PG ARRAY）
def _array(col_type):
    return ARRAY(col_type).with_variant(JSON, "sqlite")


class Base(DeclarativeBase):
    """TDCA-KB ORM 基类"""


class KnowledgeUnitORM(Base):
    """
    知识单元表 — TDCA-KG-001 §4.2 knowledge_unit 结构的 SQL 映射
    """
    __tablename__ = "knowledge_units"

    # 标识
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    chapter: Mapped[str] = mapped_column(String(128), nullable=False)
    section: Mapped[str] = mapped_column(String(128), nullable=False)

    # 内容层
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    formalization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[List[str]] = mapped_column(_array(Text), default=list)
    counter_examples: Mapped[List[str]] = mapped_column(_array(Text), default=list)

    # 关系层
    derives: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)
    contradicts: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)
    implements: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)
    tested_by: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)

    # 元数据层
    priority: Mapped[int] = mapped_column(Integer, default=3)
    stability: Mapped[str] = mapped_column(String(16), default="STABLE")
    ota_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    last_reviewed: Mapped[str] = mapped_column(String(64), default="")
    reviewed_by: Mapped[str] = mapped_column(String(64), default="")
    human_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # 应用层
    applicable_scenes: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)
    required_for_roles: Mapped[List[str]] = mapped_column(_array(String(64)), default=list)
    mou_impact: Mapped[str] = mapped_column(String(8), default="MEDIUM")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 索引：场景查询加速（TDCA-KG-001 §4.3 核心查询模式）
    __table_args__ = (
        # 按场景查询：稳定性 + 人工确认 + 优先级排序
        Index("ix_ku_scene_lookup", "stability", "human_confirmed", "priority"),
        # 按来源白皮书查询
        Index("ix_ku_source_chapter", "source", "chapter"),
    )

    def to_dataclass(self) -> "KnowledgeUnit":
        """ORM -> 领域模型转换（避免循环依赖，延迟导入）"""
        from tdca_kb.models.knowledge_unit import KnowledgeUnit
        return KnowledgeUnit(
            id=self.id, source=self.source, chapter=self.chapter,
            section=self.section, content_text=self.content_text,
            formalization=self.formalization, examples=self.examples or [],
            counter_examples=self.counter_examples or [],
            derives=self.derives or [], contradicts=self.contradicts or [],
            implements=self.implements or [], tested_by=self.tested_by or [],
            priority=self.priority, stability=self.stability,
            ota_version=self.ota_version, last_reviewed=self.last_reviewed,
            reviewed_by=self.reviewed_by, human_confirmed=self.human_confirmed,
            applicable_scenes=self.applicable_scenes or [],
            required_for_roles=self.required_for_roles or [],
            mou_impact=self.mou_impact,
        )
