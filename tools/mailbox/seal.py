# -*- coding: utf-8 -*-
# FC-ID: ENG4-MAILBOX-001 | 信箱协议形态归一（TDCA-HANDOFF-EXEC-L1SI197-ENG4-001 块6）
"""信箱工具族统一库（形态归一：统一入口 tools/mailbox + 统一参数 + 断言集 + 三态自测）。

归一口径
--------
* 统一入口：`python -m tools.mailbox.mailbox <action>`（seal / check / box / selftest）。
* 统一参数：`--mailbox-root`（env `TDCA_MAILBOX_ROOT`）、`--box`、`--file`、
  `--external`、`--require-mail`、`--verbose`。
* 断言集（box 级，四组）：件数 A1／旁注 A2／状态机 A3／四零立 Z1~Z4。
* 三态自测：`selftest` 以夹具跑 正常态／异常态／边界态，不指向真实信箱。

来源与纪律
----------
* 机验判据 C-01/C-02/C-03/C-04/C-05/C-13/C-18 移植自 `_deliver_seal_v1.py`
  （TOOL-SEAL-001 v1.2 口径，逐字保语义）；该件继续独立可用，本库为仓内归一形态。
* ⛔ 不改信箱内容与台账历史行；⛔ 不改信箱协议条例原文；⛔ 部署另句。
* 只施工不部署：本令（ENG4-001）仅落仓与自测，合并候放行令。
"""
from __future__ import annotations

import hashlib
import os
import re

ZERO = "sha256_16=0000000000000000"
FIELD_RE = re.compile(r"sha256_16=([0-9A-Za-z<]{0,64})")
HEX16_RE = re.compile(r"^[0-9A-F]{16}$")
NAME_MAX = 110

# 内部编号式样（仅 --external 时启用）
INTERNAL_ID = [
    ("GSEQ", re.compile(r"GSEQ-\d{3,}")),
    ("L1SI", re.compile(r"L1SI[-_]?\d{2,}", re.I)),
    ("NCA-日期", re.compile(r"NCA[-_]20\d{6}")),
    ("T-号", re.compile(r"\bT-\d{2,3}\b")),
    ("内部 ID", re.compile(r"\bID\d{1,3}\b")),
]

# C-18 终态字样（同行含否定语境者不计）
FINAL_TERMS = re.compile(r"(最终版|终态|定稿不再变|final\s+and\s+frozen)", re.I)
NEGATION = ("⛔", "不得", "不写", "禁止", "勿", "不许", "不应")

# 凭据八形态（只报计数，不回显命中内容）
CRED = [
    ("gitee/github 令牌前缀", re.compile(r"\b(?:ghp_|gho_|github_pat_)[A-Za-z0-9_]{10,}")),
    ("通用 sk 键", re.compile(r"\bsk-[A-Za-z0-9]{16,}")),
    ("云商访问键", re.compile(r"\bAKIA[0-9A-Z]{12,}")),
    ("私钥头", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Slack 令牌", re.compile(r"\bxox[bps]-[A-Za-z0-9-]{10,}")),
    ("JWT 三段", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("口令赋值", re.compile(r"(?i)\b(?:password|passwd|pwd|口令|密码)\s*[:=]\s*\S{6,}")),
    ("长十六进制串", re.compile(r"\b[0-9a-fA-F]{64}\b")),
]


def sha16(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()[:16]


def sha16_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()[:16]


def read_text(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    return raw, raw.decode("utf-8")


def zeroed_sha16(text: str, field_value: str) -> str:
    """零占位法：把首行该字段换成 16 个 0 后取整件哈希前 16 位。"""
    return hashlib.sha256(
        text.replace("sha256_16=" + field_value, ZERO).encode("utf-8")
    ).hexdigest().upper()[:16]


def first_line(text: str) -> str:
    return text.split("\n", 1)[0]


def is_mail(text: str) -> bool:
    return first_line(text).startswith("MAIL")


def check_one(path: str, external: bool = False, require_mail: bool = False):
    """单件机验（C-01~C-05/C-13/C-18）。返回 (状态条, 失败数)；条=(级别, 码, 说明)。"""
    out, fails = [], 0

    def add(level, code, msg):
        nonlocal fails
        out.append((level, code, msg))
        if level == "FAIL":
            fails += 1

    name = os.path.basename(path)
    if not os.path.exists(path):
        add("FAIL", "C-00", "件不存在")
        return out, fails

    add("PASS" if len(name) <= NAME_MAX else "FAIL", "C-02",
        f"件名 {len(name)} 字符" + ("" if len(name) <= NAME_MAX else f" 超 {NAME_MAX}"))

    raw, text = read_text(path)
    bom = raw.startswith(b"\xef\xbb\xbf")
    cr = b"\r" in raw
    add("PASS" if not bom and not cr else "FAIL", "C-03",
        ("UTF-8 无 BOM、LF" if not bom and not cr else
         f"编码/行尾不符（BOM={bom} CR={cr}）"))

    if not is_mail(text):
        add("SKIP", "C-01", "内部件（无 MAIL 首行），首行封签不适用")
        add("SKIP", "C-04", "内部件不投信箱，旁注不适用")
    else:
        m = FIELD_RE.search(first_line(text))
        val = m.group(1) if m else ""
        if not HEX16_RE.match(val):
            add("FAIL", "C-01", "首行 sha256_16 非 16 位大写十六进制")
        else:
            ok = zeroed_sha16(text, val) == val
            add("PASS" if ok else "FAIL", "C-01",
                "零占位法" + ("可复算" if ok else "复算不符"))
        side = path + ".sha256"
        if not os.path.exists(side):
            add("FAIL", "C-04", "缺旁注 .sha256")
        else:
            sv = open(side, "rb").read()
            s = sv.decode("utf-8", "replace").strip()
            real = sha16(path)
            ok = (len(sv) == 17 and s == real)
            add("PASS" if ok else "FAIL", "C-04",
                f"旁注 {len(sv)}B 值" + ("符" if s == real else f"不符（旁注 {s[:8]}… 实物 {real[:8]}…）"))

    if require_mail and not is_mail(text):
        add("FAIL", "C-05", "投递件首行须 MAIL 起首（现为非 MAIL）")

    hits = sum(len(rx.findall(text)) for _, rx in CRED)
    add("PASS" if hits == 0 else "FAIL", "C-13", f"凭据形态命中 {hits}")
    if external:
        idhits = sum(len(rx.findall(text)) for _, rx in INTERNAL_ID)
        add("PASS" if idhits == 0 else "FAIL", "C-13外", f"内部编号式样命中 {idhits}")

    fin = []
    for ln in text.split("\n"):
        if any(n in ln for n in NEGATION):
            continue
        for m in FINAL_TERMS.finditer(ln):
            pre = ln[max(0, m.start() - 2):m.start()]
            if not any(c in pre for c in ("无", "非", "没")):
                fin.append(ln.strip()[:40])
                break
    add("PASS" if not fin else "FAIL", "C-18",
        "无终态字样" if not fin else f"终态字样 {len(fin)} 行（如：{fin[0]}…）")
    return out, fails


def seal_one(path: str):
    """对未封签的投递件回填首行自哈希与旁注；幂等，不覆盖已符旁注。"""
    raw, text = read_text(path)
    first = first_line(text)
    if not first.startswith("MAIL"):
        return "SKIP", "内部件，不封签"
    m = FIELD_RE.search(first)
    val = m.group(1) if m else ""
    side = path + ".sha256"
    if HEX16_RE.match(val) and os.path.exists(side) and open(
            side, "rb").read().decode("utf-8", "replace").strip() == sha16(path):
        return "KEEP", "已封签且旁注符，未改动"
    if HEX16_RE.match(val) and os.path.exists(side):
        return "REFUSE", "已封签但旁注不符，须人工判定（不回改）"
    if not FIELD_RE.search(first):
        return "REFUSE", "首行无 sha256_16 字段，须人工补字段"
    base = text.replace("sha256_16=" + val, "sha256_16=" + "0" * 16)
    h0 = hashlib.sha256(base.encode("utf-8")).hexdigest().upper()[:16]
    with open(path, "wb") as f:
        f.write(base.replace(ZERO, "sha256_16=" + h0).encode("utf-8"))
    with open(side, "w", encoding="utf-8", newline="\n") as f:
        f.write(sha16(path) + "\n")
    return "SEALED", f"字段={h0} 旁注={sha16(path)}"


# ---------------- 状态机（A3） ----------------
ST_DRAFT = "DRAFT"          # MAIL 首行占位未封（全 0 或非十六进制）
ST_SEALED = "SEALED"        # 字段已回填且旁注符
ST_MISMATCH = "MISMATCH"    # 字段已回填但旁注缺/不符（REFUSE 态，须人工判定）
ST_INTERNAL = "INTERNAL"    # 非 MAIL 件（不入投递状态机）
ST_ORPHAN = "ORPHAN"        # 旁注无本体（孤儿）


def file_state(path: str) -> str:
    """单件状态机读数。件不存在的旁注由 box 断言以 ORPHAN 记。"""
    if not os.path.exists(path):
        return ST_ORPHAN
    _, text = read_text(path)
    if not is_mail(text):
        return ST_INTERNAL
    m = FIELD_RE.search(first_line(text))
    val = m.group(1) if m else ""
    sealed_field = bool(HEX16_RE.match(val))
    side = path + ".sha256"
    side_ok = os.path.exists(side) and open(
        side, "rb").read().decode("utf-8", "replace").strip() == sha16(path)
    if sealed_field and side_ok:
        return ST_SEALED
    if sealed_field and not side_ok:
        return ST_MISMATCH
    return ST_DRAFT
