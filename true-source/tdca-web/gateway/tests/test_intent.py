# -*- coding: utf-8 -*-
"""意图导航端点测试（自然语言 → 功能页直达 + 操作指引）。"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _get(q):
    r = client.get(f"/api/v1/intent?q={q}")
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert "nca_watermark" in body
    return body["data"]


def test_intent_sign():
    d = _get("我要签批一个确权申请")
    assert d["matched"] is True
    assert d["route"] == "/attestation/dynamic"
    assert d["action"] == "签批"
    assert len(d["guide"]) >= 3                     # 操作指引在位
    assert any("HUF" in step for step in d["guide"])  # 签批必含人类终裁提示


def test_intent_query_tax():
    d = _get("帮我查一下税收账单")
    assert d["route"] == "/tax"
    assert d["action"] == "查询"


def test_intent_create():
    d = _get("我想创建一个新的智能体")
    assert d["route"] == "/studio"
    assert d["action"] == "创建"


def test_intent_fallback():
    d = _get("今天天气怎么样")
    assert d["matched"] is False
    assert d["route"] == "/"                          # fail-soft 回首页 + 示例提示
    assert any("签批" in step for step in d["guide"])


def test_intent_alternatives():
    d = _get("确权和签批")                            # 多意图命中 → 备选
    assert d["matched"] is True
    assert isinstance(d["alternatives"], list)


# =====================================================================
# 意图同分排序（可增项第 4 件，2026-10-09）：并列取「命中键最长者」；
# 仍并列维持表序兜底。排序键 (命中数 ↓, 最长命中键 ↓, 表序 ↑)。
# 契约形状与 _INTENT_TABLE 零改动；改动前后对照见回报件。
# =====================================================================

def test_intent_tiebreak_longest_key_wins():
    """同分对照实证：「产权智能体后台」三处同中 1 键——/me(产权·2 字)、
    /agents(智能体后台·5 字)、/ownership(产权·2 字)。
    改动前表序胜（/me）；改动后长词胜（/agents）。"""
    d = _get("产权智能体后台")
    assert d["matched"] is True
    assert d["route"] == "/agents"                       # 最长命中键（5 字）优先
    assert [a["route"] for a in d["alternatives"]] == ["/me", "/ownership"]
    # 备选形状不变：仍恰 {route, title}（内部排序键不落响应）
    assert all(set(a.keys()) == {"route", "title"} for a in d["alternatives"])


def test_intent_tiebreak_alts_same_rule():
    """备选与最优同一裁决：加入「税」(1 字) 后 /tax 命中键短于 /ownership 的「产权」(2 字)，
    虽表序在前仍被压出前二。"""
    d = _get("产权智能体后台税")
    assert d["route"] == "/agents"
    assert [a["route"] for a in d["alternatives"]] == ["/me", "/ownership"]


def test_intent_tiebreak_full_tie_table_order():
    """全并列（命中数与最长键均同）⟹ 表序兜底：「产权积分」改动前后胜者一致（/me 先到先得）。"""
    d = _get("产权积分")
    assert d["route"] == "/me"
    assert [a["route"] for a in d["alternatives"]] == ["/ownership"]
