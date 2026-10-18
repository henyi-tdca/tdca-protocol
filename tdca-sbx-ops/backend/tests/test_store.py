# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     store 存储层测试（读写/容错/计数/id 唯一）
# 约束矩阵:     FC-SBX-OPS-001 SV-7（存证只追加）+ 测试隔离
# 先验分布:     store.py 实现
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""store 存储层测试。"""

from __future__ import annotations

import json
from pathlib import Path

from app import store
from app.models import Sandbox


class TestStore:
    def test_save_load_roundtrip(self):
        sb = Sandbox(sandbox_id=store.new_sandbox_id(), name="t", initiator_did="did:tdca:X", initiator_role="innovator")
        store.save_sandbox(sb)
        loaded = store.load_sandbox(sb.sandbox_id)
        assert loaded is not None
        assert loaded.name == "t"
        assert loaded.sandbox_id == sb.sandbox_id

    def test_load_missing_returns_none(self):
        # 合法格式但未创建 → None
        assert store.load_sandbox(f"did:tdca:sandbox:{'0' * 32}") is None

    def test_list_skips_corrupt_file(self):
        sb = Sandbox(sandbox_id=store.new_sandbox_id(), name="ok", initiator_did="did:tdca:X", initiator_role="innovator")
        store.save_sandbox(sb)
        # 写入损坏文件（覆盖同名 .json，非法 JSON 内容）
        bad = Sandbox(sandbox_id=store.new_sandbox_id(), name="bad", initiator_did="did:tdca:X", initiator_role="innovator")
        store.save_sandbox(bad)
        Path(store._DATA_DIR / f"{bad.sandbox_id.replace(':', '_')}.json").write_text("{corrupt", encoding="utf-8")  # type: ignore[attr-defined]
        items = store.list_sandboxes()
        ids = [s.sandbox_id for s in items]
        assert sb.sandbox_id in ids
        assert bad.sandbox_id not in ids  # 损坏文件跳过，不阻断全量

    def test_delete_only_test_use(self):
        sb = Sandbox(sandbox_id=store.new_sandbox_id(), name="d", initiator_did="did:tdca:X", initiator_role="innovator")
        store.save_sandbox(sb)
        assert store.delete_sandbox_file(sb.sandbox_id) is True
        assert store.delete_sandbox_file(sb.sandbox_id) is False  # 已删

    def test_count(self):
        n0 = store.count_sandboxes()
        sb = Sandbox(sandbox_id=store.new_sandbox_id(), name="c", initiator_did="did:tdca:X", initiator_role="innovator")
        store.save_sandbox(sb)
        assert store.count_sandboxes() == n0 + 1

    def test_new_sandbox_id_unique(self):
        ids = {store.new_sandbox_id() for _ in range(50)}
        assert len(ids) == 50  # did:tdca:sandbox:{uuid} 唯一
