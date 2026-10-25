# -*- coding: utf-8 -*-
"""L1SI175-A1 术语匿名脱敏与检索测试（/api/v1/knowledge/terms）。

验收映射（A1-001 回报第三/四/五项）：
  A1-1  匿名返回只出 term＋脱敏 def：T-/TDCA-件号/NC-/ID/FC- 五类编号 → 占位
        （前置核查实测 237+9+17+15+1 处来源即此表）；⛔ 匿名不含 id 字段
  A1-1  登录面保持全量：含 id、def 原文不改（脱敏不溯源）
  A1-2  检索走现有 ?q=：空词全量 / 常见词过滤 / 无匹配空表
"""
import re

import pytest
from fastapi.testclient import TestClient

import api_v1

from app import app
from db import get_sessionmaker
from db import models as M

client = TestClient(app)

_PW = "A1-pass-2026"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    api_v1._register_hits.clear()
    yield
    api_v1._register_hits.clear()


@pytest.fixture()
def _seed():
    sm = get_sessionmaker()
    rows = [
        ("T-001", "甲词", "见 TDCA-SYMBOL-RENAME-ORDER-V1.0 与 NC-2 及 ID21 的 FC-ABC1 说明", "real"),
        ("T-002", "乙词", "普通释义不含编号", "real"),
        ("T-003", "函数词", "涉及 L-6 演进与 ID29 定义", "real"),
    ]
    with sm.begin() as s:
        for tid, term, dfn, prov in rows:
            s.add(M.TermsRegistry(term_id=tid, term=term, definition=dfn,
                                  data_provenance=prov))
    yield
    with sm.begin() as s:
        for tid, *_ in rows:
            s.query(M.TermsRegistry).filter(M.TermsRegistry.term_id == tid).delete()


def _auth():
    uname = "a1tester01"
    client.post("/api/v1/auth/register", json={
        "username": uname, "password": _PW,
        "agree_contract": True, "contract_version": "V1.0"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": _PW})
    assert r.status_code == 200, r.text[:200]
    return {"Authorization": r.json()["data"]["token"]}


_SENSITIVE = ["T-001", "TDCA-SYMBOL-RENAME-ORDER-V1.0", "NC-2", "ID21", "FC-ABC1", "ID29"]


def test_anonymous_desensitized_no_id(_seed):
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200, r.text[:200]
    items = r.json()["data"]["terms"]
    by_term = {i["term"]: i for i in items}
    assert set(by_term["甲词"].keys()) == {"term", "def"}   # ⛔ 匿名不含 id
    for bad in _SENSITIVE:
        assert bad not in by_term["甲词"]["def"], f"脱敏漏网 {bad}"
        assert bad not in by_term["函数词"]["def"], f"脱敏漏网 {bad}"
    # 五类逐类：占位在册
    assert "〔内部编号〕" in by_term["甲词"]["def"]
    # 全表扫：任何匿名行都不含五类编号（含 conftest 预种行）
    import re as _re
    pat = _re.compile(r"\bT-\d{3}\b|TDCA-[A-Z0-9-]+|\bNC-\d+\b|\bID\d+\b|\bFC-[A-Z0-9]+\b")
    for it in items:
        assert not pat.search(it["def"]), f"漏网: {it['term']}"


def test_authed_full_with_id(_seed):
    r = client.get("/api/v1/knowledge/terms", headers=_auth())
    assert r.status_code == 200, r.text[:200]
    items = {i["term"]: i for i in r.json()["data"]["terms"]}
    row = items["甲词"]
    assert "id" in row and row["id"] == "T-001"            # 登录面含 id
    assert "TDCA-SYMBOL-RENAME-ORDER-V1.0" in row["def"]   # 原文不改（脱敏不溯源）
    assert "NC-2" in row["def"] and "ID21" in row["def"]


def test_search_existing_q_param(_seed):
    # 空词 → 全量（conftest 预种 8 ＋ 本件种 3 ＝ 11）
    assert client.get("/api/v1/knowledge/terms").json()["data"]["total"] == 11
    # 常见词 → 过滤（命中词或释义，本件独有词）
    r = client.get("/api/v1/knowledge/terms?q=甲词")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1
    # 释义关键词（本件独有）
    r = client.get("/api/v1/knowledge/terms?q=普通释义")
    assert r.json()["data"]["total"] == 1
    # 无匹配 → 空表
    r = client.get("/api/v1/knowledge/terms?q=绝不存在词xyz")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0


def test_search_anonymous_also_desensitized(_seed):
    """检索（匿名）命中含编号释义时，返回仍脱敏（过滤在原文上做，展示才脱敏）。"""
    r = client.get("/api/v1/knowledge/terms?q=函数词")
    assert r.status_code == 200
    items = r.json()["data"]["terms"]
    assert len(items) == 1
    assert "ID29" not in items[0]["def"] and "〔内部编号〕" in items[0]["def"]


# ---------------------------------------------------------------------------
# L1SI175-A1-AMEND-1：匿名检索侧信道整改（案 b：q 过五类编号正则即 400）
# ---------------------------------------------------------------------------

_SHELL_ROW = ("T-009", "空壳词", "NC-2", "real")  # def 全编号：脱敏后仅余占位


@pytest.fixture()
def _seed_shell():
    sm = get_sessionmaker()
    tid, term, dfn, prov = _SHELL_ROW
    with sm.begin() as s:
        s.add(M.TermsRegistry(term_id=tid, term=term, definition=dfn,
                              data_provenance=prov))
    yield
    with sm.begin() as s:
        s.query(M.TermsRegistry).filter(M.TermsRegistry.term_id == tid).delete()


def test_amend1_anon_q_sensitive_blocked(_seed):
    """验收①：五例编号探针匿名全 400（存在性侧信道封死）。"""
    for probe in ["T-001", "T-002", "NC-2", "ID21", "TDCA-SYMBOL-RENAME-ORDER"]:
        r = client.get("/api/v1/knowledge/terms", params={"q": probe})
        assert r.status_code == 400, f"{probe} → {r.status_code}"
        assert "内部编号" in r.json()["detail"]


def test_amend1_anon_normal_q_still_works(_seed):
    """验收②：正常词匿名仍可检索，且返回体五类编号 0。"""
    r = client.get("/api/v1/knowledge/terms?q=配置权")
    assert r.status_code == 200
    items = r.json()["data"]["terms"]
    assert len(items) == 1 and items[0]["term"] == "PUCR"
    import re as _re
    pat = _re.compile(r"\bT-\d{3}\b|TDCA-[A-Z0-9-]+|\bNC-\d+\b|\bID\d+\b|\bFC-[A-Z0-9]+\b")
    assert not any(pat.search(i["def"]) for i in items)


def test_amend1_anon_full_list_no_id_no_shell(_seed, _seed_shell):
    """验收③+⑤：无 q 匿名全量（8 预种＋3 本件＋1 空壳＝12，空壳剔除后 11），字段仅 term/def。"""
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["total"] == 11                    # 12 种 − 1 空壳
    terms = {i["term"] for i in body["terms"]}
    assert "空壳词" not in terms                   # 空壳条不返回
    assert all(set(i.keys()) == {"term", "def"} for i in body["terms"])
    # 登录面仍见空壳条（设计如此：源数据不动，仅匿名面剔除）
    r2 = client.get("/api/v1/knowledge/terms", headers=_auth())
    assert any(i["term"] == "空壳词" for i in r2.json()["data"]["terms"])


def test_amend1_login_q_unaffected(_seed):
    """S-1：拦 q 不得影响登录面检索——登录面按编号检索仍 200 且命中原文。"""
    h = _auth()
    r = client.get("/api/v1/knowledge/terms?q=TDCA-SYMBOL-RENAME-ORDER", headers=h)
    assert r.status_code == 200
    items = r.json()["data"]["terms"]
    assert len(items) == 1 and items[0]["id"] == "T-001"  # 登录面含 id 与原文编号


def test_amend1_q_length_and_ctrl(_seed):
    """附加②：q 长度 1~40、控制字符清理。"""
    assert client.get("/api/v1/knowledge/terms", params={"q": "x" * 41}).status_code == 400
    assert client.get("/api/v1/knowledge/terms", params={"q": ""}).status_code == 200
    # 控制字符嵌入正常词：清理后按正常词处理
    r = client.get("/api/v1/knowledge/terms", params={"q": "配\x01置权"})
    assert r.status_code == 200 and r.json()["data"]["total"] == 1


# ---------------------------------------------------------------------------
# L1SI175-A1-003：term 字段脱敏补齐（线上 term 含 ID 类 3 处漏网之修复验证）
# 种子复刻线上两行真实漏网形态，独立 fixture（不动共享 _seed 计数）
# ---------------------------------------------------------------------------

_TERM_DIRTY_ROWS = [
    ("T-010", "ID61 / ID64（里程碑编号）", "普通释义"),
    ("T-011", "ID27↔P-007+AC 映射补登记", "普通释义"),
]


@pytest.fixture()
def _seed_term_dirty():
    sm = get_sessionmaker()
    with sm.begin() as s:
        for tid, term, dfn in _TERM_DIRTY_ROWS:
            s.add(M.TermsRegistry(term_id=tid, term=term, definition=dfn,
                                  data_provenance="real"))
    yield
    with sm.begin() as s:
        for tid, *_ in _TERM_DIRTY_ROWS:
            s.query(M.TermsRegistry).filter(M.TermsRegistry.term_id == tid).delete()


def test_a1_003_anon_term_desensitized(_seed_term_dirty):
    """验收①②：匿名 term 与 def 五类编号全 0（term 也过脱敏）。"""
    import re as _re
    pat = _re.compile(r"\bT-\d{3}\b|TDCA-[A-Z0-9]+(?:-[A-Z0-9]+)*|\bNC-\d+\b|\bID\d+\b|\bFC-[A-Z0-9]+\b")
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200
    for row in r.json()["data"]["terms"]:
        assert not pat.search(row["term"]), f"term 漏网: {row['term']}"
        assert not pat.search(row["def"]), f"def 漏网: {row['term']}"
    terms = {i["term"] for i in r.json()["data"]["terms"]}
    assert "ID61 / ID64（里程碑编号）" not in terms
    # 脱敏占位形态在册
    dirty = [i for i in r.json()["data"]["terms"] if "里程碑" in i["term"]]
    assert dirty and "〔内部编号〕" in dirty[0]["term"]


def test_a1_003_login_term_original(_seed_term_dirty):
    """验收⑤/S-2：登录面 term 仍原文（含编号），行为不变。"""
    r = client.get("/api/v1/knowledge/terms", headers=_auth())
    items = {i["id"]: i for i in r.json()["data"]["terms"]}
    assert items["T-010"]["term"] == "ID61 / ID64（里程碑编号）"
    assert items["T-011"]["term"] == "ID27↔P-007+AC 映射补登记"


def test_a1_003_anon_search_term_dirty_still_hits(_seed_term_dirty):
    """匿名按普通词检索命中编号词名时，返回的 term 已脱敏。"""
    r = client.get("/api/v1/knowledge/terms?q=里程碑")
    assert r.status_code == 200
    items = r.json()["data"]["terms"]
    assert len(items) == 1
    assert "ID61" not in items[0]["term"] and "〔内部编号〕" in items[0]["term"]


# ---------------------------------------------------------------------------
# L1SI175-A1-AMEND-2：脱敏口径五类扩七类（补 P- 编号族与 S-/A- 条款位）
# 源数据实测枚举（令面硬规矩）：P- 5 处（term 1 / def 4），A-/S- 4 处（def 4）
# ---------------------------------------------------------------------------

# 七类全正则（与 api_v1._TERMS_SENSITIVE 同口径，独立书写防实现漂移）
_PAT_7 = re.compile(
    r"\bT-\d{3}\b|TDCA-[A-Z0-9]+(?:-[A-Z0-9]+)*|\bNC-\d+\b|\bID\d+\b|\bFC-[A-Z0-9]+\b"
    r"|\bP-\d{2,4}\b|\b(?:S|A)-\d{1,3}\b")

_P_ROWS = [("T-012", "P-编号词", "涉及 P-007 与 P-070 的编译器角色与批判对象"),
           ("T-013", "条款位词", "可经迁移／解构（A-8）；越级（A-11／A-12）")]


@pytest.fixture()
def _seed_p_sa():
    sm = get_sessionmaker()
    with sm.begin() as s:
        for tid, term, dfn in _P_ROWS:
            s.add(M.TermsRegistry(term_id=tid, term=term, definition=dfn,
                                  data_provenance="real"))
    yield
    with sm.begin() as s:
        for tid, *_ in _P_ROWS:
            s.query(M.TermsRegistry).filter(M.TermsRegistry.term_id == tid).delete()


def test_amend2_anon_seven_class_zero(_seed_p_sa):
    """验收①②：匿名 term+def 七类计数全 0（原五类保持 0）。"""
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200
    tc = dc = 0
    for row in r.json()["data"]["terms"]:
        tc += len(_PAT_7.findall(row["term"]))
        dc += len(_PAT_7.findall(row["def"]))
    assert tc == 0 and dc == 0, f"term={tc} def={dc}"
    # P- 种子脱敏形态在册
    p_row = [i for i in r.json()["data"]["terms"] if i["term"] == "P-编号词"]
    assert p_row and "P-007" not in p_row[0]["def"] and "〔内部编号〕" in p_row[0]["def"]
    sa_row = [i for i in r.json()["data"]["terms"] if i["term"] == "条款位词"]
    assert sa_row and "A-8" not in sa_row[0]["def"]


def test_amend2_q_probes_include_p(_seed):
    """验收③：q 拦截随扩类同步——P-007／P-070 匿名亦 400（侧信道不复活）。"""
    for probe in ["P-007", "P-070"]:
        r = client.get("/api/v1/knowledge/terms", params={"q": probe})
        assert r.status_code == 400, f"{probe} → {r.status_code}"
        assert "内部编号" in r.json()["detail"]
    # 正常词不受扩类影响
    assert client.get("/api/v1/knowledge/terms?q=配置权").status_code == 200


def test_amend2_login_original_kept(_seed_p_sa):
    """验收④：登录面仍原文（抽样 P-007 行）。"""
    r = client.get("/api/v1/knowledge/terms", headers=_auth())
    items = {i["id"]: i for i in r.json()["data"]["terms"]}
    assert "P-007" in items["T-012"]["def"] and "P-070" in items["T-012"]["def"]
    assert "A-8" in items["T-013"]["def"]


def test_amend2_no_collateral_on_seed_corpus():
    """S-1 误伤自查：既有种子语料（conftest 预种 8 行）七类正则零命中——
    即扩类对存量正常词零误脱；线上全量误伤清单以部署后 diff 为准。"""
    r = client.get("/api/v1/knowledge/terms")
    assert r.status_code == 200
    hits = []
    for row in r.json()["data"]["terms"]:
        for m in _PAT_7.findall(row["term"]) + _PAT_7.findall(row["def"]):
            hits.append((row["term"], m))
    assert not hits, f"存量误伤: {hits}"
