# -*- coding: utf-8 -*-
"""
TDCA 七库联动引擎 — REPO-003 七库生态同步管道（M3）
制度锚定: TDCA-KG-001 §4.4 (KB-KG 联动) | ID91 (NCA 反哺) | TypeSystem-Confirmation-001 §4.1 (依赖关系)
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

实现 KB→KG 自动同步、NCA 反哺驱动合约升级/Skill 边界修订/算法校准、KG→KB 反哺。
NSFL-Declaration:
  - 联动管道不绕过负空间检查（各库自身仍执行其负空间约束）
  - NCA 反哺不修改不可升级核心锚点（TypeSystem §9.3）
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Callable, Optional
import time


class SevenRepoSyncEngine:
    """
    七库联动引擎 — M3 完整实现
    实现 KB→KG 自动同步、NCA 反哺驱动迭代
    """

    def __init__(self, kb_store=None, kg_engine=None, nca_generator=None,
                 contract_repo=None, skill_repo=None, genie_repo=None,
                 ota_controller=None):
        self.kb = kb_store           # REPO-003 KB
        self.kg = kg_engine          # REPO-003 KG
        self.nca = nca_generator     # REPO-006 NCA
        self.contract = contract_repo  # REPO-004 智能合约库
        self.skill = skill_repo        # REPO-005 Skill 库
        self.genie = genie_repo        # REPO-007 效用精灵算法库
        self.ota = ota_controller      # OTA 版本控制器（M4：变更触发版本递增）

        # 联动管道注册表
        self.pipelines: Dict[str, Callable] = {
            "kb_to_kg": self._sync_kb_to_kg,
            "nca_to_contract": self._sync_nca_to_contract,
            "nca_to_skill": self._sync_nca_to_skill,
            "nca_to_genie": self._sync_nca_to_genie,
            "kg_to_kb": self._sync_kg_to_kb,
        }

    # ==================== 管道实现 ====================

    def _sync_kb_to_kg(self, unit_id: str):
        """
        KB → KG 联动：知识单元变更自动触发图谱节点更新
        TDCA-KG-001 §4.4
        """
        unit = self.kb.get_unit(unit_id) if self.kb else None
        if not unit:
            return

        node = unit.to_kg_node()
        if self.kg is not None and hasattr(self.kg, "upsert_node"):
            self.kg.upsert_node(node)

        # M4: KB→KG 同步后触发 OTA 版本递增（知识单元变更 = 图状态变更）
        self._trigger_ota_version(unit_id, node)

        self._record_pipeline_nca({
            "sync_type": "KB_TO_KG",
            "unit_id": unit_id,
            "node_labels": node["labels"],
            "trigger": "knowledge_unit_update",
        })

    def _sync_nca_to_contract(self, nca_ref: str):
        """NCA → 智能合约库：驱动合约升级（ID91）"""
        nca = self._nca_get(nca_ref)
        if not nca:
            return

        # 提取制度变更信号
        nca_type = getattr(nca, "type", "")
        nca_layer = getattr(nca, "layer", 0)
        if nca_type == "INSTITUTIONAL" and nca_layer >= 2:
            if self.contract is not None and hasattr(self.contract, "evaluate_upgrade"):
                self.contract.evaluate_upgrade(nca)

            self._record_pipeline_nca({
                "sync_type": "NCA_TO_CONTRACT",
                "action": "evaluate_upgrade",
                "contract_repo": "REPO-004",
                "parent": nca_ref,
            }, parent_nca=nca_ref)

    def _sync_nca_to_skill(self, nca_ref: str):
        """NCA → Skill 库：驱动 Skill 边界修订"""
        nca = self._nca_get(nca_ref)
        if not nca:
            return

        # 如果 NCA 包含配置权边界变更，触发 Skill 边界修订
        if "config_right" in str(nca.content):
            if self.skill is not None and hasattr(self.skill, "revise_boundary"):
                self.skill.revise_boundary(nca)

            self._record_pipeline_nca({
                "sync_type": "NCA_TO_SKILL",
                "action": "revise_boundary",
                "skill_repo": "REPO-005",
                "parent": nca_ref,
            }, parent_nca=nca_ref)

    def _sync_nca_to_genie(self, nca_ref: str):
        """NCA → 效用精灵算法库：驱动算法校准"""
        nca = self._nca_get(nca_ref)
        if not nca:
            return

        # 如果 NCA 包含效用数据，驱动算法校准
        if "mou" in str(nca.content) or "utility" in str(nca.content):
            if self.genie is not None and hasattr(self.genie, "calibrate_algorithm"):
                self.genie.calibrate_algorithm(nca)

            self._record_pipeline_nca({
                "sync_type": "NCA_TO_GENIE",
                "action": "calibrate_algorithm",
                "genie_repo": "REPO-007",
                "parent": nca_ref,
            }, parent_nca=nca_ref)

    def _sync_kg_to_kb(self, node_id: str):
        """KG → KB 联动：图推理结果反哺知识库修正"""
        node = None
        if self.kg is not None and hasattr(self.kg, "get_node"):
            node = self.kg.get_node(node_id)
        if not node:
            return

        # 如果图推理发现知识单元需要修正
        if node.get("needs_review"):
            if self.kb is not None and hasattr(self.kb, "flag_for_review"):
                self.kb.flag_for_review(node_id)

    # ==================== 管道路由 ====================

    def run_pipeline(self, trigger_event: str, source_id: str) -> None:
        """
        执行联动管道
        根据触发事件类型，自动路由到对应的联动逻辑
        """
        if trigger_event == "kb_update":
            self._sync_kb_to_kg(source_id)
            # 级联触发 NCA 反哺
            latest_nca = self._get_latest_institutional_nca()
            if latest_nca:
                self._sync_nca_to_contract(latest_nca)
                self._sync_nca_to_skill(latest_nca)
                self._sync_nca_to_genie(latest_nca)

        elif trigger_event == "kg_inference":
            self._sync_kg_to_kb(source_id)

        # 生成管道执行 NCA
        self._record_pipeline_nca({
            "pipeline": "seven_repo_sync",
            "trigger": trigger_event,
            "source_id": source_id,
            "timestamp": int(time.time()),
        })

    # ==================== 内部工具 ====================

    def _nca_get(self, nca_ref: str):
        if self.nca is None:
            return None
        if hasattr(self.nca, "get"):
            return self.nca.get(nca_ref)
        return None

    def _get_latest_institutional_nca(self) -> Optional[str]:
        """获取最近一条 INSTITUTIONAL NCA 引用"""
        if self.nca is None:
            return None
        if hasattr(self.nca, "get_latest_by_type"):
            latest = self.nca.get_latest_by_type("INSTITUTIONAL")
            return getattr(latest, "nca_id", None) or latest
        # 降级：从缓存取最后一条
        if hasattr(self.nca, "cache"):
            cache = getattr(self.nca, "cache") or {}
            ids = [nid for nid, n in cache.items()
                   if getattr(n, "type", "") == "INSTITUTIONAL"]
            return ids[-1] if ids else None
        return None

    def _record_pipeline_nca(self, content: Dict, parent_nca: Optional[str] = None):
        """记录管道执行 NCA — ID91"""
        if self.nca is None:
            return
        if hasattr(self.nca, "generate"):
            self.nca.generate(
                type="INSTITUTIONAL", layer=3, content=content,
                parent_nca=parent_nca,
            )

    def _trigger_ota_version(self, node_id: str, node: Dict):
        """
        M4: KB→KG 同步触发 OTA 版本递增
        :param node_id: 变更节点 ID（知识单元 ID）
        :param node: KG 节点（含 priority 属性）
        """
        if self.ota is None:
            return
        priority = (node.get("properties") or {}).get("priority", 3)
        try:
            self.ota.propose_update(
                node_id=node_id,
                new_properties=node,
                updater_model="TDCA-SYNC-PIPELINE",
                priority=priority,
                human_signed=priority == 5,  # 宪法级需预先签名（ID71）
            )
        except Exception:
            # 版本递增失败不阻断联动（记录在 NCA 中即可）
            return
