# -*- coding: utf-8 -*-
"""FUSE-GEAR-001 熔断同步广播工件测试（TDCA-HANDOFF-EXEC-L1SI215-FUSE-GEAR-001）。

G-1~G-4 每项一正一反用例（G-5）；组合面扇出 2~8 × n 16~4096 逐格核（G-4/C-47）。
⛔ 不改在册门槛数值；⛔ 反例只作断言模型不作实现。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app as app_module
import fuse_bcast_ops as fb


@pytest.fixture(autouse=True)
def _clean_state():
    fb._reset_state()
    yield
    fb._reset_state()


def _signed(source_id="ccp-core-01", nonce="nonce-1", event_id="ccp-fuse-sync",
            shard=fb.SHARD_GRANULARITY, payload="fuse-open"):
    sig = fb.sign_event(source_id, nonce, event_id, shard, payload)
    return {"source_id": source_id, "nonce": nonce, "signature": sig,
            "event_id": event_id, "shard": shard, "payload": payload}


# ── G-1：在册六项参数落实现 + 反向（越格拒收/篡改参数失效）──

def test_g1_params_in_register():
    """正：六项参数逐字在册（git grep 可核）＋收敛门槛 <5s。"""
    assert fb.ACK_TIMEOUT_MS == 150
    assert fb.RETRY_LIMIT == 3
    assert fb.PARALLEL_ACK_BUDGET_MS == 500
    assert fb.RATE_LIMIT_PER_SEC == 1000
    assert fb.MAX_FANOUT == 8
    assert fb.SHARD_GRANULARITY == "scenario-domain"
    assert fb.CONVERGENCE_BUDGET_MS == 5000


def test_g1_fanout_over_register_rejected():
    """反：扇出 9 越在册 ≤8 格，fail-closed 拒收给码（⛔ 降标不可过）。"""
    ok, code, _, _ = fb.validate_topology(64, 9)
    assert ok is False and code == fb.REJ_FANOUT


def test_g1_parallel_ack_budget_positive_and_negative():
    """正：扇出 8 并行 ack 总延迟 150ms < 500ms；反：扇出 9 越在册 ≤8 拒收。"""
    assert fb.parallel_ack_latency_ms(8) == 150
    assert fb.parallel_ack_latency_ms(8) < fb.PARALLEL_ACK_BUDGET_MS
    with pytest.raises(fb.FuseReject) as exc:
        fb.parallel_ack_latency_ms(9)
    assert exc.value.code == fb.REJ_FANOUT


def test_g1_endpoint_route_exists():
    """正：POST /trigger/sync 路由在位（平台等价物具名落点）。"""
    client = TestClient(app_module.app)
    r = client.post("/trigger/sync", json={})
    assert r.status_code == 422  # 缺字段→参数校验，非 404（路由在册）


# ── G-2：鉴权三要件，各一正一反 ──

def test_g2_whitelist_positive():
    fb.authenticate_trigger(**_signed())
    # 不抛即过；二次调用同 nonce 走重放（属 nonce 反例，不在此断言）


def test_g2_whitelist_negative():
    with pytest.raises(fb.FuseReject) as exc:
        fb.authenticate_trigger(**_signed(source_id="outsider-9"))
    assert exc.value.code == fb.REJ_AUTH_WHITELIST


def test_g2_nonce_positive():
    fb.authenticate_trigger(**_signed(nonce="nonce-A"))


def test_g2_nonce_replay_negative():
    fb.authenticate_trigger(**_signed(nonce="nonce-B"))
    with pytest.raises(fb.FuseReject) as exc:
        fb.authenticate_trigger(**_signed(nonce="nonce-B"))
    assert exc.value.code == fb.REJ_AUTH_NONCE


def test_g2_signature_positive():
    fb.authenticate_trigger(**_signed())


def test_g2_signature_negative():
    bad = _signed()
    bad["signature"] = "0" * 64
    with pytest.raises(fb.FuseReject) as exc:
        fb.authenticate_trigger(**bad)
    assert exc.value.code == fb.REJ_AUTH_SIGNATURE


# ── G-3：去重共享多播树（正）与「各源各建树」反例（须红）──

def test_g3_dedup_shared_tree_positive():
    """正：n 固定，源数 k=2/4/8 同一事件共享树＋去重，消息数恒 = n-1 ≤ n-1。"""
    n, fanout = 64, 4
    for k in (2, 4, 8):
        assert fb.simulate_dedup_broadcast(n, fanout, k) == n - 1
        assert fb.simulate_dedup_broadcast(n, fanout, k) <= n - 1


def test_g3_counterexample_per_source_trees_negative():
    """反（须红）：各源各建树、无去重，消息数随源数线性增长 k×(n-1)，k≥2 即越 n-1。"""
    n, fanout = 64, 4
    counts = [fb.simulate_per_source_trees(n, fanout, k) for k in (1, 2, 3, 4, 5)]
    assert counts == [k * (n - 1) for k in (1, 2, 3, 4, 5)]  # 严格线性
    assert all(c > n - 1 for c in counts[1:])              # k≥2 越界（红）


def test_g3_tree_is_connected_n_minus_1_edges():
    """正：共享树 n 节点恰 n-1 边（连通树，扇出 ≤8 在册格逐点核）。"""
    for fanout in range(2, fb.MAX_FANOUT + 1):
        for n in (16, 100, 512, 4096):
            tree = fb.build_shared_tree(n, fanout)
            assert fb.tree_edges(tree) == n - 1
            assert all(len(c) <= fanout for c in tree.values())


# ── G-4：收敛 <5s 可跑断言；扇出 2~8 × n 16~4096 逐格核；拒收给码 ──

def test_g4_convergence_positive():
    """正：扇出 8、n=4096 → 深度 4×600ms=2400ms < 5s，收。"""
    ok, code, depth, t = fb.validate_topology(4096, 8)
    assert ok and code is None
    assert depth == 4 and t == 2400 and t < fb.CONVERGENCE_BUDGET_MS


def test_g4_convergence_reject_negative():
    """反：扇出 2、n=512 重试打满 → 9×600=5400ms ≥ 5s，fail-closed 拒收给码。"""
    ok, code, depth, t = fb.validate_topology(512, 2)
    assert ok is False and code == fb.REJ_CONVERGENCE
    assert depth == 9 and t == 5400


def test_g4_grid_fanout_2_to_8_n_16_to_4096():
    """组合面（C-47）：扇出 2~8 × n {16,32,64,128,256,512,1024,2048,4096} 逐格核。
    每格不抛异常、结论非空；拒收格恰为扇出 2 且 n≥512（穷举越界档）。"""
    ns = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    rejected = []
    for fanout in range(2, fb.MAX_FANOUT + 1):
        for n in ns:
            ok, code, depth, t = fb.validate_topology(n, fanout)
            assert isinstance(ok, bool) and (code is None or isinstance(code, str))
            assert depth >= 2 and t > 0
            if not ok:
                rejected.append((fanout, n))
                assert code in (fb.REJ_CONVERGENCE, fb.REJ_FANOUT, fb.REJ_NODE_RANGE)
    assert rejected == [(2, 512), (2, 1024), (2, 2048), (2, 4096)]


def test_g4_node_range_negative():
    """反：n=8 与 n=8192 越在册格 16~4096，拒收给码。"""
    assert fb.validate_topology(8, 4)[1] == fb.REJ_NODE_RANGE
    assert fb.validate_topology(8192, 4)[1] == fb.REJ_NODE_RANGE


def test_g4_rate_limit_token_bucket():
    """限速 1000 事件/s/节点：同一瞬刻 1001 连发，恰 1000 准入、第 1001 拒。"""
    fb._reset_state()
    accepted = sum(1 for _ in range(1001) if fb.admit_event("ccp-core-01", now=1000.0))
    assert accepted == 1000  # 确定性令牌桶：桶容 1000，瞬刻无补充


# ── HTTP 面正/反 ──

def test_http_trigger_sync_positive():
    client = TestClient(app_module.app)
    body = _signed(nonce="http-1", payload="")
    body.update({"n_nodes": 64, "fanout": 4})
    r = client.post("/trigger/sync", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["accepted"] is True
    assert data["bcast_messages"] == 63 == data["bcast_bound"]
    assert data["topology"]["convergence_ms"] == 1800  # ⌈log₄64⌉=3 层 × 600ms


def test_http_trigger_sync_reject_convergence_negative():
    client = TestClient(app_module.app)
    body = _signed(nonce="http-2")
    body.update({"n_nodes": 512, "fanout": 2})
    r = client.post("/trigger/sync", json=body)
    assert r.status_code == 422
    assert r.json()["detail"]["reject_code"] == fb.REJ_CONVERGENCE


def test_http_trigger_sync_reject_whitelist_negative():
    client = TestClient(app_module.app)
    body = _signed(source_id="outsider-9", nonce="http-3")
    body.update({"n_nodes": 64, "fanout": 4})
    r = client.post("/trigger/sync", json=body)
    assert r.status_code == 422
    assert r.json()["detail"]["reject_code"] == fb.REJ_AUTH_WHITELIST
