# -*- coding: utf-8 -*-
"""DUALCH-021 双通道等价对照接口测试（四例必绿）。

令面四例：
① 匿名 GET /api/v1/dual-channel ⟹ 200·JSON 数组·十二功能域（J-1）；
② 五字段全非空（J-2）＋必填二字段（updated_at／institution_ref）＋等价型 ∈ 甲乙丙；
③ 丙型（运维手册）单测：machine_path＝none＋单侧理由非空＋显式「仅人」；
④ 人视读数字段零内部编号（GSEQ-／NCA-／TDCA-工作件号不入 human 面字段；件号只许在 institution_ref）。
"""
import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

_REQUIRED = ("human_path", "machine_path", "shared_backend",
             "equivalence_type", "single_side_reason")
# 人视读数字段（页面可渲染列）—— institution_ref 为机读字段，不在此列
_HUMAN_FIELDS = ("domain", "human_path", "machine_path", "shared_backend",
                 "equivalence_type", "single_side_reason", "updated_at")
_INTERNAL_NO = re.compile(r"GSEQ-|NCA-\d|TDCA-工作件")


def _get():
    r = client.get("/api/v1/dual-channel")
    assert r.status_code == 200, r.text[:200]
    return r.json()


# ---- ① 匿名 200·JSON 数组·十二域 ----
def test_manifest_shape():
    data = _get()
    assert isinstance(data, list), "响应须为 JSON 数组（J-1）"
    assert len(data) == 12, f"条目数须＝十二功能域，实得 {len(data)}"


# ---- ② 五字段全非空＋等价型合法 ----
def test_required_fields_non_empty():
    data = _get()
    for i, e in enumerate(data):
        for f in _REQUIRED:
            assert e.get(f) not in (None, "", []), f"条目{i}（{e.get('domain')}）缺字段 {f}"
        assert e.get("updated_at"), f"条目{i}缺 updated_at"
        assert e.get("institution_ref"), f"条目{i}缺 institution_ref"
        assert e["equivalence_type"] in ("甲", "乙", "丙"), f"条目{i}等价型非法"
        if e["equivalence_type"] in ("甲", "乙"):
            assert e["single_side_reason"] == "n/a", f"条目{i}甲乙型理由须写 n/a"


# ---- ③ 丙型单测（运维手册：仅人·不造机读镜像） ----
def test_bing_single_side():
    data = _get()
    bing = [e for e in data if e["equivalence_type"] == "丙"]
    assert len(bing) == 1, f"丙型应恰一条（基线 SITEDEP 判据 4），实得 {len(bing)}"
    e = bing[0]
    assert e["domain"] == "运维手册"
    assert e["machine_path"] == "none"
    assert "仅人" in e["single_side_reason"]
    assert "不造公开机读镜像" in e["single_side_reason"] or "非公开机通道" in e["single_side_reason"]
    assert e["shared_backend"] is False


# ---- ④ 人视读数字段零内部编号 ----
def test_no_internal_numbers_in_human_fields():
    data = _get()
    for e in data:
        for f in _HUMAN_FIELDS:
            v = e.get(f)
            if isinstance(v, str):
                assert not _INTERNAL_NO.search(v), f"{e['domain']}.{f} 含内部编号：{v[:60]}"
