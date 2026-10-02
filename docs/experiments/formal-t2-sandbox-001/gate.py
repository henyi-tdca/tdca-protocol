"""TDCA 沙盒实验 T2 · 支三闸门（被测对象）

定位句（照在册）：加载核心是入场券，沙盒验证是合格证，没有合格证不能出盒；
沙盒＝宪法法院，非测试环境。

判定之问：无叙事不经数据升入正空间。
闸门语义：fail-closed —— 任一检查不过即 BLOCK（不得先升格后补）。
退出语义不在本件；本件只给 (verdict, reasons)。

检查项（G1–G5，合取语义）：
  G1 登记：claim_id 在登记簿（在册 CLAIMS-MATRIX 或实验合成夹具）有行；
  G2 件一致：证明文件存在且其 git blob 与 bundle 所载 blob 逐字节一致；
  G3 机验绿：exit==0 ∧ sorry==0 ∧ jobs 与登记行所载机验实况逐数字一致（链完整性）；
  G4 叙事合规：无断言性禁用措辞（「制度有效」「已生效」「真实世界效果」、
     断言性「绝对安全」（否定语境「不标绝对安全」等在册原文豁免）、外稿井号编号 #N）；
     合成数据（data_origin==SYNTHETIC）之叙事须含 SIMULATED 标；
  G5 基线：parent_commit == 被保护登记簿之 HEAD。

数据性质：本闸门不区分真实/合成数据之「内容」，只执行在册判据；
合成数据之标注义务由 G4 承担（SIMULATED 标缺失即 BLOCK）。
"""

import hashlib
import re

BANNED_SUBSTRINGS = ["制度有效", "制度已生效", "已正式生效", "真实世界效果", "真实世界已验证"]
BANNED_AFFIRMATIVE_ABSOLUTE_SAFETY = re.compile(r"(?<!不标)绝对安全")
BANNED_EXTERNAL_HASH_NUMBER = re.compile(r"#[0-9]+")
JOB_PATTERN = re.compile(r"（([0-9]+) jobs／EXIT=([0-9]+)／sorry=([0-9]+)）")


def git_blob_sha1(content_bytes: bytes) -> str:
    """git blob 哈希（sha1，与 git hash-object 一致）。"""
    header = f"blob {len(content_bytes)}".encode("utf-8") + b"\x00"
    return hashlib.sha1(header + content_bytes).hexdigest()


def parse_registry_rows(matrix_text: str) -> dict:
    """解析登记簿行：{row_id: {claim, file, jobs, exit, sorry}}。"""
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


def gate(bundle: dict, registry_rows: dict, head_sha: str,
         file_reader, banned_substrings=None) -> tuple:
    """支三闸门。bundle 字段：
      claim_id, narrative, data_origin (REGISTRY/SYNTHETIC),
      evidence: {file, blob, build: {jobs, exit, sorry}, parent_commit}
    返回 (verdict, reasons)；verdict ∈ {ALLOW, BLOCK}；fail-closed。
    file_reader(path)->bytes 或 None（件不存在）。
    """
    bs = banned_substrings if banned_substrings is not None else BANNED_SUBSTRINGS
    reasons = []
    ev = bundle.get("evidence") or {}
    row = registry_rows.get(bundle.get("claim_id"))

    # G1 登记
    if row is None:
        reasons.append("G1_UNREGISTERED")
    else:
        # G3 机验绿（对照登记行所载机验实况）
        b = ev.get("build") or {}
        if not (b.get("exit") == 0 and b.get("sorry") == 0):
            reasons.append("G3_BUILD_NOT_GREEN")
        elif not (b.get("jobs") == row["jobs"] and row["exit"] == 0 and row["sorry"] == 0):
            reasons.append("G3_JOB_CHAIN_MISMATCH")
        # G2 件一致
        path = ev.get("file")
        content = file_reader(path) if path else None
        if content is None:
            reasons.append("G2_FILE_MISSING")
        else:
            actual_blob = git_blob_sha1(content)
            if actual_blob != ev.get("blob"):
                reasons.append("G2_BLOB_MISMATCH")
        # G5 基线
        if ev.get("parent_commit") != head_sha:
            reasons.append("G5_PARENT_NOT_HEAD")

    # G4 叙事合规（无论登记与否，叙事永远受检）
    text = bundle.get("narrative") or ""
    for t in bs:
        if t in text:
            reasons.append(f"G4_BANNED_TERM:{t}")
    if BANNED_AFFIRMATIVE_ABSOLUTE_SAFETY.search(text):
        reasons.append("G4_BANNED_TERM:绝对安全(断言性)")
    if BANNED_EXTERNAL_HASH_NUMBER.search(text):
        reasons.append("G4_EXTERNAL_HASH_NUMBER")
    if bundle.get("data_origin") == "SYNTHETIC" and "SIMULATED" not in text:
        reasons.append("G4_SIMULATED_LABEL_MISSING")

    verdict = "BLOCK" if reasons else "ALLOW"
    return verdict, reasons
