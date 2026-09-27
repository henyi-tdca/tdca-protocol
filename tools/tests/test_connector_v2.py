# -*- coding: utf-8 -*-
"""connector-v2 测试套件（B1 测试补缺：cop_connector / adapter_matcher）

被测行为清单（先清单后用例）：
  adapter_matcher.py
    A-1 tokenize：标点归空白；仅留 ≥2 字且非纯数字/百分号/时间样式的词
    A-2 match_clause：仅收录「关键词命中或余弦 >0」的原理；得分 = 0.6·命中率 + 0.4·余弦
    A-3 match_clause：结果按得分降序；top_k 截断；每条含 id/name/score/hit（hit 排序）
    A-4 边界：空条款 → 空结果
  cop_connector.py
    C-1 tokenize：停用词剔除；<2 字剔除；纯数字/符号剔除
    C-2 load_cops：仅收录含 soul 的合法 YAML dict；坏件/无 soul 件跳过；四维特征提取正确
    C-3 compute_u0：未验证 → 0.0；质量分公式 = 0.5 + 0.15·min(prims,4) + 0.1·min(dec,4) + 0.2·nca，封顶 1.0
    C-4 match：A = 0.5·cos(soul)+0.3·cos(prim)+0.2·cos(dec)；负空间 ≥3 字命中 → A 减半；<3 字不触发
    C-5 match：空 COP 集 → 空结果；按 (-U,-A) 排序；top_k 截断
    C-6 _resolve_cop_dir：TDCA_WS bogus → exit 2 明示；未设置 → 仓内相对探测可导入
"""
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

CONNECTOR_DIR = Path(__file__).resolve().parent.parent / "connector-v2"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, CONNECTOR_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


am = _load("adapter_matcher")
cc = _load("cop_connector")


# ---------- adapter_matcher ----------

def test_am_tokenize_filters():
    toks = am.tokenize("熔断，限制 A1 99% 的权限")
    assert "熔断" in toks and "限制" in toks
    assert not any(t.isdigit() or t.endswith("%") for t in toks)
    assert all(len(t) >= 2 for t in toks)


def test_am_match_clause_structure_and_order():
    res = am.match_clause("最小权限：仅授予最低权限，分级授权", top_k=5)
    assert 0 < len(res) <= 5
    scores = [r["score"] for r in res]
    assert scores == sorted(scores, reverse=True)
    for r in res:
        assert set(r) >= {"id", "name", "score", "hit"}
        assert r["id"] in am.PRINCIPLES
        assert r["hit"] == sorted(r["hit"])
    ids = [r["id"] for r in res]
    assert "ID76" in ids  # 配置权第三极：权限/授权关键词


def test_am_topk_truncation():
    res = am.match_clause("制度 技术 同构 映射 对齐 化合 熔断 禁止", top_k=2)
    assert len(res) == 2


def test_am_empty_clause():
    assert am.match_clause("") == []
    assert am.match_clause("，。、") == []


# ---------- cop_connector ----------

def test_cc_tokenize_filters():
    toks = cc.tokenize("的 是 一个 99% 的协作")
    assert "的" not in toks and "是" not in toks  # 停用词按整词剔除
    assert not any(len(t) < 2 for t in toks)
    assert not any(t.isdigit() for t in toks)  # 纯数字剔除（含 % 的 n-gram 夹带字，按设计保留）


def _cop(tmp_path, name, *, soul=True, validated=True, neg=None, n_prims=1, n_dec=1, nca=True):
    d = {"COP-ID": name, "validation": {"passed": validated}}
    if soul:
        d["soul"] = {"identity": f"{name}身份", "core": "正和涌现", "role": "r", "category": "测试类"}
    d["primitives"] = [{"method": "协作调度", "precond": "p", "postcond": "q",
                        "nca_emit": nca} for _ in range(n_prims)]
    d["decision"] = [{"if": "协作", "call": "f"} for _ in range(n_dec)]
    d["negative_space"] = neg or []
    p = tmp_path / f"{name}.yaml"
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    return p


def test_cc_load_cops_skips_bad_and_extracts(tmp_path):
    _cop(tmp_path, "GOOD", neg=["数据泄露"])
    (tmp_path / "nosoul.yaml").write_text(yaml.safe_dump({"COP-ID": "X"}), encoding="utf-8")
    (tmp_path / "broken.yaml").write_text("::not yaml::", encoding="utf-8")
    cops = cc.load_cops(str(tmp_path))
    assert len(cops) == 1
    c = cops[0]
    assert c["cop_id"] == "GOOD" and c["validated"] is True
    assert c["n_prims"] == 1 and c["n_dec"] == 1 and c["nca_emit"] is True
    assert "数据泄露" in c["negative_terms"]
    assert isinstance(c["soul_vec"], Counter) and c["soul_vec"]


def test_cc_compute_u0_branches():
    assert cc.compute_u0({"validated": False, "n_prims": 4, "n_dec": 4, "nca_emit": True}) == 0.0
    assert cc.compute_u0({"validated": True, "n_prims": 0, "n_dec": 0, "nca_emit": False}) == 0.6
    assert cc.compute_u0({"validated": True, "n_prims": 4, "n_dec": 4, "nca_emit": True}) == 1.0


def _mk_cop(neg=None):
    return {
        "cop_id": "T1", "identity": "协作调度身份", "category": "测试类", "core": "正和涌现",
        "soul_vec": Counter({"协作调度": 2, "正和": 1}),
        "prim_vec": Counter({"协作调度": 1}),
        "decision_vec": Counter({"协作": 1}),
        "negative_terms": set(neg or []),
        "validated": True, "n_prims": 1, "n_dec": 1, "nca_emit": True,
    }


def test_cc_match_negative_space_halves_A():
    scene = "协作调度 正和 协作"
    cop = _mk_cop()
    base = cc.match(scene, [cop], top_k=1)[0]["A"]
    cop_neg = _mk_cop(neg=["协作调度"])  # ≥3 字命中 → A 减半
    lowered = cc.match(scene, [cop_neg], top_k=1)[0]["A"]
    assert lowered == pytest.approx(base * 0.5, abs=1e-3)  # A 四舍五入到 4 位小数


def test_cc_match_short_neg_ignored():
    scene = "协作调度 正和 协作"
    cop = _mk_cop(neg=["协作"])  # 仅 2 字 → 不触发反向
    r = cc.match(scene, [cop], top_k=1)[0]
    cop0 = _mk_cop()
    assert r["A"] == cc.match(scene, [cop0], top_k=1)[0]["A"]


def test_cc_match_empty_and_sort():
    assert cc.match("任何场景", [], top_k=5) == []
    cops = [_mk_cop(), dict(_mk_cop(), cop_id="T2", soul_vec=Counter(), prim_vec=Counter(), decision_vec=Counter())]
    res = cc.match("协作调度", cops, top_k=5)
    # T1 余弦 >0（U>0）；T2 全零向量（U=0）→ (-U,-A) 降序 T1 在前
    assert [r["cop_id"] for r in res] == ["T1", "T2"]
    assert len(res) == 2


# ---------- 路径解析（子进程实测，不依赖外部服务） ----------

def test_cc_resolve_bogus_tdca_ws_exits_2():
    r = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('m', r'%s'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)" % (CONNECTOR_DIR / 'cop_connector.py').as_posix()],
        env={"TDCA_WS": "C:/__nonexistent__ws__", "PYTHONIOENCODING": "utf-8",
             "PATH": __import__("os").environ.get("PATH", "")},
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 2
    assert "不静默空跑" in r.stderr


def test_cc_import_resolves_repo_corpus():
    r = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('m', r'%s'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.load_cops(str(m.COP_DIR))))" % (CONNECTOR_DIR / 'cop_connector.py').as_posix()],
        env={"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ.get("PATH", "")},
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0
    assert int(r.stdout.strip().splitlines()[-1]) > 0
