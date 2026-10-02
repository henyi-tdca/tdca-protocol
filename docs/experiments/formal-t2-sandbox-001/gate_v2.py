"""TDCA 沙盒实验 T3 · 支三闸门第二实现（gate_v2.py · 判据表驱动＋位掩码）

T3 口径：与 gate.py 语义等价、书写不同。
- gate.py ＝ 分段 if 链早退式书写；本件＝ 判据表驱动（检查项为表行）＋位掩码累积＋按位解码。
- 语义逐条照在册，不夹带新语义：检查项 G1–G5、理由码文案、解码顺序与 gate.py 完全一致
  （解码顺序即 gate.py 之理由产生顺序：G1 → G3 → G2 → G5 → G4 子串表序 → G4 断言性
  「绝对安全」→ G4 外稿井号编号 → G4 SIMULATED 标缺失）。
- 位掩码仅为内部表示；对外输出 (verdict, reasons) 与第一实现逐字节同级一致。
"""

import hashlib
import re

BANNED_SUBSTRINGS = ["制度有效", "制度已生效", "已正式生效", "真实世界效果", "真实世界已验证"]
BANNED_AFFIRMATIVE_ABSOLUTE_SAFETY = re.compile(r"(?<!不标)绝对安全")
BANNED_EXTERNAL_HASH_NUMBER = re.compile(r"#[0-9]+")
JOB_PATTERN = re.compile(r"（([0-9]+) jobs／EXIT=([0-9]+)／sorry=([0-9]+)）")

# 位分配（解码按此表之行序，与 gate.py 理由产生顺序一致）
BIT_G1 = 1 << 0
BIT_G3_NOT_GREEN = 1 << 1
BIT_G3_CHAIN = 1 << 2
BIT_G2_MISSING = 1 << 3
BIT_G2_BLOB = 1 << 4
BIT_G5 = 1 << 5
BIT_G4_ABS = 1 << 6   # 断言性「绝对安全」
BIT_G4_EXT = 1 << 7   # 外稿井号编号
BIT_G4_SIM = 1 << 8   # SIMULATED 标缺失
# G4 子串禁用措辞之位自 1<<9 起按表序动态分配（多项可并置）
G4_TERM_BASE = 1 << 9


def git_blob_sha1(content_bytes: bytes) -> str:
    header = f"blob {len(content_bytes)}".encode("utf-8") + b"\x00"
    return hashlib.sha1(header + content_bytes).hexdigest()


def parse_registry_rows(matrix_text: str) -> dict:
    rows = {}
    for line in matrix_text.splitlines():
        line = line.strip()
        if not line or not re.match(r"^C-[0-9SIM-]", line):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        row_id, claim, file_field, verify_field = parts[0], parts[1], parts[2], parts[3]
        m = JOB_PATTERN.search(verify_field)
        rows[row_id] = {
            "claim": claim,
            "file": file_field,
            "jobs": int(m.group(1)) if m else None,
            "exit": int(m.group(2)) if m else None,
            "sorry": int(m.group(3)) if m else None,
        }
    return rows


def _check_table(ctx):
    """判据表：每行 (bit, predicate)。predicate 返回 True 即该位失守。
    表驱动——逐行求值、位掩码累积，无早退。"""
    bundle, row, head_sha, file_reader = ctx["bundle"], ctx["row"], ctx["head_sha"], ctx["file_reader"]
    ev = bundle.get("evidence") or {}
    b = ev.get("build") or {}
    path = ev.get("file")
    content = file_reader(path) if path else None
    text = bundle.get("narrative") or ""

    rows = []
    # G1 登记
    rows.append((BIT_G1, lambda: row is None))
    # G3 机验绿（登记行在场时对照；登记缺失时 G1 已失守，G3/G2/G5 各位不另立——
    # 与 gate.py 相同：其 if/else 链在 row is None 时跳过此三组检查）
    rows.append((BIT_G3_NOT_GREEN,
                 lambda: row is not None and not (b.get("exit") == 0 and b.get("sorry") == 0)))
    rows.append((BIT_G3_CHAIN,
                 lambda: row is not None and (b.get("exit") == 0 and b.get("sorry") == 0)
                 and not (b.get("jobs") == row["jobs"] and row["exit"] == 0 and row["sorry"] == 0)))
    rows.append((BIT_G2_MISSING, lambda: row is not None and content is None))
    rows.append((BIT_G2_BLOB,
                 lambda: row is not None and content is not None
                 and git_blob_sha1(content) != ev.get("blob")))
    rows.append((BIT_G5,
                 lambda: row is not None and ev.get("parent_commit") != head_sha))
    # G4 叙事合规（恒检）
    for i, t in enumerate(BANNED_SUBSTRINGS):
        rows.append((G4_TERM_BASE << i, (lambda term: (lambda: term in text))(t)))
    rows.append((BIT_G4_ABS, lambda: bool(BANNED_AFFIRMATIVE_ABSOLUTE_SAFETY.search(text))))
    rows.append((BIT_G4_EXT, lambda: bool(BANNED_EXTERNAL_HASH_NUMBER.search(text))))
    rows.append((BIT_G4_SIM,
                 lambda: bundle.get("data_origin") == "SYNTHETIC" and "SIMULATED" not in text))
    return rows


def _decode(mask, banned_substrings=None):
    """按位解码为理由码列表（顺序＝gate.py 理由产生顺序）。"""
    bs = banned_substrings if banned_substrings is not None else BANNED_SUBSTRINGS
    reasons = []
    if mask & BIT_G1:
        reasons.append("G1_UNREGISTERED")
    if mask & BIT_G3_NOT_GREEN:
        reasons.append("G3_BUILD_NOT_GREEN")
    if mask & BIT_G3_CHAIN:
        reasons.append("G3_JOB_CHAIN_MISMATCH")
    if mask & BIT_G2_MISSING:
        reasons.append("G2_FILE_MISSING")
    if mask & BIT_G2_BLOB:
        reasons.append("G2_BLOB_MISMATCH")
    if mask & BIT_G5:
        reasons.append("G5_PARENT_NOT_HEAD")
    for i, t in enumerate(bs):
        if mask & (G4_TERM_BASE << i):
            reasons.append(f"G4_BANNED_TERM:{t}")
    if mask & BIT_G4_ABS:
        reasons.append("G4_BANNED_TERM:绝对安全(断言性)")
    if mask & BIT_G4_EXT:
        reasons.append("G4_EXTERNAL_HASH_NUMBER")
    if mask & BIT_G4_SIM:
        reasons.append("G4_SIMULATED_LABEL_MISSING")
    return reasons


def gate(bundle: dict, registry_rows: dict, head_sha: str,
         file_reader, banned_substrings=None) -> tuple:
    """第二实现对外契约与 gate.gate 完全一致：(verdict, reasons)。"""
    row = registry_rows.get(bundle.get("claim_id"))
    ctx = {"bundle": bundle, "row": row, "head_sha": head_sha, "file_reader": file_reader}
    mask = 0
    for bit, predicate in _check_table(ctx):
        if predicate():
            mask |= bit
    reasons = _decode(mask, banned_substrings)
    verdict = "BLOCK" if reasons else "ALLOW"
    return verdict, reasons
