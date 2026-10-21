# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M3-7 扩展测试）
# 目标函数:     NCA-SANDBOX-FEED-001 四维取数接口测试——契约形状／断连 null／幂等／纯读证据／带数样例
# 约束矩阵:     交办令 §2 十字段契约 + §三停手五条（纯读）+ 测试隔离（conftest autouse）
# 先验分布:     tests/test_api.py（TestClient 模式）+ test_m3_dsa/cbdc（写流造数）
# 配置权边界:    L2 层；仅测试环境
# 预期分配:     确定性回归；失败=断言异常
# 审计轨迹:      测试动作，不入 NCA 链（造数走引擎自身 API，其 NCA 属引擎正常运作）
# =============================================================================

"""沙盒四维取数接口测试（NCA-SANDBOX-FEED-001）。

制度锚定: FC-SBX-OPS-001 M3-7 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

from fastapi.testclient import TestClient

import app.store as store

from app.main import app

client = TestClient(app)

_SIX = {
    "目标函数": "FEED 测试沙盒",
    "约束矩阵": "FC-SBX-OPS-001 SV-1~7",
    "先验分布": "任务书 FROZEN",
    "配置权边界": "L2 层",
    "预期分配": "测试",
    "审计轨迹": "TDCA-NCA-{YYYYMMDD}-{SEQ}",
}

_METRIC_IDS = ["FUSE_EVENTS", "POSITIVE_SUM", "MOU_ANCHOR", "COMPOUND_CHAIN"]
_FIELDS = {
    "metric_id", "value", "unit", "basis", "sample",
    "as_of", "space", "source_module", "status", "note",
}


def _feed() -> Dict:
    r = client.get("/api/v1/sandbox-feed")
    assert r.status_code == 200
    return r.json()


def _create_sandbox(name: str = "FEED") -> str:
    r = client.post(
        "/api/v1/sandboxes",
        json={
            "name": name,
            "initiator_did": "did:tdca:INNOVATOR-001",
            "initiator_role": "innovator",
            "six_elements": _SIX,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["sandbox_id"]


def _snapshot() -> Dict[str, str]:
    """数据/NCA 目录全量指纹（纯读证据用）。"""
    def _hash_dir(d: Path) -> Dict[str, str]:
        out: Dict[str, str] = {}
        if d.exists():
            for p in sorted(d.glob("*.json")):
                out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        return out

    return {
        "data": _hash_dir(Path(store._DATA_DIR)),  # type: ignore[attr-defined]
        "nca": _hash_dir(Path(store._NCA_DIR)),    # type: ignore[attr-defined]
    }


class TestFeedContract:
    """契约形状（十字段·批量包·接口熵=0）。"""

    def test_batch_shape_exact_fields(self):
        body = _feed()
        assert set(body.keys()) == {"generated_at", "pool_ref", "dimensions"}
        assert len(body["dimensions"]) == 4
        assert [d["metric_id"] for d in body["dimensions"]] == _METRIC_IDS
        for d in body["dimensions"]:
            assert set(d.keys()) == _FIELDS, f"{d['metric_id']} 字段集不符"
            assert d["unit"] in ("count", "pct", "ratio")
            assert d["space"] in ("NS", "SBX", "PCM")
            assert d["status"] in ("OK", "OUT-OF-LEDGER-NOT-CONNECTED", "PARTIAL")
            assert d["basis"].strip() and d["note"].strip(), "basis/note ⛔ 留白"
            assert d["source_module"], "source_module ⛔ 空"
            # as_of 带时区（+HH:MM 或 Z），无时区即不合规
            assert ("+" in d["as_of"]) or d["as_of"].endswith("Z"), d["as_of"]
        # pool_ref 为 64 位十六进制内容哈希
        assert len(body["pool_ref"]) == 64
        int(body["pool_ref"], 16)

    def test_disconnected_returns_null_not_zero(self):
        """断连/缺数场景：种子沙盒无四类业务记录。

        - 沙盒日志三源（正和/MOU/化合）无记录 → value=null + OUT-OF-LEDGER-NOT-CONNECTED；
        - FUSE 源（NCA 账本）可读且在册（种子建盒存证）→ 事件数真实 0，回 0 属实数非缺数。
        """
        body = _feed()
        dims = {d["metric_id"]: d for d in body["dimensions"]}
        for mid in ("POSITIVE_SUM", "MOU_ANCHOR", "COMPOUND_CHAIN"):
            d = dims[mid]
            assert d["value"] is None, f"{mid} 缺数据时必须为 null（⛔ 回 0 冒充）"
            assert d["status"] == "OUT-OF-LEDGER-NOT-CONNECTED"
            assert d["note"].strip()
        assert dims["FUSE_EVENTS"]["value"] == 0
        assert dims["FUSE_EVENTS"]["status"] == "OK"

    def test_fuse_ledger_unreachable_returns_null(self, monkeypatch):
        """真断连实测：NCA 账本读取抛 OSError → FUSE 必须 null + OUT-OF-LEDGER（⛔ 回 0）。"""
        from app import nca_logger

        def _boom() -> List[Dict]:
            raise OSError("ledger unreachable（模拟断连）")

        monkeypatch.setattr(nca_logger, "list_nca", _boom)
        body = _feed()
        fuse = body["dimensions"][0]
        assert fuse["metric_id"] == "FUSE_EVENTS"
        assert fuse["value"] is None
        assert fuse["status"] == "OUT-OF-LEDGER-NOT-CONNECTED"
        assert fuse["sample"] is None
        assert "不可达" in fuse["note"]

    def test_idempotent_same_pool_ref_same_values(self):
        a = _feed()
        b = _feed()
        assert a["pool_ref"] == b["pool_ref"], "同数据同 pool_ref（幂等锚）"
        va = [(d["metric_id"], d["value"], d["status"], d["sample"]) for d in a["dimensions"]]
        vb = [(d["metric_id"], d["value"], d["status"], d["sample"]) for d in b["dimensions"]]
        assert va == vb, "同 pool_ref 同口径同值"

    def test_readonly_evidence(self):
        """纯读证据：连取 3 次，数据/NCA 目录逐字节指纹不变。"""
        before = _snapshot()
        for _ in range(3):
            _feed()
        after = _snapshot()
        assert before == after, "取数接口产生了写副作用"
        assert len(after["nca"]) == len(before["nca"]), "NCA 链条数不得增减"


class TestFeedWithData:
    """带数样例：经引擎自身写 API 造数（引擎正常运作），核四维 OK 读数。"""

    def _setup_scenario(self) -> str:
        sid = _create_sandbox()
        # Phase0 → P0
        r = client.post(f"/api/v1/sandboxes/{sid}/start")
        assert r.status_code == 200, r.text
        # 正和验证①：非正和 → fuse=True（写日志 + FUSE NCA 后按 SV-3 抛错，路由转 422，记录已落盘）
        r = client.post(
            f"/api/v1/sandboxes/{sid}/positive-sum",
            json={"coalition_utility": 10.0, "independent_utilities": [8.0, 8.0]},
        )
        assert r.status_code == 422 and "熔断" in r.json()["detail"], r.text
        # 正和验证②：正和 → delta=4.0（最近一条含 timestamp，成为 POSITIVE_SUM 取值）
        r = client.post(
            f"/api/v1/sandboxes/{sid}/positive-sum",
            json={"coalition_utility": 20.0, "independent_utilities": [8.0, 8.0]},
        )
        assert r.status_code == 200, r.text
        # 正向化合（P0 许可；surplus 取最近正和记录）
        r = client.post(
            f"/api/v1/sandboxes/{sid}/chem/combine",
            json={
                "assets": ["IP", "knowledge", "exchange", "scene_weight", "cognitive_nca"],
                "conditions": {"indivisible": True, "emergent": True, "nonlinear": True},
                "justification": "FEED 测试五阶全资产正向化合",
            },
        )
        assert r.status_code == 200, r.text
        # 评估推进 P0 → P1
        r = client.post(
            f"/api/v1/sandboxes/{sid}/evaluate",
            json={"pcr_input": 100.0, "tax_revenue": 50.0, "employment_ss": 10.0},
        )
        assert r.status_code == 200, r.text
        assert r.json()["phase"] == "P1"
        # MOU 锚定（P1 许可；cbdc 路由独立前缀 /api/v1/cbdc）
        r = client.post(
            f"/api/v1/cbdc/{sid}/anchor",
            json={"tax_in": 10, "tax_out": 20},
        )
        assert r.status_code == 200, r.text
        return sid

    def test_four_dimensions_ok_with_data(self):
        self._setup_scenario()
        body = _feed()
        dims = {d["metric_id"]: d for d in body["dimensions"]}

        fuse = dims["FUSE_EVENTS"]
        assert fuse["status"] == "OK"
        assert isinstance(fuse["value"], int) and fuse["value"] >= 1, "非正和验证应产生 FUSE 存证"
        assert fuse["sample"] and fuse["sample"] >= fuse["value"]
        assert "事件数" in fuse["basis"]

        ps = dims["POSITIVE_SUM"]
        assert ps["status"] == "OK"
        assert ps["value"] == 4.0, "最近一条含 delta 记录：20−(8+8)=4"
        assert ps["sample"] == 2, "两条含 delta 记录（fuse 条 + 正和条）"
        assert "positive_sum_index" in ps["note"] or "is_positive_sum" in ps["note"]

        mou = dims["MOU_ANCHOR"]
        assert mou["status"] == "OK"
        assert mou["value"] == 1
        assert "SIMULATED-TAX-AUTHORITY" in mou["basis"]
        assert mou["sample"] >= 2, "分母＝沙盒池沙盒数（种子+新建）"

        chem = dims["COMPOUND_CHAIN"]
        assert chem["status"] == "OK"
        assert chem["value"] == 1
        assert "CHEM-001=1" in chem["note"]

    def test_idempotent_after_writes(self):
        """造数后连取两次：pool_ref 与四维值稳定。"""
        self._setup_scenario()
        a = _feed()
        b = _feed()
        assert a["pool_ref"] == b["pool_ref"]
        assert [d["value"] for d in a["dimensions"]] == [d["value"] for d in b["dimensions"]]

    def test_readonly_after_writes(self):
        """造数后取数仍纯读：目录指纹不变、NCA 条数不增。"""
        self._setup_scenario()
        before = _snapshot()
        _feed()
        after = _snapshot()
        assert before == after
