# -*- coding: utf-8 -*-
"""tdca-calibrator 随包自测。

覆盖：正常校准（合成样本）、三件输入缺一拒跑、四类失败面各一例、可复现双跑。
退出码：0 全部通过；1 有自检项失败（末行 [FAIL] 明细）。
"""
import hashlib
import io
import json
import sys
from contextlib import redirect_stdout

from calibrator import calibrate, Refuse, Failure

CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def run_silent(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = fn(*a, **kw)
    return r, buf.getvalue()


# ── 合成真值：y = 2.0 + 3.0*x + 噪声(固定种子) ──
import random
_rng = random.Random(7)
OBS = [{"x": round(0.2 * i, 3), "y": 2.0 + 3.0 * (0.2 * i) + _rng.uniform(-0.05, 0.05)}
       for i in range(21)]

PARAMS = json.dumps({
    "parameters": [
        {"name": "a", "min": -10.0, "max": 10.0, "unit": "u", "initial": 0.0},
        {"name": "b", "min": -10.0, "max": 10.0, "unit": "u/x", "initial": 1.0},
    ]
}, ensure_ascii=False)
CRITERIA = json.dumps({"max_rmse": 0.2, "max_iterations": 3000, "max_seconds": 20})
SAMPLES = json.dumps({
    "source": "synthetic",
    "missing_policy": "reject",
    "observations": OBS,
}, ensure_ascii=False)
MODEL = "a + b*x"


@case("正常校准：合成线性样本，判据达成，四输出齐")
def t_normal():
    out, _ = run_silent(calibrate, PARAMS, CRITERIA, SAMPLES, MODEL)
    assert out["criteria_met"] is True, out["unmet_criteria"]
    for key in ("calibrated_values", "fit_quality", "run_meta"):
        assert key in out, f"缺输出 {key}"
    assert out["error_band_95"] is not None, "误差带不可得（质量不足只给数不给限——此处应可得）"
    assert abs(out["calibrated_values"]["a"] - 2.0) < 0.15, out["calibrated_values"]
    assert abs(out["calibrated_values"]["b"] - 3.0) < 0.15, out["calibrated_values"]
    q = out["fit_quality"]
    for key in ("rmse", "residual_std", "sample_coverage", "outlier_count"):
        assert key in q, f"fit_quality 缺 {key}"
    return f"a≈{out['calibrated_values']['a']} b≈{out['calibrated_values']['b']} rmse={q['rmse']}"


@case("拒跑：三件输入缺一（缺样本），明示缺哪件")
def t_missing():
    try:
        calibrate(PARAMS, CRITERIA, None, MODEL)
    except Refuse as r:
        assert r.kind == "missing_input" and "样本" in r.detail, r.detail
        return r.detail
    raise AssertionError("未拒跑（缺样本仍执行）——违反铁律一")


@case("失败面②：样本不足（n<k+1），给最小所需量估计")
def t_insufficient():
    bad = json.dumps({"source": "synthetic", "missing_policy": "reject",
                      "observations": OBS[:2]}, ensure_ascii=False)
    try:
        calibrate(PARAMS, CRITERIA, bad, MODEL)
    except Failure as f_:
        assert f_.kind == "insufficient_samples", f_.kind
        assert "至少需 3" in f_.detail, f_.detail
        return f_.detail
    raise AssertionError("样本不足未报")


@case("失败面④：参数不可识别（模型不含参数 b），列可疑参数组")
def t_unidentifiable():
    p3 = json.dumps({"parameters": [
        {"name": "a", "min": -10.0, "max": 10.0, "unit": "u", "initial": 0.0},
        {"name": "b", "min": -10.0, "max": 10.0, "unit": "u", "initial": 0.0},
        {"name": "c", "min": -10.0, "max": 10.0, "unit": "u/x", "initial": 1.0},
    ]}, ensure_ascii=False)
    try:
        calibrate(p3, CRITERIA, SAMPLES, "a + 0*b + c*x")
    except Failure as f_:
        assert f_.kind == "unidentifiable", f_.kind
        assert "b" in f_.detail, f_.detail
        return f_.detail
    raise AssertionError("不可识别未报")


@case("失败面①：不收敛（迭代上限用尽仍不达声明判据）")
def t_not_converged():
    strict = json.dumps({"max_rmse": 1e-9, "max_iterations": 5, "max_seconds": 20})
    try:
        calibrate(PARAMS, strict, SAMPLES, MODEL)
    except Failure as f_:
        assert f_.kind == "not_converged", f_.kind
        assert "max_rmse" in f_.detail, f_.detail
        return f_.detail
    raise AssertionError("不收敛未报")


@case("失败面③：输入自相矛盾（初值越出声明值域），报冲突点")
def t_contradiction():
    badp = json.dumps({"parameters": [
        {"name": "a", "min": 0.0, "max": 1.0, "unit": "u", "initial": 5.0}]})
    try:
        calibrate(badp, CRITERIA, SAMPLES, MODEL)
    except Refuse as r:
        assert r.kind == "contradiction" and "a" in r.detail, r.detail
        return r.detail
    raise AssertionError("矛盾输入未拒跑")


@case("可复现：同输入同版本两次输出哈希一致")
def t_reproducible():
    o1, _ = run_silent(calibrate, PARAMS, CRITERIA, SAMPLES, MODEL)
    o2, _ = run_silent(calibrate, PARAMS, CRITERIA, SAMPLES, MODEL)
    for o in (o1, o2):
        o["run_meta"].pop("seconds", None)   # 耗时为环境读数，非确定性，比对前剔除
    h1 = hashlib.sha256(json.dumps(o1, sort_keys=True).encode()).hexdigest()[:16]
    h2 = hashlib.sha256(json.dumps(o2, sort_keys=True).encode()).hexdigest()[:16]
    assert h1 == h2, f"两次输出不一致 {h1} vs {h2}"
    return f"双跑哈希一致 {h1}"


def main():
    fails = []
    for name, fn in CASES:
        try:
            note = fn()
            print(f"[OK] {name}——{note}")
        except Exception as e:
            fails.append((name, e))
            print(f"[CASE-FAIL] {name}：{e}")
    if fails:
        print(f"[FAIL] {len(fails)} 项自检未过：{[n for n, _ in fails]}")
        return 1
    print(f"[OK] 全部 {len(CASES)} 项自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
