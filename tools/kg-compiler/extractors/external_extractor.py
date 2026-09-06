"""
TDCA-FC-20260803-005 FR-002 修正声明: 无（首版）
制度锚定: FC-005-SPEC FR-002, ID38(破例识别), ID79(MOU原理)
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 所有外部数据必须标注来源、更新时间、可信度等级
  - 不可信数据源自动降级
  - 外部数据接入必须调用 FC-004B 进行负空间检查
  - 敏感领域知识（政务/金融）需额外审批标记
SPDX-License-Identifier: Apache-2.0
"""

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from .nca_extractor import KnowledgeNode


class ExternalDataExtractor:
    """
    FR-002: 外部数据源接入

    支持接入外部数据源（政府开放数据、行业数据库、API接口），
    将其转化为知识图谱节点。

    支持数据源:
      1. 文件导入（CSV/JSON）
      2. 标准 API（REST/GraphQL）- 框架预留
      3. 政府开放数据 / 行业数据库 - 通过适配器

    制度约束:
      - 所有外部数据必须标注来源、更新时间、可信度等级
      - 不可信数据源自动降级
      - 负空间检查（FC-004B）
    """

    def __init__(self, nsfl_checker: Optional[callable] = None):
        """
        参数:
          nsfl_checker: 负空间检查函数 (data) -> (passed: bool, reason: str)
                        默认使用内置简单检查
        """
        self._nsfl_checker = nsfl_checker or self._default_nsfl_check

    def import_file(
        self,
        filepath: str,
        source_name: str,
        trust_level: float = 0.7,
        mapping: Optional[dict] = None,
        requires_approval: bool = False
    ) -> dict:
        """
        从文件导入外部数据并构建知识节点。

        参数:
          filepath: CSV/JSON 文件路径
          source_name: 数据源名称
          trust_level: 可信度等级 [0,1]
          mapping: 字段映射规则
          requires_approval: 是否需额外审批（敏感领域）

        返回: {
          'nodes_created': int,
          'node_refs': [node_id],
          'source_summary': {...},
          'nsfl_checked': bool,
          'needs_approval': bool,
        }
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"[NSFL-TRIGGER] 数据源文件不存在: {filepath}")

        # 负空间检查（FC-004B）
        records = self._read_file(filepath)
        nsfl_passed, nsfl_reason = self._nsfl_checker(records)
        if not nsfl_passed:
            raise ValueError(f"[NSFL-TRIGGER] 外部数据触碰负空间: {nsfl_reason}")

        # 构建知识节点
        nodes = []
        node_refs = []
        for record in records:
            node = self._build_external_node(
                record, source_name, trust_level, mapping
            )
            nodes.append(node)
            node_refs.append(node.node_id)

        return {
            'nodes_created': len(nodes),
            'node_refs': node_refs,
            'source_summary': {
                'source': source_name,
                'trust_level': trust_level,
                'record_count': len(records),
                'imported_at': datetime.now(timezone.utc).isoformat(),
            },
            'nsfl_checked': True,
            'needs_approval': requires_approval,
            'nodes': [n.to_dict() for n in nodes],
        }

    def import_api(self, url: str, source_name: str, trust_level: float = 0.6, mapping: Optional[dict] = None) -> dict:
        """
        API 数据源接入（框架预留，示例用本地 JSON 模拟）。

        实际接入时需实现 HTTP 请求 + 认证。
        """
        raise NotImplementedError(
            "[NSFL-TRIGGER] API 接入需配置认证与限流策略，当前仅支持文件导入。"
        )

    # ---- 内部方法 ----

    def _read_file(self, filepath: str) -> list:
        """读取 CSV/JSON 文件"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        elif ext in ('.csv', '.txt'):
            records = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records
        else:
            raise ValueError(f"[NSFL-TRIGGER] 不支持的文件格式: {ext}")

    def _build_external_node(
        self,
        record: dict,
        source_name: str,
        trust_level: float,
        mapping: Optional[dict]
    ) -> KnowledgeNode:
        """从单条外部记录构建知识节点"""
        # 字段映射（若有）
        mapped = {}
        if mapping:
            for target_key, source_key in mapping.items():
                if source_key in record:
                    mapped[target_key] = record[source_key]
        else:
            mapped = record

        # 可信度降级：信任等级 × 内容完整性
        content_completeness = min(1.0, len(mapped) / 5.0)
        effective_confidence = trust_level * content_completeness

        node_id = f"TDCA-KN-{uuid.uuid4().hex[:8]}"
        return KnowledgeNode(
            node_id=node_id,
            node_type='EXTERNAL_DATA',
            content={
                'objective_snapshot': str(mapped.get('objective', mapped.get('name', ''))),
                'constraint_pattern': {k: v for k, v in mapped.items() if k not in ('name', 'objective')},
                'allocation_pattern': {},
            },
            metadata={
                'source': f"external:{source_name}",
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'creator_did': 'SYSTEM',
                'external_trust': trust_level,
            },
            confidence={
                'base_score': round(content_completeness, 4),
                'mou_anchor': 0.0,  # 外部数据无税收锚定
                'recency_decay': 1.0,
                'final_score': round(effective_confidence, 4),
                'external_source': source_name,
            },
        )

    @staticmethod
    def _default_nsfl_check(records: list) -> tuple:
        """默认负空间检查：敏感关键词检测"""
        sensitive_keywords = [
            '隐私', 'privacy', '军事', 'military', '机密', 'classified',
            '个人身份证', '政治敏感', '医疗记录',
        ]
        for record in records:
            text = str(record).lower()
            for kw in sensitive_keywords:
                if kw.lower() in text:
                    return False, f"检测到敏感内容: {kw}"
        return True, ""

    def validate(self, result: dict) -> None:
        """
        自证机制：
          1. nodes_created 与 node_refs 一致
          2. nsfl_checked 必须为 True
          3. 每个节点含外部来源标记
        """
        errors = []
        if result['nodes_created'] != len(result['node_refs']):
            errors.append("nodes_created 与 node_refs 不一致")
        if not result.get('nsfl_checked'):
            errors.append("外部数据未经过负空间检查")
        for node in result.get('nodes', []):
            if 'external:' not in node['metadata'].get('source', ''):
                errors.append(f"节点 {node['node_id']} 缺少外部来源标记")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")
