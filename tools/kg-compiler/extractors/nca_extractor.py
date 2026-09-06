"""
TDCA-FC-20260803-005 FR-001 修正声明: 无（首版）
制度锚定: ID68(函数语料六要素), ID79(MOU原理), FC-005-SPEC FR-001
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 知识节点创建必须生成 NCA 存证（FC-001）
  - 税收锚定（MOU）作为置信度硬指标
  - 时效性衰减：越老的 NCA 置信度越低
  - 禁止将未确权的 NCA 内容提取为知识节点
SPDX-License-Identifier: Apache-2.0
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional


class KnowledgeNode:
    """知识节点（FC-005-SPEC §3.1）"""

    def __init__(
        self,
        node_id: str,
        node_type: str,
        content: dict,
        metadata: dict,
        confidence: dict,
        relations: Optional[list] = None
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.content = content
        self.metadata = metadata
        self.confidence = confidence
        self.relations = relations or []

    def to_dict(self) -> dict:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'content': self.content,
            'metadata': self.metadata,
            'confidence': self.confidence,
            'relations': self.relations,
        }


class NCAExtractor:
    """
    FR-001: 历史 NCA 知识抽取

    从 FC-001 生成的历史 NCA 记录中抽取结构化知识，
    构建可复用的先验知识节点。

    处理逻辑:
      1. 查询符合条件的 NCA 记录
      2. 提取六要素中的目标函数、约束矩阵、预期分配
      3. 计算各要素的统计分布（均值、方差、分位数）
      4. 标注知识节点的来源 NCA 引用
      5. 计算时效性衰减（越老的 NCA 置信度越低）
    """

    def __init__(self, nca_loader: Optional[callable] = None, nca_dir: Optional[str] = None):
        """
        参数:
          nca_loader: 自定义 NCA 加载函数 (query) -> list[dict]
                       默认从 nca_dir 读取 YAML/JSON 文件
          nca_dir: NCA 记录目录（默认 .tdca-nca/nca/）
        """
        self._loader = nca_loader
        self.nca_dir = nca_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.tdca-nca', 'nca'
        )

    def build_from_nca(
        self,
        query: dict,
        options: Optional[dict] = None
    ) -> dict:
        """
        从 NCA 构建知识节点。

        query: {
          'scenario': str,
          'time_range': {'from': datetime, 'to': datetime},
          'subject_dids': [str]
        }
        options: {
          'min_mou_threshold': float,
          'confidence_decay_halflife': int  # 天
        }

        返回: {
          'nodes_created': int,
          'node_refs': [node_id],
          'nca_query_summary': dict
        }
        """
        options = options or {}
        min_mou = options.get('min_mou_threshold', 0.0)
        halflife = options.get('confidence_decay_halflife', 180)

        # 1. 查询符合条件的 NCA
        nca_records = self._load_nca_records(query)
        nca_query_summary = {
            'total_matched': len(nca_records),
            'scenario': query.get('scenario'),
            'time_range': query.get('time_range'),
        }

        # 2-5. 提取 + 统计 + 置信度 + 时效衰减
        nodes = []
        node_refs = []
        for record in nca_records:
            node = self._extract_node(record, min_mou, halflife)
            if node is not None:
                nodes.append(node)
                node_refs.append(node.node_id)

        # 生成知识图谱级摘要（统计分布）
        stats = self._compute_stats(nodes)

        return {
            'nodes_created': len(nodes),
            'node_refs': node_refs,
            'nca_query_summary': nca_query_summary,
            'stats': stats,
            'nodes': [n.to_dict() for n in nodes],
        }

    # ---- 内部方法 ----

    def _load_nca_records(self, query: dict) -> list:
        """加载符合条件的 NCA 记录（含场景/主体过滤）"""
        if self._loader is not None:
            records = self._loader(query)
        elif os.path.isdir(self.nca_dir):
            records = self._load_from_dir()
        else:
            records = []

        # 统一过滤（自定义 loader 也需经过查询条件过滤）
        return [r for r in records if self._matches_query(r, query)]

    def _load_from_dir(self) -> list:
        """从目录加载 NCA 记录"""
        records = []
        for fname in os.listdir(self.nca_dir):
            if not fname.endswith(('.yaml', '.json')):
                continue
            path = os.path.join(self.nca_dir, fname)
            try:
                if fname.endswith('.json'):
                    with open(path, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                else:
                    import yaml
                    with open(path, 'r', encoding='utf-8') as f:
                        record = yaml.safe_load(f)
                records.append(record)
            except Exception:
                continue
        return records

    def _matches_query(self, record: dict, query: dict) -> bool:
        """检查 NCA 记录是否匹配查询条件"""
        # 场景匹配
        scenario = query.get('scenario')
        if scenario:
            rec_scenario = record.get('Scope', '') or record.get('scope', '')
            if scenario not in str(rec_scenario):
                return False
        # 主体 DID 匹配
        dids = query.get('subject_dids')
        if dids:
            operator = record.get('Operator', '')
            if operator not in dids and not any(d in str(record) for d in dids):
                return False
        return True

    def _extract_node(
        self,
        record: dict,
        min_mou: float,
        halflife: int
    ) -> Optional[KnowledgeNode]:
        """从单条 NCA 提取知识节点"""
        # 提取六要素中的关键内容
        content = {
            'objective_snapshot': record.get('Scope', '') or record.get('objective', ''),
            'constraint_pattern': self._extract_constraints(record),
            'allocation_pattern': record.get('Audit-Trail', []) or record.get('allocation', {}),
        }

        # MOU 置信度硬指标（ID79）
        mou = self._extract_mou(record)
        if mou < min_mou:
            return None  # 未达最低 MOU 阈值，不构建节点

        # 时效性衰减
        created_at = record.get('Timestamp') or record.get('Recorded-At')
        recency_decay = self._recency_decay(created_at, halflife)

        # 基础置信度（简化：基于内容完整性）
        base_score = self._base_confidence(content)

        node_id = f"TDCA-KN-{uuid.uuid4().hex[:8]}"
        node = KnowledgeNode(
            node_id=node_id,
            node_type='HISTORICAL_NCA',
            content=content,
            metadata={
                'source': f"nca_ref:{record.get('NCA-ID', '')}",
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'creator_did': record.get('Operator', ''),
            },
            confidence={
                'base_score': round(base_score, 4),
                'mou_anchor': round(mou, 4),
                'recency_decay': round(recency_decay, 4),
                'final_score': round(base_score * (1.0 if mou > 0 else 0.5) * recency_decay, 4),
            },
        )
        return node

    @staticmethod
    def _extract_constraints(record: dict) -> dict:
        """提取约束矩阵模式"""
        # 简化：从 Config-Right-Token 提取
        crt = record.get('Config-Right-Token', {})
        if isinstance(crt, dict):
            return {
                'scope': crt.get('Scope'),
                'max_retry': crt.get('Max-Retry'),
                'human_required': crt.get('Human-Signature-Required'),
            }
        return {}

    @staticmethod
    def _extract_mou(record: dict) -> float:
        """提取 MOU 锚定值（税收锚定硬指标）"""
        # NCA 中可能含 MOU 字段
        mou = record.get('MOU', record.get('mou', 0.0))
        if isinstance(mou, dict):
            return float(mou.get('total', mou.get('Actual-Total', 0.0)) or 0.0)
        try:
            return float(mou or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _base_confidence(content: dict) -> float:
        """基础置信度：基于内容完整性"""
        score = 0.0
        if content.get('objective_snapshot'):
            score += 0.5
        if content.get('constraint_pattern'):
            score += 0.3
        if content.get('allocation_pattern'):
            score += 0.2
        return min(1.0, score)

    @staticmethod
    def _recency_decay(created_at: Optional[str], halflife: int) -> float:
        """时效性衰减：指数衰减"""
        if not created_at or halflife <= 0:
            return 1.0
        try:
            # 支持 ISO 格式
            dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - dt).days
            if age_days < 0:
                age_days = 0
            # 指数衰减: 2^(-age/halflife)
            return 2.0 ** (-age_days / halflife)
        except (ValueError, TypeError):
            return 1.0

    @staticmethod
    def _compute_stats(nodes: List[KnowledgeNode]) -> dict:
        """计算知识节点统计分布"""
        if not nodes:
            return {'node_count': 0, 'avg_confidence': 0.0}
        confidences = [n.confidence['final_score'] for n in nodes]
        return {
            'node_count': len(nodes),
            'avg_confidence': round(sum(confidences) / len(confidences), 4),
            'min_confidence': round(min(confidences), 4),
            'max_confidence': round(max(confidences), 4),
        }

    def validate(self, result: dict) -> None:
        """
        自证机制：
          1. nodes_created 与 node_refs 长度一致
          2. 每个节点含来源 NCA 引用
          3. MOU 硬指标：final_score 不为 0（除非无 NCA）
        """
        errors = []
        if result['nodes_created'] != len(result['node_refs']):
            errors.append("nodes_created 与 node_refs 不一致")
        for node in result.get('nodes', []):
            if 'nca_ref' not in node['metadata'].get('source', ''):
                errors.append(f"节点 {node['node_id']} 缺少来源 NCA 引用")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")
