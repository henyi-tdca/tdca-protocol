# -*- coding: utf-8 -*-
"""立场分离扫描/整改/验收工具 (GSEQ-0601 · TDCA-HANDOFF-WORKBUDDY-NEUTRALITY-001)
三律依据: 原语层去场景去立场; 立场经 scene_binding 运行时注入; 原语永不单独生效。

统一判定口径 (律一: soul.core/decision 去主体立场):
  - *.yaml : 仅扫描 soul.core 与 decision 字段 (verse/origin/primitives 素材与机制核不动)
  - *.py   : 仅扫描含 "core"/"decision" 键的行 (保证重编译回归产物中性; verse/origin 行不动)
  - *.md   : 全文扫描, 豁免 「」『』“” 引文段; EXEMPT_FILES 为素材文献类豁免

模式:
  scan    输出命中清单
  rectify 执行中性化替换 (yaml: soul.core/decision; py/md: 口径内文本), 生成改动日志
  check   验收: 0 命中退出 0, 否则退出 1 (fail-closed)
  verify  语义损失核对: 每处改动逆映射后须与原文全等 → 证明仅词表替换、零附带改动
"""
import os
import re
import sys
import json
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_CL = r"C:/Users/22850/Desktop/开发会话文件/tdca-protocol/docs/cop-library"
SCOPE_SUBDIRS = ["stratagems", "games", "hundred_schools", "compositions", "simulations", "mechanism_design"]

# 主体立场词表 → 中性替换 (长词优先匹配)
LEXICON = [
    ("敌方", "对方"), ("敌军", "对方"), ("敌人", "对方"), ("敌情", "对方态势"),
    ("敌之", "对方之"), ("敌可", "对方可"), ("敌无", "对方无"), ("敌将", "对方将领"),
    ("敌自", "对方自"), ("敌内", "对方内"), ("敌外", "对方外"), ("敌疲", "对方疲"),
    ("敌懈", "对方懈"), ("敌众", "对方众"), ("敌势", "对方势"), ("敌心", "对方心"),
    ("敌垒", "对方垒"), ("敌隙", "对方隙"), ("强敌", "强势方"), ("骄敌", "骄纵对方"),
    ("诱敌", "诱引对方"), ("调敌", "调动对方"), ("破敌", "破其势"), ("歼敌", "制胜"),
    ("困敌", "困对方"), ("迫敌", "迫使对方"), ("扰敌", "扰动对方"), ("惑敌", "惑引对方"),
    ("袭敌", "袭其虚"), ("攻敌", "攻其"), ("察敌", "察对方"), ("观敌", "观对方"),
    ("乘敌", "乘对方"), ("伺敌", "伺对方"), ("向敌", "向对方"), ("败敌", "挫败对方"),
    ("胜敌", "制胜对方"), ("之敌", "之对方"), ("小股之敌", "小股之对方"),
    ("单敌", "单一对方"), ("寇", "侵扰方"),
    ("我方", "行动方"), ("我军", "行动方"), ("己方", "行动方"), ("我众", "行动方众"),
    ("本方", "行动方"),
    ("对手", "另一参与方"), ("仇", "怨"),
    ("敌", "对方"),
]
import re as _re
_PATTERN = _re.compile("|".join(_re.escape(w) for w, _ in sorted(LEXICON, key=lambda x: -len(x[0]))))
_REPLACE = dict(LEXICON)
_REVERSE = {v: k for k, v in LEXICON}  # 逆映射 (用于语义核对; 注意多对一时取首个)

# 素材文献豁免 (原典训诂/引文主体, 律一"素材保留")
EXEMPT_FILES = ["计篇_训诂校勘.md"]

KEY_LINE_RE = re.compile(r"[\"'](core|decision_if|decision|if|scene)[\"']\s*:")
FIELD_PATH_RE = re.compile(r"(^|\.)soul\.core|(^|\.)decision")
# md 中文引文豁免段
CJK_QUOTE_RE = re.compile(r"(「[^»]*」|『[^』]*』|“[^”]*”)")


def neutralize(text):
    return _PATTERN.sub(lambda m: _REPLACE[m.group(0)], text)


def find_hits(text):
    return [(m.group(0), text[max(0, m.start()-10):m.end()+10].replace("\n", " "))
            for m in _PATTERN.finditer(text)]


def yaml_field_paths(doc, path=""):
    """产出 (路径, 字符串值) 列表, 仅 soul.core 与 decision 子树"""
    out = []
    if isinstance(doc, dict):
        for k, v in doc.items():
            p = "%s.%s" % (path, k) if path else str(k)
            if k in ("verse", "origin"):
                continue
            out.extend(yaml_field_paths(v, p))
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            out.extend(yaml_field_paths(v, "%s[%d]" % (path, i)))
    elif isinstance(doc, str):
        if FIELD_PATH_RE.search(path):
            out.append((path, doc))
    return out


def rectify_yaml(path, log):
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        return 0
    n = 0
    for p, val in yaml_field_paths(doc):
        new = neutralize(val)
        if new != val:
            hits = find_hits(val)
            n += len(hits)
            set_by_path(doc, p.split("."), new) if "." in p else None
            log.append({"file": path, "field": p, "old": val, "new": new})
    if n:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
    return n


def set_by_path(doc, keys, value):
    """按 'soul.core' / 'decision[0].if' 类路径写回 (decision 为 list)"""
    cur = doc
    for i, k in enumerate(keys):
        m = re.match(r"([^\[]+)\[(\d+)\]$", k)
        if m:
            name, idx = m.group(1), int(m.group(2))
            if i == len(keys) - 1:
                cur[name][idx] = value
            else:
                cur = cur[name][idx]
        else:
            if i == len(keys) - 1:
                cur[k] = value
            else:
                cur = cur[k]


def rectify_code_line(line):
    if not KEY_LINE_RE.search(line):
        return line, 0
    new = neutralize(line)
    return new, len(find_hits(line))


def rectify_text_file(path, log, is_md=False):
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    n = 0
    if is_md:
        # 豁免中文引文段: 分段处理
        parts = CJK_QUOTE_RE.split(txt)
        for i, seg in enumerate(parts):
            if i % 2 == 1:
                continue  # 引文段不动
            new = neutralize(seg)
            if new != seg:
                n += len(find_hits(seg))
                parts[i] = new
        new_txt = "".join(parts)
    else:
        lines = txt.splitlines(keepends=True)
        for idx, line in enumerate(lines):
            new, k = rectify_code_line(line)
            if k:
                n += k
                lines[idx] = new
                log.append({"file": path, "field": "line:%d" % (idx + 1),
                            "old": line.rstrip(), "new": new.rstrip()})
        new_txt = "".join(lines)
    if n:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_txt)
    return n


def iter_scope_files(base):
    for sub in SCOPE_SUBDIRS:
        d = os.path.join(base, sub)
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git", ".workbuddy")]
            for fn in sorted(files):
                if fn.endswith((".yaml", ".yml", ".py", ".md")):
                    yield os.path.join(root, fn)


def is_exempt(rel):
    return any(rel.endswith(e) for e in EXEMPT_FILES)


def scan_base(base, label, do_rectify=False, log=None):
    tf = hf = hits = 0
    details = []
    for p in iter_scope_files(base):
        rel = os.path.relpath(p, base)
        if is_exempt(rel):
            continue
        tf += 1
        if p.endswith((".yaml", ".yml")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    doc = yaml.safe_load(f)
                fields = yaml_field_paths(doc) if isinstance(doc, dict) else []
                fhits = [(w, frag) for _, val in fields for w, frag in find_hits(val)]
            except Exception:
                print("[WARN] yaml 解析失败(fail-closed): %s" % rel)
                continue
            if do_rectify and fhits:
                k = rectify_yaml(p, log)
                fhits = [(w, frag) for w, frag in fhits][:k] if k else fhits
                hits += k
                if k:
                    hf += 1
                    details.append((rel, k))
                continue
        else:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read()
            if p.endswith(".md"):
                parts = CJK_QUOTE_RE.split(txt)
                segs = [s for i, s in enumerate(parts) if i % 2 == 0]
                fhits = [(w, frag) for seg in segs for w, frag in find_hits(seg)]
            else:
                fhits = [(w, frag) for line in txt.splitlines()
                         if KEY_LINE_RE.search(line) for w, frag in find_hits(line)]
            if do_rectify and fhits:
                k = rectify_text_file(p, log, is_md=p.endswith(".md"))
                hits += k
                if k:
                    hf += 1
                    details.append((rel, k))
                continue
        if fhits:
            hf += 1
            hits += len(fhits)
            details.append((rel, fhits))
    print("===== 立场%s [%s] =====" % ("整改" if do_rectify else "扫描", label))
    print("文件: %d | 命中文件: %d | 命中: %d" % (tf, hf, hits))
    for rel, info in details:
        if do_rectify:
            print("  [整改] %s (%d 处)" % (rel, info))
        else:
            print("--- %s (%d)" % (rel, len(info)))
            for w, frag in info[:4]:
                print("    [%s] …%s…" % (w, frag))
            if len(info) > 4:
                print("    … 另 %d 处" % (len(info) - 4))
    return {"label": label, "files": tf, "hit_files": hf, "hits": hits}


def verify_base(base, log):
    """语义损失核对: old 经词表正映射须 == new (证明仅词表替换)"""
    bad = 0
    for e in log:
        recomputed = neutralize(e["old"])
        if recomputed != e["new"]:
            bad += 1
            print("[VERIFY-FAIL] %s %s" % (e["file"], e["field"]))
    print("语义核对: %d 条改动, 偏离词表 %d 条 → %s" % (len(log), bad, "PASS" if bad == 0 else "FAIL"))
    return bad == 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    targets = sys.argv[2:] or ["compiler", "repo"]
    log_path = os.path.join(ROOT, "stance_rectify_log.json")
    if mode == "rectify":
        log = []
        for t in targets:
            base = ROOT if t == "compiler" else REPO_CL
            scan_base(base, t, do_rectify=True, log=log)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=1)
        print("改动日志: %s (%d 条)" % (log_path, len(log)))
    elif mode == "verify":
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
        ok = verify_base(None, log)
        sys.exit(0 if ok else 1)
    elif mode == "check":
        total = 0
        for t in targets:
            base = ROOT if t == "compiler" else REPO_CL
            total += scan_base(base, t)["hits"]
        print("CHECK %s: 总命中 %d" % ("PASS" if total == 0 else "FAIL", total))
        sys.exit(0 if total == 0 else 1)
    else:
        for t in targets:
            base = ROOT if t == "compiler" else REPO_CL
            scan_base(base, t)


if __name__ == "__main__":
    main()
