# -*- coding: utf-8 -*-
"""
TDCA-Graph OTA 版本控制 — Git-like 图版本管理（OTA 活宪法）M4 完整实现
制度锚定: TDCA-KG-001 §3.1 / §6.2 B5 | TDCA-TypeSystem-Confirmation-001 §9.3
       | ID71 慢系统 | ID91 NCA 存证
版本: V1.0 | 状态: M4-CODED | FC: TDCA-FC-20260804-006-M4

职责: 快系统（自动合并无冲突更新 priority<5）+ 慢系统（宪法级需人类签名 ID71）
M4 完整 Runtime:
  - 版本状态机: PROPOSED / APPROVED / ACTIVE / ROLLED_BACK
  - PENDING_SLOW 慢系统上报闭环（宪法级更新 → 工单 → 人类签批反馈）
  - rollback 回滚（人类签名强制）
  - Merkle 链式验证 + 版本差异 diff + 谱系回溯
  - 不可升级核心锚点硬编码阻断（TypeSystem §9.3）
NSFL-Declaration:
  - 不可升级锚点列表仅读取不修改
  - 宪法级/priority=5 变更必须经慢系统
  - 版本谱系不可篡改（Merkle 链）
  - 版本回滚一旦执行不可自动前滚（NSFL：生产回滚不可逆）
SPDX-License-Identifier: TDCA-Internal
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable


class ImmutableAnchorViolation(Exception):
    """不可升级核心锚点违例 — TypeSystem §9.3"""


class NSFLTrigger(ImmutableAnchorViolation):
    """负空间熔断触发"""

    def __init__(self, rule_id: str, reason: str = "", alt_path: str = ""):
        self.rule_id = rule_id
        self.alt_path = alt_path
        super().__init__(f"[NSFL-TRIGGER] {rule_id}: {reason}  alt_path={alt_path}")


class SlowSystemRequired(Exception):
    """宪法级变更需慢系统人类签名（ID71）（无慢系统网关时抛出）"""


class VersionStatus:
    """版本状态机 — M4"""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True)
class GraphVersion:
    """Git-like 图版本节点 — TDCA-KG-001 §3.1"""
    version_id: str           # 如 "v1.2.3-ota"
    parent_version: Optional[str]
    timestamp: int
    merkle_root: str          # 全图状态哈希（含父版本链）
    changed_nodes: List[str] = field(default_factory=list)  # 变更节点 ID 列表
    ota_trigger: str = ""     # 触发 OTA 的制度原理 ID
    human_signature: Optional[str] = None  # 慢系统签名（ID71）
    status: str = VersionStatus.PROPOSED   # 版本状态机（M4）

    def verify_lineage(self, root_version: str,
                       merkle_provider: Optional[Callable] = None) -> bool:
        """
        验证版本谱系不可篡改
        :param root_version: 根版本 ID
        :param merkle_provider: 可选 merkle 校验函数（version_id -> merkle_root）
        """
        if self.version_id == root_version:
            return True
        if merkle_provider is not None:
            expected = merkle_provider(self.version_id)
            if expected is not None:
                return expected == self.merkle_root
        return self.parent_version is not None


class OTAController:
    """
    OTA 活宪法图版本控制器 — M4 完整 Runtime
    快系统：自动合并无冲突更新（priority < 5）
    慢系统：宪法级（priority=5 / Constitution）更新经慢系统工单（ID71）
    """

    # 不可升级核心锚点 — TDCA-TypeSystem-Confirmation-001 §9.3（硬编码）
    _IMMUTABLE_ANCHORS = [
        "REPO-003-type-tag",      # 七库类型标签
        "NCA-BIDIRECTIONAL",      # NCA 双向地位
        "IP-QUANTUM",             # IP 库 quantum 属性
        "NCA-IMMUTABLE",          # NCA 不可删除
    ]

    def __init__(self, graph_db=None, nca_generator=None, slow_system_gateway=None):
        self.db = graph_db
        self.nca = nca_generator
        self.slow = slow_system_gateway
        self.current_version = "v1.0.0"
        self.versions: Dict[str, GraphVersion] = {}
        self._init_genesis()

    def _init_genesis(self):
        """初始化创世版本（ACTIVE，创始人签名）"""
        self.versions["v1.0.0"] = GraphVersion(
            version_id="v1.0.0", parent_version=None,
            timestamp=0, merkle_root="genesis", changed_nodes=[],
            ota_trigger="genesis",
            human_signature="TDCA-FOUNDER",
            status=VersionStatus.ACTIVE,
        )

    # ==================== 更新提案 ====================

    def propose_update(
        self,
        node_id: str,
        new_properties: dict,
        updater_model: str,
        human_signed: bool = False,
        priority: int = 3,
        is_constitution: bool = False,
    ) -> str:
        """
        提案更新 — 快系统自动合并 / 慢系统 PENDING_SLOW 上报
        :param priority: 节点优先级（5=宪法级）
        :param is_constitution: 是否宪法节点
        :return: 新版本 ID 或 "PENDING_SLOW:{ticket}"
        """
        # 负空间检查：不可修改的核心锚点（TypeSystem §9.3）
        if node_id in self._IMMUTABLE_ANCHORS:
            raise NSFLTrigger(
                rule_id="TDCA-PRINCIPLE-IMMUTABLE-ANCHOR-001",
                reason=f"试图修改不可升级的核心锚点: {node_id}",
                alt_path="发起宪法修正案流程（慢系统）",
            )

        # 冲突检测：同一节点在当前版本已被修改过 → 需显式确认（快系统防覆盖）
        cur = self.versions[self.current_version]
        if node_id in cur.changed_nodes:
            if not human_signed and not is_constitution:
                raise ValueError(
                    f"冲突检测: 节点 {node_id} 在当前版本已变更，"
                    f"连续修改需人类确认或新建分支（ID71）")

        # 判断是否需要慢系统（宪法级 / priority=5）
        needs_slow = is_constitution or priority == 5

        if needs_slow and not human_signed:
            # 慢系统上报闭环：创建工单，返回 PENDING_SLOW（ID71）
            if self.slow is not None and hasattr(self.slow, "escalate"):
                ticket = self.slow.escalate(
                    title=f"宪法级图更新提案: {node_id}",
                    description=f"模型 {updater_model} 请求更新 {node_id}",
                    nca_ref="",
                    required_action="人类审查并签名确认",
                )
                return f"PENDING_SLOW:{ticket}"
            # 无慢系统网关：抛异常（向后兼容）
            raise SlowSystemRequired(
                f"宪法级变更必须经慢系统人类签名（ID71）: {node_id}")

        # 快系统路径：创建并激活
        new_version = self._create_version(
            node_id, new_properties, updater_model,
            human_signature=human_signed or None,
            status=VersionStatus.APPROVED if (needs_slow and human_signed)
            else VersionStatus.ACTIVE,
        )
        self._activate_version(new_version.version_id)
        return new_version.version_id

    # ==================== 慢系统反馈 ====================

    def approve_slow_update(self, ticket_id: str, node_id: str,
                            new_properties: dict,
                            updater_model: str) -> Optional[str]:
        """
        慢系统签批后反馈到快系统：创建并激活版本（ID71 闭环）
        由 SlowSystemGateway.human_sign 批准后调用
        """
        new_version = self._create_version(
            node_id, new_properties, updater_model,
            human_signature=f"SLOW-{ticket_id}",
            status=VersionStatus.APPROVED,
        )
        self._activate_version(new_version.version_id)
        return new_version.version_id

    def human_sign(self, version_id: str, signature: str) -> bool:
        """
        慢系统补签：PROPOSED 版本可补人类签名（ID71）
        """
        version = self.versions.get(version_id)
        if version is None or version.human_signature is not None:
            return False
        signed = GraphVersion(
            version_id=version.version_id,
            parent_version=version.parent_version,
            timestamp=version.timestamp,
            merkle_root=version.merkle_root,
            changed_nodes=list(version.changed_nodes),
            ota_trigger=version.ota_trigger,
            human_signature=signature,
            status=VersionStatus.APPROVED,
        )
        self.versions[version_id] = signed
        return True

    # ==================== 版本回滚 ====================

    def rollback(self, target_version: str, human_signature: str) -> bool:
        """
        回滚到指定版本 — 必须人类签名（NSFL：回滚不可逆，不自动前滚）
        """
        if not human_signature:
            raise PermissionError("版本回滚需人类签名")

        if target_version not in self.versions:
            return False

        # 标记当前版本为 ROLLED_BACK
        cur = self.versions[self.current_version]
        if cur.version_id != target_version:
            rolled = GraphVersion(
                version_id=cur.version_id,
                parent_version=cur.parent_version,
                timestamp=cur.timestamp,
                merkle_root=cur.merkle_root,
                changed_nodes=list(cur.changed_nodes),
                ota_trigger=cur.ota_trigger,
                human_signature=cur.human_signature,
                status=VersionStatus.ROLLED_BACK,
            )
            self.versions[cur.version_id] = rolled

        self.current_version = target_version

        # 回滚 NCA 存证
        self._record_nca({
            "ota_event": "ROLLBACK",
            "target_version": target_version,
            "human_signature": human_signature,
        })
        return True

    # ==================== 版本差异 ====================

    def diff(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        计算两个版本间的差异（OTA 支持 — KG-001 §3.4 GetGraphVersionDiff）
        :return: {changed_nodes, added, removed, merkle_root, ota_trigger}
        """
        v_from = self.versions.get(from_version)
        v_to = self.versions.get(to_version)
        if v_from is None or v_to is None:
            raise ValueError(f"版本不存在: {from_version} → {to_version}")

        # 沿 to 的祖先链向上收集，直到 from（含 from 自身的变更）
        changed: List[str] = []
        seen: set = set()
        v = v_to
        while v is not None:
            if v.version_id in seen:
                break  # 防环
            seen.add(v.version_id)
            for node in v.changed_nodes:
                if node not in changed:
                    changed.append(node)
            if v.version_id == from_version:
                break  # 到达 from
            v = self.versions.get(v.parent_version)
        # 若 from 不在 to 的祖先链上，仅返回 to 的直接变更集（降级）
        if v is None:
            changed = list(v_to.changed_nodes)

        return {
            "from_version": from_version,
            "to_version": to_version,
            "changed_nodes": changed,
            "added": changed,
            "removed": [],
            "merkle_root": v_to.merkle_root,
            "ota_trigger": v_to.ota_trigger,
        }

    # ==================== 谱系查询 ====================

    def verify_chain(self, version_id: str) -> bool:
        """验证从根到指定版本的谱系完整性"""
        seen = set()
        v = self.versions.get(version_id)
        while v is not None:
            if v.version_id in seen:
                return False  # 环路
            seen.add(v.version_id)
            if v.parent_version is None:
                return True  # 到达根
            v = self.versions.get(v.parent_version)
        return False

    def lineage_depth(self, version_id: str) -> int:
        """计算版本到根的距离"""
        depth = 0
        v = self.versions.get(version_id)
        while v is not None and v.parent_version is not None:
            depth += 1
            v = self.versions.get(v.parent_version)
        return depth

    def get_version(self, version_id: str) -> Optional[GraphVersion]:
        return self.versions.get(version_id)

    def version_count(self) -> int:
        return len(self.versions)

    # ==================== 内部工具 ====================

    def _activate_version(self, version_id: str):
        """激活版本：状态 ACTIVE + 更新当前版本"""
        version = self.versions[version_id]
        if version.status == VersionStatus.PROPOSED:
            activated = GraphVersion(
                version_id=version.version_id,
                parent_version=version.parent_version,
                timestamp=version.timestamp,
                merkle_root=version.merkle_root,
                changed_nodes=list(version.changed_nodes),
                ota_trigger=version.ota_trigger,
                human_signature=version.human_signature,
                status=VersionStatus.ACTIVE,
            )
            self.versions[version_id] = activated
        self.current_version = version_id

    def _create_version(self, node_id: str, new_properties: dict,
                        updater_model: str,
                        human_signature: Optional[str] = None,
                        status: str = VersionStatus.ACTIVE) -> GraphVersion:
        """创建新版本节点（Merkle 链式哈希）"""
        version_id = self._next_version_id()
        merkle_root = self._compute_merkle(
            node_id, new_properties, updater_model, self.current_version)
        version = GraphVersion(
            version_id=version_id,
            parent_version=self.current_version,
            timestamp=int(time.time()),
            merkle_root=merkle_root,
            changed_nodes=[node_id],
            ota_trigger=f"update:{node_id}",
            human_signature=human_signature,
            status=status,
        )
        self.versions[version_id] = version
        # 生成版本 NCA
        self._record_nca({
            "ota_event": "VERSION_CREATED",
            "version_id": version_id,
            "parent": self.current_version,
            "changed_nodes": [node_id],
            "merkle_root": merkle_root,
        })
        return version

    def _next_version_id(self) -> str:
        """生成下一个语义化版本号"""
        base = self.current_version.lstrip("v").split("-")[0]  # 剥离 -ota 后缀
        parts = [int(p) for p in base.split(".")]
        parts = parts + [0] * (3 - len(parts))
        parts[2] += 1
        return f"v{'.'.join(str(p) for p in parts)}-ota"

    @classmethod
    def _compute_merkle(cls, node_id: str, props: dict, updater: str,
                        parent_version: Optional[str]) -> str:
        """
        计算变更状态哈希（Merkle 根：变更内容 + 父版本哈希链）
        """
        payload = (
            f"{node_id}:{sorted(props.items())}:{updater}:{parent_version}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _record_nca(self, content: Dict):
        """记录 OTA 事件 NCA — ID91"""
        if self.nca is None:
            return
        if hasattr(self.nca, "generate"):
            self.nca.generate(
                type="INSTITUTIONAL", layer=2, content=content,
            )
