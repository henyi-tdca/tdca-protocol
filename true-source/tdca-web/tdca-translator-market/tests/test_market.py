# -*- coding: utf-8 -*-
"""W4 翻译器市场 + MOU 分割测试（S-CSCP-001 ≥10 对 / <500ms / 定价 / Shapley <1%）。"""
from fastapi.testclient import TestClient

from translator_market.api import app
from translator_market.market import SceneTranslatorMarket
from translator_market.mou_split import MOUSplitContract, default_mou_value_fn

client = TestClient(app)


# ---- S-CSCP-001: 注册 ≥10 对 + 双向索引 ----

def test_registry_min_10_pairs():
    r = client.get("/translator/count")
    assert r.json()["count"] >= 10
    assert r.json()["pass"] is True


def test_register_custom_translator():
    r = client.post("/translator/register", json={
        "src": "SCN-TOUR", "dst": "SCN-SUPPLY", "complexity": 1.4, "desc": "自定义"})
    assert r.status_code == 201
    assert r.json()["translator_id"].startswith("TR-")


# ---- 匹配 + 定价（费用 = 复杂度 × risk_premium）----

def test_match_and_pricing():
    r = client.get("/translator/match", params={"src": "SCN-TOUR", "dst": "SCN-AGRI",
                                                      "risk_premium": 0.5})
    body = r.json()
    assert body["matched"] is True
    assert body["translation_cost"] == round(1.0 * 0.5, 4)   # 复杂度 1.0 × premium 0.5
    assert body["latency_ms"] < 500.0                        # <500ms 硬指标


def test_match_no_translator():
    r = client.get("/translator/match", params={"src": "SCN-XXX", "dst": "SCN-YYY"})
    assert r.json()["matched"] is False
    assert r.json()["reason"] == "NO_TRANSLATOR"


def test_match_reverse_only():
    r = client.get("/translator/match", params={"src": "SCN-AGRI", "dst": "SCN-TOUR"})
    assert r.json()["matched"] is True   # 反向翻译器存在（TR-AGRI-TOUR）


# ---- MOU 分割（Shapley 精确 + 协同正和）----

def test_mou_split_exact_shapley():
    r = client.post("/mou/split-preview", json={
        "scene_ids": ["A", "B", "C"],
        "contributions": {"A": 100, "B": 60, "C": 40}})
    body = r.json()
    assert body["method"] == "exact"
    split = body["shapley_split"]
    # Shapley 性质: 总和 = 大联盟价值 v({A,B,C}) = 200×(1+1.2×2×0.05)=224
    assert abs(body["total_mou"] - 224.0) < 0.01
    # 对称性: 无差异场景 Shapley 相同
    r2 = client.post("/mou/split-preview", json={
        "scene_ids": ["X", "Y"],
        "contributions": {"X": 50, "Y": 50}})
    s = r2.json()["shapley_split"]
    assert s["X"] == s["Y"]


def test_mou_split_monte_carlo_approximation():
    """n>6 蒙特卡洛近似与精确对比偏差 <1%。"""
    mou = MOUSplitContract()
    scene_ids = [f"S{i}" for i in range(7)]
    contrib = {s: 10.0 for s in scene_ids}
    fn = default_mou_value_fn(contrib)
    exact = mou.split(scene_ids, fn, exact_limit=10)          # 强制精确（7! = 5040 排列可算）
    approx = mou.split(scene_ids, fn, exact_limit=6, samples=20000)
    for s in scene_ids:
        err = abs(exact[s] - approx[s]) / exact[s] if exact[s] else 0
        assert err < 0.01, f"{s}: {err:.4f} ≥ 1%"             # 偏差 <1%（CCP T3 验收）
