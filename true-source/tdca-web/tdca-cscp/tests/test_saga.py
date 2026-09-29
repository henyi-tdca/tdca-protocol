# -*- coding: utf-8 -*-
"""Saga 补偿事务单元测试（R-CSCP-002: 回滚覆盖率 <90% 阻塞集成——本套覆盖回滚全路径）。"""
import pytest

from cscp_gateway.saga import Saga


def test_rollback_reverse_order():
    """逆序补偿（LIFO）。"""
    order = []
    saga = Saga(refund_fn=lambda: order.append("REFUND"),
                unlock_fn=lambda: order.append("UNLOCK"),
                cancel_fn=lambda: order.append("CANCEL"),
                release_fn=lambda: order.append("RELEASE"))
    saga.register("SANDBOX_UNLOCK")
    saga.register("TRANSLATOR_RESERVE_RELEASE")
    saga.register("ESCROW_REFUND")
    compensated = saga.rollback("timeout")
    assert compensated == ["ESCROW_REFUND:COMPENSATED",
                           "TRANSLATOR_RESERVE_RELEASE:COMPENSATED",
                           "SANDBOX_UNLOCK:COMPENSATED"]
    assert order == ["REFUND", "RELEASE", "UNLOCK"]


def test_rollback_clears_pending():
    saga = Saga()
    saga.register("ESCROW_REFUND")
    assert saga.pending() == ["ESCROW_REFUND"]
    saga.rollback()
    assert saga.pending() == []


def test_rollback_idempotent():
    saga = Saga()
    saga.register("ESCROW_REFUND")
    saga.rollback()
    second = saga.rollback()  # 已补偿的动作不再重复
    assert second == []


def test_register_unknown_action_rejected():
    saga = Saga()
    with pytest.raises(ValueError):
        saga.register("NOT_A_REAL_ACTION")


def test_rollback_with_reason_recorded():
    saga = Saga(refund_fn=lambda: None)
    saga.register("ESCROW_REFUND")
    compensated = saga.rollback("STEP4 timeout")
    assert len(compensated) == 1
