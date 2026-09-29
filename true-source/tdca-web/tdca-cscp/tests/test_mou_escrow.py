# -*- coding: utf-8 -*-
"""W5 MOU 分割 escrow 验证测试（Shapley 预计算 → CBDC 锁定 → escrow 释放全链路）。"""
from decimal import Decimal

from cscp_gateway.adapters import MockCBDCContractAdapter
from cscp_gateway.mou_escrow import MOUEscrowVerifier


def test_shapley_split_ratios_sum_to_one():
    v = MOUEscrowVerifier()
    split = v.compute_split(["TOUR", "AGRI", "EDU"],
                            {"TOUR": 100.0, "AGRI": 60.0, "EDU": 40.0})
    assert abs(sum(split.values()) - 1.0) < 1e-6          # Σ ratio = 1
    # 对称性: 等贡献 → 等比例
    split2 = v.compute_split(["X", "Y"], {"X": 50.0, "Y": 50.0})
    assert split2["X"] == split2["Y"] == 0.5


def test_escrow_verification_integrity():
    """Σ(ratio × budget) = escrow_total（零漂移）。"""
    v = MOUEscrowVerifier()
    split = v.compute_split(["TOUR", "AGRI", "EDU"],
                            {"TOUR": 100.0, "AGRI": 60.0, "EDU": 40.0})
    budget = 9000.0
    escrow_total = round(sum(r * budget for r in split.values()), 4)
    report = v.verify_escrow(escrow_total, split, budget)
    assert report["verified"] is True
    assert abs(report["delta"]) < 1e-6


def test_escrow_detects_tamper():
    v = MOUEscrowVerifier()
    split = v.compute_split(["A", "B", "C"], {"A": 100.0, "B": 60.0, "C": 40.0})
    report = v.verify_escrow(5000.0, split, 9000.0)   # 篡改 escrow 总额
    assert report["verified"] is False


def test_lock_with_shapley_split_via_adapter():
    """W5 全链路：lock(contributions) → Shapley 分割 escrow（Σ = budget）。"""
    adapter = MockCBDCContractAdapter()
    res = adapter.lock(request={
        "pcr_budget": 9000.0,
        "contributions": {"TOUR": 100.0, "AGRI": 60.0, "EDU": 40.0}})
    assert res["locked"] is True
    assert res["mou_split"] is not None
    assert abs(sum(res["mou_split"].values()) - 1.0) < 1e-6
    assert abs(res["escrow_total"] - 9000.0) < 1e-6      # Σ(ratio×budget) = budget


def test_lock_fallback_ratio_without_contributions():
    """无贡献 → 回退单一 mou_split_ratio（向后兼容）。"""
    adapter = MockCBDCContractAdapter(mou_enabled=False)
    res = adapter.lock(request={"pcr_budget": 1000.0, "mou_split_ratio": 0.5})
    assert res["escrow_total"] == 500.0
    assert res["mou_split"] is None


def test_refund_chain():
    """escrowRefund（M-4）全链路。"""
    adapter = MockCBDCContractAdapter()
    res = adapter.lock(request={"pcr_budget": 9000.0,
                                "contributions": {"A": 1.0, "B": 1.0, "C": 1.0}})
    refund = adapter.refund(res["escrow_id"])
    assert refund["refunded"] is True
    assert res["escrow_id"] in adapter.refunded
