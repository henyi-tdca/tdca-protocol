# -*- coding: utf-8 -*-
# FC-ID: TDCA-FC-GATE-X1-001 | X-1 A级六条守卫包 · pytest 包装（挂法①）
# 依据: TDCA-HANDOFF-EXEC-L1SI168-X1GUARD-001 §二（写法照原令代码块，一字不改）
#       ＋ TDCA-AMEND-L1SI169-X1GUARD-001（实体取件夹补投·判定式与退出码零改）
import subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
def test_x1_guard():
    r = subprocess.run([sys.executable, str(ROOT / "tools/tdca_x1_guard_v1.py"),
                        str(ROOT / "tools/fixtures/x1-samples"),
                        "--strict"],
                       capture_output=True, text=True)
    print(r.stdout)
    assert r.returncode == 0, "X1-GUARD=RED"
