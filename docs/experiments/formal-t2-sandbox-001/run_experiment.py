"""TDCA 沙盒实验 T2 · 支三实验跑法脚本（run_experiment.py）

职责：从在册登记簿取数（C-14~C-30，来源可溯），构造 26 个升盒申请包
（正例 18：在册 17＋合成合法 1；负例 7；扰动 1），逐一过闸门（gate.py），
输出确定性结果（无时间戳；同一输入两次运行输出逐字节一致）。

退出码语义：0＝全绿（误伤 0 且失守 0）；非 0＝失守（误伤>0 或 负例/扰动放行）。

数据性质：在册 17 正例之证据＝在册事实（REGISTRY，非合成数据）；
其余申请包之构造内容均为合成数据（SYNTHETIC，叙事含 SIMULATED 标）。
本脚本为新建件，不改动任何既有脚本。
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MATRIX_REL = os.path.join("core-go", "docs", "formal-proofs", "CLAIMS-MATRIX.md")
PROOFS_PREFIX = os.path.join("core-go", "docs", "formal-proofs")

sys.path.insert(0, HERE)
from gate import gate, git_blob_sha1, parse_registry_rows  # noqa: E402

ROW_IDS = [f"C-{n}" for n in range(14, 31)]  # C-14 ~ C-30（T1 全批登记行）
FIXTURE_MATRIX = os.path.join(HERE, "fixtures", "CLAIMS-MATRIX-SIMULATED.fixture.md")
SIM_FILE_REL = os.path.join("docs", "experiments", "formal-t2-sandbox-001",
                            "fixtures", "SimClaim.lean")


def read_bytes(path):
    if not path:
        return None
    full = os.path.join(REPO_ROOT, path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        return f.read()


def resolve_proof_file(file_field):
    return os.path.join(PROOFS_PREFIX, *file_field.split("/"))


def head_sha():
    out = subprocess.run(
        ["git", "rev-parse", "atomgit/main"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def build_bundles():
    with open(os.path.join(REPO_ROOT, MATRIX_REL), encoding="utf-8") as f:
        real_rows = parse_registry_rows(f.read())
    with open(FIXTURE_MATRIX, encoding="utf-8") as f:
        sim_rows = parse_registry_rows(f.read())

    h = head_sha()
    bundles = []

    # C-18 之证明文件字段为「同上（Guard.lean）」、机验字段为「同上」、C-22 为
    # 「P7FiveAll.lean（引用 M-3／M-4）」——均在册原文如此；
    # 依登记簿顺序承接前行之文件与机验字段（在册「同上」语义），并剥离文件字段之括注。
    last_file, last_verify = None, (None, None, None)
    for rid in ROW_IDS:
        row = real_rows[rid]
        row["file"] = re.sub(r"（[^）]*）\s*$", "", row["file"]).strip()
        if row["file"].startswith("同上"):
            row["file"] = last_file
        if row["jobs"] is None:  # 机验字段「同上」：承接前行（jobs, exit, sorry）
            row["jobs"], row["exit"], row["sorry"] = last_verify
        last_file = row["file"]
        last_verify = (row["jobs"], row["exit"], row["sorry"])

    # —— 正例 P1：在册 17 行（T1 全批；证据为在册事实）——
    for rid in ROW_IDS:
        row = real_rows[rid]
        path = resolve_proof_file(row["file"])
        content = read_bytes(path)
        assert content is not None, f"missing proof file: {path}"
        bundles.append({
            "case_id": f"P1-{rid}", "branch": "POSITIVE_REGISTRY",
            "claim_id": rid, "data_origin": "REGISTRY",
            "narrative": row["claim"],
            "evidence": {
                "file": path,
                "blob": git_blob_sha1(content),
                "build": {"jobs": row["jobs"], "exit": row["exit"], "sorry": row["sorry"]},
                "parent_commit": h,
            },
            "registry": "REAL",
            "expected": "ALLOW",
        })

    # —— 正例 P2：合成合法用例（SIMULATED；夹具登记簿）——
    sim_path = SIM_FILE_REL.replace("\\", "/")
    sim_content = read_bytes(sim_path)
    sim_row = sim_rows["C-SIM-1"]
    bundles.append({
        "case_id": "P2-C-SIM-1", "branch": "POSITIVE_SYNTHETIC",
        "claim_id": "C-SIM-1", "data_origin": "SYNTHETIC",
        "narrative": sim_row["claim"] + "（SIMULATED）",
        "evidence": {
            "file": sim_path,
            "blob": git_blob_sha1(sim_content),
            "build": {"jobs": sim_row["jobs"], "exit": sim_row["exit"], "sorry": sim_row["sorry"]},
            "parent_commit": h,
        },
        "registry": "FIXTURE",
        "expected": "ALLOW",
    })

    # —— 负例（构造内容均为合成数据）——
    base = bundles[16]  # C-30 CoordLoop 之合法包（作负例改造基底）

    # 负例之叙事沿用基底在册原文（REGISTRY 文本），故 data_origin=REGISTRY——
    # 攻击构造体现在证据字段与 claim_id 之变异，不在叙事文本；
    # 如此 G4 之 SIMULATED 标义务不干扰各负例分支之检查项隔离。
    def neg(case_id, mutate, narrative=None, claim_id=None, data_origin="REGISTRY"):
        import copy
        b = copy.deepcopy(base)
        b.update({"case_id": case_id, "branch": "NEGATIVE", "expected": "BLOCK",
                  "registry": "REAL", "data_origin": data_origin,
                  "claim_id": claim_id or b["claim_id"]})
        if narrative is not None:
            b["narrative"] = narrative
        mutate(b)
        bundles.append(b)

    # N1 裸叙事：无证据、未登记
    neg("N1-BARE-NARRATIVE", lambda b: b.update({"claim_id": "C-31", "evidence": {}}))
    # N2 伪·件不存在：登记行在，文件路径指向不存在件
    neg("N2-FILE-MISSING", lambda b: b["evidence"].update({"file": PROOFS_PREFIX.replace("\\", "/") + "/lean-tdca/TDCA/NotExist.lean"}))
    # N3 伪·blob 篡改：件真实、所载 blob 被改
    neg("N3-BLOB-TAMPERED", lambda b: b["evidence"].update({"blob": "0" * 64}))
    # N4 伪·机验失守：exit 非 0（构建失败之叙事）
    neg("N4-BUILD-NOT-GREEN", lambda b: b["evidence"]["build"].update({"exit": 1}))
    # N5 伪·未登记：件与 blob 皆真，登记簿无此行
    neg("N5-UNREGISTERED", lambda b: b.update({"claim_id": "C-31"}))
    # N6 伪·叙事越界：证据全真，叙事含断言性禁用措辞与外稿井号编号
    neg("N6-NARRATIVE-VIOLATION",
        lambda b: None,
        narrative=base["narrative"] + "（本件已证制度有效、绝对安全，真实世界效果已验证 #42）")
    # N7 伪·基线错位：父提交非 HEAD
    neg("N7-PARENT-NOT-HEAD", lambda b: b["evidence"].update({"parent_commit": "f" * 40}))
    # D1 扰动档（声明 1 档：链完整性 off-by-one，jobs −1 之陈旧数据）
    neg("D1-JOB-CHAIN-OFFBYONE", lambda b: b["evidence"]["build"].update({"jobs": b["evidence"]["build"]["jobs"] - 1}))
    bundles[-1]["branch"] = "PERTURBATION"

    return bundles, real_rows, sim_rows, h


def main():
    bundles, real_rows, sim_rows, h = build_bundles()
    registries = {"REAL": real_rows, "FIXTURE": sim_rows}

    lines = []
    lines.append("T2-SANDBOX-EXP v1 | head=" + h)
    stats = {"total": 0, "false_positive": 0, "breach": 0}
    for b in bundles:
        verdict, reasons = gate(b, registries[b["registry"]], h, read_bytes)
        ok = (verdict == b["expected"])
        if b["expected"] == "ALLOW" and verdict != "ALLOW":
            stats["false_positive"] += 1
        if b["expected"] == "BLOCK" and verdict != "BLOCK":
            stats["breach"] += 1
        stats["total"] += 1
        lines.append(f"{b['case_id']} | {b['branch']} | expected={b['expected']} "
                     f"| verdict={verdict} | reasons={','.join(reasons) if reasons else '-'} "
                     f"| {'OK' if ok else 'MISMATCH'}")
    lines.append(f"SUMMARY | total={stats['total']} false_positive={stats['false_positive']} "
                 f"breach={stats['breach']}")
    out = "\n".join(lines) + "\n"
    sys.stdout.write(out)

    # 机器可读结果（确定性）
    result = {
        "head": h,
        "stats": stats,
        "cases": [
            {"case_id": b["case_id"], "branch": b["branch"], "expected": b["expected"],
             "verdict": gate(b, registries[b["registry"]], h, read_bytes)[0],
             "reasons": gate(b, registries[b["registry"]], h, read_bytes)[1]}
            for b in bundles
        ],
    }
    with open(os.path.join(HERE, "results", "last_run.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    return 0 if (stats["false_positive"] == 0 and stats["breach"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
