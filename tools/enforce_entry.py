#!/usr/bin/env python3
# FC-ID: TDCA-ENFORCE-ENTRY-SPEC-001 | OPC S0 准入自检与 NCA 生成器
# 约束矩阵: 只读校验（--check/--verify 不改既有 NCA）；--new 只新建草稿；
#           无网络依赖；全部输出含 [SIMULATED] 声明（ID92）；NSFL 负空间熔断绝不静默通过
"""TDCA 五元协作开源社区 · 准入 NCA 自检工具（L1 缔约者）

用法:
  python enforce_entry.py --new                  # 交互生成准入 NCA 草稿
  python enforce_entry.py --check <file.yaml>    # 校验准入 NCA（R1~R10 全过才 PASS）
  python enforce_entry.py --verify               # nca-archives/ 全链连续性校验
  python enforce_entry.py --list                 # 列出当前 L1 缔约者

制度锚定: TDCA-OPC-COMMUNITY-001 + TDCA-ADMIT-TEMPLATE-001 + NSFL-V0.2
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[SIMULATED] 缺少依赖 pyyaml：pip install pyyaml", file=sys.stderr)
    sys.exit(2)

_ROOT = Path(__file__).resolve().parent.parent
ARCHIVES = _ROOT / "nca-archives"
NSFL_LOG = ARCHIVES / ".nsfl-log"

ID_RE = re.compile(r"^TDCA-ADMIT-(\d{8})-(\d{3})$")
NSFL_FORBIDDEN = ["发币", "代币", "公售", "分红承诺", "承诺分红", "DAO 公售",
                  "拉踩", "token sale", "airdrop"]
NSFL_REQUIRED_HINTS = ["不发币", "不承诺分红", "不代币化", "负空间"]
# R10 行级否定豁免：禁词若出现在含否定标记（不/禁/勿/杜绝/反对/拒绝）的行内且否定标记
# 位于禁词之前，视为红线声明（如「不发币」）而非违规提议。豁免是行级粗粒度——
# 熔断日志供守门人复核，宁可误报不可漏报，但法定红线自述不得误伤（否则任何合规准入都过不了）。
NSFL_NEGATION = ("不", "禁", "勿", "杜绝", "反对", "拒绝")


def _load(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"__parse_error__": str(e)}


def _nsfl_fuse(nca_id: str, reason: str):
    """负空间熔断日志（供守门人复核）。"""
    NSFL_LOG.mkdir(parents=True, exist_ok=True)
    entry = (f"[SIMULATED] {datetime.now(timezone.utc).isoformat()} | "
             f"{nca_id} | {reason}\n")
    with (NSFL_LOG / "fuse.log").open("a", encoding="utf-8") as f:
        f.write(entry)


# ---- R1~R10 校验规则（独立函数，便于测试与审查）----

def r1_structure(doc) -> list:
    errs = []
    if not isinstance(doc, dict) or "__parse_error__" in doc:
        return [f"R1 YAML 不可解析: {doc.get('__parse_error__', '非字典结构')}"]
    for k in ("NCA-ID", "Operation-Type", "Operator", "Timestamp", "Scope",
              "Contractor", "Base-Protocol-Acceptance", "Red-Lines-Acknowledged",
              "Provenance", "Human-Signature"):
        if k not in doc:
            errs.append(f"R1 缺顶层字段: {k}")
    return errs


def r2_id(doc, existing_ids: set) -> list:
    nid = str(doc.get("NCA-ID", ""))
    m = ID_RE.match(nid)
    if not m:
        return [f"R2 编号格式错误（须 TDCA-ADMIT-YYYYMMDD-NNN）: {nid}"]
    try:
        datetime.strptime(m.group(1), "%Y%m%d")
    except ValueError:
        return [f"R2 日期段非法: {m.group(1)}"]
    if nid in existing_ids:
        return [f"R2 序号冲突（库内已存在）: {nid}"]
    return []


def r3_type(doc) -> list:
    return [] if doc.get("Operation-Type") == "AdmissionNCA" else \
        [f"R3 Operation-Type 须为 AdmissionNCA: {doc.get('Operation-Type')}"]


def r4_identity(doc) -> list:
    c = doc.get("Contractor") or {}
    gid, op = str(c.get("GitHub-ID", "")).strip(), str(doc.get("Operator", "")).strip()
    if not gid:
        return ["R4 Contractor.GitHub-ID 为空"]
    # Operator 允许带中文备注后缀，取首个 token 比对
    if not op or op.split()[0].split("（")[0] != gid:
        return [f"R4 GitHub-ID({gid}) 与 Operator({op}) 不一致"]
    return []


def r5_base_protocol(doc) -> list:
    bpa = doc.get("Base-Protocol-Acceptance")
    if not isinstance(bpa, dict) or not isinstance(bpa.get("Accepted"), bool):
        return ["R5 Base-Protocol-Acceptance 结构不合（须含 Accepted: true/false）"]
    items = [k for k in bpa if k != "Accepted"]
    if len(items) < 4:
        return [f"R5 基协议须四项全列（当前 {len(items)} 项）"]
    return [] if bpa["Accepted"] is True else ["R5 基协议未全部接受（Accepted != true）"]


def r6_red_lines(doc) -> list:
    rl = doc.get("Red-Lines-Acknowledged")
    if not rl:
        return ["R6 红线清单为空"]
    text = " ".join(str(x) for x in rl)
    if not any(h in text for h in NSFL_REQUIRED_HINTS):
        return ["R6 红线清单未包含 NSFL 负空间条款（不发币/不承诺分红/不代币化）"]
    return []


def r7_provenance(doc) -> list:
    p = (doc.get("Provenance") or {}).get("Status")
    return [] if p == "Simulated" else \
        [f"R7 Provenance.Status 须为 Simulated（真实态缔约未开放）: {p}"]


def r8_signature(doc) -> list:
    sig = doc.get("Human-Signature") or {}
    gid = str((doc.get("Contractor") or {}).get("GitHub-ID", "")).strip()
    if sig.get("Status") != "Signed":
        return [f"R8 Human-Signature.Status 须为 Signed: {sig.get('Status')}"]
    if str(sig.get("Signed-By", "")).strip() != gid:
        return [f"R8 Signed-By({sig.get('Signed-By')}) 非本人({gid})——自签署，不可代签"]
    return []


def scan_nsfl_text(text: str) -> list:
    """NSFL 禁词行级扫描（否定语境豁免）。供 enforce_entry R10 与 mcp_bridge 熔断复用。"""
    hits = set()
    for line in text.splitlines():
        for w in NSFL_FORBIDDEN:
            start = 0
            while True:
                i = line.find(w, start)
                if i < 0:
                    break
                if not any(n in line[:i] for n in NSFL_NEGATION):
                    hits.add(w)
                start = i + len(w)
    return sorted(hits)


def r10_nsfl_scan(path: Path, doc) -> list:
    text = path.read_text(encoding="utf-8")
    hits = scan_nsfl_text(text)
    if hits:
        _nsfl_fuse(str(doc.get("NCA-ID", "?")), f"R10 禁止项命中: {hits}")
        return [f"R10 内容含 NSFL 禁止项 {hits}（负空间熔断已落日志）"]
    return []


def check_file(path: Path, existing_ids: set = None) -> tuple:
    """单文件全规则校验。返回 (ok, [原因清单])。R9（哈希一致性）为 WARN 不阻断。"""
    doc = _load(path)
    existing_ids = existing_ids or set()
    reasons = []
    for fn in (r1_structure, r3_type, r4_identity, r5_base_protocol,
               r6_red_lines, r7_provenance, r8_signature):
        reasons += fn(doc)
    if isinstance(doc, dict) and "__parse_error__" not in doc:
        reasons += r2_id(doc, existing_ids)
        reasons += r10_nsfl_scan(path, doc)
    return (not reasons, reasons)


# ---- 链校验 / 列表 / 生成 ----

def _archive_files() -> list:
    if not ARCHIVES.is_dir():
        return []
    return sorted(p for p in ARCHIVES.glob("TDCA-ADMIT-*.yaml"))


def verify_chain() -> tuple:
    """序号连续性 + 时间戳单调（轻量口径：本链无哈希字段时只验序号与时间）。"""
    files = _archive_files()
    if not files:
        return True, ["（空档案库，无链可验）"]
    errs, seen, prev_ts = [], set(), None
    seqs = []
    for p in files:
        doc = _load(p)
        nid = str(doc.get("NCA-ID", "")) if isinstance(doc, dict) else ""
        m = ID_RE.match(nid)
        if not m:
            errs.append(f"{p.name}: 编号非法")
            continue
        seqs.append((m.group(1), int(m.group(2)), p.name))
        if nid in seen:
            errs.append(f"{p.name}: 序号重复 {nid}")
        seen.add(nid)
        ts = str(doc.get("Timestamp", ""))
        if prev_ts and ts < prev_ts:
            errs.append(f"{p.name}: 时间戳倒挂（{ts} < {prev_ts}）")
        prev_ts = ts
    by_date: dict = {}
    for d, s, name in seqs:
        by_date.setdefault(d, []).append(s)
    for d, ss in by_date.items():
        ss.sort()
        if ss != list(range(1, len(ss) + 1)):
            errs.append(f"{d}: 序号断链（现存 {ss}，须 1..{len(ss)} 连续）")
    return (not errs), errs or [f"链校验通过：{len(files)} 条，序号连续、时间戳单调"]


def list_contractors() -> list:
    rows = []
    for p in _archive_files():
        doc = _load(p)
        if isinstance(doc, dict):
            rows.append((str(doc.get("NCA-ID", "?")),
                         str((doc.get("Contractor") or {}).get("GitHub-ID", "?")),
                         str(doc.get("Timestamp", "?"))))
    return rows


def new_draft() -> Path:
    """交互生成准入 NCA 草稿（序号=库内当日最大序号+1）。"""
    gid = input("GitHub ID: ").strip()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    existing = [int(m.group(2)) for p in _archive_files()
                if (m := ID_RE.match(p.stem)) and m.group(1) == today]
    seq = max(existing, default=0) + 1
    nid = f"TDCA-ADMIT-{today}-{seq:03d}"
    now = datetime.now(timezone.utc).isoformat()
    body = f"""# TDCA 五元协作开源社区 · 准入 NCA（L1 缔约者）[SIMULATED]
# 制度锚定: TDCA-OPC-COMMUNITY-001 + TDCA-CONST + NSFL-V0.2
# ID92: 本准入不构成真实配置权执行路径；缔约权利为荣誉凭证，无金钱承诺、不可转让、不可交易
NCA-ID: {nid}
Operation-Type: AdmissionNCA
Operator: {gid}
Timestamp: '{now}'
Scope: 加入 TDCA 五元协作开源社区，成为 L1 缔约者；接受基协议声明；认领任务与参与讨论的权利登记
Contractor:
  GitHub-ID: {gid}
  Legal-Name: ''
  Contact: ''
  Jurisdiction: 中国境内
  Joined-At: '{now}'
Base-Protocol-Acceptance:
  TDCA-CONST: true
  NSFL-V0.2: true
  TDCA-WORKING-SPEC-001: true
  TDCA-OPC-COMMUNITY-001: true
  Accepted: true
Red-Lines-Acknowledged:
  - 不发起/建议任何发币、公售、承诺分红或代币化（NSFL 负空间一票否决）
  - 社区内容涉真实资金/真实税务数据前保持 simulated 标注（ID92）
  - 不拉踩其他协议（MCP/A2A/x402 一律正交/挂载表述）
  - 贡献确权（节点 NCA）为荣誉凭证，无交易属性与收益预期
  - 真实态结算只走 e-CNY 法币轨道，不接稳定币
Provenance:
  Status: Simulated
  Note: 准入自声明；GitHub ID 与提交行为可由仓库 git log 核验
Commit-Ref: ''
Human-Signature:
  Status: Signed
  Signed-By: {gid}
  Signed-At: '{now}'
Negative-Space-Check:
  NSFL-Version: V0.2
  Triggered: false
  Trigger-Reason: null
  Checked-By: enforce_entry.py（准入自检）
"""
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    out = ARCHIVES / f"{nid}.yaml"
    out.write_text(body, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="TDCA 准入 NCA 自检与生成器 [SIMULATED]")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new", action="store_true", help="交互生成准入 NCA 草稿")
    g.add_argument("--check", metavar="FILE", help="校验准入 NCA 文件")
    g.add_argument("--verify", action="store_true", help="nca-archives/ 全链校验")
    g.add_argument("--list", action="store_true", help="列出 L1 缔约者")
    args = ap.parse_args()

    print("[SIMULATED] enforce_entry.py —— 准入校验为工程动作，制度确认归守门人", file=sys.stderr)

    if args.new:
        out = new_draft()
        print(f"草稿已生成: {out}\n下一步: 核对字段后运行 --check {out.name}")
        return 0
    if args.check:
        p = Path(args.check).resolve()  # 归一化为绝对路径，确保自排除比对成立
        if not p.is_file():
            print(f"FAIL: 文件不存在 {p}")
            return 1
        existing = {x.stem for x in _archive_files() if x != p}
        ok, reasons = check_file(p, existing)
        if ok:
            print(f"PASS: {p.name}（R1~R10 全过）")
            return 0
        print(f"FAIL: {p.name}")
        for r in reasons:
            print(f"  - {r}")
        return 1
    if args.verify:
        ok, msgs = verify_chain()
        for m in msgs:
            print(("PASS: " if ok else "FAIL: ") + m if len(msgs) == 1 else f"  - {m}")
        return 0 if ok else 1
    if args.list:
        rows = list_contractors()
        if not rows:
            print("（暂无 L1 缔约者）")
            return 0
        print(f"{'NCA-ID':<26} {'GitHub-ID':<20} Timestamp")
        for nid, gid, ts in rows:
            print(f"{nid:<26} {gid:<20} {ts}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
