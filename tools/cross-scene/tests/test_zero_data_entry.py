# SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-
"""T-P3-002 零数据企业入盒通道测试（强制交互验证 / 激活系数门槛 / PCR 资金锁定释放 / <48h）。"""
from cross_scene.zero_data_entry import ENTRY_THRESHOLD, ZeroDataCrossSceneEntry


def _entry():
    return ZeroDataCrossSceneEntry(
        existing_scene_ids=["SCN-TOUR", "SCN-AGRI", "SCN-EDU"],
        mou_map={"SCN-TOUR": 100.0, "SCN-AGRI": 60.0, "SCN-EDU": 40.0},
        pcr_map={"SCN-TOUR": 100.0, "SCN-AGRI": 100.0, "SCN-EDU": 100.0})


def test_submit_locks_gov_pcr():
    e = _entry()
    entry = e.submit("DID-ZERO-001", pucr_pre_sale=5000.0, gov_pcr=1000.0)
    assert entry.gov_pcr_locked is True          # 政府 PCR 资金数字人民币锁定
    assert entry.status == "SUBMITTED"


def test_enter_high_activation_approved():
    """大额预售 → 激活系数 >1.2 → 出盒进入市场 + 里程碑释放。"""
    e = _entry()
    entry = e.submit("DID-ZERO-001", pucr_pre_sale=50000.0, gov_pcr=1000.0)
    r = e.verify_and_enter(entry.entry_id)
    assert r["status"] == "APPROVED"
    assert r["market_entry"] is True
    assert r["gov_pcr_released"] == 500.0       # 50% 里程碑释放
    assert r["entry_hours"] < 48.0               # 验收：申请到入盒 <48h


def test_enter_low_activation_rejected():
    """低预售 → 激活系数 ≤1.2 → 拒绝（不出盒）。"""
    e = _entry()
    entry = e.submit("DID-ZERO-002", pucr_pre_sale=1.0, gov_pcr=1000.0)
    r = e.verify_and_enter(entry.entry_id)
    assert r["status"] == "REJECTED"
    assert r["activation"] <= ENTRY_THRESHOLD
