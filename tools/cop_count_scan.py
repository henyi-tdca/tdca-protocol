# -*- coding: utf-8 -*-
"""COP 计数实扫脚本（count manifest 生成器）

口径：仅统计 git 跟踪件（git ls-files），不含工作树未跟踪文件。
分类：docs/cop-library/ 下含 COMPOSED- 标识的 yaml 计为「化合」，其余计为「原生」。

用法（仓库根目录）：
    python tools/cop_count_scan.py
退出码：恒 0（纯统计，无门禁）。
"""
import re
import subprocess
import sys
import collections


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True).stdout
    return out.decode("utf-8", errors="replace").splitlines()


def main():
    files = tracked_files()
    cop_yaml = [f for f in files if f.startswith("docs/cop-library/") and f.endswith(".yaml")]
    proto_yaml = [f for f in files if f.startswith("protocols/") and f.endswith(".yaml")]
    chengyu_new = [f for f in cop_yaml if f.startswith("docs/cop-library/chengyu/")]
    chengyu_old = [f for f in files if f.startswith("docs/cognitive-compiler/chengyu/")]

    composed, native = 0, 0
    for f in cop_yaml:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                head = fh.read(800)
        except OSError:
            head = ""
        if re.search(r"COMPOSED-", head):
            composed += 1
        else:
            native += 1

    per_dir = collections.Counter(f.split("/")[2] for f in cop_yaml)

    print("# COP count manifest（实扫口径：git 跟踪件）")
    print("docs/cop-library/**/*.yaml 总数 : %d" % len(cop_yaml))
    print("  原生（无 COMPOSED- 标识）     : %d" % native)
    print("  化合（含 COMPOSED- 标识）     : %d" % composed)
    print("protocols/**/*.yaml 总数        : %d" % len(proto_yaml))
    print("docs/cop-library/chengyu/       : %d" % len(chengyu_new))
    print("docs/cognitive-compiler/chengyu/: %d 文件" % len(chengyu_old))
    print("仓库跟踪件总数                  : %d" % len(files))
    print("\n## docs/cop-library 分家族")
    for k, v in sorted(per_dir.items()):
        print("  %-18s %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
