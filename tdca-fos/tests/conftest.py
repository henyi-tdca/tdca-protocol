# -*- coding: utf-8 -*-
"""
TDCA-FOS M1 测试夹具
制度锚定: TDCA-KG-001 | FC: TDCA-FC-20260804-006
SPDX-License-Identifier: TDCA-Internal

提供：
  1) InMemoryDriver — Neo4j 内存假驱动（run_single/run_all 语义，测试友好）
  2) sqlite session — KB 存储测试用 SQLite 内存库
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InMemoryResult:
    """模拟 neo4j result 单行"""

    def __init__(self, data: dict):
        self._data = data

    def data(self) -> dict:
        return self._data


class InMemoryDriver:
    """
    Neo4j 内存假驱动
    按查询关键字返回预置结果；未匹配则返回默认（接口熵 0、空列表）。
    """

    def __init__(self):
        self.results = {}
        self.executed = []          # (query, params) 执行记录
        self.nodes = {}             # node_id -> props

    def route(self, keyword: str, data: dict):
        """预置查询结果（keyword 为查询中包含的子串）"""
        self.results[keyword] = data

    def run_single(self, query: str, params: dict) -> dict:
        self.executed.append((query, params))
        for kw, data in self.results.items():
            if kw in query:
                return data
        return {"total_interface_entropy": 0}

    def run_all(self, query: str, params: dict) -> list:
        self.executed.append((query, params))
        for kw, data in self.results.items():
            if kw in query:
                return data if isinstance(data, list) else [data]
        return []

    def session(self):
        return _FakeSession(self)


class _FakeSession:
    """模拟 neo4j session（兼容真实驱动路径）"""

    def __init__(self, driver):
        self._driver = driver

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def run(self, query: str, params: dict):
        for kw, data in self._driver.results.items():
            if kw in query:
                if isinstance(data, list):
                    return [InMemoryResult(d) for d in data]
                return [InMemoryResult(data)]
        return [InMemoryResult({"total_interface_entropy": 0})]


@pytest.fixture
def memory_driver():
    """Neo4j 内存假驱动 fixture"""
    return InMemoryDriver()


@pytest.fixture
def kb_session():
    """SQLite 内存 KB session fixture（生产为 PG）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from tdca_kb.db.models import Base

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def nca_placeholder():
    """NCA 占位生成器 fixture"""
    from checks.nca_placeholder import NCAGeneratorPlaceholder
    return NCAGeneratorPlaceholder()


@pytest.fixture
def kb_store(kb_session, nca_placeholder):
    """KB 存储 fixture"""
    from tdca_kb.db.store import KnowledgeBaseStore
    return KnowledgeBaseStore(kb_session, nca_generator=nca_placeholder)


@pytest.fixture
def sample_unit():
    """标准知识单元 fixture"""
    from tdca_kb.models.knowledge_unit import KnowledgeUnit
    return KnowledgeUnit(
        id="KB-INST-001", source="制度白皮书", chapter="宪法十六条", section="第一条",
        content_text="制度基座具有不可还原的第一性",
        formalization="∀x ∈ 制度基座, ¬∃y: y 可还原为 x",
        examples=["法律底层不可编码"], counter_examples=["试图用技术替代法律"],
        derives=["KB-INST-002"], applicable_scenes=["沙盒准入"],
        required_for_roles=["Constitution-Trainer"], priority=5,
        human_confirmed=True, reviewed_by="智谱-GLM5.2",
    )
