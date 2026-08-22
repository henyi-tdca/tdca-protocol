# FC-ID: TDCA-TASK-CTS-L1-001 | 用例注册表
from . import c1, c2, c3, c4, c5_c6, g

ALL_CASES = c1.CASES + c2.CASES + c3.CASES + c4.CASES + c5_c6.CASES + g.CASES


def run_all(target):
    return [fn(target) for fn in ALL_CASES]
