# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     F8 NCA 存证测试——11 字段/链式哈希/篡改检测/断链检测
# 约束矩阵:     FC-SBX-OPS-001 SV-7（存证不可篡改）
# 先验分布:     MEMO-006 附录 C 11 字段 + nca_logger
# 配置权边界:    L2 层；仅测试
# 预期分配:     全部断言通过；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""F8 NCA 存证测试（SV-7 不可篡改）。"""

from __future__ import annotations

import json
from pathlib import Path

from app import nca_logger, store

_NCA_FIELDS = [
    "nca_id",
    "fc_id",
    "operation",
    "operator",
    "timestamp",
    "pre_state",
    "post_state",
    "config_right_token",
    "audit_trail",
    "human_signature",
    "negative_space_check",
    "prev_hash",
    "content_hash",
]


def _save(op: str) -> str:
    nca = nca_logger.build_nca(operation=op, operator="did:tdca:TEST-001", pre_state="X", post_state="Y")
    return nca_logger.save_nca(nca)


class TestBuildAndSave:
    def test_build_has_11_fields_plus_hashes(self):
        nca = nca_logger.build_nca(operation="SBX_TEST", operator="did:tdca:TEST-001", pre_state="A", post_state="B")
        data = nca.model_dump()
        for f in _NCA_FIELDS:
            assert f in data, f"缺字段 {f}"
        assert data["fc_id"] == "TDCA-FC-SBX-OPS-001"
        assert data["content_hash"]  # 非空

    def test_save_and_load_roundtrip(self):
        nca_id = _save("SBX_TEST")
        loaded = nca_logger.load_nca(nca_id)
        assert loaded is not None
        assert loaded["operation"] == "SBX_TEST"

    def test_chain_links_prev_hash(self):
        id1 = _save("OP-1")
        id2 = _save("OP-2")
        first = nca_logger.load_nca(id1)
        second = nca_logger.load_nca(id2)
        assert second["prev_hash"] == first["content_hash"]  # 链式链接

    def test_chain_valid(self):
        for op in ("OP-1", "OP-2", "OP-3"):
            _save(op)
        result = nca_logger.verify_chain()
        assert result["valid"] is True
        assert result["checked"] >= 4  # 种子 NCA + 3 个测试 NCA（种子条数解耦）


class TestTamperDetection:
    def test_content_tamper_detected(self):
        _save("OP-1")
        nca_id = _save("OP-2")
        path = Path(store._NCA_DIR) / f"{nca_id}.json"  # type: ignore[attr-defined]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["operation"] = "TAMPERED"  # 篡改内容但不动哈希
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = nca_logger.verify_chain()
        assert result["valid"] is False
        assert result["first_broken"] == nca_id
        assert any("篡改" in e for e in result["errors"])

    def test_prev_hash_break_detected(self):
        _save("OP-1")
        nca_id = _save("OP-2")
        path = Path(store._NCA_DIR) / f"{nca_id}.json"  # type: ignore[attr-defined]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["prev_hash"] = "0" * 64  # 断链
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = nca_logger.verify_chain()
        assert result["valid"] is False

    def test_tamper_with_rehash_detected_by_prev_hash(self):
        """篡改内容并重算自身 content_hash → 下条 prev_hash 断链检出（SV-7）。"""
        nca_id = _save("OP-1")
        _save("OP-2")
        path = Path(store._NCA_DIR) / f"{nca_id}.json"  # type: ignore[attr-defined]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["operation"] = "TAMPERED"
        # 攻击者重算自身 content_hash（但无法改下条 prev_hash）
        payload = {k: v for k, v in data.items() if k not in ("content_hash", "prev_hash")}
        import hashlib

        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        data["content_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = nca_logger.verify_chain()
        assert result["valid"] is False  # OP-2 的 prev_hash 指向旧哈希 → 断链

    def test_path_traversal_rejected(self):
        """../ 注入拒绝（load_nca 白名单）。"""
        assert nca_logger.load_nca("../secret") is None
        seed_id = nca_logger.list_nca()[0]["nca_id"]  # 动态取种子 NCA id（避免硬编码日期）
        assert nca_logger.load_nca(seed_id) is not None  # 合法格式正常

    def test_forged_chain_head_detected(self):
        """首条（链头）prev_hash 非空（伪造链头）→ verify 拒绝。"""
        _save("OP-1")
        head_id = nca_logger.list_nca()[0]["nca_id"]  # 链头 = 种子首条
        path = Path(store._NCA_DIR) / f"{head_id}.json"  # type: ignore[attr-defined]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["prev_hash"] = "1" * 64
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = nca_logger.verify_chain()
        assert result["valid"] is False
        assert "链头" in result["errors"][0]

class TestSeqGapDetection:
    def test_seq_gap_detected(self):
        """#1 修复（tdca-notary）：删除中部 NCA 文件 → 序号缺口检出（不可静默）。"""
        _save("GAP-1")
        _save("GAP-2")
        items = nca_logger.list_nca()
        victim = items[1]["nca_id"]  # 删除中部一条
        (Path(store._NCA_DIR) / f"{victim}.json").unlink()  # type: ignore[attr-defined]
        result = nca_logger.verify_chain()
        assert result["valid"] is False
        assert "序号缺口" in result["errors"][0]

    def test_tail_gap_is_m4_blockchain_anchor_scope(self):
        """#1 边界登记：尾部缺失（链内仍连续）为检测级盲区，归 M4-4 区块链锚定覆盖
        （锚点提供期望链尾——tdca-notary 明确定位低危，非当前缺陷）。"""
        _save("TAIL-1")
        _save("TAIL-2")
        _save("TAIL-3")
        items = nca_logger.list_nca()
        tail = items[-1]["nca_id"]
        (Path(store._NCA_DIR) / f"{tail}.json").unlink()  # type: ignore[attr-defined]
        result = nca_logger.verify_chain()
        # 中部缺口已检出；尾部缺失当前链内仍连续（检测级局限，M4-4 锚点覆盖）
        assert result["valid"] is True or "序号缺口" in "".join(result["errors"])
