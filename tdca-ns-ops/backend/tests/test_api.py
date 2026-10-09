# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M1 原型）
# 目标函数:     后端测试（pytest）——约束 CRUD / BV-3 门 / 沙盒 / 调整权全流程 / F3 校验
# 约束矩阵:     FC-NS-OPS-001 BV-1~7 + 测试隔离（不污染生产数据）
# 先验分布:     seed 数据 + FastAPI TestClient
# 配置权边界:    L2 层；测试用独立数据目录
# 预期分配:     全绿；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""NS-OPS M1 后端测试。

制度锚定: FC-NS-OPS-001 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 测试数据目录隔离
_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.store as store  # noqa: E402

from app.main import app  # noqa: E402

HUMAN = "HUMAN-FOUNDER-001"
HUMAN2 = "HUMAN-ENGINEER-001"
HUMAN3 = "HUMAN-AUDITOR-001"
AI = "AI-SUBAGENT-01"

client = TestClient(app)


# ---------------------------------------------------------------------------
# F1 约束 CRUD + BV-3
# ---------------------------------------------------------------------------


def test_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_loaded():
    r = client.get("/api/v1/constraints")
    assert r.status_code == 200
    assert len(r.json()) >= 6


def test_create_constraint_with_human_signature():
    payload = {
        "layer": "subject",
        "scope": "personal",
        "action": "我不会向未授权方共享位置数据",
        "action_code": "NSFL: ⊗ location.share(unauthorized)",
        "certainty": "high",
        "human_signature": HUMAN,
        "owner": "OPC-Developer-002",
        "bottom_lines": ["合理", "合规"],
    }
    r = client.post("/api/v1/constraints", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "draft"
    assert body["version"] == 1
    assert len(body["nca_refs"]) >= 1


def test_create_constraint_without_signature_blocked():
    payload = {
        "layer": "subject",
        "scope": "personal",
        "action": "我不会做某事",
        "human_signature": AI,  # AI 签名 → BV-3 拒绝
    }
    r = client.post("/api/v1/constraints", json=payload)
    assert r.status_code == 403
    assert "BV-3" in r.json()["detail"]


def test_update_constraint_version_increment():
    payload = {
        "layer": "subject",
        "scope": "personal",
        "action": "我不会向未授权方共享位置数据（更新版）",
        "human_signature": HUMAN,
    }
    r = client.post("/api/v1/constraints", json=payload)
    cid = r.json()["id"]

    up = client.put(f"/api/v1/constraints/{cid}", json={
        "action": "我不会向未授权方共享任何位置数据",
        "human_signature": HUMAN,
    })
    assert up.status_code == 200
    assert up.json()["version"] == 2


def test_delete_institutional_blocked():
    r = client.delete("/api/v1/constraints/NS-INST-001", params={"human_signature": HUMAN})
    assert r.status_code == 403
    assert "制度负空间" in r.json()["detail"]


def test_delete_subject_with_signature():
    payload = {
        "layer": "subject",
        "scope": "personal",
        "action": "我不会删除测试用约束",
        "human_signature": HUMAN,
    }
    r = client.post("/api/v1/constraints", json=payload)
    cid = r.json()["id"]
    d = client.delete(f"/api/v1/constraints/{cid}", params={"human_signature": HUMAN})
    assert d.status_code == 200
    assert d.json()["deleted"] == cid


# ---------------------------------------------------------------------------
# F1 三层视图
# ---------------------------------------------------------------------------


def test_triple_layer_view():
    r = client.get("/api/v1/views/triple-layer")
    assert r.status_code == 200
    body = r.json()
    # H4：多主体/多场景结构
    assert "subjects" in body and "scenes" in body and "institutional" in body
    assert len(body["institutional"]["entries"]) >= 2
    assert "合法" in body["bottom_lines"]


# ---------------------------------------------------------------------------
# F3 声明-行为校验
# ---------------------------------------------------------------------------


def test_judgment_institutional_fuse():
    r = client.post("/api/v1/judgments", json={
        "actor": "agent-x",
        "action": "实施违反法律底线的行为",
        "scene": "community",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "block"
    assert body["fuse_triggered"] is True


def test_judgment_allow():
    r = client.post("/api/v1/judgments", json={
        "actor": "agent-x",
        "action": "提交开源代码贡献",
        "scene": "community",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "allow"


# ---------------------------------------------------------------------------
# F2 调整权全流程（NS-011 状态机）
# ---------------------------------------------------------------------------


def _start_adjustment() -> str:
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": "NS-SUBJECT-001",
        "trigger": "社会变化：新隐私法规出台",
        "proposal": "将隐私约束从 high 升级为 absolute",
        "initiator": HUMAN,
        "human_signature": HUMAN,
    })
    assert r.status_code == 201, r.text
    return r.json()["adjustment_id"]


def _transition(aid: str, to_status: str, signer: str = HUMAN, **kw):
    return client.post(
        f"/api/v1/adjustments/{aid}/transition",
        params={"to_status": to_status, "human_signature": signer, **kw},
    )


def test_adjustment_full_flow():
    aid = _start_adjustment()

    # 1. deliberation → sandbox
    r = _transition(aid, "sandbox")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "sandbox"

    # 2. sandbox → determination（H2：确定记录在 determination 步完成——生效时间/回滚/3 签名）
    r = _transition(
        aid, "determination",
        final_version=2, effective_date="2026-09-01", rollback_version=1,
        extra_signatures=f"{HUMAN2},{HUMAN3}",
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "determination"
    det = r.json()["determination"]
    assert det is not None, "determination 步必须生成确定记录（H2）"
    assert len(det["human_signatures"]) == 3
    assert det["final_version"] == 2
    assert det["effective_date"] == "2026-09-01"
    assert det["rollback_version"] == 1

    # 3. determination → encoding（H2：编码步将约束置 rigid 刚性态）
    r = _transition(aid, "encoding")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "encoding"
    c = client.get("/api/v1/constraints/NS-SUBJECT-001").json()
    assert c["status"] == "rigid"
    assert c["version"] == 2
    # M4：刚性约束同步确定签名
    assert len(c["human_signatures"]) == 3

    # 4. encoding → deployment（H2：部署步仅部署记录，不再改约束）
    r = _transition(aid, "deployment")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "deployment"
    assert r.json()["deployment"]["status"] == "gray"

    # 5. deployment → feedback → closed（B3：feedback 步生成 NCA——nca_refs 数量 +1）
    n_before = len(r.json()["nca_refs"] or [])
    r = _transition(aid, "feedback")
    assert r.status_code == 200
    assert len(r.json()["nca_refs"] or []) == n_before + 1, "feedback 步须生成 NCA（B3）"
    r = _transition(aid, "closed")
    assert r.status_code == 200
    assert r.json()["status"] == "closed"


def test_adjustment_requires_signature():
    aid = _start_adjustment()
    # AI 签名推进 → BV-3 拒绝
    r = _transition(aid, "sandbox", signer=AI)
    assert r.status_code == 403


def test_adjustment_illegal_transition():
    aid = _start_adjustment()
    # deliberation 直接跳 deployment → 非法迁移
    r = _transition(aid, "deployment")
    assert r.status_code == 422
    assert "非法状态迁移" in r.json()["detail"]


def test_adjustment_encoding_needs_three_signatures():
    aid = _start_adjustment()
    _transition(aid, "sandbox")
    # 只给 1 个签名 + 无生效时间 → 422（BV-3 签名不足；H3 生效时间必填）
    r = _transition(aid, "determination", final_version=2)
    assert r.status_code == 422
    assert "BV-3" in r.json()["detail"]


# ---- REV 修复回归测试（B1/B2/B3/M5/H3） ----

def test_b1_institutional_certainty_cannot_be_weakened():
    """B1 回归：PUT 不得绕过制度层 absolute 强制。"""
    # 制度层禁止直接 PUT（B2/M7）
    r = client.put("/api/v1/constraints/NS-INST-001", json={
        "action": "任何人不能实施违反 L0 法律底线的行为（试图放宽）",
        "human_signature": HUMAN,
    })
    assert r.status_code == 403
    assert "禁止直接修改" in r.json()["detail"]
    # 列表仍正常（不 500）
    assert client.get("/api/v1/constraints").status_code == 200


def test_b2_institutional_write_requires_l0():
    """B2 回归：L2 工程师不可写制度层约束。"""
    payload = {
        "layer": "institutional",
        "scope": "global",
        "action": "任何人不能越权立法",
        "certainty": "absolute",
        "human_signature": HUMAN2,  # L2 工程师
    }
    r = client.post("/api/v1/constraints", json=payload)
    assert r.status_code == 403
    assert "L0" in r.json()["detail"]


def test_b3_start_adjustment_generates_nca():
    """B3 回归：发起调整即生成 NCA（Operation-Type=Adjust-Start）。"""
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": "NS-SUBJECT-002",
        "trigger": "回归测试",
        "proposal": "测试 NCA",
        "initiator": HUMAN,
        "human_signature": HUMAN,
    })
    assert r.status_code == 201, r.text
    nca_refs = r.json()["nca_refs"]
    assert len(nca_refs) >= 1
    # 校验 NCA 文件 Operation-Type（E6：用 _BACKEND 绝对路径，不依赖 cwd）
    nca_path = store._NCA_DIR / f"NCA-{nca_refs[0]}.yaml"
    assert nca_path.exists(), f"NCA 文件缺失: {nca_path}"
    content = nca_path.read_text(encoding="utf-8")
    assert "Adjust-Start" in content, "发起调整 NCA 的 Operation-Type 应为 Adjust-Start（B3）"


def test_m5_initiator_must_match_signature():
    """M5 回归：initiator 与签名不符 → 422。"""
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": "NS-SUBJECT-002",
        "trigger": "回归测试",
        "proposal": "伪造发起人",
        "initiator": "AI-SUBAGENT-01",
        "human_signature": HUMAN,
    })
    assert r.status_code == 422
    assert "initiator" in r.json()["detail"]


def test_h3_determination_requires_effective_date():
    """H3 回归：确定态必须指定生效时间（不可立即生效）。"""
    aid = _start_adjustment()
    _transition(aid, "sandbox")
    r = _transition(aid, "determination", final_version=2,
                    extra_signatures=f"{HUMAN2},{HUMAN3}")
    assert r.status_code == 422
    assert "生效时间" in r.json()["detail"]


def test_h4_triple_layer_multiple_subjects():
    """H4 回归：三层视图返回全部主体/场景（种子含 2 主体 2 场景）。"""
    r = client.get("/api/v1/views/triple-layer")
    assert r.status_code == 200
    body = r.json()
    assert "subjects" in body and "scenes" in body
    assert len(body["subjects"]) >= 2
    assert len(body["scenes"]) >= 2

def test_e1_institutional_adjustment_blocked():
    """E1 回归：制度层约束禁止走调整流程（L2 不可经状态机改写 L0 底线）。"""
    r = client.post("/api/v1/adjustments", json={
        "target_constraint_id": "NS-INST-001",
        "trigger": "试图调整制度约束",
        "proposal": "放宽制度约束",
        "initiator": HUMAN,
        "human_signature": HUMAN,
    })
    assert r.status_code == 403
    assert "制度负空间约束禁止走调整流程" in r.json()["detail"]


def test_e3_rollback_version_required():
    """E3 回归：确定态必须显式指定回滚版本（缺省拒绝）。"""
    aid = _start_adjustment()
    _transition(aid, "sandbox")
    r = _transition(aid, "determination", final_version=2, effective_date="2026-09-01",
                    extra_signatures=f"{HUMAN2},{HUMAN3}")
    assert r.status_code == 422
    assert "回滚版本" in r.json()["detail"]


def test_e2_constraint_nca_records_signer():
    """E2 回归：约束创建 NCA 记录实际签名者（Signed-By 非空）。"""
    payload = {
        "layer": "subject", "scope": "personal",
        "action": "我不会记录签名者测试约束",
        "human_signature": HUMAN,
    }
    r = client.post("/api/v1/constraints", json=payload)
    assert r.status_code == 201, r.text
    nca_id = r.json()["nca_refs"][0]
    nca_path = store._NCA_DIR / f"NCA-{nca_id}.yaml"
    content = nca_path.read_text(encoding="utf-8")
    assert HUMAN in content, "NCA 应记录签名者（E2）"