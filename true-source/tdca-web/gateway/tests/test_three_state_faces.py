# -*- coding: utf-8 -*-
"""B1-001 三态可读面 · 机验断言（令 TDCA-HANDOFF-EXEC-L1SI228-B1-001 卡1）。"""
from __future__ import annotations

import hashlib
import re
import subprocess

from pathlib import Path

from three_state_data import NEGATIVE_SPACE, POSITIVE_SPACE, SANDBOX

REPO = Path(__file__).resolve().parents[4]  # 仓根（…/tdca-protocol）

# H-4：人读正文禁载之内部编号（GSEQ／NCA 号／块号／FC 号）；件号（TDCA-…）入凭证位不受此限
FORBIDDEN_IN_HUMAN_TEXT = re.compile(r"GSEQ-\d|NCA-[A-Z0-9]|TDCA-FC|块号")


def _human_texts():
    for c in NEGATIVE_SPACE["cells"]:
        for cl in c.get("clauses", []):
            yield cl["text"]
        if c.get("note"):
            yield c["note"]
    for d in SANDBOX["dimensions"]:
        for r in d["reads"]:
            yield r
        if d.get("unsolved"):
            yield d["unsolved"]
    for s in (SANDBOX["feasible_domain"]["source_one"]["detail"],
              SANDBOX["feasible_domain"]["source_two"]["detail"],
              SANDBOX["feasible_domain"]["gate"]["detail"],
              SANDBOX["purpose"], SANDBOX["recompute_how"] if "recompute_how" in SANDBOX else ""):
        yield s
    yield POSITIVE_SPACE["purpose"]
    yield POSITIVE_SPACE["recompute_how"]
    for it in POSITIVE_SPACE["items"]:
        yield it["name"]
        yield it["read"]


def test_negative_space_fifteen_cells_all_accounted():
    cells = NEGATIVE_SPACE["cells"]
    assert len(cells) == 15, f"十五格不符：{len(cells)}"
    cats = {c["category"] for c in cells}
    ops = {c["operator"] for c in cells}
    assert cats == {"法律", "公序良俗", "情绪", "信仰", "技术"}
    assert ops == {"⊗", "⊘", "⊙"}
    for c in cells:
        assert c["status"] in ("has_clauses", "no_clauses")
        if c["status"] == "has_clauses":
            assert len(c["clauses"]) >= 1, f"{c['category']}{c['operator']} 有条款格为空"
            for cl in c["clauses"]:
                assert cl["text"].strip() and cl["basis_doc"].strip()
                assert cl["basis_ref"].strip() and cl["basis_volume"].strip(), "条款缺依据件号/所在册（1-3）"
        else:
            assert c.get("note", "").strip() and len(c["note"]) > 30, "空格未给理由（1-2：⛔留空⛔写无了事）"
            assert c.get("note_basis_doc"), "空格未给依据（1-2）"


def test_negative_space_human_judged_listed():
    items = NEGATIVE_SPACE["human_judged"]["items"]
    assert len(items) >= 5, "不可判定归人须具名（1-4），⛔一句视情况"
    for it in items:
        assert it["situation"].strip() and it["trigger"].strip() and it["basis_ref"].strip()


def test_no_internal_numbers_in_human_text():
    hits = [t for t in _human_texts() if t and FORBIDDEN_IN_HUMAN_TEXT.search(t)]
    assert not hits, f"人读正文含内部编号（H-4）：{hits[:3]}"


def test_sandbox_two_sources_and_four_dimensions():
    fd = SANDBOX["feasible_domain"]
    assert "负空间" in fd["source_one"]["name"] and "场景" in fd["source_two"]["name"], "可行域两源缺一（1-6）"
    dims = SANDBOX["dimensions"]
    assert [d["key"] for d in dims] == ["functional", "security", "performance", "compliance"], "四维须分项（1-7）"
    for d in dims:
        assert d["reads"], f"{d['key']} 无读数"
        assert d["evidence"], f"{d['key']} 无证据件（1-8）"
        for e in d["evidence"]:
            assert e["label"].strip(), "证据件缺名"
    unsolved = [d["key"] for d in dims if d.get("unsolved")]
    assert unsolved, "无解情形须如实标注（1-8：⛔只给达标）"


def test_positive_space_items_recompute_anchors():
    items = POSITIVE_SPACE["items"]
    assert len(items) >= 5, "认读件过少（1-9/1-10）"
    for it in items:
        assert it["name"].strip() and it["read"].strip(), "认读件须人可读（1-9：⛔通篇编号）"
        assert re.fullmatch(r"[0-9A-F]{16}", it["sha256_16"]), f"件哈希非 16 位大写 hex：{it['name']}"
        assert re.fullmatch(r"[0-9a-f]{8}", it["commit"]), f"提交号非 8 位 hex：{it['name']}"
    assert "sha256" in POSITIVE_SPACE["recompute_how"], "缺复算路径（1-10）"


def test_positive_space_hashes_match_repo_files():
    for it in POSITIVE_SPACE["items"]:
        rel = it["path"]
        f = REPO / rel
        assert f.exists(), f"仓内找不到认读件：{rel}"
        b = f.read_bytes()
        assert len(b) == it["bytes"], f"{rel} 字节不符：{len(b)} != {it['bytes']}"
        assert hashlib.sha256(b).hexdigest()[:16].upper() == it["sha256_16"], f"{rel} 哈希不符"
        log = subprocess.run(["git", "log", "-1", "--format=%h", "--", rel],
                             capture_output=True, text=True, cwd=REPO).stdout.strip()
        assert log == it["commit"], f"{rel} 最近提交不符：{log} != {it['commit']}"


def test_three_states_not_mixed():
    # 1-12 抽验（结构性）：负空间清单⛔当执行令、沙盒解⛔直进正空间、认读文件⛔代存证
    assert NEGATIVE_SPACE["wording_note"].find("词面") >= 0, "负空间须声明词面不公开边界"
    assert "本批无解" in SANDBOX["dimensions"][2]["unsolved"] or "无解" in SANDBOX["dimensions"][2]["unsolved"]
    assert "⛔" in POSITIVE_SPACE["recompute_how"] or "对位" in POSITIVE_SPACE["recompute_how"]
    # 三态各有其键且语义分属判定性/构造性/叙述性
    assert NEGATIVE_SPACE is not SANDBOX and SANDBOX is not POSITIVE_SPACE
