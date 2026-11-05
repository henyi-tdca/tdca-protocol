# -*- coding: utf-8 -*-
"""TDCA 通用校准器（tdca-calibrator v1.0）。

自研件：按使用者声明之参数集做经验校准。参数名／值域／单位皆由使用者输入给定，
本器不硬编码任何特定参数。

三条铁律（⛔ 通融）：
1. 三件输入缺一拒跑：参数声明＋判据声明＋样本（含来源标注与缺失值口径），缺任一件
   明示缺哪件并退出码 2，⛔ 取默认值。
2. 四件输出齐：校准值＋误差带／拟合质量读数＋未达声明判据之说明＋运行元信息；
   质量不足⛔ 只给数不给限（误差带不可得时如实标 null 并说明）。
3. 失败面四类如实报：不收敛／样本不足／参数不可识别／输入自相矛盾，⛔ 择一执行。

退出码：0 校准完成（判据达成与否都如实写进输出）；2 拒跑／读数不可得；1 自检失败。
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import random

VERSION = "1.0"

# ───────────────────────── 输入模型 ─────────────────────────

class Refuse(Exception):
    """拒跑：缺件或矛盾，exit 2。"""
    def __init__(self, kind, detail):
        self.kind = kind          # missing_input | contradiction
        self.detail = detail

class Failure(Exception):
    """四类失败面，如实报。"""
    def __init__(self, kind, detail):
        self.kind = kind          # not_converged | insufficient_samples | unidentifiable | contradiction
        self.detail = detail


def _require(cond, kind, detail):
    if not cond:
        raise Refuse(kind, detail)


def load_inputs(params_json, criteria_json, samples_json):
    """三件输入载入与结构校验。缺一即 Refuse（missing_input）。"""
    missing = [n for n, p in (("参数声明", params_json), ("判据声明", criteria_json), ("样本", samples_json)) if p is None]
    if missing:
        raise Refuse("missing_input", "缺输入：" + "、".join(missing))
    try:
        P = json.loads(params_json)
    except Exception as e:
        raise Refuse("missing_input", f"参数声明非合法 JSON：{e}")
    try:
        C = json.loads(criteria_json)
    except Exception as e:
        raise Refuse("missing_input", f"判据声明非合法 JSON：{e}")
    try:
        S = json.loads(samples_json)
    except Exception as e:
        raise Refuse("missing_input", f"样本非合法 JSON：{e}")

    # 参数声明：名／值域／单位／初值
    _require(isinstance(P, dict) and isinstance(P.get("parameters"), list) and P["parameters"],
             "missing_input", "参数声明须含非空 parameters 列表")
    seen = set()
    for p in P["parameters"]:
        for k in ("name", "min", "max", "unit", "initial"):
            _require(k in p, "missing_input", f"参数 {p.get('name','?')} 缺字段 {k}")
        _require(p["name"] not in seen, "contradiction", f"参数名重复：{p['name']}")
        seen.add(p["name"])
        _require(isinstance(p["min"], (int, float)) and isinstance(p["max"], (int, float)),
                 "contradiction", f"参数 {p['name']} 值域非数值")
        _require(p["min"] < p["max"], "contradiction",
                 f"参数 {p['name']} 值域矛盾：min {p['min']} ≥ max {p['max']}")
        _require(isinstance(p["initial"], (int, float)), "contradiction",
                 f"参数 {p['name']} 初值非数值")
        _require(p["min"] <= p["initial"] <= p["max"], "contradiction",
                 f"参数 {p['name']} 初值 {p['initial']} 越出声明值域 [{p['min']}, {p['max']}]")

    # 判据声明：收敛或误差带 ＋ 迭代或耗时上限（至少各一）
    has_conv = ("max_rmse" in C) or ("max_error_band" in C)
    has_cap = ("max_iterations" in C) or ("max_seconds" in C)
    _require(has_conv, "missing_input", "判据声明缺收敛判据（max_rmse 或 max_error_band 至少其一）")
    _require(has_cap, "missing_input", "判据声明缺上限（max_iterations 或 max_seconds 至少其一）")
    if "max_iterations" in C:
        _require(isinstance(C["max_iterations"], int) and C["max_iterations"] > 0,
                 "contradiction", "max_iterations 须为正整数")
    if "max_seconds" in C:
        _require(C["max_seconds"] > 0, "contradiction", "max_seconds 须为正数")
    if "max_rmse" in C:
        _require(C["max_rmse"] > 0, "contradiction", "max_rmse 须为正数")
    if "max_error_band" in C:
        _require(C["max_error_band"] > 0, "contradiction", "max_error_band 须为正数")

    # 样本：样本量＋来源标注＋缺失值口径；每个观测须有目标 y；
    # 协变量（如 x／温度等）为观测自身字段，由模型表达式引用，不强制逐参数读数。
    _require(isinstance(S, dict), "missing_input", "样本须为对象")
    src = S.get("source")
    _require(src in ("real", "synthetic", "simulated"), "missing_input",
             "样本缺来源标注 source（real／synthetic／simulated 三者其一）")
    _require("missing_policy" in S, "missing_input",
             "样本缺缺失值口径 missing_policy（如 reject／skip_mean）")
    obs = S.get("observations")
    _require(isinstance(obs, list) and obs, "missing_input", "样本须含非空 observations 列表")
    for i, o in enumerate(obs):
        _require(isinstance(o, dict), "missing_input", f"第 {i} 个观测非对象")
        _require("y" in o, "insufficient_samples", f"第 {i} 个观测缺目标 y")
    return P, C, S


# ───────────────────────── 模型与目标 ─────────────────────────

def build_model(P, model_expr):
    """model_expr：以参数名与观测字段为变元的 Python 表达式（eval 受限命名空间）。
    参数名取校准值 theta；其余名字符（x、温度等）取自观测字段。"""
    names = [p["name"] for p in P["parameters"]]
    if not model_expr:
        return None
    code = compile(model_expr, "<model>", "eval")
    def f(obs, theta):
        env = {k: v for k, v in obs.items() if k != "y"}
        env.update(dict(zip(names, theta)))
        env.update({"exp": math.exp, "log": math.log, "sqrt": math.sqrt,
                    "sin": math.sin, "cos": math.cos, "pi": math.pi})
        return eval(code, {"__builtins__": {}}, env)
    return f


def residuals(f, theta, obs):
    if f is None:
        mean_y = sum(o["y"] for o in obs) / len(obs)
        return [o["y"] - mean_y for o in obs]
    return [o["y"] - f(o, theta) for o in obs]


# ───────────────────────── 校准主体 ─────────────────────────

def calibrate(params_json, criteria_json, samples_json, model_expr=None, seed=20261106):
    """主入口：四输出 dict；失败面以 Failure 抛出；拒跑以 Refuse 抛出。"""
    t0 = time.time()
    P, C, S = load_inputs(params_json, criteria_json, samples_json)
    obs = S["observations"]
    n = len(obs)
    k = len(P["parameters"])
    in_hash = hashlib.sha256(
        (params_json + "|" + criteria_json + "|" + samples_json).encode("utf-8")
    ).hexdigest()[:16]

    meta = {
        "tool": "tdca-calibrator",
        "version": VERSION,
        "input_summary_sha256_16": in_hash,
        "sample_source": S["source"],
        "missing_policy": S["missing_policy"],
        "n_samples": n,
        "n_parameters": k,
        "seed": seed,
    }

    # 失败面①：输入自相矛盾（值域／初值／判据已在载入核过，此处核样本量与模型需求）
    # 失败面②：样本不足（n < k+1 且无重复性信息 ⟹ 自由度不足）
    if n < k + 1:
        raise Failure("insufficient_samples",
                      f"样本量 {n} 不足以定 {k} 个参数（至少需 {k+1}，建议 ≥ {2*(k+1)}）："
                      f"每参数至少两个不同读数方可估误差带")

    # 无模型表达式 ⟹ 参数→目标映射不可得：输入自相矛盾（⛔ 择一执行／⛔ 空跑）
    if not model_expr:
        raise Failure("contradiction",
                      "未给模型表达式（model_expr）：无法建立参数到目标的映射，"
                      "请补 model.txt（以参数名与 x 为变元的表达式）")

    f = build_model(P, model_expr)

    # 随机采样校准：值域内均匀采样＋初值邻域，取残差平方和最小者
    rng = random.Random(seed)
    max_iter = C.get("max_iterations", 100000)
    max_sec = C.get("max_seconds", 30.0)
    best = None
    it = 0
    while it < max_iter and time.time() - t0 < max_sec:
        it += 1
        if it == 1:
            theta = [p["initial"] for p in P["parameters"]]
        else:
            theta = [rng.uniform(p["min"], p["max"]) for p in P["parameters"]]
        ss = 0.0
        for o in obs:
            try:
                pred = f(o, theta)
            except (OverflowError, ValueError, ZeroDivisionError):
                ss = float("inf"); break
            ss += (o["y"] - pred) ** 2
        if best is None or ss < best[0]:
            best = (ss, list(theta))

    # 局部细化：坐标轮询减半步长（ deterministic，种子无关 ），把随机初值的近优解磨到位
    ss, theta = best
    steps = [(p["max"] - p["min"]) / 4.0 for p in P["parameters"]]
    def _ss(th):
        s = 0.0
        for o in obs:
            try:
                s += (o["y"] - f(o, th)) ** 2
            except (OverflowError, ValueError, ZeroDivisionError):
                return float("inf")
        return s
    for _round in range(60):
        improved = False
        for j in range(k):
            for direction in (1.0, -1.0):
                th2 = list(theta); th2[j] += direction * steps[j]
                if th2[j] < P["parameters"][j]["min"] or th2[j] > P["parameters"][j]["max"]:
                    continue
                s2 = _ss(th2)
                if s2 < ss:
                    ss, theta = s2, th2
                    improved = True
        if not improved:
            steps = [s / 2.0 for s in steps]
            if max(steps) < 1e-10:
                break
    it += 60
    meta["iterations"] = it
    meta["seconds"] = round(time.time() - t0, 6)

    rmse = math.sqrt(ss / n)
    res = []
    names = [p["name"] for p in P["parameters"]]
    for o in obs:
        pred = f(o, theta)
        res.append(o["y"] - pred)

    # 误差带：残差标准误 × 1.96（大样本近正态）；覆盖度与异常点
    dof = max(n - k, 1)
    var = sum(r * r for r in res) / dof
    resid_std = math.sqrt(var)
    band = 1.96 * resid_std / math.sqrt(n) if n > k else None
    mean_abs = sum(abs(r) for r in res) / n
    within = sum(1 for r in res if abs(r) <= 1.96 * resid_std) if resid_std > 0 else n
    coverage = within / n
    outliers = [i for i, r in enumerate(res) if resid_std > 0 and abs(r) > 3 * resid_std]

    quality = {
        "rmse": round(rmse, 10),
        "residual_std": round(resid_std, 10),
        "mean_abs_residual": round(mean_abs, 10),
        "sample_coverage": round(coverage, 4),
        "outlier_count": len(outliers),
        "outlier_indices": outliers,
        "dof": dof,
    }

    # 判据达成核算
    unmet = []
    if "max_rmse" in C and rmse > C["max_rmse"]:
        unmet.append(f"max_rmse：声明 {C['max_rmse']}，实测 RMSE {round(rmse,6)}")
    if "max_error_band" in C and (band is None or band > C["max_error_band"]):
        unmet.append(f"max_error_band：声明 {C['max_error_band']}，实测误差带 "
                     f"{band if band is not None else '不可得'}")

    # 失败面③：不收敛（用尽上限仍未达声明判据）
    if unmet and it >= max_iter:
        raise Failure("not_converged",
                      f"迭代上限 {max_iter} 用尽仍不达判据；" + "；".join(unmet))

    # 失败面④：参数不可识别（Jacobian 敏感度近零 ⟹ 该参数对 y 无影响）
    eps = 1e-6
    weak = []
    base_pred = [f(o, theta) for o in obs]
    for j, p in enumerate(P["parameters"]):
        t2 = list(theta); t2[j] += eps
        try:
            d = [abs(f(o, t2) - bp) for o, bp in zip(obs, base_pred)]
        except Exception:
            d = [0.0]
        sens = max(d) / eps if d else 0.0
        if sens < 1e-8:
            weak.append(p["name"])
    ident = {"weak_parameters": weak}
    if weak:
        raise Failure("unidentifiable",
                      "可疑参数组（对目标无敏感度，疑不可识别）：" + "、".join(weak))

    return {
        "calibrated_values": {name: round(v, 10) for name, v in zip(names, theta)},
        "error_band_95": round(band, 10) if band is not None else None,
        "fit_quality": quality,
        "unmet_criteria": unmet,
        "criteria_met": not unmet,
        "run_meta": meta,
    }


def main(argv):
    if len(argv) < 4:
        print("[REFUSE] missing_input：用法 calibrator.py <params.json> <criteria.json> <samples.json> [model.txt]")
        return 2
    try:
        params = open(argv[1], encoding="utf-8").read()
        criteria = open(argv[2], encoding="utf-8").read()
        samples = open(argv[3], encoding="utf-8").read()
        model = open(argv[4], encoding="utf-8").read().strip() if len(argv) > 4 else None
    except OSError as e:
        print(f"[REFUSE] missing_input：文件不可读：{e}")
        return 2
    try:
        out = calibrate(params, criteria, samples, model)
    except Refuse as r:
        print(f"[REFUSE] {r.kind}：{r.detail}")
        return 2
    except Failure as f_:
        # 退出码口径：1 有差（校准未成／未收敛／不可识别）；2 读数不可得
        # （输入矛盾／样本不足，读数给不出）。
        print(f"[FAIL] {f_.kind}：{f_.detail}")
        if f_.kind in ("not_converged", "unidentifiable"):
            return 1
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
