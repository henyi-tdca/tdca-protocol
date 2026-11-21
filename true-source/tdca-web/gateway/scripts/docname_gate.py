# -*- coding: utf-8 -*-
"""docname_gate.py — 文档命名三步闸 + 第零步族级入册（DOCNAME-001 / L1SI225）

制度水印:
  FC-ID: TDCA-FC-OPS-INGEST-002 | 交办: TDCA-HANDOFF-EXEC-L1SI225-DOCNAME-001
  口径: 「访客能不能找到并读对这件」——会受影响的才是病（甲类硬拦），
        只是不漂亮的不是病（乙类不拦不改，靠显示名层收口）。
  硬要求: 三步任一不过即不入站（fail-closed），⛔先上后补、⛔人工放行；
        判定纯函数、可重跑、同件同结论（同输入必同输出，无随机无时钟）。

甲类五条（命中任一即拒）:
  A1 裸通用名——件名（路径末段 stem）仅 README/OPENING/OPENING-LEDGER/INDEX/
     CHANGELOG/LICENSE 等通用词，且族内相对路径无目录前缀（无前缀才无区分信息）。
  A2 含空格（半角或全角空白）。
  A3 件名（路径末段，含扩展名）> 80 字符。
  A4 含未定稿字样: DRAFT/TENTATIVE/待审/待签批/征求意见（⛔不含 V0.x 版本号）。
  A5 连续连字符 -- 或件名首尾连字符。

闸序（第⓿步先行，解「族未入册恒拒」死结）:
  ⓿ 族级入册: family 键须在 _PUBLIC_DOCS（值可为空件表＝空开族，不放任何件）；
     族未入册 ⟹ 拒收，判语必写「待族入册后重过」（⛔写「该文档不存在」）。
  ① 甲类机检（上五条，正则可判）。
  ② 白名单在册核对: 族内相对路径须在 _PUBLIC_DOCS[family] 件表内；
     族已入册但件未入表 ⟹ 仍拒（未在册不得进站）。
  ③ 显示名映射校验: 件若在 _DISPLAY_NAME，键必为在册件名（public_docs_ops
     导入期已断言），值不得含内部编号（T-/GSEQ-/ID）与未定稿字样（DRAFT/待审）。

用法（CLI，供重跑样例与巡检）:
  python3 docname_gate.py check <family> <族内相对路径>   # 单件判闸，打印 PASS/REJECT
  python3 docname_gate.py audit                            # 全白名单甲类巡检（只报不拦，
                                                           # 存量豁免由测试锁定清单）
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# A1 裸通用名集合（stem 大写匹配；含扩展名剥离）
_GENERIC_STEMS = frozenset({
    "README", "OPENING", "OPENING-LEDGER", "INDEX", "CHANGELOG", "LICENSE",
})

# 甲类判据（DOCNAME-001 §二，判据逐字取令面，⛔自增自减）
_A2 = re.compile(r"[ \t　]")  # 半角空格/制表或全角空白
_A3_MAX = 80                  # 件名（路径末段）字符上限
_A4 = re.compile(r"DRAFT|TENTATIVE|待审|待签批|征求意见")

# ingest 族名 → _PUBLIC_DOCS 族键（两处命名不同源，照实映射，⛔猜）
_FAMILY_ALIAS = {
    "whitepaper": "whitepapers",
    "paper": "papers",
}

# ③ 显示名映射值禁含（内部编号与未定稿字样，令面清单）
_DISPLAY_BANNED = ("T-", "GSEQ-", "ID", "DRAFT", "待审")


def classify_a(rel: str) -> list[str]:
    """甲类机检（①）：返回命中条号列表（空＝过）。rel＝族内相对路径（posix 形）。"""
    rel = rel.replace("\\", "/")
    last = rel.rsplit("/", 1)[-1]
    stem = last.rsplit(".", 1)[0] if "." in last else last
    hits: list[str] = []
    if stem.upper() in _GENERIC_STEMS and "/" not in rel:
        hits.append("A1")  # 裸通用名且无目录前缀区分
    if _A2.search(last):
        hits.append("A2")
    if len(last) > _A3_MAX:
        hits.append("A3")
    if _A4.search(last):
        hits.append("A4")
    if "--" in stem or stem.startswith("-") or stem.endswith("-"):
        hits.append("A5")
    return hits


def load_registry(gateway_dir: Path | None = None):
    """读同层 public_docs_ops.py 之 _PUBLIC_DOCS 与 _DISPLAY_NAME（ast 直取，不 import 服务代码）。
    任一缺失即 fail-closed 中止（闸不可用＝全拒，⛔裸放）。"""
    base = gateway_dir or Path(__file__).resolve().parent.parent
    src = (base / "public_docs_ops.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    docs = display = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            tid = getattr(node.targets[0], "id", "")
            if tid == "_PUBLIC_DOCS":
                docs = ast.literal_eval(node.value)
            elif tid == "_DISPLAY_NAME":
                display = ast.literal_eval(node.value)
    if docs is None:
        raise SystemExit("WHITELIST_UNAVAILABLE: _PUBLIC_DOCS 未找到，fail-closed 中止")
    return docs, (display or {})


def gate(family: str, rel: str, docs, display) -> tuple[str, str]:
    """三步闸＋第⓿步，纯函数。返回 (verdict, reason)：verdict ∈ {PASS, REJECT}；
    族未入册拒收判语固定「待族入册后重过」（令面语义，⛔写「该文档不存在」）。"""
    fam = _FAMILY_ALIAS.get(family, family)
    rel = rel.replace("\\", "/")
    hits = classify_a(rel)
    if hits:
        return ("REJECT", f"①甲类机检命中 {'+'.join(hits)}: {rel}")
    if fam not in docs:
        return ("REJECT", f"⓿族未入册（{fam}）：待族入册后重过")
    if rel not in docs[fam]:
        return ("REJECT", f"②未在册（族已入册但件未入表）：{fam}/{rel}")
    if rel in display:
        value = display[rel]
        bad = [b for b in _DISPLAY_BANNED if b in value]
        if bad:
            return ("REJECT", f"③显示名映射值含违禁字样 {bad}: {value}")
    return ("PASS", "")


def audit(docs) -> list[tuple[str, str, list[str]]]:
    """全白名单甲类巡检（只报不拦）：返回 (family, rel, hits) 三元组，hits 非空者为存量病件。"""
    rows = []
    for fam, names in docs.items():
        for name in names:
            hits = classify_a(name)
            if hits:
                rows.append((fam, name, hits))
    return rows


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[1] == "check":
        docs, display = load_registry()
        verdict, reason = gate(argv[2], argv[3], docs, display)
        print(f"{verdict} [{argv[2]}] {argv[3]}" + (f"  — {reason}" if reason else ""))
        return 0 if verdict == "PASS" else 2
    if len(argv) == 2 and argv[1] == "audit":
        docs, _ = load_registry()
        rows = audit(docs)
        print(f"audit: 甲类存量 {len(rows)} 件（只报不拦，豁免清单由测试锁定）")
        for fam, name, hits in rows:
            print(f"  {fam}/{name}  ->  {'+'.join(hits)}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
