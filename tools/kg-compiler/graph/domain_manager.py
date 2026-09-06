"""
TDCA-FC-20260803-005 FR-003 修正声明: 无（首版）
制度锚定: FC-005-SPEC FR-003, ID91(自反化合原理)
Granted-By: FC-005-SPEC

NSFL-Declaration:
  - 知识条目发布需审批流
  - 版本控制支持回滚
  - 知识条目创建必须生成 NCA 存证
  - 敏感领域知识需额外审批标记
SPDX-License-Identifier: Apache-2.0
"""

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional


class DomainKnowledgeManager:
    """
    FR-003: 领域知识库管理

    支持人工录入和维护领域知识，形成可版本控制的领域知识库。

    功能点:
      1. 知识条目 CRUD
      2. 版本控制（支持回滚）
      3. 审批流（知识发布需审核）
      4. 分类标签体系
      5. 关联 NCA 引用
    """

    STATUS_DRAFT = 'DRAFT'
    STATUS_PENDING = 'PENDING_APPROVAL'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    def __init__(self, storage_dir: Optional[str] = None, nca_generator: Optional[callable] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.tdca-nca', 'domain_knowledge'
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        # LIM-001: 注入 NCA 生成器（FC-001），确保知识条目创建强制生成 NCA 存证
        self._nca_generator = nca_generator

    # ---- CRUD ----

    def create_entry(
        self,
        title: str,
        content: dict,
        category: str,
        tags: List[str] = None,
        creator_did: str = 'SYSTEM',
        nca_ref: Optional[str] = None,
        sensitive: bool = False
    ) -> dict:
        """创建知识条目（草稿状态）

        LIM-001: nca_ref 为 None 时强制调用 nca_generator.generate() 生成 NCA 存证。
        """
        entry_id = f"TDCA-DK-{uuid.uuid4().hex[:8]}"

        # LIM-001: 强制生成 NCA 存证（NSFL-Declaration 第三条）
        if nca_ref is None:
            if self._nca_generator is None:
                raise ValueError(
                    "[NSFL-TRIGGER] 知识条目创建必须生成 NCA 存证，"
                    "但未注入 nca_generator（FC-001）。请通过构造参数注入。"
                )
            nca = self._nca_generator()
            nca_ref = nca.get('NCA-ID') if isinstance(nca, dict) else str(nca)

        entry = {
            'entry_id': entry_id,
            'title': title,
            'content': content,
            'category': category,
            'tags': tags or [],
            'status': self.STATUS_DRAFT,
            'version': 1,
            'versions': [self._version_snapshot(title, content, category, tags, creator_did)],
            'creator_did': creator_did,
            'nca_ref': nca_ref,
            'sensitive': sensitive,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        self._save_entry(entry)
        return entry

    def get_entry(self, entry_id: str) -> Optional[dict]:
        """读取知识条目"""
        path = self._entry_path(entry_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def update_entry(self, entry_id: str, content: dict = None, title: str = None,
                     tags: List[str] = None) -> dict:
        """更新知识条目（自动版本递增 + 重置为草稿）"""
        entry = self.get_entry(entry_id)
        if entry is None:
            raise KeyError(f"[NSFL-TRIGGER] 知识条目不存在: {entry_id}")

        if title:
            entry['title'] = title
        if content is not None:
            entry['content'] = content
        if tags is not None:
            entry['tags'] = tags

        entry['version'] += 1
        entry['status'] = self.STATUS_DRAFT  # 修改后需重新审批
        entry['versions'].append(self._version_snapshot(
            entry['title'], entry['content'], entry['category'], entry['tags'], entry['creator_did']
        ))
        entry['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_entry(entry)
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """删除知识条目"""
        path = self._entry_path(entry_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    # ---- 版本控制 ----

    def rollback(self, entry_id: str, target_version: int) -> dict:
        """回滚到指定版本"""
        entry = self.get_entry(entry_id)
        if entry is None:
            raise KeyError(f"[NSFL-TRIGGER] 知识条目不存在: {entry_id}")
        if target_version < 1 or target_version > entry['version']:
            raise ValueError(f"[NSFL-TRIGGER] 无效版本: {target_version}")

        target = entry['versions'][target_version - 1]
        entry['title'] = target['title']
        entry['content'] = target['content']
        entry['category'] = target['category']
        entry['tags'] = target['tags']
        entry['version'] += 1
        entry['status'] = self.STATUS_DRAFT
        entry['versions'].append(target)
        entry['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_entry(entry)
        return entry

    def get_version_history(self, entry_id: str) -> List[dict]:
        """获取版本历史"""
        entry = self.get_entry(entry_id)
        if entry is None:
            return []
        return entry.get('versions', [])

    # ---- 审批流 ----

    def submit_for_approval(self, entry_id: str) -> dict:
        """提交审批"""
        entry = self.get_entry(entry_id)
        if entry is None:
            raise KeyError(f"[NSFL-TRIGGER] 知识条目不存在: {entry_id}")
        if entry['status'] != self.STATUS_DRAFT:
            raise ValueError(f"[NSFL-TRIGGER] 仅草稿可提交审批，当前: {entry['status']}")
        entry['status'] = self.STATUS_PENDING
        entry['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_entry(entry)
        return entry

    def approve(self, entry_id: str, approver_did: str) -> dict:
        """审批通过"""
        entry = self.get_entry(entry_id)
        if entry is None:
            raise KeyError(f"[NSFL-TRIGGER] 知识条目不存在: {entry_id}")
        if entry['status'] != self.STATUS_PENDING:
            raise ValueError(f"[NSFL-TRIGGER] 仅待审批可审批，当前: {entry['status']}")
        entry['status'] = self.STATUS_APPROVED
        entry['approved_by'] = approver_did
        entry['approved_at'] = datetime.now(timezone.utc).isoformat()
        entry['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_entry(entry)
        return entry

    def reject(self, entry_id: str, approver_did: str, reason: str) -> dict:
        """审批拒绝"""
        entry = self.get_entry(entry_id)
        if entry is None:
            raise KeyError(f"[NSFL-TRIGGER] 知识条目不存在: {entry_id}")
        entry['status'] = self.STATUS_REJECTED
        entry['rejected_by'] = approver_did
        entry['reject_reason'] = reason
        entry['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_entry(entry)
        return entry

    # ---- 查询 ----

    def list_entries(self, category: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
        """列出知识条目"""
        results = []
        for fname in os.listdir(self.storage_dir):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(self.storage_dir, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                if category and entry.get('category') != category:
                    continue
                if status and entry.get('status') != status:
                    continue
                results.append(entry)
            except Exception:
                continue
        return results

    # ---- 内部方法 ----

    def _version_snapshot(self, title, content, category, tags, creator_did) -> dict:
        return {
            'version': 0,  # 由调用方设置
            'title': title,
            'content': content,
            'category': category,
            'tags': tags or [],
            'created_by': creator_did,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def _entry_path(self, entry_id: str) -> str:
        return os.path.join(self.storage_dir, f"{entry_id}.json")

    def _save_entry(self, entry: dict):
        with open(self._entry_path(entry['entry_id']), 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

    def validate(self, entry: dict) -> None:
        """
        自证机制：
          1. 必填字段（entry_id/title/content/status/version）
          2. 敏感条目需审批标记
          3. 版本与版本历史一致
        """
        errors = []
        for field in ['entry_id', 'title', 'content', 'status', 'version']:
            if field not in entry:
                errors.append(f"缺失字段: {field}")
        if entry.get('sensitive') and entry.get('status') not in (self.STATUS_PENDING, self.STATUS_APPROVED):
            errors.append("敏感知识条目需审批流程")
        if entry.get('version', 0) != len(entry.get('versions', [])):
            errors.append("版本号与版本历史不一致")
        if errors:
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {'; '.join(errors)}")
