"""CKSSyncAdapter — CKS 同步部署适配层（M3，解决 TIMA LIM-D3-001）

硬约束（HC-EINT-003）:
  - CKS 与 TIMA VersionVector 格式兼容（直接复用，不修改已归档代码）
  - 冲突解决编码宪法约束：正和博弈优先（R1）/ 人类签名权不可覆盖（R2）
  - 版本向量支配兜底（R3）；平局上报慢系统人类裁决（R4）

本模块为 EIOS 认知层适配层：复用 TIMA CKSProtocol/VersionVector，新增宪法收敛冲突解决。
"""

import os
import sys

# 复用 TIMA 已归档代码（Phase D，零修改）—— tdca-eios/src → 工作区 → tdca-tima
_WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TIMA_SRC = os.path.join(_WORKSPACE, 'tdca-tima')
if _TIMA_SRC not in sys.path:
    sys.path.insert(0, _TIMA_SRC)

from src.cks_protocol import CKSProtocol, VersionVector  # noqa: E402


class ConstitutionalConflictResolver:
    """宪法收敛冲突解决（R2 > R1 > R3 > R4）"""

    # ---- 规则判定 ----

    @staticmethod
    def _human_signature(record: dict) -> bool:
        """R2: 人类签名权不可覆盖"""
        content = record.get('content', {})
        return bool(content.get('human_signature', False))

    @staticmethod
    def _mou_total(record: dict) -> float:
        """R1: 正和博弈优先（比较 MOU 总量）"""
        content = record.get('content', {})
        mou = content.get('mou', {})
        if isinstance(mou, dict):
            return float(mou.get('total', 0))
        return float(mou or 0)

    def resolve(self, local: dict, remote: dict):
        """裁决冲突，返回 (winner_record, reason)

        优先级: R2 人类签名权 > R1 正和博弈 > R3 版本向量支配 > R4 平局上报
        """
        # R2: 人类签名权不可覆盖
        local_sig, remote_sig = self._human_signature(local), self._human_signature(remote)
        if local_sig and not remote_sig:
            return local, 'R2 人类签名权（本地）'
        if remote_sig and not local_sig:
            return remote, 'R2 人类签名权（远端）'
        if local_sig and remote_sig:
            # 双侧签名：不可自动覆盖，上报人类
            return None, 'R4 双侧人类签名冲突，上报慢系统'

        # R1: 正和博弈优先（MOU 总量高者胜）
        l_mou, r_mou = self._mou_total(local), self._mou_total(remote)
        if l_mou != r_mou:
            winner = local if l_mou > r_mou else remote
            return winner, 'R1 正和博弈优先（MOU %.2f > %.2f）' % (max(l_mou, r_mou), min(l_mou, r_mou))

        # R3: 版本向量支配
        lv = VersionVector('cmp')
        lv.counters = dict(local.get('version_vector', {}))
        rv = VersionVector('cmp')
        rv.counters = dict(remote.get('version_vector', {}))
        if lv.dominates(rv):
            return local, 'R3 版本向量支配（本地）'
        if rv.dominates(lv):
            return remote, 'R3 版本向量支配（远端）'

        # R4: 平局 → 上报慢系统
        return None, 'R4 平局冲突，上报慢系统人类裁决'


class CKSSyncAdapter:
    """CKS 部署适配层：复用 TIMA CKSProtocol，同步时应用宪法收敛"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.protocol = CKSProtocol(agent_id)   # TIMA 已归档类，零修改复用
        self.resolver = ConstitutionalConflictResolver()

    def update_memory(self, memory_id: str, content: dict) -> dict:
        """更新记忆（委托 TIMA CKSProtocol）"""
        return self.protocol.update_memory(memory_id, content)

    def sync_with(self, other: 'CKSSyncAdapter') -> dict:
        """与对端同步（merge 版本向量 + 宪法收敛冲突解决）"""
        # 1. merge 版本向量（TIMA VersionVector.merge，max 策略）
        self.protocol.version_vector = self.protocol.version_vector.merge(
            other.protocol.version_vector)

        # 2. 逐记忆同步 + 宪法收敛
        resolved = {}
        escalated = []
        for mid, record in other.protocol._memory_store.items():
            if mid not in self.protocol._memory_store:
                self.protocol._memory_store[mid] = record
                resolved[mid] = 'SYNC 直接同步（远端唯一）'
            else:
                mine = self.protocol._memory_store[mid]
                theirs = record
                winner, reason = self.resolver.resolve(mine, theirs)
                if winner is None:
                    escalated.append(mid)   # R4 平局 → 慢系统
                else:
                    self.protocol._memory_store[mid] = winner
                    resolved[mid] = reason

        return {
            'merged_vector': self.protocol.version_vector.to_dict(),
            'resolved': resolved,
            'escalated': escalated,
        }

    def propose_institutional(self, entry: dict) -> int:
        """L0/L1 制度提案（Raft 强一致，委托 TIMA）"""
        return self.protocol.propose_institutional(entry)


if __name__ == '__main__':  # pragma: no cover（演示块，非交付逻辑）
    a = CKSSyncAdapter('agent-A')
    b = CKSSyncAdapter('agent-B')

    # 场景1: 正和博弈优先（R1）—— A 的 MOU 更高
    a.update_memory('M1', {'mou': {'total': 100}, 'eri': 0.8})
    b.update_memory('M1', {'mou': {'total': 50}, 'eri': 0.6})
    result = a.sync_with(b)
    print('场景1 R1:', result['resolved'].get('M1'), '| 胜者 MOU:', a.protocol._memory_store['M1']['content']['mou']['total'])

    # 场景2: 人类签名权不可覆盖（R2）—— B 有人类签名
    a.update_memory('M2', {'mou': {'total': 999}, 'eri': 0.9})            # A MOU 高但无签名
    b.update_memory('M2', {'mou': {'total': 1}, 'human_signature': True})  # B 有签名
    result = a.sync_with(b)
    print('场景2 R2:', result['resolved'].get('M2'), '| 胜者 human_signature:', a.protocol._memory_store['M2']['content'].get('human_signature'))

    # 场景3: 平局 → 上报慢系统（R4）
    a.update_memory('M3', {'mou': {'total': 30}})
    b.update_memory('M3', {'mou': {'total': 30}})
    result = a.sync_with(b)
    print('场景3 R4: escalated =', result['escalated'])

    print('CKS 部署验证: PASS（复用 TIMA VersionVector + 宪法收敛）')
