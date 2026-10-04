# -*- coding: utf-8 -*-
"""产物库 10 子库预检扫描 v2：细化内部编号模式，分离人名／凭据值复核。

命中只报「库／件／类型／行号」，⛔ 不抄原文。
退出码：0＝全零命中；1＝有命中或读件失败。
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ["chengyu", "compositions", "emissary", "engineering-three", "games",
        "hundred_schools", "marxism", "microeconomics", "simulations", "stratagems"]

# 内部运作编号：NCA 确权链 / GSEQ 序列 / 纯数字 NCA 号 / nca 字段
PAT_INTERNAL = [
    (re.compile(r"TDCA-REASONIX-\d{8}-\d+"), "NCA确权链号"),
    (re.compile(r"\bGSEQ-\d+\b"), "GSEQ序列号"),
    (re.compile(r"(?<![A-Z0-9-])NCA-\d{2,}(?![0-9])"), "NCA纯数字号"),
    (re.compile(r"(?i)\b[a-z_]*_?nca\b\s*:"), "nca编号字段"),
]
# 凭据值
PAT_SECRET = [
    (re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), "私钥材料"),
    (re.compile(r"ssh-(rsa|ed25519)\s+[A-Za-z0-9+/=]{20,}"), "SSH公钥材料"),
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[^\s'\"]{6,}"), "凭据赋值样式"),
    (re.compile(r"47\.76\.42\.139|tdca-cloud-deploy|gitee-deploy|TDCA_SITE_GATE_KEY"), "部署面凭据痕迹"),
]
# 拉丁专名（人名疑点，人工复核）
PAT_NAME = [
    (re.compile(r"(?i)\b(reasonix)\b"), "拉丁专名（需人工判定人名/代号）"),
]

PATTERNS = ([(p, k, "内部编号") for p, k in PAT_INTERNAL]
            + [(p, k, "凭据值") for p, k in PAT_SECRET]
            + [(p, k, "人名疑点") for p, k in PAT_NAME])


def tracked():
    out = subprocess.run(["git", "ls-files"], capture_output=True, cwd=ROOT).stdout
    return out.decode("utf-8", errors="replace").splitlines()


def main():
    files = [f for f in tracked() if any(f.startswith(f"docs/cop-library/{d}/") for d in LIBS)]
    print(f"# 预检范围：{len(files)} 件")
    per_lib_hits = {d: {} for d in LIBS}
    unreadable = []
    for f in files:
        lib = f.split("/")[2]
        try:
            text = (ROOT / f).read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError) as e:
            unreadable.append((f, type(e).__name__))
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat, kind, cat in PATTERNS:
                if pat.search(line):
                    per_lib_hits[lib].setdefault(kind, []).append((f, i))
    print("\n## 逐库命中汇总（内部编号／人名／凭据值）")
    total = 0
    for d in LIBS:
        kinds = per_lib_hits[d]
        if not kinds:
            print(f"  {d:18s} 零命中")
            continue
        n = sum(len(v) for v in kinds.values())
        total += n
        print(f"  {d:18s} {n} 处：" + "；".join(f"{k}×{len(v)}" for k, v in kinds.items()))
    print(f"\n## 命中明细（{total} 处）")
    for d in LIBS:
        for kind, rows in per_lib_hits[d].items():
            for f, i in rows:
                print(f"  [{kind}] {f}:{i}")
    print(f"\n## 不可读件：{len(unreadable)}")
    for f, why in unreadable:
        print(f"  {f} ({why})")
    return 1 if total or unreadable else 0


if __name__ == "__main__":
    sys.exit(main())
