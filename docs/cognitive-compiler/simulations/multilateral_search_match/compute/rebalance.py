# -*- coding: utf-8 -*-
"""滚动时窗动态再平衡 (搜索比配引擎 v2 升级)
=========================================================
战术 3: 将有限时窗 H 设计为"滚动时窗"。每隔 step 个月, 基于近 step 个月实际业务
贡献数据, 重算夏普利值并生成"夏普利值调整协商通知", 推动联盟分成再协商。

actuals: dict[party_id] -> 实际贡献系数 (0..1.2, 相对承诺值的实现度)。
  None 时给合成演示值 (各主体在 0.7~1.1 间波动), 模拟"某方掉队/某方超预期"。
重算方式: 用实际系数缩放各主体逐维能力 -> 重跑精确夏普利 -> 新旧分成对比 + 通知。
生产环境: actuals 由业务系统/链上指标回灌 (本模块只定义接口与重算机制)。
"""
import types
from .shapley import shapley
from .coalition import coalition_value


def _proxy(c, w, dims):
    return types.SimpleNamespace(
        id=c.id, name=c.name, cop=getattr(c, "cop", ""), batna=c.batna,
        res={d: round(c.res.get(d, 0.0) * w, 3) for d in dims},
    )


def rolling_rebalance(coalition, need, dims, value_base,
                      actuals=None, step_months=3, strength=False,
                      seed=42):
    """返回 {step_months, actuals, old_phi, new_phi, notice, deltas}"""
    if actuals is None:
        import random
        rnd = random.Random(seed)
        actuals = {c.id: round(rnd.uniform(0.7, 1.1), 2) for c in coalition}

    proxies = [_proxy(c, actuals.get(c.id, 1.0), dims) for c in coalition]

    old_phi, mode = shapley(coalition, need, dims, value_base, strength=strength)
    new_phi, _ = shapley(proxies, need, dims, value_base, strength=strength)

    # 新旧对比 + 再协商阈值
    deltas = {}
    renegotiate = []
    for c in coalition:
        o, nw = old_phi[c.id], new_phi[c.id]
        d = round(nw - o, 1)
        deltas[c.id] = {"name": c.name, "old": o, "new": nw, "delta": d}
        # 实际贡献较承诺下滑 >15% -> 触发再协商/补偿
        if actuals.get(c.id, 1.0) < 0.85 and d < 0:
            renegotiate.append(c.name)

    notice = _render_notice(step_months, deltas, renegotiate, actuals)
    return {
        "step_months": step_months,
        "actuals": actuals,
        "old_phi": old_phi,
        "new_phi": new_phi,
        "deltas": deltas,
        "renegotiate": renegotiate,
        "notice": notice,
        "mode": mode,
    }


def _render_notice(step_months, deltas, renegotiate, actuals):
    lines = [
        f"【夏普利值调整协商通知 · 滚动时窗 H={step_months}月】",
        f"基于近 {step_months} 个月实际业务贡献数据重算联盟分成, 各方相对变化:",
    ]
    for cid, d in deltas.items():
        arrow = "↑" if d["delta"] > 0 else ("↓" if d["delta"] < 0 else "→")
        lines.append(f"  - {d['name']}: {d['old']} -> {d['new']} ({arrow}{abs(d['delta'])}) "
                     f"[实际贡献系数 {actuals.get(cid,1.0)}]")
    if renegotiate:
        lines.append(f"⚠ 再协商触发: {', '.join(renegotiate)} 实际贡献较承诺下滑>15%, "
                     f"建议联盟启动分成再协商并经 NCA 修订承诺。")
    else:
        lines.append("✓ 各方贡献均在承诺区间, 无需强制再协商 (可选择性确认)。")
    return "\n".join(lines)
